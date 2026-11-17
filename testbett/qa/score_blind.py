"""Score the three blind QA conditions and print every aggregate table.

Conditions:
  T  text description of the screen (one file per input)
  C  no input, questions only (guessing baseline)
  I  the PNG images themselves

The per-question judgements below were made by hand against answers.json with the rubric in
ergebnisse/qa_auswertung.md. The script recomputes accuracy per input and category,
calibration (from the blind_answers_*.json confidences) and accuracy per input token.

    python qa/score_blind.py                 # print tables, write out/blind_scores.json
    python qa/score_blind.py --out ../ergebnisse
"""
import argparse
import json
import math
import os

QA = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(QA)

TXT, WID, LAY, ZWIN, CNT, TMP = ("text reading", "widget state", "layout/spatial",
                                 "z-order/window", "counting", "temporal/change")
CATS = [TXT, WID, LAY, ZWIN, CNT, TMP]

# id: (category, score_T, score_C, score_I)
S = {
    "screen1_q01": (ZWIN, 1, 0.5, 1),
    "screen1_q02": (ZWIN, 1, 0.5, 1),
    "screen1_q03": (WID, 1, 1, 1),
    "screen1_q04": (WID, 1, 1, 1),
    "screen1_q05": (TXT, 1, 0, 1),
    "screen1_q06": (TXT, 1, 0, 1),
    "screen1_q07": (WID, 1, 0, 1),
    "screen1_q08": (WID, 1, 0, 1),
    "screen1_q09": (CNT, 1, 0.5, 1),
    "screen1_q10": (LAY, 1, 0, 1),
    "screen1_q11": (TXT, 1, 1, 1),
    "screen1_q12": (LAY, 1, 0.5, 1),
    "screen1_q13": (TXT, 1, 0, 1),
    "screen1_q14": (WID, 1, 0, 1),
    "screen2_q01": (TXT, 0, 0, 1),
    "screen2_q02": (WID, 1, 0, 1),
    "screen2_q03": (TXT, 1, 0, 1),
    "screen2_q04": (WID, 1, 1, 1),
    "screen2_q05": (WID, 1, 1, 1),
    "screen2_q06": (TXT, 0.5, 0, 1),
    "screen2_q07": (LAY, 1, 0, 1),
    "screen2_q08": (TXT, 1, 0, 1),
    "screen2_q09": (LAY, 1, 1, 1),
    "screen2_q10": (TXT, 1, 1, 1),
    "screen2_q11": (TXT, 1, 0.5, 1),
    "screen2_q12": (WID, 0, 1, 1),
    "screen2_q13": (TXT, 1, 0.5, 1),
    "screen3_q01": (TXT, 1, 0, 1),
    "screen3_q02": (WID, 1, 1, 1),
    "screen3_q03": (TXT, 1, 0, 1),
    "screen3_q04": (TXT, 1, 0, 1),
    "screen3_q05": (TXT, 1, 0.5, 1),
    "screen3_q06": (TXT, 1, 0.5, 1),
    "screen3_q07": (WID, 1, 0, 1),
    "screen3_q08": (WID, 1, 1, 1),
    "screen3_q09": (WID, 1, 0.5, 1),
    "screen3_q10": (TXT, 1, 0, 1),
    "screen3_q11": (TXT, 1, 1, 1),
    "screen3_q12": (LAY, 1, 1, 1),
    "screen3_q13": (LAY, 1, 1, 1),
    "screen3_q14": (ZWIN, 1, 0, 1),
    "sequence_workflow_q01": (TMP, 1, 0.5, 1),
    "sequence_workflow_q02": (TMP, 1, 1, 1),
    "sequence_workflow_q03": (TMP, 1, 1, 1),
    "sequence_workflow_q04": (TMP, 1, 0, 1),
    "sequence_workflow_q05": (TMP, 1, 1, 1),
    "sequence_workflow_q06": (TMP, 1, 0.5, 1),
    "sequence_workflow_q07": (TXT, 1, 0.5, 1),
    "sequence_workflow_q08": (TMP, 1, 0, 1),
    "sequence_workflow_q09": (WID, 1, 1, 1),
    "sequence_workflow_q10": (TMP, 1, 0.5, 1),
    "sequence_workflow_q11": (TMP, 1, 1, 1),
    "sequence_workflow_q12": (WID, 1, 1, 1),
    "sequence_workflow_q13": (TMP, 1, 1, 0.5),
    "sequence_workflow_q14": (TMP, 1, 0, 1),
}

# input tokens per condition (T: o200k_base count of the text input; I: frames x tokens per 1080p frame)
T_TOKENS = {"screen1": 816, "screen2": 667, "screen3": 592, "sequence_workflow": 860}
FRAMES = {"screen1": 1, "screen2": 1, "screen3": 1, "sequence_workflow": 40}
IMG_TOKENS_FORMULA = 1844   # 1920x1080 scaled to long edge 1568, w*h/750
IMG_TOKENS_PUBLISHED = 2691  # published per-frame figure for 1080p


def pct(x, n):
    return f"{100 * x / n:.1f}%"


