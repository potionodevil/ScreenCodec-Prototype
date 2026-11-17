#!/usr/bin/env python3
"""Synthetic GUI generator: test screens with exact ground truth.

Draws 1920x1080 desktops with PIL and writes exact ground truth (element type,
box, text, state) plus every drawn text span as JSON next to each PNG.

Usage:
  python synth_gui.py              # static dev/test/de sets + all sequences
  python synth_gui.py --only seq   # only the animated sequences
"""
import argparse
import copy
import json
import os
import random
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
W, H = 1920, 1080
TASKBAR_H = 48
TB_H = 32  # title bar height
FPS = 2.0

FONT_FILES = {
    "dejavu": ("/usr/share/fonts/TTF/DejaVuSans.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"),
    "liberation": ("/usr/share/fonts/liberation/LiberationSans-Regular.ttf",
                   "/usr/share/fonts/liberation/LiberationSans-Bold.ttf"),
    "noto": ("/usr/share/fonts/noto/NotoSans-Regular.ttf", "/usr/share/fonts/noto/NotoSans-Bold.ttf"),
    "roboto": ("/usr/share/fonts/TTF/Roboto-Regular.ttf", "/usr/share/fonts/TTF/Roboto-Bold.ttf"),
}


@lru_cache(None)
def font(family, size, bold=False):
    return ImageFont.truetype(FONT_FILES[family][1 if bold else 0], size)


def tlen(fam, size, s, bold=False):
    return int(font(fam, size, bold).getlength(s))


LIGHT = dict(name="light", win=(243, 243, 243), text=(28, 28, 28), sub=(100, 100, 100),
             border=(150, 150, 150), field=(255, 255, 255), field_border=(130, 130, 130),
             title_in=(228, 228, 228), title_in_text=(90, 90, 90), btn=(225, 225, 225),
             btn_border=(170, 170, 170), btn_hover=(214, 232, 250), list=(255, 255, 255),
             track=(214, 214, 214), ph=(150, 150, 150), taskbar=(32, 32, 32), taskbar_text=(240, 240, 240),
             toast=(250, 250, 250), shadow=70, thumb=(160, 160, 160))
DARK = dict(name="dark", win=(32, 32, 32), text=(232, 232, 232), sub=(170, 170, 170),
            border=(76, 76, 76), field=(48, 48, 48), field_border=(120, 120, 120),
            title_in=(46, 46, 46), title_in_text=(170, 170, 170), btn=(62, 62, 62),
            btn_border=(96, 96, 96), btn_hover=(80, 80, 80), list=(40, 40, 40), track=(72, 72, 72),
            ph=(128, 128, 128), taskbar=(18, 18, 18), taskbar_text=(240, 240, 240),
            toast=(44, 44, 44), shadow=120, thumb=(110, 110, 110))
ACCENTS = [(0, 103, 192), (38, 99, 173), (16, 124, 16), (118, 77, 173), (196, 43, 28), (0, 120, 140)]
DESK_COLORS = [(0, 84, 147), (28, 60, 90), (60, 40, 90), (20, 90, 80), (90, 90, 100), (130, 60, 40)]

# ----------------------------------------------------------------------------- vocabulary
EN = dict(
    titles=["Settings", "File Explorer", "Mail - Inbox", "Untitled - Notepad", "System Properties",
            "Network Setup", "Backup Manager", "Photo Viewer", "Account", "Printer Options", "Downloads",
            "Project Report - Writer", "Calendar", "Install Wizard", "Preferences", "Media Player",
            "Disk Cleanup", "Sync Status", "New Contact", "Export Data"],
    labels={"Email": ["anna.schmidt@example.com", "info@northwind.io", "ben.ortiz@mail.org"],
            "Full name": ["Anna Schmidt", "Ben Ortiz", "Clara Novak", "David Kim"],
            "Server": ["mail.example.org", "10.0.4.17", "files.northwind.io"],
            "Port": ["8080", "443", "5432"], "Display name": ["Living Room PC", "Office Laptop"],
            "Folder": ["C:\\Users\\mara\\Documents", "/media/mara/Pictures", "D:\\Backups\\2026"],
            "Language": ["English (UK)", "English (US)"], "Time zone": ["UTC+01:00 Berlin", "UTC-05:00 New York"],
            "Phone": ["+49 30 1234567", "+1 415 555 0199"], "Company": ["Northwind Traders", "Contoso Ltd"],
            "City": ["Hamburg", "Vienna", "Zurich"], "Subject": ["Quarterly report Q3", "Meeting notes"],
            "Device name": ["DESKTOP-7Q2K", "pixel-tablet"], "Proxy": ["proxy.local:3128"],
            "Host": ["db.internal", "192.168.1.20"], "Username": ["mklein", "admin", "j.doe"]},
    placeholders=["Enter a value", "Search files", "you@example.com", "Optional", "Type here..."],
    checks=["Remember me", "Enable notifications", "Start at login", "Use dark mode", "Show hidden files",
            "Auto-save every 5 minutes", "Send usage statistics", "Check for updates", "Compress backups",
            "Open in new window"],
    buttons=["Apply", "Save", "Browse...", "Delete", "Send", "Next >", "< Back", "Install", "Close",
             "Search", "Connect", "Retry", "Export", "Help", "Reset", "Open"],
    sentences=["The update will be installed when you restart.", "Your files are synced with the cloud.",
               "Last backup: today at 09:41.", "3 items selected (2.4 MB)", "No new messages in this folder.",
               "Connection secured with TLS 1.3", "Free space: 128 GB of 512 GB", "Changes are saved automatically.",
               "Version 4.2.1 (build 2087)", "Drag files here to upload them.", "Battery: 76% remaining",
               "Printer is ready.", "Sync paused until Wi-Fi is available.", "Select a folder to continue."],
    menus=["File", "Edit", "View", "Tools", "Help"],
    status=["Copying files", "Downloading update", "Scanning disk", "Uploading photos", "Exporting data"],
    ok="OK", cancel="Cancel",
    toasts=[("Download complete", "report_2026.pdf was saved."), ("New message", "Ben Ortiz: Lunch at 12?"),
            ("Backup finished", "1,204 files in 3 min"), ("Battery low", "12% remaining")],
)
DE = dict(
    titles=["Einstellungen", "Dateimanager", "Über dieses Gerät", "Drucker hinzufügen", "Größe ändern",
            "Benachrichtigungen", "Schlüsselbund", "Straßenkarte"],
    labels={"Benutzername": ["jürgen.müller", "größe_ändern"], "Straße": ["Hauptstraße 12", "Königsallee 5"],
            "Größe": ["2,4 MB", "Groß"], "Schlüssel": ["ÄÖÜ-4711", "geheim"], "Ort": ["München", "Düsseldorf"],
            "Gerät": ["Bürodrucker", "Küchen-PC"]},
    placeholders=["Wert eingeben", "Dateien durchsuchen", "Optional"],
    checks=["Beim Start öffnen", "Benachrichtigungen aktivieren", "Größe automatisch anpassen",
            "Versteckte Dateien anzeigen", "Für alle Benutzer übernehmen"],
    buttons=["Übernehmen", "Schließen", "Öffnen", "Löschen", "Weiter", "Zurück", "Durchsuchen..."],
    sentences=["Änderungen werden automatisch gespeichert.", "Möchten Sie die Datei wirklich löschen?",
               "Größe: 2,4 MB, geändert: gestern", "Drücken Sie Strg+S zum Speichern.", "Überprüfung läuft."],
    menus=["Datei", "Bearbeiten", "Ansicht", "Hilfe"],
    status=["Dateien werden kopiert", "Update wird geladen"],
    ok="OK", cancel="Abbrechen",
    toasts=[("Download abgeschlossen", "Bericht_März.pdf gespeichert."), ("Neue Nachricht", "Jürgen: Mittagessen?")],
)
FILE_STEMS = ["report_", "IMG_", "invoice-", "notes", "budget_Q", "slides_v", "backup_", "scan_", "draft-", "photo_"]
FILE_EXTS = ["pdf", "jpg", "txt", "xlsx", "pptx", "zip", "png", "docx", "csv"]
NAMES = ["Anna Schmidt", "Ben Ortiz", "Clara Novak", "David Kim", "Elif Yilmaz", "Felix Braun", "Grace Liu",
         "Hannah Weber", "Ivan Petrov", "Julia Rossi", "Karim Haddad", "Lena Fischer"]
