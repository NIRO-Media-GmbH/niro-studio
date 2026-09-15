"""O-Ton-Kandidaten wortgenau verorten (nur FX3 = Ton-Kamera).

Aufruf: kandidaten.py [Filter]   -> druckt je Kandidat In/Out, Dauer, Sprecher,
Wortlaut und 3 s Kontext davor/danach (Regie-Stimmen am Schnittpunkt).
Schreibt _intern/kandidaten.json (Grundlage für Plan + Dauer-Summen).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

INTERN = Path(__file__).resolve().parent
sys.path.insert(0, str(INTERN))
from find_tc import fmt, load, locate, secs  # noqa: E402

# (id, clip, anfang, ende, nach)
K = [
    # Friedrich Ludwig — FX3_0222
    ("L_hook", "FX3_0222", "Anzeigen sind schon lange tot", None, None),
    ("L_intro", "FX3_0222", "Hallo mein Name ist Friedrich Ludwig", "Spezialisten in diesem Bereich", "07:50"),
    ("L_pain_a", "FX3_0222", "In der Vergangenheit hat es immer gut funktioniert", "diese Menschen sind uns weggebrochen", "08:40"),
    ("L_pain_b", "FX3_0222", "Und da hat man dann alles versucht", "da überhaupt jemand zu finden", "08:40"),
    ("L_pain_c", "FX3_0222", "Trotzdem war", "mit Landwirtschaft doch in Ruhe", None),
    ("L_kapazitaet", "FX3_0222", "Wie bilde ich die jetzt aus", "Das ist für uns ein Glücksfall", None),
    ("L_zurueck", "FX3_0222", "und deswegen kommen wir jetzt wieder dahin zurück", "Wir sind da sehr glücklich darüber", "05:27"),
    ("L_steuerrecht", "FX3_0222", "Im landwirtschaftlichen Bereich wo man", "um den Betrieb optimal beraten zu können", "10:27"),
    ("L_nixhilft", "FX3_0222", "da hilft das reine Steuerrecht gar nix", "um den Betrieb optimal beraten zu können", "10:27"),
    ("L_zwingend", "FX3_0222", "Wir brauchen zwingend und elementar", "um erfolgreich zu sein", None),
    ("L_andersrum", "FX3_0222", "Es ist viel leichter wie jemand", "andersrum funktioniert's letztendlich gar net", None),
    ("L_produktiv", "FX3_0222", "Aber man kann vom Grundsatz her sagen", "von Mitarbeit sprechen", None),
    ("L_aufgaben", "FX3_0222", "zuerst mit Buchhaltungen an sich an", "die kommen dann später", None),
    ("L_deadline", "FX3_0222", "Sie haben halt Sonntagabend Deadline", "weil man später in der Praxis auch braucht", None),
    ("L_jedewoche", "FX3_0222", "Das Controlling von Taxodia ist sehr angenehm", "an den Tag legt", None),
    ("L_fair", "FX3_0222", "Das Abrechnungssystem ist ja so schön", "da haben wir 'n Problem", None),
    ("L_rechnung", "FX3_0222", "ist es ein sehr adäquates Modell", "hier hier zu geben", "23:35"),
    ("L_480", "FX3_0222", "Und wenn man überlegt dass ich ja für vierhundertachtzig Euro", "gute Leute finden", None),
    ("L_online", "FX3_0222", "man kann eine Ausbildung wie's Taxodia macht", "hier funktioniert es", None),
    ("L_probieren", "FX3_0222", "Das wär der Ratschlag den ich jedem geben kann", "was halt in vielen anderen Bereichen es dann nicht tut", None),
    ("L_empfehlung", "FX3_0222", "Deshalb ist Taxodia für alle", "die Lösung die einfach alles bietet", None),
    # Jörn Flammann — FX3_0223
    ("F_intro", "FX3_0223", "Hallo ich bin Jörn", "praxistauglich einsatzbereit zu bekommen", "00:45"),
    ("F_erfahrung", "FX3_0223", "die Taxodia habe ich", "in Präsenz durchgeführt haben", None),
    ("F_fall", "FX3_0223", "Ein aktueller Fall in der Taxodia", "auf jeden Fall funktioniert", None),
    ("F_leichter", "FX3_0223", "Es ist leichter einem Landwirt", "als einem Steuerrechtler die Landwirtschaft", None),
    ("F_einstieg", "FX3_0223", "Der Einstiegskurs hat zweiunddreißig Unterrichtsstunden", "in der Kanzlei fortfahren", None),
    ("F_bachelor", "FX3_0223", "Der Kurs den wir anbieten ist ein Vorbereitungskurs", "seit 1975 so in der Form existiert", "11:41"),
    ("F_teil1", "FX3_0223", "Wenn jemand nach dem ersten Teil des Kurses", "Dazu ist er auf jeden Fall in der Lage", "14:52"),
    ("F_lerneinheit", "FX3_0223", "Der gesamte Kurs den haben wir modular aufgebaut", "ab mit den Übungen", None),
    ("F_software", "FX3_0223", "Das heißt also die Kanzlei bekommt den Mitarbeiter", "in der Praxis eingesetzt werden", None),
    ("F_reporting", "FX3_0223", "Grundsätzlich haben wir jedes Wochenende ein Reporting", "warum Sie hinterherhinken", None),
    ("F_anfassbar", "FX3_0223", "wir wollen eine anfassbare Steuerfachschule sein", "sondern zurückrufen", None),
    ("F_ampel", "FX3_0223", "Wir haben um einen guten Überblick zu behalten", "mit dem Vorgesetzten der Kanzlei", None),
    ("F_ernte", "FX3_0223", "Sollte jemand durch Krankheit Urlaub oder Erntezeit", "das Verpasste nachholen", "24:31"),
    ("F_vorquali", "FX3_0223", "Um bei uns im Kurs zu starten", "Zugang zum Steuerrecht", None),
    ("F_bezahl", "FX3_0223", "Deswegen haben wir unser Bezahlmodell so gewählt", "Transparenz und Vertrauen aus unserer Sicht", None),
    ("F_pruefung", "FX3_0223", "In den zwei Wochen vor der eigentlichen Abschlussprüfung", "in Live-Präsenz haben", None),
    ("F_ergebnis", "FX3_0223", "Wir haben äh in der Online-Ausbildung sogar die zwei Besten", "online sich fortbilden zu lassen", None),
    ("F_fuerwen", "FX3_0223", "Wir haben aber immer mehr das Problem", "ist natürlich die Online-Ausbildung ideal weil flexibel", None),
    ("F_stolz", "FX3_0223", "Das letzte Prüfungsergebnis im Bachelor Professional", "dieser Erfolg auch eingetreten ist", None),
    ("F_cta", "FX3_0223", "ich kann nur appellieren", "Rückmeldung geben werden", "36:59"),
    ("F_preis", "FX3_0223", "kann man fast sagen dass ein Online-Kurs", "an Kosten verursachen wird", None),
    # Jan Philipp Hein — FX3_0228
    ("H_intro", "FX3_0228", "Mein Name ist Jan-Philipp", "mittlerweile auch abgeschlossen", "00:39"),
    ("H_motivation", "FX3_0228", "Ich hab zu Hause 'n landwirtschaftlichen Betrieb", "diese Steuerthemen", None),
    ("H_wahlfach", "FX3_0228", "im Studium war äh Steuerrecht 'n Wahlfach", "das tägliche Doing in der Steuerkanzlei ist", None),
    ("H_beispiel", "FX3_0228", "So was hab ich jetzt im Studium", "ausführlich besprochen", None),
    ("H_regen", "FX3_0228", "wenn jetzt Regentage waren", "meiner Tätigkeit nachkommen kann", None),
    ("H_16std", "FX3_0228", "Ich hab den Kurs bei der", "um die Woche zu wiederholen", None),
    ("H_online", "FX3_0228", "Aber dadurch dass der Kurs wirklich online konzipiert wurde", "sehr schnell genommen", None),
    ("H_mail", "FX3_0228", "sobald man irgendwelche fachlichen Fragen hat", "am gleichen Tag noch 'ne Antwort", None),
    ("H_praxis", "FX3_0228", "Man hat durch den Taxodia-Kurs", "insbesondere beim Rechnungswesen entstehen", None),
    ("H_wochen", "FX3_0228", "nach den ersten fünf sechs Wochen", "die ersten Tätigkeiten übernehmen", None),
    ("H_pruefung", "FX3_0228", "Also die letzten zwei Wochen vor der Abschlussprüfung", "tatsächlich live", None),
    ("H_flammann", "FX3_0228", "durch die langjährige Erfahrung vom Herrn", "man fühlt sich gut vorbereitet", "10:10"),
    ("H_vertrauen", "FX3_0228", "nachdem ich die Fortbildung abgeschlossen hab", "im Steuerrecht sich erarbeitet hat", None),
    ("H_alleine", "FX3_0228", "Ich hätt gern vor dem Kurs gewusst", "nicht alleingelassen wird", None),
    ("H_note", "FX3_0228", "mein Abschluss mit eins Komma null sechs", "dass es so gut ähm äh wird", "13:27"),
    ("H_empfehlung", "FX3_0228", "ich würd die Fortbildung jedem empfehlen", "die Tage frei einteilen zu können", None),
    ("H_karriere", "FX3_0228", "Durch die Fortbildung vom Bachelor Professional", "vielleicht der Steuerberater", None),
    ("H_ohne", "FX3_0228", "ohne den Taxodia-Kurs wär ich ziemlich sicher", "diesen Karriereweg ermöglicht", None),
    ("H_ohne_kurz", "FX3_0228", "ohne den Taxodia-Kurs wär ich ziemlich sicher", "nicht im Steuerrecht gelandet", None),
    ("H_cta", "FX3_0228", "Also wenn auch du einen landwirtschaftlichen Hintergrund hast auf der Suche", "ob auch das Steuerrecht für dich was ist", "21:30"),
    ("H_cta_alt", "FX3_0228", "Also wenn du auch einen landwirtschaftlichen Hintergrund hast", "ob nicht auch das Steuerrecht für dich was ist", "20:07"),
]


def main() -> None:
    filt = sys.argv[1] if len(sys.argv) > 1 else ""
    out = []
    cache: dict[str, list] = {}
    for kid, clip, a_phr, b_phr, nach in K:
        if filt and filt not in kid:
            continue
        words = cache.setdefault(clip, load(clip))
        after_s = secs(nach) if nach else 0.0
        a, b = locate(words, a_phr, after_s=after_s)
        if a is None:
            print(f"!! {kid}: ANFANG NICHT GEFUNDEN {a_phr!r}")
            continue
        if b_phr:
            _, b = locate(words, b_phr, after_idx=a - 1, after_s=words[a]["start"])
            if b is None:
                print(f"!! {kid}: ENDE NICHT GEFUNDEN {b_phr!r}")
                continue
        t0, t1 = words[a]["start"], words[b]["end"]
        sprecher = sorted({w.get("speaker") for w in words[a:b + 1] if w.get("speaker")})
        text = " ".join(w["text"] for w in words[a:b + 1])
        vor = [w for w in words[:a] if w["end"] >= t0 - 3]
        nach_w = [w for w in words[b + 1:] if w["start"] <= t1 + 3]
        rec = {"id": kid, "clip": clip, "in": fmt(t0), "out": fmt(t1), "in_s": round(t0, 2),
               "out_s": round(t1, 2), "dauer_s": round(t1 - t0, 1), "sprecher": sprecher, "text": text,
               "davor": " ".join(f"{w['text']}[{(w.get('speaker') or '?')[-1]}]" for w in vor),
               "danach": " ".join(f"{w['text']}[{(w.get('speaker') or '?')[-1]}]" for w in nach_w),
               "luecke_davor_s": round(t0 - vor[-1]["end"], 2) if vor else None,
               "luecke_danach_s": round(nach_w[0]["start"] - t1, 2) if nach_w else None}
        out.append(rec)
        print(f"{kid:<14} {clip} {rec['in']}–{rec['out']} ({rec['dauer_s']:>5.1f} s) {sprecher}")
        print(f"   TEXT: {text}")
        print(f"   DAVOR ({rec['luecke_davor_s']} s): {rec['davor'][-160:]}")
        print(f"   DANACH ({rec['luecke_danach_s']} s): {rec['danach'][:160]}")
    if not filt:
        (INTERN / "kandidaten.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
