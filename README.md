# ScreenCodec

**KI-Agenten sehen den Bildschirm mit einem Bruchteil der Tokens.**

![Status](https://img.shields.io/badge/Status-Forschungsprototyp-orange)
![Sprache](https://img.shields.io/badge/Sprache-Deutsch-blue)
![Lizenz](https://img.shields.io/badge/Lizenz-Alle%20Rechte%20vorbehalten-lightgrey)

Forschungsprototyp, nicht veröffentlicht. Stand 17.11.2026.

## Auf einen Blick

- 57 Tokens pro Sekunde im Mittel über 8 Bildschirmsequenzen bei 2 Bildern pro Sekunde (gemessen). Ein Bildstrom kostet 1.820 bis 5.382 Tokens pro Sekunde (berechnet nach Anbieterformeln).
- Ein Kontext mit 200.000 Tokens reicht damit 59 Minuten statt 37 bis 110 Sekunden.
- Im Blindtest mit 55 Fragen beantwortet ein Sprachmodell 95,5 % richtig. Mit Bildern sind es 99,1 %, ohne Eingabe 48,2 % (gemessen).
- Ein typisches Folgebild braucht 85 ms auf einem CPU-Kern (gemessen).

Schreibweise: Tok/s heißt Tokens pro Sekunde. FPS heißt Bilder pro Sekunde.

## Problem

Sprachmodelle sehen einen Bildschirm heute als Bild. Ein Full-HD-Bild (1920 x 1080) kostet 2026 je nach Anbieter 910 bis 2.691 Tokens.

| Anbieter und Stufe | Tokens pro Bild | Tok/s bei 2 FPS | Kontext mit 200.000 Tokens voll nach |
|---|---|---|---|
| Claude ab Version 4.7 | 2.691 | 5.382 | 37 s |
| gpt-5.5 high | 2.448 | 4.896 | 41 s |
| Claude Standardstufe | 1.560 | 3.120 | 64 s |
| Gemini 3 | 1.120 | 2.240 | 89 s |
| gpt-5 Kachelmodus | 910 | 1.820 | 110 s |

Quelle: Dokumentation der Anbieter. Füllzeiten berechnet.

- Eine Stunde Bildstrom mit Claude ab 4.7 umfasst 19,4 Mio. Tokens. Bei 4 US-Dollar pro Mio. Input-Tokens kostet sie 77,50 US-Dollar (berechnet).
- Claude nimmt bei 200k-Modellen höchstens 100 Bilder pro Anfrage. Bei 2 FPS sind das 50 Sekunden Bildschirm.
- Menschen lösen 72,36 % der 369 Aufgaben im Benchmark OSWorld (2024). Ein Agent, der länger zusieht, füllt seinen Kontext nach Minuten.

## Ergebnisse

Testbedingungen: Prototyp auf der CPU, Bildschirme mit 1920 x 1080 Pixeln, 2 FPS. Tokens gezählt mit tiktoken o200k_base.

### Tokens und Kontext

| Darstellung | Tok/s bei 2 FPS | 200.000 Tokens voll nach | 1 Mio. Tokens voll nach | Art |
|---|---|---|---|---|
| Bildstrom Claude ab 4.7 | 5.382 | 37 s | 3,1 min | berechnet |
| Bildstrom gpt-5 Kachelmodus | 1.820 | 110 s | 9,2 min | berechnet |
| Bildstrom Gemini 3 low | 560 | 6,0 min | 30 min | berechnet |
| ScreenCodec, Mittel über 8 Sequenzen | 56,6 | 59 min | 4,9 h | gemessen |
| ScreenCodec, ruhiger Bildschirm | 7,9 | 7,0 h | 35 h | berechnet aus Messwerten |

- Die 8 Sequenzen dauern 12 bis 20 Sekunden und umfassen 254 Bilder: Tippen, Fortschrittsbalken, Dialog, Fenster verschieben, Scrollen, Mauszeiger, Benachrichtigung, Arbeitsablauf.
- Ein einzelner Bildschirm kostet 474 Tokens im Mittel (40 Testbildschirme, 260 bis 760). Ein Bild kostet 910 bis 2.691 Tokens.
- Eine Stunde ScreenCodec umfasst 203.760 Tokens für 0,82 US-Dollar. Der Bildstrom kostet 77,50 US-Dollar (berechnet).
- Gegen einen optimierten Bildstrom, der nur geänderte Bildausschnitte sendet, ist ScreenCodec 3,2- bis 4,4-mal billiger (gemessen, Prüfrunde 1). Die Genauigkeit dieser Vergleichsbasis ist ungemessen.

### Blindtest

55 Fragen zu 3 Bildschirmen und 1 Sequenz mit 40 Bildern. Leser: Claude Opus 5.5, ein Durchlauf pro Bedingung (gemessen).

| Bedingung | Eingabe-Tokens | richtig |
|---|---|---|
| ScreenCodec | 2.935 | 95,5 % |
| Bilder (43 PNG, 1920 x 1080) | 79.292 bis 115.713 | 99,1 % |
| keine Eingabe (Raten) | 0 | 48,2 % |

| Eingabe | Fragen | ScreenCodec | Bilder | Raten |
|---|---|---|---|---|
| Mail-Fenster hinter Anmeldedialog | 14 | 100 % | 100 % | 35,7 % |
| dunkler Foto-Betrachter | 13 | 80,8 % | 100 % | 46,2 % |
| Einstellungsdialog (HTML) | 14 | 100 % | 100 % | 46,4 % |
| Arbeitsablauf, 40 Bilder | 14 | 100 % | 96,4 % | 64,3 % |

- ScreenCodec schlägt Raten auf 34 Fragen, Raten schlägt ScreenCodec auf 1 (Vorzeichentest p = 2 x 10^-9).
- Auf Einzelbildschirmen erzielt ScreenCodec 2,5- bis 3,7-mal mehr Punkte pro Token als Bilder.
- ScreenCodec verlor Punkte auf 3 Fragen, alle auf dem Foto-Betrachter. Eine Textzeile fehlte. Eine Zahl war falsch gelesen (129 % statt 12 %). Die Theme-Farbe erfasst der Prototyp bewusst nicht.
- Der Leser machte 0 eigene Fehler. Ohne die Theme-Frage liegt ScreenCodec bei 97,2 %.

### Erfassung und Lesegenauigkeit

Precision und Recall beziehen sich auf die erfassten Bedienelemente (Überlappung IoU mindestens 0,5). Die Zeichenfehlerrate misst den gelesenen Bildschirmtext.

| Testmenge | Bildschirme | Precision | Recall | Zeichenfehlerrate | Art |
|---|---|---|---|---|---|
| synthetische Testbildschirme | 40 | 0,99 | 0,99 | 2,7 % | gemessen |
| eigene HTML-Seiten, Entwicklung | 12 | 0,94 | 0,95 | 2,3 % | gemessen |
| neue HTML-Seiten, nach dem Einfrieren geschrieben | 4 | 0,68 | 0,85 | 0,1 % | gemessen |
| deutsche Oberflächen mit Umlauten | 8 | 1,00 | 0,99 | 5,2 % | gemessen |

Nachmessungen in den Prüfrunden 1 bis 3 (gemessen):

- Neue HTML-Seiten: Eine Korrektur hebt die Precision von 0,675 auf 0,979. Die Seiten haben die Korrektur angeregt, der Wert ist daher kein unabhängiger Testwert mehr.
- Deutsche Umlaute: Die Zeichenfehlerrate sinkt von 3,8 % auf 1,4 % (135 Textzeilen, Prüfrunde 2).
- 300 deutsche Oberflächentexte aus 50 Programmen: Die Zeichenfehlerrate sinkt von 2,4 % auf 1,7 % bis 2,0 %. Englische Texte bleiben bei 0,84 % (Prüfrunde 3).

### Rechenzeit

| Fall | Zeit pro Bild | Bedingung | Art |
|---|---|---|---|
| typisches Folgebild | 85 ms | 1 CPU-Kern | gemessen |
| neuer Bildschirm | 150 bis 290 ms | 4 bis 16 Threads | gemessen |
| neuer Bildschirm | 380 bis 600 ms | 1 CPU-Kern | gemessen |
| Folgebild unter Fremdlast | 289 ms Median, 370 ms p90 | geteilter Rechner, Last 10 bis 20 | gemessen |

Bei 2 FPS stehen 500 ms pro Bild zur Verfügung.

## Grenzen

- Alle Testbildschirme sind synthetisch oder selbst gebaute HTML-Seiten. Echte Desktops unter Windows, macOS, GTK und Qt, HiDPI-Skalierung und Videos sind ungetestet.
- Auf 4 neuen HTML-Seiten fällt die Precision auf 0,68. Diese Zahl ist die realistische Schätzung für unbekannte Oberflächen.
- Der Blindtest lief auf Entwicklungsdaten, mit einem Durchlauf pro Bedingung und einem Lesermodell. Die Bewertung war nicht verblindet.
- Bei 3 bis 4 abweichenden Fragen belegt der Test keine Gleichwertigkeit mit Bildern. Er zeigt, dass die gefragten Inhalte beim Modell ankommen.
- Ein Aufgabentest mit einem handelnden Agenten fehlt.
- Theme-Farben, Schriften sowie Hover- und gedrückte Zustände fehlen in der Ausgabe. Fotos und Videos beschreibt der Prototyp nur grob.
- Ganzseitiges Scrollen und Fensterwechsel kosten im Prototyp bis 948 Tok/s.
- Bildschirmtext erreicht das Modell ohne Herkunftsangabe. Ein Schutz gegen eingeschleuste Anweisungen fehlt im Prototyp.
- Tokens sind mit tiktoken o200k_base gezählt, Bild-Tokens mit den Formeln der Anbieter geschätzt. Die Verhältnisse sind Näherungen.
- Das Projekt lag ohne Versionskontrolle. Ob die Erfassung vor dem Bau der neuen HTML-Seiten eingefroren war, ist nicht prüfbar.

## Stand und Fahrplan

| Phase | Inhalt | Stand |
|---|---|---|
| Phase 1 | Prototyp, Labormessung, Blindtest | abgeschlossen |
| Prüfrunden 1 bis 3 | Gegenprüfung, Korrekturen, Nachmessungen | abgeschlossen |
| Phase 2 | Tests auf echten Desktops (Linux und Windows in virtuellen Maschinen). Ziel: Precision und Recall je mindestens 0,85 | geplant |
| Phase 3 | Blindtest auf fremden Seiten, 5 Durchläufe, Bewertung ohne Kenntnis der Bedingung | geplant |
| Phase 4 | Benchmark gegen etablierte Screenshot-Agenten auf OSWorld (369 Aufgaben). Ziel: 80 % des Screenshot-Erfolgs mit höchstens 10 % der Tokens | geplant |
| Phase 5 | Sicherheit und Datenschutz für Bildschirminhalte | geplant |

## Projektstruktur

```
screencodec/
  README.md
  MANIFEST.md
  requirements.txt
  testbett/      Testdaten, Generatoren, Bewertungsskripte
  ergebnisse/    Messwerte und Auswertungen
```

Das Repository enthält das Testbett und die Ergebnisse. Jede Datei steht mit Zweck und Größe in `MANIFEST.md`. Code und Methodik des Verfahrens sind nicht Teil dieses Repositorys.

## Zugehörige Arbeit

- Interner Forschungsbericht, November 2026, unveröffentlicht.
- Eigene Vorarbeit (2026): KI-Effizienz auf Consumer-Hardware. Unveröffentlicht.

## Lizenz

Alle Rechte vorbehalten. Keine Nutzung ohne Zustimmung.

Kontakt: auf Anfrage