ICON_KINDS = ["folder", "document", "image", "music", "gear", "trash", "mail", "terminal", "globe", "search",
              "star", "home"]
DESK_ICON_LABELS = {"folder": ["Projects", "Photos", "Archive"], "document": ["Notes.txt", "CV.pdf"],
                    "trash": ["Recycle Bin"], "globe": ["Browser"], "terminal": ["Terminal"], "mail": ["Mail"],
                    "music": ["Music"], "image": ["Wallpaper.png"], "gear": ["Settings"], "home": ["Home"],
                    "search": ["Search"], "star": ["Favorites"]}


def rand_file(rng):
    return f"{rng.choice(FILE_STEMS)}{rng.randint(1, 2099):04d}.{rng.choice(FILE_EXTS)}"


# ----------------------------------------------------------------------------- drawing helpers
class Ctx:
    """Drawing context that records ground truth while drawing."""

    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img)
        self.gt, self.spans, self.occluders = [], [], []
        self.layer = 0

    def add(self, etype, box, text="", parent=None, eid=None, **state):
        self.gt.append(dict(id=eid, type=etype, box=[int(round(v)) for v in box], text=text,
                            parent=parent, layer=self.layer, state=state))

    def text(self, xy, s, fnt, fill, owner=None, anchor="la", shadow=None):
        if shadow is not None:
            self.d.text((xy[0] + 1, xy[1] + 1), s, font=fnt, fill=shadow, anchor=anchor)
        self.d.text(xy, s, font=fnt, fill=fill, anchor=anchor)
        bb = self.d.textbbox(xy, s, font=fnt, anchor=anchor)
        self.spans.append(dict(text=s, box=[int(v) for v in bb], layer=self.layer, owner=owner))
        return bb


def shade(c, f):
    return tuple(int(max(0, min(255, v * f))) for v in c)


def draw_shadow(ctx, box, strength, blur=8):
    x0, y0, x1, y1 = box
    pad = 3 * blur
    layer = Image.new("L", (x1 - x0 + 2 * pad, y1 - y0 + 2 * pad), 0)
    ImageDraw.Draw(layer).rectangle([pad, pad + 4, pad + x1 - x0, pad + y1 - y0 + 4], fill=strength)
    layer = layer.filter(ImageFilter.BoxBlur(blur))
    ctx.img.paste(Image.new("RGB", layer.size, (0, 0, 0)), (x0 - pad, y0 - pad), layer)


