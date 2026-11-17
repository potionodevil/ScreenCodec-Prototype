# Manifest: Testbett Bildschirm-Textbeschreibung

Alle geteilten Dateien. Freigegeben sind Testwerkzeuge (Generatoren, Fragen und Antworten, Bewertungsskript) und Ergebnistabellen.

| Pfad | Zweck | Herkunft | Größe (Bytes) |
|---|---|---|---|
| `.gitignore` | schließt Caches und erzeugte Daten aus | neu erstellt | 186 |
| `requirements.txt` | Python-Pakete der Testbett-Skripte | neu erstellt | 25 |
| `testbett/synth_gui.py` | erzeugt synthetische Desktop-Bildschirme 1920x1080 mit exakter Referenz (Elemente, Boxen, Texte, Zustände), Sequenzen mit 2 FPS und die zwei QA-Szenen | Prototyp, Kopfkommentar bereinigt, ein Beispielpfad ersetzt | 55.910 |
| `testbett/render_html.py` | rendert die HTML-Testseiten mit headless Chromium und liest die Referenz aus der Seite | Prototyp, Kommentare bereinigt, keine absoluten Pfade in den Metadaten | 2.390 |
| `testbett/html_pages/gt.js` | exportiert Referenzdaten (Typ, Box, Text, Zustand) aller markierten Elemente einer Testseite | Prototyp, Kommentar bereinigt | 3.685 |
| `testbett/html_pages/common.css` | gemeinsames Stylesheet der Testseiten | Prototyp, unverändert | 1.382 |
| `testbett/html_pages/login.html` | Testseite Anmeldung, 3 Zustände | Prototyp, unverändert | 3.737 |
| `testbett/html_pages/settings.html` | Testseite Einstellungen, 3 Zustände | Prototyp, unverändert | 8.042 |
| `testbett/html_pages/files.html` | Testseite Dateimanager, 3 Zustände | Prototyp, unverändert | 9.164 |
| `testbett/html_pages/editor.html` | Testseite Editor, 3 Zustände | Prototyp, unverändert | 7.309 |
| `testbett/html_pages/mail.html` | Testseite Mail (zurückgehaltene Seite), 2 Zustände | Prototyp, Produktname ersetzt | 5.902 |
| `testbett/html_pages/checkout.html` | Testseite Bestellung (zurückgehaltene Seite), 2 Zustände | Prototyp, unverändert | 5.624 |
| `testbett/html_pages/photo.png` | prozedural erzeugtes Landschaftsbild für die Dateimanager-Seite | Prototyp, unverändert | 247.565 |
| `testbett/qa/questions.json` | 55 Fragen zu 3 Bildschirmen und einer 40-Bilder-Sequenz | Prototyp, Anleitung neutral formuliert, Eingaben umbenannt | 7.135 |
| `testbett/qa/answers.json` | Referenzantworten aus Szenendefinition und Seitenreferenz | Prototyp, Quellenangabe neutral formuliert | 5.219 |
| `testbett/qa/blind_answers_text.json` | Antworten und Konfidenzen des Lesers mit Textbeschreibung (T) | Prototyp, Belegfelder entfernt | 5.027 |
| `testbett/qa/blind_answers_images.json` | Antworten und Konfidenzen des Lesers mit Bildern (I) | Prototyp, Belegfelder entfernt | 4.978 |
| `testbett/qa/blind_answers_control_noinput.json` | Antworten und Konfidenzen ohne Eingabe (C) | Prototyp, unverändert bis auf Format | 4.227 |
| `testbett/qa/score_blind.py` | rechnet Genauigkeit, Kalibrierung und Punkte pro Token aus den Einzelwertungen | Prototyp, Notizen und Formatbezüge entfernt, Tokenzahlen als Konstanten | 7.905 |
| `ergebnisse/blind_scores.json` | Einzelwertung pro Frage und Bedingung mit Konfidenz | erzeugt mit score_blind.py | 10.384 |
| `ergebnisse/qa_auswertung.md` | Auswertung der Blind-QA: Regeln, Genauigkeit, Kalibrierung, Tokenkosten, Fehler | neu geschrieben aus der Prototyp-Auswertung | 4.973 |
| `MANIFEST.md` | diese Liste | neu erstellt | - |

Summe der aufgeführten Dateien: 400.769 Bytes (0,4 MB). `README.md` und `assets/` werden getrennt gepflegt und sind hier nicht aufgeführt.

## Voraussetzungen

- Python 3.10+, `pip install -r requirements.txt`
- Schriften DejaVu Sans, Liberation Sans, Noto Sans, Roboto unter `/usr/share/fonts` (Pfade in `FONT_FILES` von `synth_gui.py`)
- Chromium im Pfad für `render_html.py`
- Aufrufe aus `testbett/`: `python synth_gui.py` (alle Daten, etwa 20 s), `python render_html.py` (etwa 10 s), `python qa/score_blind.py`

## Nicht enthalten

- Methodencode des Verfahrens und seine Konfiguration
- das interne Textformat, seine Beispiele und die daraus erzeugten QA-Eingaben
- Auswertungsskripte der Verbesserungsrunden, die Verfahrensschritte ausführen
- Messprotokolle, Register und Entwurfsnotizen
- erzeugte Bild- und Referenzdaten (etwa 52 MB); `synth_gui.py` und `render_html.py` erzeugen sie neu