def sign_test(wins, losses):
    """Two-sided exact sign test p-value."""
    n, k = wins + losses, min(wins, losses)
    if n == 0:
        return 1.0
    p = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out"))
    a = ap.parse_args()
    qs = json.load(open(os.path.join(QA, "questions.json")))["questions"]
    conf = {c: json.load(open(os.path.join(QA, f))) for c, f in
            [("T", "blind_answers_text.json"), ("C", "blind_answers_control_noinput.json"),
             ("I", "blind_answers_images.json")]}
    assert [q["id"] for q in qs] == list(S), "question ids out of sync"
    rows = []
    for q in qs:
        cat, t, c, i = S[q["id"]]
        rows.append(dict(id=q["id"], input=q["input"], category=cat, score_T=t, score_C=c, score_I=i,
                         conf_T=conf["T"][q["id"]]["confidence"], conf_C=conf["C"][q["id"]]["confidence"],
                         conf_I=conf["I"][q["id"]]["confidence"]))
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "blind_scores.json"), "w") as f:
        json.dump(rows, f, indent=1, ensure_ascii=False)

    def table(key, groups):
        print(f"| {key} | n | T | C | I | T-C | I-T |\n|---|---|---|---|---|---|---|")
        for g in groups:
            if key == "excluding":
                sel = [r for r in rows if r["id"] != "screen2_q12"]
            else:
                sel = [r for r in rows if g == "all" or r[key] == g]
            n = len(sel)
            t, c, i = (sum(r[f"score_{k}"] for r in sel) for k in "TCI")
            print(f"| {g} | {n} | {t:g} ({pct(t, n)}) | {c:g} ({pct(c, n)}) | {i:g} ({pct(i, n)}) | "
                  f"{100 * (t - c) / n:+.1f} pp | {100 * (i - t) / n:+.1f} pp |")
        print()

    table("input", ["all"] + list(T_TOKENS))
    table("excluding", ["excluding screen2_q12 (theme)"])
    table("category", CATS)

    for x, y in (("T", "C"), ("I", "T")):
        w = sum(r[f"score_{x}"] > r[f"score_{y}"] for r in rows)
        l = sum(r[f"score_{x}"] < r[f"score_{y}"] for r in rows)
        print(f"{x} beats {y} on {w}, {y} beats {x} on {l}; sign test p = {sign_test(w, l):.2g}")
    print()

    print("| condition | n | mean confidence | accuracy | conf - acc | Brier | mean conf on items < 1 |\n"
          "|---|---|---|---|---|---|---|")
    for k in "TCI":
        cs = [r[f"conf_{k}"] for r in rows]
        ss = [r[f"score_{k}"] for r in rows]
        wrong = [c for c, s in zip(cs, ss) if s < 1]
        mc, acc = sum(cs) / len(cs), sum(ss) / len(ss)
        brier = sum((c - s) ** 2 for c, s in zip(cs, ss)) / len(cs)
        mw = f"{sum(wrong) / len(wrong):.2f} (n={len(wrong)})" if wrong else "-"
        print(f"| {k} | {len(cs)} | {mc:.3f} | {acc:.3f} | {mc - acc:+.3f} | {brier:.3f} | {mw} |")
    print()

    n = len(rows)
    tok_T = sum(T_TOKENS.values())
    tok_If = sum(FRAMES[k] * IMG_TOKENS_FORMULA for k in FRAMES)
    tok_Ip = sum(FRAMES[k] * IMG_TOKENS_PUBLISHED for k in FRAMES)
    sT, sC, sI = (sum(r[f"score_{k}"] for r in rows) for k in "TCI")
    print("| condition | input tokens | points | accuracy | points per 1,000 tokens |\n|---|---|---|---|---|")
    for name, tok, s in [("T", tok_T, sT), ("C (no input)", 0, sC),
                         (f"I ({IMG_TOKENS_FORMULA:,}/frame)", tok_If, sI),
                         (f"I ({IMG_TOKENS_PUBLISHED:,}/frame)", tok_Ip, sI)]:
        per = f"{1000 * s / tok:.2f}" if tok else "-"
        print(f"| {name} | {tok:,} | {s:g} | {pct(s, n)} | {per} |")
    print("\n| input | n | T tokens | T points | T pts/1k | I tokens | I points | I pts/1k |\n"
          "|---|---|---|---|---|---|---|---|")
    for inp in T_TOKENS:
        sel = [r for r in rows if r["input"] == inp]
        t, i = sum(r["score_T"] for r in sel), sum(r["score_I"] for r in sel)
        it = FRAMES[inp] * IMG_TOKENS_FORMULA
        print(f"| {inp} | {len(sel)} | {T_TOKENS[inp]} | {t:g} | {1000 * t / T_TOKENS[inp]:.2f} | {it:,} | {i:g} | "
              f"{1000 * i / it:.2f} |")

    print("\nT below 1:", [(r["id"], r["score_T"]) for r in rows if r["score_T"] < 1])
    print("I below 1:", [(r["id"], r["score_I"]) for r in rows if r["score_I"] < 1])


if __name__ == "__main__":
    main()
