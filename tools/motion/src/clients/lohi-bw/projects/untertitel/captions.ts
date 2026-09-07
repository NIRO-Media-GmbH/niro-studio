// ============================================================
// LohiBW — Recruiting-Ads, Untertiteldaten
// ERZEUGT von _intern/build_captions.py — nicht von Hand ändern.
// Quelle: ElevenLabs Scribe auf dem fertigen Schnitt + gemessene
// Belegung der bestehenden Keyword-Kästen (overlays.json).
//
// mode "normal"  = Untertitel im Mittelband
// mode "shifted" = weicht einem langen Keyword-Kasten nach unten aus
// Seiten unter kurzen Kästen und im Hook-Fenster fehlen bewusst.
// ============================================================

export type CaptionWord = {
  text: string;
  startSec: number;
  endSec: number;
  accent?: boolean;
};

export type CaptionPage = {
  startSec: number;
  endSec: number;
  mode: "normal" | "shifted";
  lines: CaptionWord[][];
};

/** Fenster, in dem das Untertitelband nach unten ausweicht. */
export type ShiftWindow = { startSec: number; endSec: number };

export const VIDEO_1: CaptionPage[] = [
  {
    "startSec": 0.199,
    "endSec": 1.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "In",
          "startSec": 0.199,
          "endSec": 0.299
        },
        {
          "text": "welcher",
          "startSec": 0.34,
          "endSec": 0.579
        },
        {
          "text": "Steuerkanzlei",
          "startSec": 0.62,
          "endSec": 1.319,
          "accent": true
        },
        {
          "text": "wirst",
          "startSec": 1.399,
          "endSec": 1.62
        }
      ],
      [
        {
          "text": "du",
          "startSec": 1.659,
          "endSec": 1.759
        }
      ]
    ]
  },
  {
    "startSec": 8.559,
    "endSec": 9.779,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "In",
          "startSec": 8.559,
          "endSec": 8.64
        },
        {
          "text": "den",
          "startSec": 8.659,
          "endSec": 8.8
        },
        {
          "text": "meisten",
          "startSec": 8.84,
          "endSec": 9.159
        },
        {
          "text": "Kanzleien",
          "startSec": 9.199,
          "endSec": 9.659
        }
      ]
    ]
  },
  {
    "startSec": 9.779,
    "endSec": 11.46,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "bleibst",
          "startSec": 9.779,
          "endSec": 10.019
        },
        {
          "text": "du",
          "startSec": 10.059,
          "endSec": 10.139
        },
        {
          "text": "als",
          "startSec": 10.179,
          "endSec": 10.319
        }
      ],
      [
        {
          "text": "Steuerfachangestellter",
          "startSec": 10.42,
          "endSec": 11.399,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 11.46,
    "endSec": 13.96,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "ein",
          "startSec": 11.46,
          "endSec": 11.559
        },
        {
          "text": "Sachbearbeiter.",
          "startSec": 11.639,
          "endSec": 12.439,
          "accent": true
        },
        {
          "text": "Für",
          "startSec": 12.5,
          "endSec": 12.599
        },
        {
          "text": "eine",
          "startSec": 12.639,
          "endSec": 12.84
        }
      ],
      [
        {
          "text": "Führungsrolle",
          "startSec": 12.899,
          "endSec": 13.619
        },
        {
          "text": "brauchst",
          "startSec": 13.679,
          "endSec": 13.92
        }
      ]
    ]
  },
  {
    "startSec": 13.96,
    "endSec": 17.539,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "du",
          "startSec": 13.96,
          "endSec": 14.019
        },
        {
          "text": "den",
          "startSec": 14.099,
          "endSec": 14.34
        },
        {
          "text": "Fachwirt",
          "startSec": 14.439,
          "endSec": 15.019
        },
        {
          "text": "oder",
          "startSec": 15.119,
          "endSec": 15.279
        },
        {
          "text": "ein",
          "startSec": 15.339,
          "endSec": 15.42
        }
      ],
      [
        {
          "text": "Steuerberaterexamen.",
          "startSec": 15.519,
          "endSec": 16.539,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 22.979,
    "endSec": 24.519,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Die",
          "startSec": 22.979,
          "endSec": 23.059
        },
        {
          "text": "meisten",
          "startSec": 23.1,
          "endSec": 23.42
        },
        {
          "text": "Beratungsstellen",
          "startSec": 23.459,
          "endSec": 24.199,
          "accent": true
        }
      ],
      [
        {
          "text": "werden",
          "startSec": 24.26,
          "endSec": 24.459
        }
      ]
    ]
  },
  {
    "startSec": 24.519,
    "endSec": 26.459,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "übergeben,",
          "startSec": 24.519,
          "endSec": 25.019
        },
        {
          "text": "nicht",
          "startSec": 25.319,
          "endSec": 25.479
        },
        {
          "text": "neu",
          "startSec": 25.519,
          "endSec": 25.659
        }
      ],
      [
        {
          "text": "gegründet.",
          "startSec": 25.719,
          "endSec": 26.239
        }
      ]
    ]
  },
  {
    "startSec": 26.459,
    "endSec": 27.539,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Du",
          "startSec": 26.459,
          "endSec": 26.5
        },
        {
          "text": "übernimmst",
          "startSec": 26.559,
          "endSec": 26.899
        },
        {
          "text": "deine",
          "startSec": 26.92,
          "endSec": 27.099
        },
        {
          "text": "Stelle",
          "startSec": 27.159,
          "endSec": 27.479
        }
      ]
    ]
  },
  {
    "startSec": 27.539,
    "endSec": 29.6,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "mit",
          "startSec": 27.539,
          "endSec": 27.639
        },
        {
          "text": "bestehenden",
          "startSec": 27.699,
          "endSec": 28.139,
          "accent": true
        },
        {
          "text": "Mitgliedern",
          "startSec": 28.199,
          "endSec": 28.639
        }
      ]
    ]
  },
  {
    "startSec": 33.38,
    "endSec": 34.399,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Wenig",
          "startSec": 33.38,
          "endSec": 33.639
        },
        {
          "text": "arbeiten",
          "startSec": 33.739,
          "endSec": 34.04
        },
        {
          "text": "und",
          "startSec": 34.079,
          "endSec": 34.159
        },
        {
          "text": "viel",
          "startSec": 34.239,
          "endSec": 34.34
        }
      ]
    ]
  },
  {
    "startSec": 34.399,
    "endSec": 35.88,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "verdienen",
          "startSec": 34.399,
          "endSec": 34.779
        },
        {
          "text": "gibt",
          "startSec": 35.0,
          "endSec": 35.139
        },
        {
          "text": "es",
          "startSec": 35.18,
          "endSec": 35.279
        },
        {
          "text": "hier",
          "startSec": 35.299,
          "endSec": 35.419
        },
        {
          "text": "nicht.",
          "startSec": 35.459,
          "endSec": 35.84
        }
      ]
    ]
  },
  {
    "startSec": 35.88,
    "endSec": 37.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Dein",
          "startSec": 35.88,
          "endSec": 36.02
        },
        {
          "text": "Einkommen",
          "startSec": 36.079,
          "endSec": 36.419
        },
        {
          "text": "hängt",
          "startSec": 36.459,
          "endSec": 36.599
        },
        {
          "text": "an",
          "startSec": 36.639,
          "endSec": 36.719
        }
      ],
      [
        {
          "text": "deinem",
          "startSec": 36.779,
          "endSec": 37.0
        },
        {
          "text": "Einsatz.",
          "startSec": 37.059,
          "endSec": 37.479
        }
      ]
    ]
  },
  {
    "startSec": 40.18,
    "endSec": 41.259,
    "mode": "shifted",
    "lines": [
      [
        {
          "text": "Also",
          "startSec": 40.18,
          "endSec": 40.479
        },
        {
          "text": "Klick",
          "startSec": 40.759,
          "endSec": 40.899
        },
        {
          "text": "auf",
          "startSec": 40.939,
          "endSec": 41.02
        },
        {
          "text": "den",
          "startSec": 41.079,
          "endSec": 41.2
        }
      ]
    ]
  },
  {
    "startSec": 41.259,
    "endSec": 42.86,
    "mode": "shifted",
    "lines": [
      [
        {
          "text": "Button,",
          "startSec": 41.259,
          "endSec": 41.639
        },
        {
          "text": "trag",
          "startSec": 41.959,
          "endSec": 42.2
        },
        {
          "text": "dich",
          "startSec": 42.259,
          "endSec": 42.459
        },
        {
          "text": "ein",
          "startSec": 42.54,
          "endSec": 42.819
        }
      ]
    ]
  },
  {
    "startSec": 42.86,
    "endSec": 45.34,
    "mode": "shifted",
    "lines": [
      [
        {
          "text": "und",
          "startSec": 42.86,
          "endSec": 42.959
        },
        {
          "text": "wir",
          "startSec": 43.02,
          "endSec": 43.119
        },
        {
          "text": "lernen",
          "startSec": 43.159,
          "endSec": 43.34
        },
        {
          "text": "uns",
          "startSec": 43.379,
          "endSec": 43.5
        },
        {
          "text": "persönlich",
          "startSec": 43.559,
          "endSec": 44.059
        }
      ],
      [
        {
          "text": "kennen.",
          "startSec": 44.119,
          "endSec": 44.34
        }
      ]
    ]
  }
];

