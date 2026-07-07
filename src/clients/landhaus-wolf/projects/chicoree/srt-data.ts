import { parseSrt } from "../../timeline/parse-srt";

const SRT_RAW = `1
00:00:00,020 --> 00:00:04,040
Sollen wir ab nächster Woche mit Chicorée im Gourmet arbeiten? Ich zeige euch jetzt mal unseren

2
00:00:04,040 --> 00:00:08,500
Vorschlag, wie wir es machen würden. Die meisten kennen Chicorée klassisch als Salat. Wir haben uns

3
00:00:08,500 --> 00:00:12,460
dafür entschieden, diesen einfach mal zu karamellisieren. Da haben wir verschiedene Komponenten.

4
00:00:12,580 --> 00:00:19,940
Einen weißen Portwein, Orangensaft und unser Sommelier hat einen 76er Riesling Auslöse aus der

5
00:00:19,940 --> 00:00:23,820
Schatzkammer geholt. So, jetzt haben wir hier den Chicorée. Wir vierteln den jetzt zuerst mal.

6
00:00:24,739 --> 00:00:30,850
Machen hinten den Strung raus. Dann gehen wir hin, schneiden den erstmal grob. in kleine Stücke.

7
00:00:31,289 --> 00:00:36,390
Hier haben wir jetzt den Topf, dann lasse ich da ein wenig Zucker reinrieseln. Jetzt müssen wir

8
00:00:36,390 --> 00:00:38,049
kurz warten, bis der leicht karamellisiert.

9
00:00:39,820 --> 00:00:43,820
Sieht man, es geht langsam los, es bilden sich Bläschen. Jetzt löschen wir zuerst mit ein bisschen

10
00:00:43,820 --> 00:00:44,439
Portwein ab,

11
00:00:48,979 --> 00:00:56,770
anschließend mit dem Orangensaft und ganz zum Schluss eben unsere Riesling-Ausläse von 76.

12
00:00:57,250 --> 00:00:58,609
Das sieht man schon an der Farbe.

13
00:01:00,920 --> 00:01:04,930
Jetzt schauen wir hier, dass sich die Karamellschicht unten ein bisschen löst. Jetzt bringen wir

14
00:01:04,930 --> 00:01:06,329
den Chicorée. Geben wir jetzt dazu.

15
00:01:10,129 --> 00:01:14,530
So, nur die Frage an dich. Sollen wir diese Chicorée-Variante nächste Woche Mittwoch im Gourmet

16
00:01:14,530 --> 00:01:15,209
-Restaurant servieren?`;

/** Parsed SRT entries for Chicorée video */
export const SRT = parseSrt(SRT_RAW);
