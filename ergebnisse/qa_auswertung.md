# Blind-QA: Textbeschreibung (T), ohne Eingabe (C), Bilder (I)

T erreicht 95,5 %, C 48,2 %, I 99,1 % auf 55 Fragen. T liegt 47,3 Punkte über Raten (T − C). T liegt 3,6 Punkte unter den Bildern (I − T). T liest 2.935 Tokens, I liest 79.292 bis 115.713 Tokens.

Bewertet am 17.11.2026. Ein Leser pro Bedingung, ein Durchlauf, ein Bewerter. Alle Tabellen druckt `testbett/qa/score_blind.py`. Die Einzelwertungen stehen in `blind_scores.json`.

## Bedingungen

| Kürzel | Eingabe des Lesers |
|---|---|
| T | Textbeschreibung des Bildschirms, eine Datei pro Eingabe |
| C | keine Eingabe, nur die Fragen |
| I | die PNG-Bilder (1920x1080), 1 Bild pro Bildschirm, 40 Bilder für die Sequenz |

## Bewertungsregeln (vor der Bewertung festgelegt)

1. Exakter Text (Beschriftungen, Feldinhalte, Titel, Dateinamen, Uhrzeit, Platzhalter): 1 bei Übereinstimmung, Groß- und Kleinschreibung und triviale Satzzeichen egal. 0,5 bei einem falschen, fehlenden oder zusätzlichen Wort, einem verlesenen Zeichen oder vertauschter Wortfolge. Sonst 0.
2. Listen (Menüs, Abschnitte, angehakte Boxen): 1 wenn alle Einträge stimmen, 0,5 bei genau einem Fehler. Sonst 0.
3. Kategorisch (ja/nein, vorderes Fenster, relative Lage, Element unter dem Zeiger): 1 oder 0. 0,5 für einen vertretbaren Beinahe-Treffer: richtiges Element per Rolle mit falscher Beschriftung, oder richtiges Fenster ohne Titel.
4. Zweiteilige Fragen: 1 wenn beide Teile stimmen, 0,5 bei einem.
5. Anzahlen und Zeiten: 1 wenn exakt; Zeiten gelten innerhalb 0,5 s (1 Bild bei 2 FPS) als exakt. 0,5 bei Abweichung um eins bzw. um ein weiteres Bild.
6. "unknown" gibt 0. Eine abgesicherte Antwort zählt mit dem, worauf sie sich festlegt.
7. Mehrdeutige Frage zwischen zwei sichtbaren Texten eines Elements: 0,5 für den anderen Text.
8. Fehler der Referenz: Widerspricht das gerenderte Bild `answers.json`, gibt eine bildkonforme Antwort 0,5. Betroffen: sequence_workflow_q13.

## Genauigkeit

| Umfang | n | T | C | I | T − C | I − T |
|---|---|---|---|---|---|---|
| alle Fragen | 55 | 52,5 (95,5 %) | 26,5 (48,2 %) | 54,5 (99,1 %) | +47,3 Pkt. | +3,6 Pkt. |
| ohne screen2_q12 (Farbschema) | 54 | 52,5 (97,2 %) | 25,5 (47,2 %) | 53,5 (99,1 %) | +50,0 Pkt. | +1,9 Pkt. |

- T schlägt C bei 34 Fragen, C schlägt T bei 1. Vorzeichentest: p = 2e-9.
- I schlägt T bei 3 Fragen, T schlägt I bei 1. Vorzeichentest: p = 0,62. Bei n = 55 und einem Durchlauf ist die Lücke von 3,6 Punkten nicht von null zu unterscheiden.
- C erreicht volle Punkte bei 20 Fragen. 10 davon sind binär, 10 verrät der Fragetext oder eine UI-Konvention.

### Pro Eingabe

| Eingabe | Inhalt | n | T | C | I |
|---|---|---|---|---|---|
| screen1 | Mail-Fenster plus Anmeldedialog | 14 | 100 % | 35,7 % | 100 % |
| screen2 | Bildbetrachter, dunkles Schema | 13 | 80,8 % | 46,2 % | 100 % |
| screen3 | HTML-Einstellungsseite | 14 | 100 % | 46,4 % | 100 % |
| sequence_workflow | 40 Bilder, Formular ausfüllen und speichern | 14 | 100 % | 64,3 % | 96,4 % |

### Pro Kategorie

| Kategorie | n | T | C | I |
|---|---|---|---|---|
| Text lesen | 19 | 92,1 % | 28,9 % | 100 % |
| Widget-Zustand | 15 | 93,3 % | 63,3 % | 100 % |
| Layout/Lage | 6 | 100 % | 58,3 % | 100 % |
| Fensterreihenfolge | 3 | 100 % | 33,3 % | 100 % |
| Zählen | 1 | 100 % | 50 % | 100 % |
| zeitlicher Ablauf | 11 | 100 % | 59,1 % | 95,5 % |

## Kalibrierung

| Bedingung | mittlere Konfidenz | Genauigkeit | Konfidenz − Genauigkeit | Brier | Konfidenz auf Antworten < 1 |
|---|---|---|---|---|---|
| T | 0,882 | 0,955 | −0,072 | 0,039 | 0,70 (n = 3) |
| C | 0,299 | 0,482 | −0,183 | 0,163 | 0,21 (n = 35) |
| I | 0,949 | 0,991 | −0,042 | 0,005 | 0,70 (n = 1) |

Alle drei Leser sind im Mittel unterkonfident.

## Tokenkosten

T-Tokens sind mit tiktoken o200k_base gezählt. Bild-Tokens sind geschätzt: 1.844 pro 1080p-Bild (Skalierung auf 1568 Pixel lange Kante, w·h/750) oder 2.691 pro Bild (veröffentlichter Wert). Die Einheiten stammen aus verschiedenen Tokenizern, die Verhältnisse sind Näherungen.

| Bedingung | Eingabe-Tokens | Punkte | Genauigkeit | Punkte pro 1.000 Tokens |
|---|---|---|---|---|
| T | 2.935 | 52,5 | 95,5 % | 17,89 |
| C | 0 | 26,5 | 48,2 % | - |
| I (1.844 pro Bild) | 79.292 | 54,5 | 99,1 % | 0,69 |
| I (2.691 pro Bild) | 115.713 | 54,5 | 99,1 % | 0,47 |

Auf einem Einzelbildschirm braucht T 592 bis 816 Tokens gegen 1.844 für ein Bild. Auf der 40-Bilder-Sequenz braucht T 860 Tokens gegen 73.760 und erreicht 14 von 14 Punkten.

## Fehler von T

3 von 55 Fragen, alle auf screen2.

| Frage | T-Punkte | Ursache |
|---|---|---|
| screen2_q01 Dateiname des Fotos | 0 | Der Dateiname fehlt in der Textbeschreibung. |
| screen2_q06 Text der Benachrichtigung | 0,5 | Die Textbeschreibung enthält "129 % remaining" statt "12 % remaining". |
| screen2_q12 Farbschema | 0 | Die Textbeschreibung enthält keine Hintergrundfarbe. |

Die einzige Abweichung von I (sequence_workflow_q13, 0,5) ist der Referenzfehler aus Regel 8.