def draw_icon(d, kind, x, y, s, color=None):
    """Procedural icons. Same kind and size gives identical pixels."""
    u = s / 24.0

    def P(px, py):
        return (x + px * u, y + py * u)

    if kind == "folder":
        d.polygon([P(1, 4), P(9, 4), P(11, 7), P(23, 7), P(23, 21), P(1, 21)], fill=(222, 170, 40),
                  outline=(160, 110, 20))
        d.rectangle([P(1, 9), P(23, 21)], fill=(250, 202, 72), outline=(160, 110, 20))
    elif kind == "document":
        d.polygon([P(4, 1), P(15, 1), P(20, 6), P(20, 23), P(4, 23)], fill=(255, 255, 255), outline=(110, 110, 110))
        d.line([P(15, 1), P(15, 6), P(20, 6)], fill=(110, 110, 110))
        for k in range(4):
            d.line([P(7, 10 + 3 * k), P(17, 10 + 3 * k)], fill=(70, 120, 200), width=max(1, int(u)))
    elif kind == "image":
        d.rectangle([P(1, 3), P(23, 21)], fill=(170, 210, 245), outline=(60, 90, 140))
        d.polygon([P(2, 20), P(9, 10), P(15, 20)], fill=(40, 150, 70))
        d.polygon([P(10, 20), P(16, 13), P(22, 20)], fill=(30, 120, 60))
        d.ellipse([P(15, 5), P(20, 10)], fill=(250, 210, 60))
    elif kind == "music":
        d.rounded_rectangle([P(1, 1), P(23, 23)], radius=4 * u, fill=(230, 220, 250), outline=(120, 70, 190))
        d.ellipse([P(5, 14), P(11, 19)], fill=(120, 70, 190))
        d.line([P(10, 16), P(10, 5), P(18, 4)], fill=(120, 70, 190), width=max(2, int(2 * u)))
        d.ellipse([P(13, 12), P(19, 17)], fill=(120, 70, 190))
    elif kind == "gear":
        import math
        cx, cy = x + 12 * u, y + 12 * u
        pts = []
        for k in range(16):
            r = 11 * u if k % 2 == 0 else 8 * u
            a = k * math.pi / 8
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        d.polygon(pts, fill=(120, 130, 140), outline=(70, 80, 90))
        d.ellipse([cx - 4 * u, cy - 4 * u, cx + 4 * u, cy + 4 * u], fill=(235, 235, 235))
    elif kind == "trash":
        d.rectangle([P(5, 7), P(19, 23)], fill=(150, 170, 190), outline=(60, 75, 90))
        d.rectangle([P(3, 4), P(21, 7)], fill=(110, 130, 150))
        d.rectangle([P(9, 1), P(15, 4)], outline=(60, 75, 90))
        for k in range(3):
            d.line([P(8 + 4 * k, 10), P(8 + 4 * k, 20)], fill=(60, 75, 90))
    elif kind == "mail":
        d.rectangle([P(1, 5), P(23, 19)], fill=(255, 255, 255), outline=(30, 100, 200))
        d.line([P(1, 5), P(12, 13), P(23, 5)], fill=(30, 100, 200), width=max(1, int(u)))
    elif kind == "terminal":
        d.rounded_rectangle([P(1, 3), P(23, 21)], radius=3 * u, fill=(25, 25, 25), outline=(90, 90, 90))
        d.line([P(5, 8), P(9, 12), P(5, 16)], fill=(60, 220, 90), width=max(1, int(1.5 * u)))
        d.line([P(11, 16), P(18, 16)], fill=(60, 220, 90), width=max(1, int(1.5 * u)))
    elif kind == "globe":
        d.ellipse([P(1, 1), P(23, 23)], fill=(40, 120, 220), outline=(20, 70, 150))
        d.ellipse([P(7, 1), P(17, 23)], outline=(220, 235, 255))
        d.line([P(1, 12), P(23, 12)], fill=(220, 235, 255))
        d.line([P(3, 6), P(21, 6)], fill=(220, 235, 255))
        d.line([P(3, 18), P(21, 18)], fill=(220, 235, 255))
    elif kind == "search":
        d.ellipse([P(2, 2), P(15, 15)], outline=(50, 50, 60), width=max(2, int(2 * u)))
        d.line([P(13, 13), P(22, 22)], fill=(50, 50, 60), width=max(2, int(3 * u)))
    elif kind == "star":
        d.polygon([P(12, 1), P(15, 8), P(23, 9), P(17, 14), P(19, 22), P(12, 18), P(5, 22), P(7, 14), P(1, 9),
                   P(9, 8)], fill=(250, 190, 30), outline=(190, 130, 10))
    elif kind == "home":
        d.polygon([P(12, 1), P(23, 11), P(20, 11), P(20, 23), P(4, 23), P(4, 11), P(1, 11)], fill=(240, 130, 50),
                  outline=(160, 70, 20))
        d.rectangle([P(10, 15), P(14, 23)], fill=(255, 240, 220))
    elif kind == "win_close":
        d.line([(x, y), (x + s - 1, y + s - 1)], fill=color, width=1)
        d.line([(x, y + s - 1), (x + s - 1, y)], fill=color, width=1)
    elif kind == "win_max":
        d.rectangle([x, y, x + s - 1, y + s - 1], outline=color)
    elif kind == "win_min":
        d.line([(x, y + s // 2), (x + s - 1, y + s // 2)], fill=color, width=1)
    elif kind == "start":
        g = s // 2 - 1
        for (dx, dy) in [(0, 0), (g + 2, 0), (0, g + 2), (g + 2, g + 2)]:
            d.rectangle([x + dx, y + dy, x + dx + g - 1, y + dy + g - 1], fill=(80, 170, 255))


CURSOR = [(0, 0), (0, 16), (4, 12), (7, 19), (9, 18), (6, 11), (11, 11)]


def draw_cursor(d, x, y):
    d.polygon([(x + px, y + py) for px, py in CURSOR], fill=(0, 0, 0), outline=(255, 255, 255))


_PHOTO_CACHE = {}


def photo(w, h, seed):
    """Procedural landscape with sensor-like noise, uint8 HxWx3."""
    key = (w, h, seed)
    if key in _PHOTO_CACHE:
        return _PHOTO_CACHE[key]
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
    top = rng.uniform([20, 60, 140], [120, 170, 250])
    bot = rng.uniform([150, 170, 190], [255, 230, 220])
    img = np.broadcast_to(top * (1 - t) + bot * t, (h, w, 3)).astype(np.float32).copy()
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = rng.uniform(0.1, 0.9) * w, rng.uniform(0.1, 0.35) * h
    r = rng.uniform(0.04, 0.09) * min(w, h) + 4
    img[(xx - cx) ** 2 + (yy - cy) ** 2 < r * r] = (255, 232, 160)
    for k in range(3):
        base = h * (0.42 + 0.17 * k)
        walk = np.cumsum(rng.normal(0, 1, w + 40))
        walk = np.convolve(walk, np.ones(31) / 31, mode="same")[20:20 + w]
        walk = (walk - walk.min()) / (np.ptp(walk) + 1e-6)
        ridge = base - h * 0.14 * walk
        col = np.array(rng.choice([(60, 120, 50), (90, 140, 60), (110, 90, 60), (40, 90, 60), (70, 100, 120)]),
                       dtype=np.float32) * rng.uniform(0.8, 1.15)
        m = yy > ridge[None, :]
        shadef = (0.75 + 0.35 * (yy / h))[..., None]
        img = np.where(m[..., None], col[None, None, :] * shadef, img)
    for _ in range(int(w * h / 4000)):
        tx, ty = rng.integers(0, w), rng.integers(int(h * 0.5), h)
        tr = rng.integers(2, 6)
        img[max(0, ty - tr):ty + tr, max(0, tx - tr):tx + tr] *= 0.6
    img += rng.normal(0, 7, (h, w, 3))
    out = np.clip(img, 0, 255).astype(np.uint8)
    if w * h < 400_000:
        _PHOTO_CACHE[key] = out
    return out


# ----------------------------------------------------------------------------- widgets
def draw_widget(ctx, wd, ox, oy, th, acc, fam, parent):
    k = wd["kind"]
    x, y = ox + wd["x"], oy + wd["y"]
    w, h = wd.get("w", 0), wd.get("h", 0)
    eid = wd["id"]
    if k == "label":
        f = font(fam, wd.get("size", 14), wd.get("bold", False))
        col = th["sub"] if wd.get("muted") else th["text"]
        bb = ctx.text((x, y + h // 2), wd["text"], f, col, owner=eid, anchor="lm")
        ctx.add("text", bb, wd["text"], parent, eid)
    elif k == "button":
        primary = wd.get("primary", False)
        fill = acc if primary else th["btn"]
        if wd.get("hover"):
            fill = shade(acc, 1.18) if primary else th["btn_hover"]
        if wd.get("pressed"):
            fill = shade(fill, 0.8)
        ctx.d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=4, fill=fill,
                                outline=None if primary else th["btn_border"])
        tc = (255, 255, 255) if primary else th["text"]
        ctx.text((x + w / 2, y + h / 2), wd["text"], font(fam, 14), tc, owner=eid, anchor="mm")
        ctx.add("button", (x, y, x + w, y + h), wd["text"], parent, eid, primary=primary,
                hover=bool(wd.get("hover")), pressed=bool(wd.get("pressed")))
    elif k == "field":
        foc = wd.get("focused", False)
        ctx.d.rectangle([x, y, x + w - 1, y + h - 1], fill=th["field"], outline=acc if foc else th["field_border"],
                        width=2 if foc else 1)
        txt, ph = wd.get("text", ""), wd.get("placeholder", "")
        f = font(fam, 14)
        if txt:
            ctx.text((x + 8, y + h / 2), txt, f, th["text"], owner=eid, anchor="lm")
        elif ph:
            ctx.text((x + 8, y + h / 2), ph, f, th["ph"], owner=eid, anchor="lm")
        if foc and wd.get("caret", False):
            cx = x + 9 + (tlen(fam, 14, txt) if txt else 0)
            ctx.d.line([(cx, y + 6), (cx, y + h - 7)], fill=th["text"])
        ctx.add("textfield", (x, y, x + w, y + h), txt or ph, parent, eid, focused=foc,
                placeholder=(not txt and bool(ph)))
    elif k == "checkbox":
        s = 16
        bx, by = x, y + (h - s) // 2
        if wd.get("checked"):
            ctx.d.rounded_rectangle([bx, by, bx + s - 1, by + s - 1], radius=3, fill=acc)
            ctx.d.line([(bx + 3, by + 8), (bx + 6, by + 11), (bx + 12, by + 4)], fill=(255, 255, 255), width=2)
        else:
            ctx.d.rounded_rectangle([bx, by, bx + s - 1, by + s - 1], radius=3, fill=th["field"],
                                    outline=th["field_border"])
        ctx.text((bx + s + 8, y + h / 2), wd["text"], font(fam, 14), th["text"], owner=eid, anchor="lm")
        ctx.add("checkbox", (bx, by, bx + s, by + s), wd["text"], parent, eid, checked=bool(wd.get("checked")))
    elif k == "list":
        rh = wd.get("rh", 22)
        items, sel, scroll = wd["items"], wd.get("selected", -1), wd.get("scroll", 0)
        nvis = (h - 2) // rh
        sbw = 10 if len(items) > nvis else 0
        ctx.d.rectangle([x, y, x + w - 1, y + h - 1], fill=th["list"], outline=th["border"])
        f = font(fam, 14)
        for i in range(nvis):
            idx = scroll + i
            if idx >= len(items):
                break
            ry = y + 1 + i * rh
            is_sel = idx == sel
            if is_sel:
                ctx.d.rectangle([x + 1, ry, x + w - 2 - sbw, ry + rh - 1], fill=acc)
            ctx.text((x + 8, ry + rh / 2), items[idx], f, (255, 255, 255) if is_sel else th["text"],
                     owner=f"{eid}.i{idx}", anchor="lm")
            ctx.add("listitem", (x + 1, ry, x + w - 1 - sbw, ry + rh), items[idx], eid, f"{eid}.i{idx}",
                    selected=is_sel)
        if sbw:
            tx0 = x + w - 1 - sbw
            ctx.d.rectangle([tx0, y + 1, x + w - 2, y + h - 2], fill=th["track"])
            th_h = max(20, int((h - 4) * nvis / len(items)))
            th_y = y + 2 + int((h - 4 - th_h) * scroll / max(1, len(items) - nvis))
            ctx.d.rectangle([tx0 + 2, th_y, x + w - 4, th_y + th_h], fill=th["thumb"])
        ctx.add("list", (x, y, x + w, y + h), "", parent, eid, n_items=len(items), scroll=scroll)
    elif k == "progress":
        v = max(0.0, min(1.0, wd["value"]))
        r = h // 2
        ctx.d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=r, fill=th["track"])
        fw = int(round(w * v))
        if fw >= 2:
            ctx.d.rounded_rectangle([x, y, x + fw - 1, y + h - 1], radius=min(r, fw // 2), fill=acc)
        ctx.add("progressbar", (x, y, x + w, y + h), "", parent, eid, value=int(round(v * 100)))
    elif k == "image":
        ctx.img.paste(Image.fromarray(photo(w, h, wd["seed"])), (x, y))
        ctx.add("image", (x, y, x + w, y + h), "", parent, eid)
    elif k == "icon":
        draw_icon(ctx.d, wd["icon"], x, y, w)
        lab = wd.get("label", "")
        if lab:
            ctx.text((x + w / 2, y + w + 5), lab, font(fam, 12), th["text"], owner=eid, anchor="ma")
        ctx.add("icon", (x, y, x + w, y + w), lab, parent, eid, kind=wd["icon"])
    elif k == "separator":
        ctx.d.line([(x, y), (x + w - 1, y)], fill=th["border"])
    else:
        raise ValueError(k)


def draw_window(ctx, win, th, acc, fam):
    x, y, w, h, wid = win["x"], win["y"], win["w"], win["h"], win["id"]
    active = win.get("active", False)
    style = win.get("title_style", "accent")
    draw_shadow(ctx, (x, y, x + w, y + h), th["shadow"] if active else th["shadow"] // 2)
    ctx.d.rectangle([x, y, x + w - 1, y + h - 1], fill=th["win"], outline=th["border"])
    if style == "accent" and active:
        tb, tc = acc, (255, 255, 255)
    elif style == "plain":
        tb, tc = th["win"], (th["text"] if active else th["sub"])
    else:
        tb, tc = th["title_in"], th["title_in_text"]
    ctx.d.rectangle([x + 1, y + 1, x + w - 2, y + TB_H], fill=tb)
    if style == "plain":
        ctx.d.line([(x + 1, y + TB_H), (x + w - 2, y + TB_H)], fill=th["border"])
    f = font(fam, 14, bold=win.get("title_bold", False))
    if win.get("title_center"):
        ctx.text((x + w / 2, y + TB_H / 2 + 1), win["title"], f, tc, owner=wid + ".title", anchor="mm")
    else:
        ctx.text((x + 12, y + TB_H / 2 + 1), win["title"], f, tc, owner=wid + ".title", anchor="lm")
    for i, kind in enumerate(["win_close", "win_max", "win_min"]):
        cx, cy = x + w - 24 - i * 46, y + TB_H // 2 + 1
        draw_icon(ctx.d, kind, cx - 5, cy - 5, 11, color=tc)
        ctx.add("icon", (cx - 5, cy - 5, cx + 6, cy + 6), "", wid, f"{wid}.{kind}", kind=kind)
    ctx.add("titlebar", (x + 1, y + 1, x + w - 1, y + TB_H + 1), win["title"], wid, wid + ".title")
    ctx.add("window", (x, y, x + w, y + h), win["title"], None, wid, active=active)
    ox, oy = x + 1, y + TB_H + 1
    for wd in win["widgets"]:
        draw_widget(ctx, wd, ox, oy, th, acc, fam, wid)


def draw_toast(ctx, t, th, acc, fam):
    x, y, w, h = t["x"], t["y"], t.get("w", 360), t.get("h", 92)
    draw_shadow(ctx, (x, y, x + w, y + h), th["shadow"])
    ctx.d.rounded_rectangle([x, y, x + w - 1, y + h - 1], radius=8, fill=th["toast"], outline=th["border"])
    draw_icon(ctx.d, t.get("icon", "mail"), x + 16, y + 18, 32)
    ctx.add("icon", (x + 16, y + 18, x + 48, y + 50), "", t["id"], t["id"] + ".icon", kind=t.get("icon", "mail"))
    ctx.text((x + 62, y + 28), t["title"], font(fam, 14, True), th["text"], owner=t["id"] + ".t", anchor="lm")
    ctx.add("text", ctx.spans[-1]["box"], t["title"], t["id"], t["id"] + ".t")
    ctx.text((x + 62, y + 54), t["msg"], font(fam, 13), th["sub"], owner=t["id"] + ".m", anchor="lm")
    ctx.add("text", ctx.spans[-1]["box"], t["msg"], t["id"], t["id"] + ".m")
    ctx.add("toast", (x, y, x + w, y + h), t["title"], None, t["id"])


def draw_desktop(ctx, desk, th, fam):
    bg = desk["bg"]
    if bg["kind"] == "solid":
        ctx.d.rectangle([0, 0, W, H], fill=tuple(bg["color"]))
    elif bg["kind"] == "gradient":
        a, b = np.array(bg["color"], np.float32), np.array(bg["color2"], np.float32)
        t = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        arr = np.broadcast_to(a * (1 - t) + b * t, (H, W, 3)).astype(np.uint8)
        ctx.img.paste(Image.fromarray(np.ascontiguousarray(arr)), (0, 0))
    else:
        ctx.img.paste(Image.fromarray(photo(W, H, bg["seed"])), (0, 0))
        ctx.add("image", (0, 0, W, H - TASKBAR_H), "", None, "wallpaper", wallpaper=True)
    for ic in desk.get("icons", []):
        x, y, s = ic["x"], ic["y"], 48
        draw_icon(ctx.d, ic["icon"], x, y, s)
        ctx.text((x + s / 2, y + s + 6), ic["label"], font(fam, 13), (255, 255, 255), owner=ic["id"], anchor="ma",
                 shadow=(0, 0, 0))
        ctx.add("icon", (x, y, x + s, y + s), ic["label"], None, ic["id"], kind=ic["icon"])
    tbar = desk.get("taskbar")
    if tbar:
        y0 = H - TASKBAR_H
        ctx.d.rectangle([0, y0, W, H], fill=th["taskbar"])
        ctx.add("panel", (0, y0, W, H), "", None, "taskbar")
        draw_icon(ctx.d, "start", 14, y0 + 12, 24)
        ctx.add("icon", (14, y0 + 12, 38, y0 + 36), "", "taskbar", "taskbar.start", kind="start")
        for i, kind in enumerate(tbar["icons"]):
            ix = 64 + i * 48
            draw_icon(ctx.d, kind, ix, y0 + 12, 24)
            ctx.add("icon", (ix, y0 + 12, ix + 24, y0 + 36), "", "taskbar", f"taskbar.app{i}", kind=kind)
        f = font(fam, 13)
        bb = ctx.text((W - 16, y0 + 15), tbar["clock"], f, th["taskbar_text"], owner="taskbar.clock", anchor="rm")
        ctx.add("text", bb, tbar["clock"], "taskbar", "taskbar.clock")
        bb = ctx.text((W - 16, y0 + 34), tbar["date"], f, th["taskbar_text"], owner="taskbar.date", anchor="rm")
        ctx.add("text", bb, tbar["date"], "taskbar", "taskbar.date")


def coverage(box, occ):
    """Fraction of box covered by the union of occluder boxes."""
    x0, y0, x1, y1 = box
    if x1 <= x0 or y1 <= y0:
        return 1.0
    rel = [o for o in occ if o[0] < x1 and o[2] > x0 and o[1] < y1 and o[3] > y0]
    if not rel:
        return 0.0
    s = 4 if (x1 - x0) * (y1 - y0) > 200_000 else 1
    m = np.zeros(((y1 - y0 + s - 1) // s, (x1 - x0 + s - 1) // s), bool)
    for o in rel:
        m[max(0, (o[1] - y0) // s):max(0, (o[3] - y0 + s - 1) // s), max(0, (o[0] - x0) // s):max(0, (o[2] - x0 + s - 1) // s)] = True
    return float(m.mean())


def render(scene):
    """Render a scene dict. Returns (PIL image, ground-truth dict)."""
    th = DARK if scene["theme"] == "dark" else LIGHT
    acc, fam = tuple(scene["accent"]), scene["font"]
    img = Image.new("RGB", (W, H))
    ctx = Ctx(img)
    draw_desktop(ctx, scene["desktop"], th, fam)
    for win in scene["windows"]:
        ctx.layer += 1
        ctx.occluders.append((ctx.layer, (win["x"], win["y"], win["x"] + win["w"], win["y"] + win["h"])))
        draw_window(ctx, win, th, acc, fam)
    for t in scene.get("toasts", []):
        ctx.layer += 1
        ctx.occluders.append((ctx.layer, (t["x"], t["y"], t["x"] + t.get("w", 360), t["y"] + t.get("h", 92))))
        draw_toast(ctx, t, th, acc, fam)
    # occlusion: hidden elements are dropped, partially hidden ones are flagged ignore
    keep = []
    for e in ctx.gt:
        cov = coverage(e["box"], [b for (l, b) in ctx.occluders if l > e["layer"]])
        if cov > 0.97:
            continue
        # window-control glyphs (close/max/min) have no visible button body; they are not scored
        e["ignore"] = (cov > 0.0 or bool(e["state"].get("wallpaper"))
                       or str(e["state"].get("kind", "")).startswith("win_"))
        keep.append(e)
    spans = []
    for s in ctx.spans:
        cov = coverage(s["box"], [b for (l, b) in ctx.occluders if l > s["layer"]])
        if cov > 0.0:
            continue
        spans.append(s)
    cur = scene.get("cursor")
    if cur:
        draw_cursor(ctx.d, cur[0], cur[1])
        keep.append(dict(id="cursor", type="cursor", box=[cur[0], cur[1], cur[0] + 12, cur[1] + 20], text="",
                         parent=None, layer=999, state={}, ignore=False))
        cb = (cur[0], cur[1], cur[0] + 12, cur[1] + 20)
        for s in spans:  # text under the cursor cannot be read exactly
            b = s["box"]
            if b[0] < cb[2] and b[2] > cb[0] and b[1] < cb[3] and b[3] > cb[1]:
                s["under_cursor"] = True
    # z-order of windows, front first
    zorder = [w["id"] for w in reversed(scene["windows"])]
    gt = dict(size=[W, H], elements=keep, spans=spans, zorder=zorder, theme=scene["theme"])
    return img, gt


# ----------------------------------------------------------------------------- random scenes
def build_rows(rng, kind, cw, fam, wid, voc, focus_field=False):
    ws = []
    n = [0]

    def nid(p):
        n[0] += 1
        return f"{wid}.{p}{n[0]}"

    y = 12
    if kind in ("filelist", "editor") or rng.random() < 0.3:
        x = 10
        for m in voc["menus"]:
            tw = tlen(fam, 14, m)
            ws.append(dict(kind="label", id=nid("m"), x=x, y=y, h=20, text=m))
            x += tw + 20
        y += 26
        ws.append(dict(kind="separator", id=nid("s"), x=0, y=y, w=cw))
        y += 8
    rows = {
        "form": ["field"] * rng.randint(2, 4) + ["check"] * rng.randint(1, 3) + ["buttons"],
        "filelist": ["toolbar", "list", "para", "buttons"],
        "viewer": ["image", "buttons"],
        "progress": ["progress", "para", "buttons"],
        "mixed": rng.sample(["field", "check", "progress", "para", "icons"], 3) + ["buttons"],
        "icons": ["toolbar", "icons", "para"],
    }[kind]
    labels = list(voc["labels"].keys())
    rng.shuffle(labels)
    lw = max(tlen(fam, 14, l) for l in labels) + 18
    focused_done = not focus_field
    for row in rows:
        if row == "field":
            lab = labels.pop()
            ws.append(dict(kind="label", id=nid("l"), x=20, y=y, h=28, text=lab))
            r = rng.random()
            fd = dict(kind="field", id=nid("f"), x=20 + lw, y=y, w=cw - 40 - lw, h=28)
            if r < 0.6:
                fd["text"] = rng.choice(voc["labels"][lab])
            elif r < 0.9:
                fd["placeholder"] = rng.choice(voc["placeholders"])
            if not focused_done:
                fd["focused"], fd["caret"] = True, True
                focused_done = True
            ws.append(fd)
            y += 28 + 10
        elif row == "check":
            ws.append(dict(kind="checkbox", id=nid("c"), x=20, y=y, h=22, text=rng.choice(voc["checks"]),
                           checked=rng.random() < 0.5))
            y += 22 + 8
        elif row == "buttons":
            texts = [voc["ok"], voc["cancel"]] if rng.random() < 0.6 else rng.sample(voc["buttons"], rng.randint(1, 3))
            x = cw - 20
            y += 6
            for i, t in enumerate(reversed(texts)):
                bw = max(80, tlen(fam, 14, t) + 32)
                x -= bw
                ws.append(dict(kind="button", id=nid("b"), x=x, y=y, w=bw, h=30, text=t,
                               primary=(i == len(texts) - 1)))
                x -= 8
            y += 30 + 10
        elif row == "toolbar":
            x = 16
            for _ in range(rng.randint(4, 7)):
                ws.append(dict(kind="icon", id=nid("k"), x=x, y=y, w=24, icon=rng.choice(ICON_KINDS)))
                x += 38
            y += 24 + 12
        elif row == "list":
            nvis = rng.randint(4, 8)
            items = [rand_file(rng) if rng.random() < 0.7 else rng.choice(NAMES) for _ in range(rng.choice([nvis, nvis + 6]))]
            ws.append(dict(kind="list", id=nid("L"), x=20, y=y, w=cw - 40, h=nvis * 22 + 2, rh=22, items=items,
                           selected=rng.randrange(nvis) if rng.random() < 0.8 else -1, scroll=0))
            y += nvis * 22 + 2 + 12
        elif row == "para":
            for _ in range(rng.randint(1, 2)):
                s = rng.choice(voc["sentences"])
                while tlen(fam, 14, s) > cw - 40:
                    s = s[:-2]
                ws.append(dict(kind="label", id=nid("t"), x=20, y=y, h=20, text=s, muted=rng.random() < 0.3))
                y += 22
            y += 6
        elif row == "progress":
            ws.append(dict(kind="label", id=nid("t"), x=20, y=y, h=20,
                           text=f"{rng.choice(voc['status'])} ({rng.randint(1, 40)} of 40)"))
            y += 26
            ph = rng.choice([8, 10, 12, 16])
            v = rng.random()
            ws.append(dict(kind="progress", id=nid("p"), x=20, y=y, w=cw - 40 - 56, h=ph, value=v))
            ws.append(dict(kind="label", id=nid("t"), x=cw - 20 - 44, y=y + ph // 2 - 10, h=20, text=f"{int(round(v * 100))}%"))
            y += max(ph, 20) + 12
        elif row == "image":
            iw, ih = rng.randint(200, 340), rng.randint(120, 210)
            ws.append(dict(kind="image", id=nid("g"), x=20, y=y, w=iw, h=ih, seed=rng.randint(0, 10**6)))
            tx = 20 + iw + 16
            for j in range(rng.randint(2, 4)):
                s = rng.choice(voc["sentences"])
                while tlen(fam, 14, s) > cw - tx - 16 and len(s) > 4:
                    s = s[:-2]
                ws.append(dict(kind="label", id=nid("t"), x=tx, y=y + 4 + j * 24, h=20, text=s))
            y += ih + 12
        elif row == "icons":
            x = 20
            for _ in range(rng.randint(3, 5)):
                ic = rng.choice(["folder", "document", "image", "music"])
                lab = rand_file(rng)[:12] if ic != "folder" else rng.choice(["Projects", "Photos", "Archive", "Music"])
                ws.append(dict(kind="icon", id=nid("k"), x=x + 26, y=y, w=48, icon=ic, label=lab))
                x += 110
            y += 48 + 30
    return ws, y + 8


def make_window(rng, wid, fam, voc, kind=None, focus=False):
    kind = kind or rng.choice(["form", "form", "filelist", "viewer", "progress", "mixed", "icons"])
    cw = {"form": rng.randint(440, 600), "filelist": rng.randint(520, 700), "viewer": rng.randint(600, 760),
          "progress": rng.randint(440, 540), "mixed": rng.randint(500, 680), "icons": rng.randint(560, 700)}[kind]
    widgets, ch = build_rows(rng, kind, cw, fam, wid, voc, focus_field=focus)
    return dict(id=wid, title=rng.choice(voc["titles"]), x=0, y=0, w=cw + 2, h=ch + TB_H + 2, widgets=widgets,
                title_style=rng.choice(["accent", "accent", "plain"]), title_center=rng.random() < 0.25,
                title_bold=rng.random() < 0.3)


def make_desktop(rng, theme, voc, allow_photo=True):
    r = rng.random()
    if r < 0.15 and allow_photo:
        bg = dict(kind="photo", seed=rng.randint(0, 10**6))
    elif r < 0.55:
        c = rng.choice(DESK_COLORS)
        bg = dict(kind="gradient", color=c, color2=shade(c, 0.55))
    else:
        bg = dict(kind="solid", color=rng.choice(DESK_COLORS))
    icons = []
    kinds = rng.sample(list(DESK_ICON_LABELS), rng.randint(3, 6))
    if rng.random() < 0.5:
        kinds.append(kinds[0])  # repeated icon kind
    used = set()
    for i, k in enumerate(kinds):
        lab = rng.choice(DESK_ICON_LABELS[k])
        if lab in used:
            lab += " 2"
        used.add(lab)
        icons.append(dict(id=f"d{i}", icon=k, label=lab, x=26, y=20 + i * 100))
    tbar = dict(icons=rng.sample(ICON_KINDS, rng.randint(3, 6)), clock=f"{rng.randint(0, 23):02d}:{rng.randint(0, 59):02d}",
                date=f"{rng.randint(1, 28):02d}.{rng.randint(1, 12):02d}.2026")
    return dict(bg=bg, icons=icons, taskbar=tbar)


def place(rng, win, others):
    best = None
    for _ in range(30):
        x = rng.randint(130, max(131, W - win["w"] - 20))
        y = rng.randint(16, max(17, H - TASKBAR_H - win["h"] - 12))
        ov = sum(max(0, min(x + win["w"], o["x"] + o["w"]) - max(x, o["x"])) *
                 max(0, min(y + win["h"], o["y"] + o["h"]) - max(y, o["y"])) for o in others)
        if best is None or ov < best[0]:
            best = (ov, x, y)
        if ov == 0 and rng.random() < 0.7:
            break
    win["x"], win["y"] = best[1], best[2]


def make_static_scene(seed, lang="en"):
    rng = random.Random(seed)
    voc = DE if lang == "de" else EN
    theme = "dark" if rng.random() < 0.25 else "light"
    fam = rng.choice(list(FONT_FILES))
    desk = make_desktop(rng, theme, voc)
    wins = []
    nw = rng.choice([1, 2, 2, 3])
    for i in range(nw):
        win = make_window(rng, f"w{i + 1}", fam, voc, focus=(i == nw - 1 and rng.random() < 0.6))
        place(rng, win, wins)
        wins.append(win)
    wins[-1]["active"] = True
    toasts = []
    if rng.random() < 0.3:
        tt, tm = rng.choice(voc["toasts"])
        toasts.append(dict(id="toast1", x=W - 380, y=H - TASKBAR_H - 110, title=tt, msg=tm, icon=rng.choice(["mail", "star", "document"])))
    return dict(theme=theme, accent=rng.choice(ACCENTS), font=fam, desktop=desk, windows=wins, toasts=toasts,
                cursor=[rng.randint(200, W - 200), rng.randint(100, H - 150)], seed=seed, lang=lang)


# ----------------------------------------------------------------------------- sequences
def base_scene(seed, theme="light", fam="dejavu", accent=0):
    rng = random.Random(seed)
    desk = make_desktop(rng, theme, EN, allow_photo=False)
    return dict(theme=theme, accent=ACCENTS[accent], font=fam, desktop=desk, windows=[], toasts=[],
                cursor=[1500, 700], seed=seed, lang="en")


def W_(kind, wid, n, **kw):
    return dict(kind=kind, id=f"{wid}.{n}", **kw)


def settings_window(wid="w1", x=560, y=180, fam="dejavu"):
    cw = 560
    ws = [W_("label", wid, "l1", x=20, y=16, h=28, text="Full name"),
          W_("field", wid, "f1", x=140, y=16, w=cw - 160, h=28, placeholder="Enter a value"),
          W_("label", wid, "l2", x=20, y=54, h=28, text="Email"),
          W_("field", wid, "f2", x=140, y=54, w=cw - 160, h=28, text="mara.klein@example.com"),
          W_("label", wid, "l3", x=20, y=92, h=28, text="Language"),
          W_("field", wid, "f3", x=140, y=92, w=cw - 160, h=28, text="English (UK)"),
          W_("checkbox", wid, "c1", x=20, y=134, h=22, text="Enable notifications", checked=False),
          W_("checkbox", wid, "c2", x=20, y=164, h=22, text="Start at login", checked=True),
          W_("checkbox", wid, "c3", x=20, y=194, h=22, text="Send usage statistics", checked=False),
          W_("label", wid, "t1", x=20, y=228, h=20, text="Changes are saved when you press Save.", muted=True),
          W_("button", wid, "b1", x=cw - 20 - 80, y=262, w=80, h=30, text="Cancel"),
          W_("button", wid, "b2", x=cw - 20 - 80 - 8 - 80, y=262, w=80, h=30, text="Save", primary=True)]
    return dict(id=wid, title="Settings", x=x, y=y, w=cw + 2, h=262 + 30 + 14 + TB_H + 2, widgets=ws,
                title_style="accent", active=True)


def explorer_window(wid, x, y, items, sel=1, nvis=8, scroll=0, title="File Explorer", active=False):
    cw = 620
    ws = [W_("label", wid, "m1", x=10, y=8, h=20, text="File"), W_("label", wid, "m2", x=50, y=8, h=20, text="Edit"),
          W_("label", wid, "m3", x=92, y=8, h=20, text="View"), W_("label", wid, "m4", x=138, y=8, h=20, text="Help"),
          W_("separator", wid, "s1", x=0, y=34, w=cw)]
    for i, k in enumerate(["folder", "document", "trash", "search", "gear"]):
        ws.append(W_("icon", wid, f"k{i}", x=16 + i * 38, y=44, w=24, icon=k))
    ws.append(W_("field", wid, "f1", x=cw - 220, y=42, w=200, h=28, placeholder="Search files"))
    ws.append(W_("list", wid, "L1", x=20, y=82, w=cw - 40, h=nvis * 22 + 2, rh=22, items=items, selected=sel, scroll=scroll))
    ly = 82 + nvis * 22 + 2 + 12
    ws.append(W_("label", wid, "t1", x=20, y=ly, h=20, text=f"{len(items)} items", muted=True))
    ws.append(W_("button", wid, "b1", x=cw - 20 - 90, y=ly + 28, w=90, h=30, text="Open", primary=True))
    ws.append(W_("button", wid, "b2", x=cw - 20 - 90 - 8 - 90, y=ly + 28, w=90, h=30, text="Delete"))
    return dict(id=wid, title=title, x=x, y=y, w=cw + 2, h=ly + 28 + 30 + 14 + TB_H + 2, widgets=ws,
                title_style="accent", active=active)


def find(win, suffix):
    for wd in win["widgets"]:
        if wd["id"].endswith("." + suffix):
            return wd
    raise KeyError(suffix)


def lerp(a, b, t):
    return int(round(a + (b - a) * t))


def seq_typing():
    s = base_scene(11)
    win = settings_window()
    s["windows"] = [win]
    f1 = find(win, "f1")
    text = "Mara Klein, Product Design"
    frames, events = [], []
    s["cursor"] = [win["x"] + 400, win["y"] + TB_H + 30]
    n = 0
    for i in range(30):
        f1["focused"] = i >= 2
        f1["caret"] = f1["focused"] and (i % 2 == 0)
        if i >= 4 and n < len(text):
            n = min(len(text), n + (2 if i % 3 else 1))
        if n:
            f1["text"] = text[:n]
            f1.pop("placeholder", None)
        frames.append(copy.deepcopy(s))
    events = [dict(t=1.0, what="Full name field gets focus (blue border, caret)"),
              dict(t=2.0, what="typing starts in Full name field"),
              dict(t=frames_time_done(frames, text), what=f"typing finished: '{text}'")]
    return frames, events


def frames_time_done(frames, text):
    for i, fr in enumerate(frames):
        if find(fr["windows"][0], "f1").get("text") == text:
            return i / FPS
    return None


def seq_progress():
    s = base_scene(12, theme="dark", fam="noto", accent=2)
    cw = 480
    wid = "w1"
    ws = [W_("label", wid, "t1", x=20, y=16, h=20, text="Copying files (0 of 40)"),
          W_("label", wid, "t2", x=20, y=42, h=20, text="IMG_0001.jpg", muted=True),
          W_("progress", wid, "p1", x=20, y=74, w=cw - 96, h=12, value=0.0),
          W_("label", wid, "t3", x=cw - 64, y=70, h=20, text="0%"),
          W_("button", wid, "b1", x=cw - 100, y=110, w=80, h=30, text="Cancel")]
    win = dict(id=wid, title="Copying 40 files", x=700, y=360, w=cw + 2, h=110 + 30 + 14 + TB_H + 2, widgets=ws,
               title_style="accent", active=True)
    s["windows"] = [explorer_window("w0", 200, 120, [rand_file(random.Random(k)) for k in range(12)]), win]
    s["cursor"] = [1300, 800]
    frames = []
    for i in range(40):
        k = min(40, int(round(i * 40 / 34)))
        find(win, "p1")["value"] = k / 40
        find(win, "t1")["text"] = f"Copying files ({k} of 40)"
        find(win, "t2")["text"] = f"IMG_{k:04d}.jpg" if k < 40 else "Done"
        find(win, "t3")["text"] = f"{int(round(100 * k / 40))}%"
        if k == 40:
            find(win, "b1")["text"] = "Close"
            win["title"] = "Copy complete"
        frames.append(copy.deepcopy(s))
    events = [dict(t=0.5, what="progress starts advancing, label counts files"),
              dict(t=17.0, what="progress reaches 100%, button text Cancel -> Close, title -> 'Copy complete'")]
    return frames, events


def seq_dialog():
    s = base_scene(13, fam="liberation", accent=1)
    items = ["report_2026.pdf", "IMG_0412.jpg", "IMG_0413.jpg", "IMG_0414.jpg", "budget_Q3.xlsx", "notes.txt",
             "slides_v2.pptx", "backup_0917.zip"]
    ex = explorer_window("w1", 380, 140, items, sel=2, active=True)
    s["windows"] = [ex]
    s["cursor"] = [900, 520]
    cw = 420
    dlg = dict(id="w2", title="Confirm delete", x=700, y=380, w=cw + 2, h=100 + 30 + 14 + TB_H + 2, title_style="accent",
               active=True, widgets=[W_("label", "w2", "t1", x=20, y=20, h=20, text="Delete 3 selected files?"),
                                     W_("label", "w2", "t2", x=20, y=48, h=20, text="This cannot be undone.", muted=True),
                                     W_("button", "w2", "b1", x=cw - 20 - 90, y=100, w=90, h=30, text="Cancel"),
                                     W_("button", "w2", "b2", x=cw - 20 - 90 - 8 - 90, y=100, w=90, h=30, text="Delete",
                                        primary=True)])
    frames = []
    for i in range(24):
        t = i / FPS
        if 3.0 <= t < 7.5:
            if len(s["windows"]) == 1:
                ex["active"] = False
                s["windows"].append(dlg)
            if t >= 4.0:
                k = min(1.0, (t - 4.0) / 1.5)
                s["cursor"] = [lerp(900, 700 + cw - 65, k), lerp(520, 380 + TB_H + 1 + 115, k)]
            find(dlg, "b1")["hover"] = t >= 5.5
        elif t >= 7.5 and len(s["windows"]) == 2:
            s["windows"].pop()
            ex["active"] = True
        frames.append(copy.deepcopy(s))
    events = [dict(t=3.0, what="modal dialog 'Confirm delete' appears: 'Delete 3 selected files?' [Delete] [Cancel]"),
              dict(t=4.0, what="cursor moves toward the Cancel button"),
              dict(t=5.5, what="cursor hovers Cancel (button highlight)"),
              dict(t=7.5, what="dialog closes, File Explorer active again")]
    return frames, events


def seq_window_move():
    s = base_scene(14, fam="roboto", accent=3)
    back = settings_window("w1", 1100, 380)
    back["active"] = False
    front = explorer_window("w2", 200, 120, [rand_file(random.Random(50 + k)) for k in range(10)], active=True,
                            title="Downloads")
    s["windows"] = [back, front]
    frames = []
    for i in range(30):
        k = min(1.0, max(0.0, (i - 4) / 16))
        front["x"], front["y"] = lerp(200, 760, k), lerp(120, 300, k)
        s["cursor"] = [front["x"] + 300, front["y"] + 14]
        frames.append(copy.deepcopy(s))
    events = [dict(t=2.0, what="Downloads window starts moving (dragged by title bar)"),
              dict(t=10.0, what="Downloads window stops at its new position, now overlapping Settings")]
    return frames, events


def seq_scroll():
    s = base_scene(15, fam="dejavu", accent=0)
    items = [f"{n}" for n in sorted({rand_file(random.Random(100 + k)) for k in range(40)})]
    ex = explorer_window("w1", 500, 140, items, sel=5, nvis=10, active=True, title="Archive")
    s["windows"] = [ex]
    L = find(ex, "L1")
    s["cursor"] = [800, 400]
    frames = []
    for i in range(30):
        L["scroll"] = max(0, min(20, i - 4))
        frames.append(copy.deepcopy(s))
    events = [dict(t=2.5, what="file list starts scrolling down one row per frame"),
              dict(t=12.0, what="scrolling stops after 20 rows")]
    return frames, events


def seq_cursor():
    s = base_scene(16, fam="noto", accent=4)
    win = settings_window("w1", 700, 260)
    s["windows"] = [win]
    pts = [(300, 900), (700, 700), (1100, 500), (win["x"] + 1 + 400, win["y"] + TB_H + 1 + 275), (1500, 300), (1700, 200)]
    frames = []
    for i in range(30):
        seg = min(len(pts) - 2, i // 6)
        k = (i % 6) / 6 if i < 30 else 1
        p0, p1 = pts[seg], pts[seg + 1]
        cx, cy = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
        s["cursor"] = [cx, cy]
        b2 = find(win, "b2")
        bx, by = win["x"] + 1 + b2["x"], win["y"] + TB_H + 1 + b2["y"]
        b2["hover"] = bx <= cx < bx + b2["w"] and by <= cy < by + b2["h"]
        frames.append(copy.deepcopy(s))
    events = [dict(t=0.0, what="cursor moves across the screen along a path"),
              dict(t=9.0, what="cursor passes over the Save button (hover highlight)")]
    return frames, events


def seq_toast():
    s = base_scene(17, theme="dark", fam="roboto", accent=5)
    win = explorer_window("w1", 300, 160, [rand_file(random.Random(200 + k)) for k in range(9)], active=True)
    s["windows"] = [win]
    s["cursor"] = [700, 500]
    frames = []
    for i in range(30):
        t = i / FPS
        s["toasts"] = []
        if 4.0 <= t < 10.0:
            k = min(1.0, (t - 4.0) / 1.0)
            s["toasts"] = [dict(id="toast1", x=lerp(W, W - 380, k), y=H - TASKBAR_H - 110, title="Backup finished",
                                msg="1,204 files in 3 min", icon="star")]
        frames.append(copy.deepcopy(s))
    events = [dict(t=4.0, what="notification toast 'Backup finished' slides in at bottom right"),
              dict(t=10.0, what="toast disappears")]
    return frames, events


def seq_workflow():
    """QA sequence: fill a form, tick a box, save, toast."""
    s = base_scene(18, fam="dejavu", accent=0)
    win = settings_window("w1", 640, 200)
    s["windows"] = [win]
    f1, c1, b2 = find(win, "f1"), find(win, "c1"), find(win, "b2")
    ox, oy = win["x"] + 1, win["y"] + TB_H + 1
    text = "Jonas Berger"
    frames, events = [], []
    for i in range(40):
        t = i / FPS
        if t < 1.5:
            s["cursor"] = [lerp(1500, ox + 300, t / 1.5), lerp(800, oy + 30, t / 1.5)]
        if t >= 1.5:
            f1["focused"] = True
            f1["caret"] = i % 2 == 0
        if t >= 2.0:
            n = min(len(text), int((t - 2.0) * 4) + 1)
            f1["text"] = text[:n]
            f1.pop("placeholder", None)
        if 6.0 <= t < 7.0:
            s["cursor"] = [lerp(ox + 300, ox + 28, (t - 6.0)), lerp(oy + 30, oy + 145, (t - 6.0))]
        if t >= 7.0:
            c1["checked"] = True
        if 8.0 <= t < 9.0:
            s["cursor"] = [lerp(ox + 28, b2["x"] + ox + 40, (t - 8.0)), lerp(oy + 145, b2["y"] + oy + 15, (t - 8.0))]
        if t >= 9.0:
            f1["focused"], f1["caret"] = False, False
        b2["hover"] = 9.0 <= t < 10.0
        b2["pressed"] = t == 9.5
        if 10.0 <= t < 16.0:
            s["toasts"] = [dict(id="toast1", x=W - 380, y=H - TASKBAR_H - 110, title="Settings saved",
                                msg="Your profile was updated.", icon="star")]
        else:
            s["toasts"] = []
        if t >= 10.0:
            win["title"] = "Settings - saved"
        frames.append(copy.deepcopy(s))
    events = [dict(t=0.0, what="cursor moves to the Full name field"),
              dict(t=1.5, what="Full name field gets focus"),
              dict(t=2.0, what=f"typing '{text}' into Full name (about 4 chars/s), done at t=4.75"),
              dict(t=7.0, what="'Enable notifications' checkbox becomes checked"),
              dict(t=9.0, what="Save button hovered, pressed at t=9.5"),
              dict(t=10.0, what="toast 'Settings saved' appears; window title changes to 'Settings - saved'"),
              dict(t=16.0, what="toast disappears")]
    return frames, events


SEQUENCES = {"typing": seq_typing, "progress": seq_progress, "dialog": seq_dialog, "window_move": seq_window_move,
             "scroll": seq_scroll, "cursor": seq_cursor, "toast": seq_toast, "workflow": seq_workflow}


# ----------------------------------------------------------------------------- QA scenes (fixed layouts)
def qa_scene_mail():
    """Two windows: mail client in back, login dialog in front."""
    s = base_scene(31, fam="dejavu", accent=0)
    items = ["Ben Ortiz - Lunch at 12?", "Grace Liu - Invoice 2026-114", "IT Desk - Password expires soon",
             "Clara Novak - Slides v3", "Newsletter - November issue", "David Kim - Re: Budget"]
    mail = explorer_window("w1", 160, 90, items, sel=2, nvis=6, title="Mail - Inbox", active=False)
    mail["widgets"] = [wd for wd in mail["widgets"] if not wd["id"].endswith(".f1")]
    mail["widgets"].append(W_("field", "w1", "f9", x=400, y=42, w=200, h=28, placeholder="Search mail"))
    find(mail, "b1")["text"] = "Reply"
    find(mail, "b2")["text"] = "Archive"
    cw = 440
    wid = "w2"
    login = dict(id=wid, title="Sign in to Northwind VPN", x=820, y=330, w=cw + 2, h=0, title_style="accent", active=True,
                 widgets=[W_("label", wid, "l1", x=20, y=18, h=28, text="Username"),
                          W_("field", wid, "f1", x=130, y=18, w=cw - 150, h=28, text="mklein"),
                          W_("label", wid, "l2", x=20, y=56, h=28, text="Server"),
                          W_("field", wid, "f2", x=130, y=56, w=cw - 150, h=28, text="vpn.northwind.io", focused=True),
                          W_("checkbox", wid, "c1", x=20, y=98, h=22, text="Remember me", checked=True),
                          W_("checkbox", wid, "c2", x=20, y=128, h=22, text="Use smart card", checked=False),
                          W_("button", wid, "b1", x=cw - 20 - 90, y=170, w=90, h=30, text="Cancel"),
                          W_("button", wid, "b2", x=cw - 20 - 90 - 8 - 100, y=170, w=100, h=30, text="Connect",
                             primary=True)])
    login["h"] = 170 + 30 + 14 + TB_H + 2
    s["windows"] = [mail, login]
    s["cursor"] = [1100, 560]
    return s


def qa_scene_media():
    """Photo viewer with image, progress and a toast; dark theme."""
    s = base_scene(32, theme="dark", fam="noto", accent=3)
    cw = 720
    wid = "w1"
    ws = [W_("label", wid, "m1", x=10, y=8, h=20, text="File"), W_("label", wid, "m2", x=50, y=8, h=20, text="Edit"),
          W_("label", wid, "m3", x=92, y=8, h=20, text="View"), W_("separator", wid, "s1", x=0, y=34, w=cw),
          W_("image", wid, "g1", x=20, y=48, w=420, h=260, seed=777),
          W_("label", wid, "t1", x=460, y=56, h=20, text="Lake_Sunset_0412.jpg"),
          W_("label", wid, "t2", x=460, y=82, h=20, text="4032 x 3024, 3.1 MB", muted=True),
          W_("label", wid, "t3", x=460, y=108, h=20, text="Taken: 14.08.2026 19:42", muted=True),
          W_("checkbox", wid, "c1", x=460, y=146, h=22, text="Show location", checked=False),
          W_("checkbox", wid, "c2", x=460, y=176, h=22, text="Auto-enhance", checked=True),
          W_("label", wid, "t4", x=20, y=322, h=20, text="Uploading to cloud (7 of 12)"),
          W_("progress", wid, "p1", x=20, y=350, w=cw - 100, h=10, value=0.58),
          W_("label", wid, "t5", x=cw - 64, y=345, h=20, text="58%"),
          W_("button", wid, "b1", x=cw - 20 - 90, y=380, w=90, h=30, text="Pause"),
          W_("button", wid, "b2", x=cw - 20 - 90 - 8 - 90, y=380, w=90, h=30, text="Share", primary=True)]
    win = dict(id=wid, title="Photo Viewer", x=520, y=150, w=cw + 2, h=380 + 30 + 14 + TB_H + 2, widgets=ws,
               title_style="accent", active=True)
    s["windows"] = [win]
    s["toasts"] = [dict(id="toast1", x=W - 380, y=H - TASKBAR_H - 110, title="Battery low", msg="12% remaining",
                        icon="star")]
    s["cursor"] = [700, 900]
    return s


QA_SCENES = {"qa_mail": qa_scene_mail, "qa_media": qa_scene_media}


# ----------------------------------------------------------------------------- IO
def save(img, gt, path_png, meta=None):
    img.save(path_png, compress_level=3)
    if meta:
        gt["meta"] = meta
    with open(path_png[:-4] + ".json", "w") as f:
        json.dump(gt, f, ensure_ascii=False)


def gen_static(split, seeds, lang="en"):
    out = os.path.join(DATA, "synth", split)
    os.makedirs(out, exist_ok=True)
    for sd in seeds:
        sc = make_static_scene(sd, lang)
        img, gt = render(sc)
        save(img, gt, os.path.join(out, f"scr_{sd:03d}.png"), meta=dict(seed=sd, lang=lang, font=sc["font"], theme=sc["theme"]))
    print(f"{split}: {len(seeds)} screens -> {out}")


def gen_sequences(names=None):
    for name, fn in SEQUENCES.items():
        if names and name not in names:
            continue
        out = os.path.join(DATA, "seq", name)
        os.makedirs(out, exist_ok=True)
        frames, events = fn()
        for i, sc in enumerate(frames):
            img, gt = render(sc)
            save(img, gt, os.path.join(out, f"f_{i:03d}.png"), meta=dict(t=i / FPS, index=i))
        with open(os.path.join(out, "events.json"), "w") as f:
            json.dump(dict(name=name, fps=FPS, n_frames=len(frames), events=events), f, indent=1)
        print(f"seq {name}: {len(frames)} frames")


def gen_qa_scenes():
    out = os.path.join(DATA, "qa_scenes")
    os.makedirs(out, exist_ok=True)
    for name, fn in QA_SCENES.items():
        sc = fn()
        img, gt = render(sc)
        save(img, gt, os.path.join(out, f"{name}.png"))
        with open(os.path.join(out, f"{name}.scene.json"), "w") as f:
            json.dump(sc, f, ensure_ascii=False, indent=1)
    print(f"qa scenes -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["static", "seq", "qa"], default=None)
    a = ap.parse_args()
    if a.only in (None, "static"):
        gen_static("dev", range(0, 12))
        gen_static("test", range(100, 140))
        gen_static("de", range(200, 208), lang="de")
    if a.only in (None, "seq"):
        gen_sequences()
    if a.only in (None, "qa"):
        gen_qa_scenes()


if __name__ == "__main__":
    main()
