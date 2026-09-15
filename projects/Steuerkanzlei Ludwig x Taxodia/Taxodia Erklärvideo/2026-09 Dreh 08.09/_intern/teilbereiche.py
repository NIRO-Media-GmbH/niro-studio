"""Teilbereiche (Kürzungen, Sperren) wortgenau verorten. Aufruf: teilbereiche.py"""
import sys
from pathlib import Path
INTERN = Path(__file__).resolve().parent
sys.path.insert(0, str(INTERN))
from find_tc import fmt, load, locate, secs  # noqa: E402

Q = [
    # Kürzungen
    ("L_intro_A", "FX3_0222", "Hallo mein Name ist Friedrich Ludwig", "im Radius von fünfzig Kilometern", "07:50"),
    ("L_intro_B", "FX3_0222", "sind da Spezialisten in diesem Bereich", None, "07:50"),
    ("L_kap_A", "FX3_0222", "Wie bilde ich die jetzt aus", "Wir haben die Kapazitäten gar nicht", None),
    ("L_kap_A2", "FX3_0222", "Wir können nicht auch noch ein zwei Leute abstellen", "Ausbildung noch äh sicherstellen", None),
    ("L_kap_B", "FX3_0222", "Und deswegen ist 'ne Online-Ausbildung", "Das ist für uns ein Glücksfall", "04:30"),
    ("L_kap_B_ohne", "FX3_0222", "für uns 'n genialer Gewinn", "Das ist für uns ein Glücksfall", "04:30"),
    ("L_rech_A", "FX3_0222", "Wenn man das aus finanzieller Sicht betrachtet", "die 'ne fertige Ausbildung haben", "23:35"),
    ("L_rech_B", "FX3_0222", "Also es ist auch was die Kosten angeht", "Auftrag hier hier zu geben", None),
    ("L_fair_A", "FX3_0222", "Jeder jeder Kurs jeder Abschnitt", "Das ist sehr fair", None),
    ("L_fair_B", "FX3_0222", "Und wenn was Schlimmes ist", "da haben wir 'n Problem", None),
    ("L_woche", "FX3_0222", "Ich schaue jede Woche", "an den Tag legt", "19:45"),
    ("F_intro_A", "FX3_0223", "Hallo ich bin Jörn", "Online-Steuerfachschule", "00:45"),
    ("F_intro_A2", "FX3_0223", "mit dem Schwerpunkt des landwirtschaftlichen Steuerrechts", "ohne steuerrechtliche Vorkenntnisse", "00:45"),
    ("F_ein_A", "FX3_0223", "Der Einstiegskurs hat zweiunddreißig Unterrichtsstunden", "geht über vier Wochen", None),
    ("F_ein_A2", "FX3_0223", "so lange bleibt man in seinem bisherigen Beruf", None, None),
    ("F_ein_B", "FX3_0223", "man schafft ein Arbeitsverhältnis", "in der Kanzlei fortfahren", None),
    ("F_ampel_A", "FX3_0223", "Wir haben um einen guten Überblick", "Ampelprinzip eingeführt", None),
    ("F_ampel_A1", "FX3_0223", "Wir haben um einen", None, "22:20"),
    ("F_ampel_A2", "FX3_0223", "haben wir ein Controlling nach einem Ampelprinzip eingeführt", None, "22:20"),
    ("F_ampel_G", "FX3_0223", "Wenn der Teilnehmer das Soll", "dann läuft die Ampel in Grün", None),
    ("F_ampel_G2", "FX3_0223", "durchgeführt hat in der Woche", "dann läuft die Ampel in Grün", None),
    ("F_ampel_R", "FX3_0223", "Wenn der Teilnehmer ähm bis zu einer Woche", "mit dem Vorgesetzten der Kanzlei", None),
    ("F_cta_A", "FX3_0223", "ich kann nur appellieren", "über das Taxodia-System", "36:59"),
    ("F_cta_B", "FX3_0223", "Die Erfahrung zeigt", "Probieren Sie den Einstiegskurs aus", "36:59"),
    ("F_cta_C", "FX3_0223", "Und Sie haben mit uns im Grunde", "Rückmeldung geben werden", "36:59"),
    ("H_16_A", "FX3_0228", "Ich hab den Kurs bei der", "16 Stunden Unterricht pro Woche", None),
    ("H_regen_A", "FX3_0228", "das heißt wenn jetzt Regentage waren", "meiner Tätigkeit nachkommen kann", None),
    ("H_wochen_A", "FX3_0228", "Aber ich würd sagen ab den", "die ersten Tätigkeiten übernehmen", "08:50"),
    ("H_online_A", "FX3_0228", "Also mein Studium ist", "ob das so gut funktioniert", "04:45"),
    ("H_online_A2", "FX3_0228", "und da hatt ich dann bisschen Bedenken", "ob das so gut funktioniert", "04:45"),
    ("H_online_B", "FX3_0228", "Aber dadurch dass der Kurs wirklich online", "sondern wirklich als neuer Online-Kurs gedacht ist", None),
    ("H_online_C", "FX3_0228", "Von daher wurden die Zweifel", "sehr schnell genommen", None),
    ("H_note_A", "FX3_0228", "mein Abschluss mit eins Komma null sechs", "Ich bin sehr stolz drauf", "13:27"),
    # Sperren / Warnstellen
    ("X_recruiter", "FX3_0222", "Recruiter sind Geschäftsmodelle", "liefern nichts", None),
    ("X_veganer1", "FX3_0222", "Dann sind sie noch Veganer", "nix zu tun haben", None),
    ("X_veganer2", "FX3_0222", "Eine Sache die du nicht machen darfst", "Nein einfach nein", None),
    ("X_ausfall", "FX3_0222", "Dieser Umstand macht's", "um erfolgreich zu sein", None),
    ("X_veganer3", "FX3_0222", "Nee es hat also nur angezeigt", "dass sie alle Steakesser sein müssen", None),
    ("X_sueddeutschland", "FX3_0222", "Es gibt eigentlich nur noch uns in Süddeutschland", "sonst gibt's nichts mehr", None),
    ("X_zahlen", "FX3_0222", "wenn man circa 10.000 Euro rechnet", "in der Anfangsphase schon bezahlt", None),
    ("X_musterkurs", "FX3_0223", "dann können die durchaus zu uns kommen", "Wir finanzieren das", None),
    ("X_fall", "FX3_0223", "Ein aktueller Fall in der Taxodia", "auf jeden Fall funktioniert", None),
    ("X_durchfaller", "FX3_0223", "Wir haben auch aus der", "es gibt durchaus Durchfaller", None),
    ("X_tuer", "FX3_0223", "Ich habe ja in meiner beruflichen Laufbahn", "was ich mit der Taxodia vorhatte", None),
    ("X_fachwirt", "FX3_0228", "Mein Name ist Jan-Philipp", "Fachwirt ist ja eigentlich nicht mehr aktuell", None),
    ("X_ohne", "FX3_0228", "Ohne ohne den Taxodia-Kurs", None, "15:40"),
    ("X_heins_note_q", "FX3_0228", "Ich glaub du musst noch dazu sagen", "Das ist 'n scheidender Junge", None),
]
for kid, clip, a_phr, b_phr, nach in Q:
    w = load(clip)
    a, b = locate(w, a_phr, after_s=secs(nach) if nach else 0.0)
    if a is None:
        print(f"!! {kid}: nicht gefunden {a_phr!r}"); continue
    if b_phr:
        _, b = locate(w, b_phr, after_idx=a - 1, after_s=w[a]["start"])
        if b is None:
            print(f"!! {kid}: Ende nicht gefunden {b_phr!r}"); continue
    t0, t1 = w[a]["start"], w[b]["end"]
    nxt = w[b + 1] if b + 1 < len(w) else None
    prv = w[a - 1] if a > 0 else None
    print(f"{kid:<18} {clip} {fmt(t0)}–{fmt(t1)} ({t1-t0:4.1f} s)  davor '{prv['text'] if prv else ''}' +{(t0-prv['end']) if prv else 0:.2f}s | danach '{nxt['text'] if nxt else ''}' +{(nxt['start']-t1) if nxt else 0:.2f}s")