export const VIDEO_1_SHIFTS: ShiftWindow[] = [
  {
    "startSec": 40.18,
    "endSec": 45.34
  }
];

export const VIDEO_2: CaptionPage[] = [
  {
    "startSec": 2.74,
    "endSec": 3.819,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "In",
          "startSec": 2.74,
          "endSec": 2.779
        },
        {
          "text": "der",
          "startSec": 2.819,
          "endSec": 2.899
        },
        {
          "text": "Kanzlei",
          "startSec": 2.939,
          "endSec": 3.5
        },
        {
          "text": "kennst",
          "startSec": 3.559,
          "endSec": 3.779
        }
      ]
    ]
  },
  {
    "startSec": 3.819,
    "endSec": 5.259,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "du",
          "startSec": 3.819,
          "endSec": 3.919
        },
        {
          "text": "das",
          "startSec": 3.98,
          "endSec": 4.099
        },
        {
          "text": "wahrscheinlich.",
          "startSec": 4.139,
          "endSec": 4.819
        }
      ]
    ]
  },
  {
    "startSec": 5.259,
    "endSec": 7.599,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Umsatzsteuervoranmeldung,",
          "startSec": 5.259,
          "endSec": 6.46,
          "accent": true
        }
      ],
      [
        {
          "text": "Lohnfristen,",
          "startSec": 6.699,
          "endSec": 7.379
        }
      ]
    ]
  },
  {
    "startSec": 7.599,
    "endSec": 10.099,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Jahresabschlüsse,",
          "startSec": 7.599,
          "endSec": 8.439,
          "accent": true
        },
        {
          "text": "immer",
          "startSec": 8.72,
          "endSec": 8.88
        }
      ],
      [
        {
          "text": "Vorarbeiten,",
          "startSec": 8.979,
          "endSec": 9.639
        },
        {
          "text": "immer",
          "startSec": 9.88,
          "endSec": 10.039
        }
      ]
    ]
  },
  {
    "startSec": 10.099,
    "endSec": 12.079,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "der",
          "startSec": 10.099,
          "endSec": 10.179
        },
        {
          "text": "nächste",
          "startSec": 10.239,
          "endSec": 10.519
        },
        {
          "text": "Stichtag.",
          "startSec": 10.579,
          "endSec": 11.079,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 16.379,
    "endSec": 16.879,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Bei",
          "startSec": 16.379,
          "endSec": 16.459
        },
        {
          "text": "uns",
          "startSec": 16.52,
          "endSec": 16.659
        },
        {
          "text": "in",
          "startSec": 16.699,
          "endSec": 16.78
        },
        {
          "text": "der",
          "startSec": 16.78,
          "endSec": 16.84
        }
      ]
    ]
  },
  {
    "startSec": 16.879,
    "endSec": 18.2,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Lohnsteuerhilfe,",
          "startSec": 16.879,
          "endSec": 17.579,
          "accent": true
        },
        {
          "text": "wir",
          "startSec": 17.659,
          "endSec": 17.719
        },
        {
          "text": "haben",
          "startSec": 17.779,
          "endSec": 17.899
        }
      ]
    ]
  },
  {
    "startSec": 24.039,
    "endSec": 24.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Bei",
          "startSec": 24.039,
          "endSec": 24.1
        },
        {
          "text": "der",
          "startSec": 24.139,
          "endSec": 24.219
        },
        {
          "text": "LohiBW",
          "startSec": 24.26,
          "endSec": 24.699
        }
      ]
    ]
  },
  {
    "startSec": 26.599,
    "endSec": 27.24,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Das",
          "startSec": 26.599,
          "endSec": 26.68
        },
        {
          "text": "heißt",
          "startSec": 26.739,
          "endSec": 26.86
        },
        {
          "text": "für",
          "startSec": 26.879,
          "endSec": 26.959
        },
        {
          "text": "dich",
          "startSec": 27.0,
          "endSec": 27.139
        }
      ]
    ]
  },
  {
    "startSec": 30.0,
    "endSec": 31.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Das",
          "startSec": 30.0,
          "endSec": 30.119
        },
        {
          "text": "heißt",
          "startSec": 30.179,
          "endSec": 30.319
        },
        {
          "text": "nicht,",
          "startSec": 30.359,
          "endSec": 30.479
        },
        {
          "text": "dass",
          "startSec": 30.5,
          "endSec": 30.639
        }
      ],
      [
        {
          "text": "Langeweile",
          "startSec": 30.699,
          "endSec": 31.179,
          "accent": true
        },
        {
          "text": "herrscht.",
          "startSec": 31.219,
          "endSec": 31.599
        }
      ]
    ]
  },
  {
    "startSec": 35.88,
    "endSec": 36.799,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Klick",
          "startSec": 35.88,
          "endSec": 36.04
        },
        {
          "text": "auf",
          "startSec": 36.079,
          "endSec": 36.159
        },
        {
          "text": "den",
          "startSec": 36.2,
          "endSec": 36.299
        },
        {
          "text": "Button,",
          "startSec": 36.34,
          "endSec": 36.599
        }
      ]
    ]
  },
  {
    "startSec": 36.799,
    "endSec": 37.619,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "trag",
          "startSec": 36.799,
          "endSec": 36.979
        },
        {
          "text": "dich",
          "startSec": 37.0,
          "endSec": 37.119
        },
        {
          "text": "ein",
          "startSec": 37.18,
          "endSec": 37.299
        },
        {
          "text": "und",
          "startSec": 37.54,
          "endSec": 37.599
        }
      ]
    ]
  },
  {
    "startSec": 37.619,
    "endSec": 39.739,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "wir",
          "startSec": 37.619,
          "endSec": 37.7
        },
        {
          "text": "lernen",
          "startSec": 37.739,
          "endSec": 37.899
        },
        {
          "text": "uns",
          "startSec": 37.939,
          "endSec": 38.04
        },
        {
          "text": "persönlich",
          "startSec": 38.079,
          "endSec": 38.439,
          "accent": true
        }
      ],
      [
        {
          "text": "kennen.",
          "startSec": 38.479,
          "endSec": 38.739
        }
      ]
    ]
  }
];

export const VIDEO_2_SHIFTS: ShiftWindow[] = [];

export const VIDEO_3: CaptionPage[] = [
  {
    "startSec": 3.74,
    "endSec": 5.319,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "In",
          "startSec": 3.74,
          "endSec": 3.799
        },
        {
          "text": "vielen",
          "startSec": 3.859,
          "endSec": 4.139
        },
        {
          "text": "Kanzleien",
          "startSec": 4.199,
          "endSec": 4.799,
          "accent": true
        },
        {
          "text": "sitzt",
          "startSec": 5.059,
          "endSec": 5.279
        }
      ]
    ]
  },
  {
    "startSec": 5.319,
    "endSec": 6.659,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "du",
          "startSec": 5.319,
          "endSec": 5.38
        },
        {
          "text": "im",
          "startSec": 5.42,
          "endSec": 5.5
        },
        {
          "text": "Hintergrund.",
          "startSec": 5.559,
          "endSec": 6.159,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 6.659,
    "endSec": 9.479,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Buchhaltung,",
          "startSec": 6.659,
          "endSec": 7.259,
          "accent": true
        },
        {
          "text": "Zahlen,",
          "startSec": 7.48,
          "endSec": 8.019
        }
      ],
      [
        {
          "text": "Formulare,",
          "startSec": 8.179,
          "endSec": 8.88
        }
      ]
    ]
  },
  {
    "startSec": 9.479,
    "endSec": 12.279,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Kontakt",
          "startSec": 9.479,
          "endSec": 9.899
        },
        {
          "text": "nach",
          "startSec": 9.939,
          "endSec": 10.079
        },
        {
          "text": "außen",
          "startSec": 10.159,
          "endSec": 10.439
        },
        {
          "text": "wenig.",
          "startSec": 10.84,
          "endSec": 11.279
        }
      ]
    ]
  },
  {
    "startSec": 16.039,
    "endSec": 17.1,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Auch",
          "startSec": 16.039,
          "endSec": 16.159
        },
        {
          "text": "wenn's",
          "startSec": 16.199,
          "endSec": 16.379
        },
        {
          "text": "traurig",
          "startSec": 16.44,
          "endSec": 16.779
        },
        {
          "text": "ist,",
          "startSec": 16.84,
          "endSec": 17.02
        }
      ]
    ]
  },
  {
    "startSec": 17.1,
    "endSec": 18.26,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "wenn",
          "startSec": 17.1,
          "endSec": 17.219
        },
        {
          "text": "einer",
          "startSec": 17.34,
          "endSec": 17.539
        },
        {
          "text": "seinen",
          "startSec": 17.6,
          "endSec": 17.799
        },
        {
          "text": "Partner",
          "startSec": 17.859,
          "endSec": 18.179
        }
      ]
    ]
  },
  {
    "startSec": 18.26,
    "endSec": 19.26,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "verloren",
          "startSec": 18.26,
          "endSec": 18.639,
          "accent": true
        },
        {
          "text": "hat,",
          "startSec": 18.699,
          "endSec": 18.879
        },
        {
          "text": "der",
          "startSec": 18.92,
          "endSec": 19.02
        },
        {
          "text": "sich",
          "startSec": 19.079,
          "endSec": 19.22
        }
      ]
    ]
  },
  {
    "startSec": 19.26,
    "endSec": 21.4,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "immer",
          "startSec": 19.26,
          "endSec": 19.379
        },
        {
          "text": "den",
          "startSec": 19.579,
          "endSec": 19.7
        },
        {
          "text": "ganzen",
          "startSec": 19.719,
          "endSec": 20.039
        },
        {
          "text": "Sachverhalt",
          "startSec": 20.079,
          "endSec": 20.579,
          "accent": true
        }
      ],
      [
        {
          "text": "gekümmert",
          "startSec": 20.639,
          "endSec": 21.02
        },
        {
          "text": "hat.",
          "startSec": 21.059,
          "endSec": 21.159
        }
      ]
    ]
  },
  {
    "startSec": 31.019,
    "endSec": 32.419,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Dann",
          "startSec": 31.019,
          "endSec": 31.179
        },
        {
          "text": "passt",
          "startSec": 31.239,
          "endSec": 31.42
        },
        {
          "text": "du",
          "startSec": 31.479,
          "endSec": 31.619
        },
        {
          "text": "zu",
          "startSec": 31.679,
          "endSec": 31.76
        },
        {
          "text": "uns.",
          "startSec": 31.84,
          "endSec": 32.099
        }
      ]
    ]
  },
  {
    "startSec": 32.419,
    "endSec": 33.34,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Also",
          "startSec": 32.419,
          "endSec": 32.599
        },
        {
          "text": "klick",
          "startSec": 32.88,
          "endSec": 33.04
        },
        {
          "text": "auf",
          "startSec": 33.079,
          "endSec": 33.159
        },
        {
          "text": "den",
          "startSec": 33.2,
          "endSec": 33.299
        }
      ]
    ]
  },
  {
    "startSec": 33.34,
    "endSec": 34.54,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Button,",
          "startSec": 33.34,
          "endSec": 33.739
        },
        {
          "text": "trag",
          "startSec": 33.799,
          "endSec": 33.959
        },
        {
          "text": "dich",
          "startSec": 34.0,
          "endSec": 34.119
        },
        {
          "text": "ein",
          "startSec": 34.18,
          "endSec": 34.299
        }
      ]
    ]
  },
  {
    "startSec": 34.54,
    "endSec": 36.659,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "und",
          "startSec": 34.54,
          "endSec": 34.619
        },
        {
          "text": "wir",
          "startSec": 34.639,
          "endSec": 34.7
        },
        {
          "text": "lernen",
          "startSec": 34.759,
          "endSec": 34.899
        },
        {
          "text": "uns",
          "startSec": 34.939,
          "endSec": 35.04
        },
        {
          "text": "persönlich",
          "startSec": 35.099,
          "endSec": 35.439,
          "accent": true
        }
      ],
      [
        {
          "text": "kennen.",
          "startSec": 35.479,
          "endSec": 35.659
        }
      ]
    ]
  }
];

export const VIDEO_3_SHIFTS: ShiftWindow[] = [];

export const VIDEO_4: CaptionPage[] = [
  {
    "startSec": 4.779,
    "endSec": 5.619,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Wenn",
          "startSec": 4.779,
          "endSec": 4.859
        },
        {
          "text": "der",
          "startSec": 4.88,
          "endSec": 4.94
        },
        {
          "text": "Mitarbeiter",
          "startSec": 4.98,
          "endSec": 5.44,
          "accent": true
        },
        {
          "text": "zu",
          "startSec": 5.5,
          "endSec": 5.559
        }
      ]
    ]
  },
  {
    "startSec": 5.619,
    "endSec": 6.339,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "mir",
          "startSec": 5.619,
          "endSec": 5.719
        },
        {
          "text": "kommt",
          "startSec": 5.779,
          "endSec": 5.94
        },
        {
          "text": "und",
          "startSec": 5.98,
          "endSec": 6.079
        },
        {
          "text": "sagt:",
          "startSec": 6.119,
          "endSec": 6.299
        }
      ]
    ]
  },
  {
    "startSec": 6.339,
    "endSec": 7.44,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "\"Hey,",
          "startSec": 6.339,
          "endSec": 6.5
        },
        {
          "text": "an",
          "startSec": 6.719,
          "endSec": 6.799
        },
        {
          "text": "dem",
          "startSec": 6.839,
          "endSec": 6.98
        },
        {
          "text": "Tag",
          "startSec": 7.039,
          "endSec": 7.299
        }
      ]
    ]
  },
  {
    "startSec": 7.44,
    "endSec": 8.899,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "sollte",
          "startSec": 7.44,
          "endSec": 7.699
        },
        {
          "text": "ich",
          "startSec": 7.779,
          "endSec": 7.919
        },
        {
          "text": "früher",
          "startSec": 8.079,
          "endSec": 8.34
        },
        {
          "text": "gehen.\"",
          "startSec": 8.42,
          "endSec": 8.739
        }
      ]
    ]
  },
  {
    "startSec": 9.18,
    "endSec": 10.579,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "\"Okay,",
          "startSec": 9.18,
          "endSec": 9.3
        },
        {
          "text": "ist",
          "startSec": 9.359,
          "endSec": 9.479
        },
        {
          "text": "kein",
          "startSec": 9.519,
          "endSec": 9.659
        },
        {
          "text": "Problem.\"",
          "startSec": 9.739,
          "endSec": 10.099
        }
      ]
    ]
  },
  {
    "startSec": 10.579,
    "endSec": 11.34,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Dann",
          "startSec": 10.579,
          "endSec": 10.739
        },
        {
          "text": "wird's",
          "startSec": 10.899,
          "endSec": 11.079
        },
        {
          "text": "halt",
          "startSec": 11.099,
          "endSec": 11.179
        },
        {
          "text": "an",
          "startSec": 11.239,
          "endSec": 11.3
        }
      ]
    ]
  },
  {
    "startSec": 11.34,
    "endSec": 12.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "dem",
          "startSec": 11.34,
          "endSec": 11.439
        },
        {
          "text": "anderen",
          "startSec": 11.5,
          "endSec": 11.699
        },
        {
          "text": "Tag",
          "startSec": 11.739,
          "endSec": 11.899
        },
        {
          "text": "nachgeholt.",
          "startSec": 11.939,
          "endSec": 12.619
        }
      ]
    ]
  },
  {
    "startSec": 18.639,
    "endSec": 20.539,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Also",
          "startSec": 18.639,
          "endSec": 18.819
        },
        {
          "text": "Arbeit",
          "startSec": 18.939,
          "endSec": 19.199
        },
        {
          "text": "und",
          "startSec": 19.239,
          "endSec": 19.34
        },
        {
          "text": "Privatleben,",
          "startSec": 19.399,
          "endSec": 20.239,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 20.539,
    "endSec": 21.42,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "bekommt",
          "startSec": 20.539,
          "endSec": 20.84
        },
        {
          "text": "man",
          "startSec": 20.86,
          "endSec": 20.86
        },
        {
          "text": "eigentlich",
          "startSec": 20.92,
          "endSec": 21.1
        },
        {
          "text": "ganz",
          "startSec": 21.139,
          "endSec": 21.359
        }
      ]
    ]
  },
  {
    "startSec": 21.42,
    "endSec": 22.659,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "gut",
          "startSec": 21.42,
          "endSec": 21.52
        },
        {
          "text": "unter",
          "startSec": 21.579,
          "endSec": 21.819
        },
        {
          "text": "einen",
          "startSec": 21.879,
          "endSec": 22.1
        },
        {
          "text": "Hut.",
          "startSec": 22.18,
          "endSec": 22.419
        }
      ]
    ]
  },
  {
    "startSec": 22.659,
    "endSec": 24.459,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Dauerhaftes",
          "startSec": 22.659,
          "endSec": 23.139,
          "accent": true
        },
        {
          "text": "Homeoffice",
          "startSec": 23.159,
          "endSec": 23.719
        },
        {
          "text": "vom",
          "startSec": 23.879,
          "endSec": 24.0
        }
      ],
      [
        {
          "text": "Wohnzimmer",
          "startSec": 24.019,
          "endSec": 24.42
        }
      ]
    ]
  },
  {
    "startSec": 24.459,
    "endSec": 25.959,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "aus",
          "startSec": 24.459,
          "endSec": 24.659
        },
        {
          "text": "gibt",
          "startSec": 24.84,
          "endSec": 24.979
        },
        {
          "text": "es",
          "startSec": 25.039,
          "endSec": 25.139
        },
        {
          "text": "nicht.",
          "startSec": 25.199,
          "endSec": 25.439
        }
      ]
    ]
  },
  {
    "startSec": 25.959,
    "endSec": 27.8,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Beratung",
          "startSec": 25.959,
          "endSec": 26.34
        },
        {
          "text": "läuft",
          "startSec": 26.42,
          "endSec": 26.619
        },
        {
          "text": "in",
          "startSec": 26.659,
          "endSec": 26.719
        },
        {
          "text": "der",
          "startSec": 26.739,
          "endSec": 26.84
        }
      ],
      [
        {
          "text": "Beratungsstelle.",
          "startSec": 26.859,
          "endSec": 27.599,
          "accent": true
        }
      ]
    ]
  },
  {
    "startSec": 29.619,
    "endSec": 30.76,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Das",
          "startSec": 29.619,
          "endSec": 29.739
        },
        {
          "text": "Einkommen",
          "startSec": 29.799,
          "endSec": 30.179
        },
        {
          "text": "richtet",
          "startSec": 30.359,
          "endSec": 30.579
        },
        {
          "text": "sich",
          "startSec": 30.619,
          "endSec": 30.719
        }
      ]
    ]
  },
  {
    "startSec": 30.76,
    "endSec": 31.699,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "nach",
          "startSec": 30.76,
          "endSec": 30.859
        },
        {
          "text": "der",
          "startSec": 30.899,
          "endSec": 31.0
        },
        {
          "text": "Leistung.",
          "startSec": 31.019,
          "endSec": 31.599
        }
      ]
    ]
  },
  {
    "startSec": 31.699,
    "endSec": 32.559,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Also",
          "startSec": 31.699,
          "endSec": 31.999
        },
        {
          "text": "wenn",
          "startSec": 32.059,
          "endSec": 32.18
        },
        {
          "text": "du",
          "startSec": 32.239,
          "endSec": 32.299
        },
        {
          "text": "einen",
          "startSec": 32.36,
          "endSec": 32.52
        }
      ]
    ]
  },
  {
    "startSec": 32.559,
    "endSec": 34.479,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Teilzeitjob",
          "startSec": 32.559,
          "endSec": 33.259
        },
        {
          "text": "oder",
          "startSec": 33.299,
          "endSec": 33.479
        },
        {
          "text": "Wiedereinstieg",
          "startSec": 33.5,
          "endSec": 34.299,
          "accent": true
        }
      ],
      [
        {
          "text": "in",
          "startSec": 34.36,
          "endSec": 34.439
        }
      ]
    ]
  },
  {
    "startSec": 34.479,
    "endSec": 35.979,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "den",
          "startSec": 34.479,
          "endSec": 34.579
        },
        {
          "text": "Steuerbereich",
          "startSec": 34.639,
          "endSec": 35.279,
          "accent": true
        },
        {
          "text": "suchst,",
          "startSec": 35.34,
          "endSec": 35.739
        },
        {
          "text": "dann",
          "startSec": 35.779,
          "endSec": 35.9
        }
      ]
    ]
  },
  {
    "startSec": 35.979,
    "endSec": 36.899,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "klick",
          "startSec": 35.979,
          "endSec": 36.159
        },
        {
          "text": "doch",
          "startSec": 36.2,
          "endSec": 36.34
        },
        {
          "text": "einfach",
          "startSec": 36.38,
          "endSec": 36.7
        },
        {
          "text": "auf",
          "startSec": 36.719,
          "endSec": 36.88
        }
      ]
    ]
  },
  {
    "startSec": 36.899,
    "endSec": 38.739,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "den",
          "startSec": 36.899,
          "endSec": 37.04
        },
        {
          "text": "Button,",
          "startSec": 37.079,
          "endSec": 37.479
        },
        {
          "text": "trag",
          "startSec": 37.54,
          "endSec": 37.759
        },
        {
          "text": "dich",
          "startSec": 37.819,
          "endSec": 37.959
        },
        {
          "text": "ein.",
          "startSec": 38.059,
          "endSec": 38.659
        }
      ]
    ]
  },
  {
    "startSec": 38.739,
    "endSec": 40.799,
    "mode": "normal",
    "lines": [
      [
        {
          "text": "Ich",
          "startSec": 38.739,
          "endSec": 38.88
        },
        {
          "text": "freue",
          "startSec": 38.899,
          "endSec": 39.099
        },
        {
          "text": "mich",
          "startSec": 39.139,
          "endSec": 39.279
        },
        {
          "text": "auf",
          "startSec": 39.34,
          "endSec": 39.52
        },
        {
          "text": "dich.",
          "startSec": 39.559,
          "endSec": 39.799
        }
      ]
    ]
  }
];

export const VIDEO_4_SHIFTS: ShiftWindow[] = [];
