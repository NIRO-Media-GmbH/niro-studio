"use strict";
(() => {
  // ---------- Helfer ---------------------------------------------------------------------------------------------
  const $ = (sel, wurzel = document) => wurzel.querySelector(sel);
  const el = (tag, attrs = {}, ...kinder) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") e.className = v;
      else if (k === "text") e.textContent = v;
      else if (k === "html") e.innerHTML = v;
      else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
      else if (k === "checked" || k === "disabled" || k === "open" || k === "hidden") e[k] = true;
      else e.setAttribute(k, v);
    }
    for (const kind of kinder.flat(Infinity)) if (kind !== null && kind !== undefined && kind !== false) e.append(kind);
    return e;
  };
  const enc = encodeURIComponent;
  const ICON = {
    play: '<svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>',
    pause: '<svg viewBox="0 0 24 24"><path d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg>',
    zurueck: '<svg viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6 8.5 6V6z"/></svg>',
    vor: '<svg viewBox="0 0 24 24"><path d="M16 6h2v12h-2zM6 18l8.5-6L6 6z"/></svg>',
    schleife: '<svg viewBox="0 0 24 24"><path d="M7 7h10v3l4-4-4-4v3H5v6h2zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2z"/></svg>',
    ton: '<svg viewBox="0 0 24 24"><path d="M3 9v6h4l5 5V4L7 9zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4z"/></svg>',
    stumm: '<svg viewBox="0 0 24 24"><path d="M4.3 3 3 4.3 7.7 9H3v6h4l5 5v-6.7l4.3 4.3-1.4 1.4 2.8 2.8 1.3-1.3zM12 4 9.9 6.1 12 8.2zm4.5 8A4.5 4.5 0 0 0 14 8v2.2l2.5 2.5z"/></svg>',
    vollbild: '<svg viewBox="0 0 24 24"><path d="M7 14H5v5h5v-2H7zm-2-4h2V7h3V5H5zm12 7h-3v2h5v-5h-2zm-3-12v2h3v3h2V5z"/></svg>',
  };
  const ZUSTAND = { "review-offen": "Review offen", "bei-claude": "bei Claude", freigegeben: "Freigegeben", leer: "keine Version" };
  const STATUS = { offen: "offen", umgesetzt: "umgesetzt", rueckfrage: "Rückfrage", erledigt: "erledigt" };

  const Z = {
    index: null, route: {}, detail: null, detailStand: "", versionNr: null, version: null,
    autor: "", suche: "", fps: 25, frames: 0, frame: 0, video: null, dom: {}, pollTimer: null, rvfc: null,
    eingabe: { aktiv: false, frame: null, bis: null, allgemein: false }, hervor: null, startFrame: null,
  };
  try { Z.autor = localStorage.getItem("niroReviewAutor") || ""; } catch (e) { Z.autor = ""; }

  async function api(pfad, body) {
    const optionen = body ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) } : {};
    const r = await fetch("/api/" + pfad, optionen);
    const text = await r.text();
    let daten = {};
    try { daten = text ? JSON.parse(text) : {}; } catch (e) { daten = { fehler: text }; }
    if (!r.ok) throw new Error(daten.fehler || ("HTTP " + r.status));
    return daten;
  }

  const frameAusZeit = (t, fps = Z.fps) => Math.max(0, Math.floor(t * fps + 0.001));
  function tc(frame, fps = Z.fps) {
    if (frame === null || frame === undefined) return "—";
    const b = Math.max(1, Math.round(fps));
    const s = Math.floor(frame / b), ff = frame % b;
    return [Math.floor(s / 3600), Math.floor((s % 3600) / 60), s % 60, ff].map((n) => String(n).padStart(2, "0")).join(":");
  }
  function wann(iso) {
    if (!iso) return "";
    const heute = new Date().toISOString().slice(0, 10);
    const t = iso.slice(11, 16);
    return iso.slice(0, 10) === heute ? t : `${iso.slice(8, 10)}.${iso.slice(5, 7)}. ${t}`;
  }
  function toast(text, art = "", knopf = null) {
    const t = el("div", { class: "toast " + art }, el("span", { text }));
    if (knopf) t.append(el("button", { class: "primaer", text: knopf.text, onclick: () => { knopf.tu(); t.remove(); } }));
    t.append(el("button", { class: "leise", text: "×", onclick: () => t.remove() }));
    $("#toasts").append(t);
    setTimeout(() => t.remove(), art === "fehler" ? 12000 : 7000);
  }
  const fehler = (e) => toast(e && e.message ? e.message : String(e), "fehler");

  // ---------- Routing --------------------------------------------------------------------------------------------
  function route() {
    const h = location.hash.replace(/^#\/?/, "");
    const t = h ? h.split("/").map((s) => { try { return decodeURIComponent(s); } catch (e) { return s; } }) : [];
    const r = { kunde: t[0] || null, projekt: t[1] || null, video: t[2] || null, version: null, frame: null };
    if (t[3] && /^V\d+$/.test(t[3])) r.version = parseInt(t[3].slice(1), 10);
    if (t[4] && /^F\d+$/.test(t[4])) r.frame = parseInt(t[4].slice(1), 10);
    return r;
  }
  function pfad(kunde, projekt, video, version, frame) {
    const teile = [kunde, projekt, video].filter((x) => x !== null && x !== undefined).map(enc);
    if (version) teile.push("V" + version);
    if (version && frame !== null && frame !== undefined) teile.push("F" + frame);
    return "#/" + teile.join("/");
  }
  const geheZu = (...a) => { location.hash = pfad(...a); };

  // ---------- Index, Baum, Krumen --------------------------------------------------------------------------------
  async function ladeIndex(frisch = false) {
    try { Z.index = await api("index" + (frisch ? "?frisch=1" : "")); }
    catch (e) { if (!Z.index) Z.index = { kunden: [] }; if (!/NAS/.test(e.message)) fehler(e); }
    return Z.index;
  }
  function projekte() {
    const out = [];
    for (const k of Z.index.kunden) for (const p of k.projekte) out.push({ kunde: k.name, ...p });
    return out;
  }
  function projekt(kunde, name) { return projekte().find((p) => p.kunde === kunde && p.name === name) || null; }
  function renderBaum() {
    const baum = $("#baum");
    const q = Z.suche.trim().toLowerCase();
    const r = Z.route;
    baum.replaceChildren();
    for (const k of Z.index.kunden) {
      const ps = k.projekte.filter((p) => !q || (k.name + " " + p.name).toLowerCase().includes(q) || p.videos.some((v) => v.titel.toLowerCase().includes(q)));
      if (!ps.length) continue;
      const kunde = el("div", { class: "kunde" }, el("div", { class: "kunde-name", text: k.name }));
      for (const p of ps) {
        kunde.append(el("a", { class: "projekt" + (r.kunde === k.name && r.projekt === p.name ? " aktiv" : ""), href: pfad(k.name, p.name) },
          el("span", { class: "name", text: p.name }),
          p.review_offen ? el("span", { class: "zahl gruen", text: String(p.review_offen), title: p.review_offen + " im Review" + (p.offen ? " · " + p.offen + " offene Kommentare" : "") }) : null,
          p.bei_claude ? el("span", { class: "zahl blau", text: String(p.bei_claude), title: p.bei_claude + " bei Claude" }) : null));
      }
      baum.append(kunde);
    }
    if (!baum.children.length) baum.append(el("div", { class: "leer", text: Z.index.kunden.length ? "Nichts gefunden." : "Noch keine Reviews." }));
  }
  function renderKrumen() {
    const r = Z.route, k = $("#krumen");
    k.replaceChildren();
    if (!r.kunde) return;
    k.append(el("a", { href: "#/", text: "Projekte" }), el("span", { class: "trenner", text: "›" }));
    if (!r.video) { k.append(el("span", { class: "aktuell", text: `${r.kunde} · ${r.projekt}` })); return; }
    k.append(el("a", { href: pfad(r.kunde, r.projekt), text: `${r.kunde} · ${r.projekt}` }), el("span", { class: "trenner", text: "›" }),
      el("span", { class: "aktuell", text: r.video }));
  }

  // ---------- Übersichten ----------------------------------------------------------------------------------------
  function chipZustand(z) { return el("span", { class: "chip zustand " + z, text: ZUSTAND[z] || z }); }
  function renderStart() {
    const inhalt = $("#inhalt");
    const ps = projekte();
    const raster = el("div", { class: "raster" });
    for (const p of ps) {
      const letzte = p.videos.map((v) => v.angelegt || "").sort().pop() || "";
      raster.append(el("div", { class: "karte projekt-karte", onclick: () => geheZu(p.kunde, p.name) },
        el("div", { class: "text" },
          el("div", { class: "gedaempft", text: p.kunde }),
          el("div", { class: "titel", text: p.name }),
          el("div", { class: "meta" }, el("span", { text: `${p.videos.length} Video${p.videos.length === 1 ? "" : "s"}` }), el("span", { text: wann(letzte) })),
          el("div", { class: "meta" },
            p.review_offen ? el("span", { class: "chip review-offen", text: `${p.review_offen} im Review` }) : el("span"),
            p.bei_claude ? el("span", { class: "chip bei-claude", text: `${p.bei_claude} bei Claude` }) : el("span")))));
    }
    inhalt.replaceChildren(el("div", { class: "uebersicht" }, el("h1", { text: "Projekte" }),
      el("div", { class: "unter", text: ps.length ? `${ps.length} Projekt${ps.length === 1 ? "" : "e"} im Review` : "Noch keine Reviews — Claude legt Stände mit „review.py hinzufuegen“ ab." }),
      raster));
  }
  function renderProjekt() {
    const r = Z.route, inhalt = $("#inhalt");
    const p = projekt(r.kunde, r.projekt);
    if (!p) { inhalt.replaceChildren(el("div", { class: "leer", text: `Kein Review-Projekt ${r.kunde}/${r.projekt}.` })); return; }
    const q = Z.suche.trim().toLowerCase();
    const raster = el("div", { class: "raster" });
    for (const v of p.videos) {
      if (q && !v.titel.toLowerCase().includes(q)) continue;
      raster.append(el("div", { class: "karte", onclick: () => geheZu(p.kunde, p.name, v.titel) },
        el("div", { class: "bild" },
          v.vorschau ? el("img", { src: v.vorschau, alt: "", loading: "lazy" }) : el("span", { class: "gedaempft", text: "kein Bild" }),
          v.neueste ? el("span", { class: "chip version", text: "V" + v.neueste }) : null,
          chipZustand(v.zustand)),
        el("div", { class: "text" },
          el("div", { class: "titel", text: v.titel, title: v.titel }),
          el("div", { class: "meta" },
            el("span", { text: v.gesamt ? `${v.gesamt} Kommentar${v.gesamt === 1 ? "" : "e"}${v.offen ? ` · ${v.offen} offen` : ""}` : "keine Kommentare" }),
            el("span", { text: wann(v.angelegt) })),
          v.notiz ? el("div", { class: "meta gedaempft", text: v.notiz, title: v.notiz }) : null)));
    }
    inhalt.replaceChildren(el("div", { class: "uebersicht" }, el("h1", { text: p.name }),
      el("div", { class: "unter", text: `${p.kunde} · ${p.videos.length} Video${p.videos.length === 1 ? "" : "s"}${p.review_offen ? ` · ${p.review_offen} im Review` : ""}${p.bei_claude ? ` · ${p.bei_claude} bei Claude` : ""}` }),
      raster.children.length ? raster : el("div", { class: "leer", text: "Nichts gefunden." })));
  }

  // ---------- Player ---------------------------------------------------------------------------------------------
  async function ladeDetail() {
    const r = Z.route;
    return api(`video?kunde=${enc(r.kunde)}&projekt=${enc(r.projekt)}&video=${enc(r.video)}`);
  }
  async function renderPlayer() {
    const r = Z.route, inhalt = $("#inhalt");
    let detail;
    try { detail = await ladeDetail(); }
    catch (e) { inhalt.replaceChildren(el("div", { class: "leer", text: "Video nicht gefunden: " + e.message })); return; }
    Z.detail = detail; Z.detailStand = JSON.stringify(detail);
    const nrs = detail.versionen.map((v) => v.nr);
    if (!nrs.length) { inhalt.replaceChildren(el("div", { class: "leer", text: "Dieses Video hat noch keine Version." })); return; }
    Z.versionNr = r.version && nrs.includes(r.version) ? r.version : nrs[nrs.length - 1];
    Z.startFrame = r.frame;
    Z.eingabe = { aktiv: false, frame: null, bis: null, allgemein: false };
    Z.hervor = null;
    bauePlayer();
    Z.pollTimer = setInterval(() => aktualisierePlayer().catch(() => {}), 5000);
  }
  function versionAktuell() { return Z.detail.versionen.find((v) => v.nr === Z.versionNr); }
  function versionBasis() {
    const v = versionAktuell();
    return v && v.basis ? Z.detail.versionen.find((x) => x.nr === v.basis) || null : null;
  }

  function bauePlayer() {
    const inhalt = $("#inhalt");
    const v = versionAktuell();
    Z.version = v; Z.fps = Number(v.fps) || 25; Z.frames = Number(v.frames) || 0; Z.frame = 0;
    const video = el("video", { src: v.video_url, playsinline: "", preload: "auto" });
    Z.video = video;
    const d = Z.dom = {};
    d.kopf = el("div", { class: "player-kopf" });
    d.zeit = el("span", { class: "zeit" }, el("span", { text: tc(0) }), el("small", { text: `F 0 / ${Z.frames}` }));
    d.fortschritt = el("div", { class: "fortschritt" });
    d.kopfPunkt = el("div", { class: "kopf" });
    d.marker = el("div", { class: "marker-schicht" });
    d.scrubber = el("div", { class: "scrubber", title: "Klicken oder ziehen" }, el("div", { class: "spur" }), d.fortschritt, d.marker, d.kopfPunkt);
    d.play = el("button", { class: "knopf", html: ICON.play, title: "Play/Pause (Leertaste)", onclick: umschalten });
    d.schleife = el("button", { class: "knopf", html: ICON.schleife, title: "Schleife", onclick: () => { video.loop = !video.loop; d.schleife.classList.toggle("aktiv", video.loop); } });
    d.ton = el("button", { class: "knopf", html: ICON.ton, title: "Stumm (M)", onclick: stumm });
    const lautstaerke = el("input", { type: "range", min: "0", max: "1", step: "0.02", value: "1", title: "Lautstärke", oninput: (ev) => { video.volume = Number(ev.target.value); video.muted = false; d.ton.innerHTML = ICON.ton; } });
    const leiste = el("div", { class: "leiste" },
      d.play,
      el("button", { class: "knopf", html: ICON.zurueck, title: "Ein Frame zurück (←)", onclick: () => schritt(-1) }),
      el("button", { class: "knopf", html: ICON.vor, title: "Ein Frame vor (→)", onclick: () => schritt(1) }),
      d.zeit, d.scrubber,
      el("span", { class: "zeit", text: tc(Math.max(0, Z.frames - 1)), title: "Dauer" }),
      d.schleife, d.ton, lautstaerke,
      el("button", { class: "knopf", html: ICON.vollbild, title: "Vollbild (F)", onclick: vollbild }));
    d.notiz = el("div", { class: "notiz" });
    const buehne = el("div", { class: "buehne" }, el("div", { class: "video-rahmen" }, video), leiste, d.notiz);
    d.seite = el("aside", { class: "kommentare" });
    inhalt.replaceChildren(el("div", { class: "player" }, d.kopf, el("div", { class: "player-koerper" }, buehne, d.seite)));
    renderKopf(); renderSeite();

    // Video-Ereignisse
    video.addEventListener("loadedmetadata", () => {
      if (!Z.frames && video.duration) { Z.frames = Math.round(video.duration * Z.fps); d.zeit.lastChild.textContent = `F 0 / ${Z.frames}`; }
      if (Z.startFrame !== null && Z.startFrame !== undefined) { springe(Z.startFrame); Z.startFrame = null; }
      else springe(0);  // erstes Bild zeichnen (sonst bleibt der Player bis zum Play schwarz)
      renderMarker();
    });
    video.addEventListener("play", () => { d.play.innerHTML = ICON.pause; frameSchleife(); });
    video.addEventListener("pause", () => { d.play.innerHTML = ICON.play; setzeFrame(frameAusZeit(video.currentTime)); });
    video.addEventListener("ended", () => { d.play.innerHTML = ICON.play; });
    video.addEventListener("timeupdate", () => { if (!video.requestVideoFrameCallback) setzeFrame(frameAusZeit(video.currentTime)); });
    video.addEventListener("seeked", () => { if (!video.seeking) setzeFrame(frameAusZeit(video.currentTime)); });
    video.addEventListener("click", umschalten);
    video.addEventListener("error", () => toast("Video lässt sich nicht laden (" + (video.error ? video.error.message || video.error.code : "?") + ").", "fehler"));

    // Scrubber
    let zieht = false;
    const frameAusEreignis = (ev) => {
      const r = d.scrubber.getBoundingClientRect();
      const anteil = Math.min(1, Math.max(0, (ev.clientX - r.left) / r.width));
      return Math.round(anteil * Math.max(0, Z.frames - 1));
    };
    d.scrubber.addEventListener("pointerdown", (ev) => { if (ev.target.classList.contains("marker")) return; zieht = true; d.scrubber.setPointerCapture(ev.pointerId); video.pause(); springe(frameAusEreignis(ev)); });
    d.scrubber.addEventListener("pointermove", (ev) => { if (zieht) springe(frameAusEreignis(ev)); });
    d.scrubber.addEventListener("pointerup", () => { zieht = false; });
    d.scrubber.addEventListener("pointercancel", () => { zieht = false; });
  }

  function frameSchleife() {
    const video = Z.video;
    if (!video || !video.requestVideoFrameCallback) return;
    if (Z.rvfc) video.cancelVideoFrameCallback(Z.rvfc);
    const cb = (now, meta) => { if (Z.video !== video) return; setzeFrame(frameAusZeit(meta.mediaTime)); if (!video.paused) Z.rvfc = video.requestVideoFrameCallback(cb); };
    Z.rvfc = video.requestVideoFrameCallback(cb);
  }
  function setzeFrame(f) {
    const max = Z.frames > 0 ? Z.frames - 1 : Math.max(f, 0);
    f = Math.max(0, Math.min(max, f));
    Z.frame = f;
    const d = Z.dom;
    if (!d.zeit) return;
    d.zeit.firstChild.textContent = tc(f);
    d.zeit.lastChild.textContent = `F ${f} / ${Z.frames}`;
    const anteil = Z.frames > 1 ? (f / (Z.frames - 1)) * 100 : 0;
    d.fortschritt.style.width = anteil + "%";
    d.kopfPunkt.style.left = anteil + "%";
  }
  function springe(f) {
    const video = Z.video;
    f = Math.max(0, Math.min(Z.frames > 0 ? Z.frames - 1 : f, Math.round(f)));
    video.currentTime = (f + 0.5) / Z.fps;
    setzeFrame(f);
  }
  function schritt(n) { Z.video.pause(); springe(Z.frame + n); }
  function umschalten() { const v = Z.video; if (v.paused) { if (v.ended || (Z.frames && Z.frame >= Z.frames - 1)) springe(0); v.play().catch(() => {}); } else v.pause(); }
  function stumm() { const v = Z.video; v.muted = !v.muted; Z.dom.ton.innerHTML = v.muted ? ICON.stumm : ICON.ton; }
  function vollbild() { const r = Z.video.closest(".video-rahmen"); if (document.fullscreenElement) document.exitFullscreen(); else if (r.requestFullscreen) r.requestFullscreen(); else if (Z.video.webkitEnterFullscreen) Z.video.webkitEnterFullscreen(); }

  // ---------- Kopf, Marker, Kommentar-Seite ---------------------------------------------------------------------
  function renderKopf() {
    const d = Z.dom, det = Z.detail, v = versionAktuell();
    const zustand = det.video.freigegeben ? "freigegeben" : (v.abgeschlossen ? "bei-claude" : "review-offen");
    const pillen = el("div", { class: "versionen" }, det.versionen.map((x) => el("button", { class: x.nr === Z.versionNr ? "aktiv" : "", text: "V" + x.nr, title: (x.notiz || "") + (x.abgeschlossen ? " · abgeschlossen" : ""), onclick: () => geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, x.nr) })));
    const aktionen = el("div", { class: "aktionen" });
    if (det.video.freigegeben) {
      aktionen.append(el("button", { text: "Freigabe zurücknehmen", onclick: () => videoAktion("video/freigabe_zuruecknehmen") }));
    } else {
      aktionen.append(v.abgeschlossen
        ? el("button", { text: "Wieder öffnen", onclick: () => versionAktion("version/wieder_oeffnen") })
        : el("button", { class: "primaer", text: "Review abschließen", title: "Sperrt V" + v.nr + " für neue Kommentare — dann Claude Bescheid sagen", onclick: () => versionAktion("version/abschliessen") }));
      aktionen.append(el("button", { text: "Freigeben", title: "Video ist fertig", onclick: () => { if (confirm(`„${det.video.titel}“ freigeben?`)) videoAktion("video/freigeben"); } }));
    }
    d.kopf.replaceChildren(el("h1", { text: det.video.titel, title: det.video.titel }), chipZustand(zustand), pillen, aktionen);
    const teile = [`V${v.nr} · ${wann(v.angelegt)}${v.von ? " · " + v.von : ""} · ${Number(v.dauer_s || 0).toFixed(2)} s · ${v.breite}×${v.hoehe} · ${Z.fps} fps`];
    d.notiz.replaceChildren(...[el("span", { text: teile[0] }), v.notiz ? el("span", { html: " · <b>Notiz:</b> " }) : null, v.notiz ? el("span", { text: v.notiz }) : null,
      v.abgeschlossen ? el("span", { text: ` · abgeschlossen ${wann(v.abgeschlossen.am)} von ${v.abgeschlossen.von}` }) : null].filter(Boolean));
  }
  function kommentareSortiert(liste) {
    const nr = (k) => parseInt(String(k.id).slice(1), 10) || 0;
    return [...liste].sort((a, b) => (a.frame === null) !== (b.frame === null) ? (a.frame === null ? -1 : 1) : (a.frame === null ? nr(a) - nr(b) : (a.frame - b.frame) || nr(a) - nr(b)));
  }
  function renderMarker() {
    const d = Z.dom, v = versionAktuell();
    d.marker.replaceChildren();
    if (!Z.frames) return;
    for (const k of v.kommentare) {
      if (k.frame === null || k.frame === undefined) continue;
      const links = (k.frame / Math.max(1, Z.frames - 1)) * 100;
      const m = el("div", { class: "marker status-" + k.status + (Z.hervor === k.id ? " hervor" : ""), "data-id": k.id, title: `${tc(k.frame)} ${k.autor}: ${k.text}`, onclick: (ev) => { ev.stopPropagation(); Z.video.pause(); springe(k.frame); hervorheben(k.id); } });
      m.style.left = links + "%";
      if (k.bis_frame !== null && k.bis_frame !== undefined) { m.classList.add("bereich"); m.style.width = Math.max(0.5, ((k.bis_frame - k.frame) / Math.max(1, Z.frames - 1)) * 100) + "%"; }
      d.marker.append(m);
    }
  }
  function hervorheben(id) {
    Z.hervor = id;
    for (const e of Z.dom.seite.querySelectorAll(".kommentar")) e.classList.toggle("hervor", e.dataset.id === id);
    for (const e of Z.dom.marker.children) e.classList.toggle("hervor", e.dataset.id === id);
    const ziel = Z.dom.seite.querySelector(`.kommentar[data-id="${id}"]`);
    if (ziel) ziel.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
  function renderSeite() {
    const d = Z.dom, det = Z.detail, v = versionAktuell();
    const liste = el("div", { class: "liste" });
    const basis = versionBasis();
    if (basis) {
      const eintraege = basis.kommentare.filter((k) => k.antwort_claude || k.status === "umgesetzt" || k.status === "rueckfrage");
      if (eintraege.length) liste.append(seitBlock(basis, eintraege));
    }
    const ks = kommentareSortiert(v.kommentare);
    liste.append(el("div", { class: "kopfzeile" }, el("span", { text: `Kommentare V${v.nr}` }), el("span", { text: ks.length ? `${ks.length}` : "keine" })));
    for (const k of ks) liste.append(kommentarElement(k, v.nr));
    d.liste = liste;
    d.seite.replaceChildren(liste, eingabeElement(v, det));
    renderMarker();
  }
  function seitBlock(basis, eintraege) {
    const block = el("details", { class: "seit-block", open: true }, el("summary", {}, el("span", { text: `Seit V${basis.nr} geändert` }), el("span", { class: "zahl", text: String(eintraege.length) })));
    for (const k of kommentareSortiert(eintraege)) {
      const e = el("div", { class: "eintrag " + (k.status === "rueckfrage" ? "rueckfrage" : "") },
        el("div", { class: "orig" }, el("span", { class: "tc", text: k.frame !== null ? tc(k.frame) : "allg." }), el("span", { text: `${k.id} · ${k.autor}: ${k.text}` })),
        k.antwort_claude ? el("div", { class: "antwort" }, el("b", { text: k.status === "rueckfrage" ? "Claude · Rückfrage: " : "Claude: " }), el("span", { text: k.antwort_claude })) : null,
        k.antworten && k.antworten.length ? el("div", { class: "thread" }, k.antworten.map((a) => el("div", { class: "antwort" }, el("b", { text: a.autor + ": " }), el("span", { text: a.text })))) : null,
        el("div", { class: "zeile" },
          k.frame_neu !== null && k.frame_neu !== undefined ? el("button", { class: "leise", text: "→ " + tc(k.frame_neu), title: "Stelle in V" + Z.versionNr, onclick: () => { Z.video.pause(); springe(k.frame_neu); } }) : null,
          el("span", { class: "chip status-" + k.status, text: STATUS[k.status] || k.status }),
          el("label", {}, el("input", { type: "checkbox", checked: k.status === "erledigt", onchange: (ev) => kommentarStatus(basis.nr, k.id, ev.target.checked ? "erledigt" : "offen") }), "erledigt"),
          k.status === "rueckfrage" ? el("button", { class: "leise", text: "Antworten", onclick: (ev) => antwortForm(ev.target.closest(".eintrag"), basis.nr, k.id) }) : null));
      block.append(e);
    }
    return block;
  }
  function kommentarElement(k, versionNr) {
    const eigener = k.autor === Z.autor;
    const zeit = k.frame === null || k.frame === undefined
      ? el("span", { class: "tc allgemein", text: "allgemein" })
      : el("span", { class: "tc", text: tc(k.frame) + (k.bis_frame !== null && k.bis_frame !== undefined ? " → " + tc(k.bis_frame) : ""), title: "Zur Stelle springen", onclick: () => { Z.video.pause(); springe(k.frame); hervorheben(k.id); } });
    const e = el("div", { class: "kommentar status-" + k.status + (Z.hervor === k.id ? " hervor" : ""), "data-id": k.id, onclick: () => hervorheben(k.id) },
      el("div", { class: "zeile-1" }, zeit, el("span", { class: "autor", text: k.autor }), k.status !== "offen" ? el("span", { class: "chip status-" + k.status, text: STATUS[k.status] || k.status }) : null, el("span", { class: "wann", text: wann(k.angelegt) + (k.geaendert ? " ✎" : ""), title: k.id })),
      el("div", { class: "text", text: k.text }));
    if (k.antwort_claude) e.append(el("div", { class: "antwort-claude " + (k.status === "rueckfrage" ? "rueckfrage" : "") }, el("b", { text: k.status === "rueckfrage" ? "Claude · Rückfrage" : "Claude" }), el("span", { text: " " + k.antwort_claude }),
      k.frame_neu !== null && k.frame_neu !== undefined ? el("a", { class: "sprung", text: `→ V${versionNr + 1} ${tc(k.frame_neu)}`, href: pfad(Z.route.kunde, Z.route.projekt, Z.route.video, versionNr + 1, k.frame_neu), onclick: (ev) => ev.stopPropagation() }) : null));
    if (k.antworten && k.antworten.length) e.append(el("div", { class: "thread" }, k.antworten.map((a) => el("div", { class: "antwort" }, el("b", { text: a.autor + ": " }), el("span", { text: a.text })))));
    e.append(el("div", { class: "werkzeuge" },
      el("button", { class: "leise", text: "Antworten", onclick: (ev) => { ev.stopPropagation(); antwortForm(e, versionNr, k.id); } }),
      el("button", { class: "leise", text: k.status === "erledigt" ? "Wieder öffnen" : "Erledigt", onclick: (ev) => { ev.stopPropagation(); kommentarStatus(versionNr, k.id, k.status === "erledigt" ? "offen" : "erledigt"); } }),
      eigener ? el("button", { class: "leise", text: "Bearbeiten", onclick: (ev) => { ev.stopPropagation(); bearbeiten(e, versionNr, k); } }) : null,
      eigener ? el("button", { class: "leise gefahr", text: "Löschen", onclick: (ev) => { ev.stopPropagation(); if (confirm(`${k.id} löschen?`)) kommentarAendern(versionNr, { id: k.id, loeschen: true }); } }) : null));
    return e;
  }
  function antwortForm(container, versionNr, id) {
    if (container.querySelector(".antwort-form")) return;
    const input = el("input", { type: "text", placeholder: "Antwort …", maxlength: "2000" });
    const form = el("form", { class: "antwort-form", onsubmit: async (ev) => { ev.preventDefault(); if (!input.value.trim()) return; try { await api("antwort", { ...basisDaten(versionNr), id, autor: Z.autor, text: input.value.trim() }); form.remove(); await aktualisierePlayer(true); } catch (e) { fehler(e); } } },
      input, el("button", { class: "primaer", type: "submit", text: "Senden" }), el("button", { class: "leise", type: "button", text: "×", onclick: () => form.remove() }));
    container.append(form);
    input.focus();
  }
  function bearbeiten(e, versionNr, k) {
    if (e.querySelector("textarea.bearbeiten")) return;
    const ta = el("textarea", { class: "bearbeiten", text: k.text });
    const form = el("div", { class: "antwort-form" }, el("button", { class: "primaer", text: "Speichern", onclick: () => kommentarAendern(versionNr, { id: k.id, text: ta.value }) }), el("button", { class: "leise", text: "Abbrechen", onclick: () => { ta.remove(); form.remove(); } }));
    e.querySelector(".text").after(ta, form);
    ta.focus();
  }
  function basisDaten(versionNr) { return { kunde: Z.route.kunde, projekt: Z.route.projekt, video: Z.route.video, version: versionNr }; }
  async function kommentarAendern(versionNr, felder) {
    try { await api("kommentar/aendern", { ...basisDaten(versionNr), autor: Z.autor, ...felder }); await aktualisierePlayer(true); }
    catch (e) { fehler(e); }
  }
  const kommentarStatus = (versionNr, id, status) => kommentarAendern(versionNr, { id, status });
  async function versionAktion(weg) {
    try { await api(weg, { ...basisDaten(Z.versionNr), autor: Z.autor }); await aktualisierePlayer(true); toast(weg.endsWith("abschliessen") ? `V${Z.versionNr} abgeschlossen — sag Claude Bescheid („Review: ${Z.route.kunde}/${Z.route.projekt}“).` : `V${Z.versionNr} wieder offen.`, "gut"); }
    catch (e) { fehler(e); }
  }
  async function videoAktion(weg) {
    try { await api(weg, { kunde: Z.route.kunde, projekt: Z.route.projekt, video: Z.route.video, autor: Z.autor }); await aktualisierePlayer(true); ladeIndex(true).then(renderBaum); }
    catch (e) { fehler(e); }
  }

  // ---------- Eingabe --------------------------------------------------------------------------------------------
  function eingabeElement(v, det) {
    if (det.video.freigegeben) return el("div", { class: "eingabe gesperrt" }, el("div", { class: "sperre" }, el("span", { text: `Freigegeben ${wann(det.video.freigegeben.am)} von ${det.video.freigegeben.von}.` }), el("button", { text: "Freigabe zurücknehmen", onclick: () => videoAktion("video/freigabe_zuruecknehmen") })));
    if (v.abgeschlossen) return el("div", { class: "eingabe gesperrt" }, el("div", { class: "sperre" }, el("span", { text: `V${v.nr} ist abgeschlossen (bei Claude). Neue Kommentare erst nach „Wieder öffnen“.` }), el("button", { text: "Wieder öffnen", onclick: () => versionAktion("version/wieder_oeffnen") })));
    const d = Z.dom;
    d.stelle = el("div", { class: "stelle" });
    d.textarea = el("textarea", { placeholder: "Kommentar an der aktuellen Stelle … (C = hierher, ⌘↩ = senden)", onfocus: () => { Z.video.pause(); if (!Z.eingabe.aktiv) { Z.eingabe.aktiv = true; if (!Z.eingabe.allgemein && Z.eingabe.frame === null) Z.eingabe.frame = Z.frame; } renderStelle(); } });
    const eingabe = el("div", { class: "eingabe" }, d.stelle, d.textarea,
      el("div", { class: "senden" }, el("span", { class: "hinweis", text: "I/O = Bereich · Esc = Video weiter" }), el("button", { class: "primaer", text: "Kommentar senden", onclick: senden })));
    renderStelle();
    return eingabe;
  }
  function renderStelle() {
    const d = Z.dom, e = Z.eingabe;
    if (!d.stelle) return;
    const frame = e.aktiv && e.frame !== null ? e.frame : Z.frame;
    d.stelle.replaceChildren(...[
      el("button", { class: e.allgemein ? "aktiv" : "", text: "Allgemein", title: "ohne Zeitbezug", onclick: () => { e.allgemein = !e.allgemein; e.aktiv = true; if (!e.allgemein && e.frame === null) e.frame = Z.frame; renderStelle(); } }),
      e.allgemein ? el("span", { text: "kein Zeitbezug" }) : el("span", {}, el("span", { text: "am " }), el("span", { class: "tc", text: tc(frame) })),
      !e.allgemein ? el("button", { text: "hierher", title: "auf den aktuellen Frame setzen (I)", onclick: () => { e.aktiv = true; e.frame = Z.frame; if (e.bis !== null && e.bis <= e.frame) e.bis = null; renderStelle(); } }) : null,
      !e.allgemein ? (e.bis !== null
        ? el("span", {}, el("span", { text: "bis " }), el("span", { class: "tc", text: tc(e.bis) }), el("button", { class: "leise", text: "×", title: "Bereich aufheben", onclick: () => { e.bis = null; renderStelle(); } }))
        : el("button", { text: "Bereich bis hier", title: "Out auf den aktuellen Frame (O)", onclick: setzeOut })) : null].filter(Boolean));
  }
  function setzeIn() { const e = Z.eingabe; e.aktiv = true; e.allgemein = false; e.frame = Z.frame; if (e.bis !== null && e.bis <= e.frame) e.bis = null; renderStelle(); }
  function setzeOut() { const e = Z.eingabe; e.aktiv = true; e.allgemein = false; if (e.frame === null) e.frame = Z.frame; if (Z.frame <= e.frame) { toast("Out muss nach In liegen — erst weiter scrubben.", ""); return; } e.bis = Z.frame; renderStelle(); if (Z.dom.textarea) Z.dom.textarea.focus(); }
  async function senden() {
    const d = Z.dom, e = Z.eingabe;
    if (!d.textarea) return;
    const text = d.textarea.value.trim();
    if (!text) { d.textarea.focus(); return; }
    const frame = e.allgemein ? null : (e.frame !== null ? e.frame : Z.frame);
    try {
      await api("kommentar", { ...basisDaten(Z.versionNr), autor: Z.autor, text, frame, bis_frame: e.allgemein ? null : e.bis });
      d.textarea.value = "";
      Z.eingabe = { aktiv: false, frame: null, bis: null, allgemein: false };
      d.textarea.blur();
      await aktualisierePlayer(true);
      renderStelle();
    } catch (err) { fehler(err); }
  }

  // ---------- Aktualisierung -------------------------------------------------------------------------------------
  async function aktualisierePlayer(erzwingen = false) {
    if (!Z.detail) return;
    const detail = await ladeDetail();
    const stand = JSON.stringify(detail);
    if (!erzwingen && stand === Z.detailStand) return;
    const vorher = Z.detail.versionen.length;
    Z.detail = detail; Z.detailStand = stand;
    if (!versionAktuell()) { geheZu(Z.route.kunde, Z.route.projekt, Z.route.video); return; }
    renderKopf();
    const aktiv = document.activeElement === Z.dom.textarea;
    const entwurf = Z.dom.textarea ? Z.dom.textarea.value : "";
    renderSeite();
    if (Z.dom.textarea) { Z.dom.textarea.value = entwurf; if (aktiv) Z.dom.textarea.focus(); }
    if (detail.versionen.length > vorher) {
      const neu = detail.versionen[detail.versionen.length - 1];
      toast(`V${neu.nr} ist da${neu.notiz ? ": " + neu.notiz : ""}`, "gut", { text: "Öffnen", tu: () => geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, neu.nr) });
    }
    ladeIndex(true).then(renderBaum).catch(() => {});
  }

  // ---------- Tastatur -------------------------------------------------------------------------------------------
  document.addEventListener("keydown", (ev) => {
    const ziel = ev.target;
    const tippt = ziel && (ziel.tagName === "TEXTAREA" || ziel.tagName === "INPUT");
    if (tippt) {
      if (ev.key === "Escape") { ziel.blur(); ev.preventDefault(); }
      else if (ev.key === "Enter" && (ev.metaKey || ev.ctrlKey) && ziel === Z.dom.textarea) { ev.preventDefault(); senden(); }
      return;
    }
    if (!Z.video || $("#autor-dialog").open) return;
    const fps = Math.max(1, Math.round(Z.fps));
    switch (ev.key) {
      case " ": ev.preventDefault(); umschalten(); break;
      case "ArrowLeft": ev.preventDefault(); schritt(ev.shiftKey ? -fps : -1); break;
      case "ArrowRight": ev.preventDefault(); schritt(ev.shiftKey ? fps : 1); break;
      case "Home": ev.preventDefault(); Z.video.pause(); springe(0); break;
      case "End": ev.preventDefault(); Z.video.pause(); springe(Z.frames - 1); break;
      case "i": case "I": ev.preventDefault(); setzeIn(); break;
      case "o": case "O": ev.preventDefault(); setzeOut(); break;
      case "c": case "C": ev.preventDefault(); if (Z.dom.textarea) Z.dom.textarea.focus(); break;
      case "m": case "M": ev.preventDefault(); stumm(); break;
      case "f": case "F": ev.preventDefault(); vollbild(); break;
      default:
        if (/^[1-9]$/.test(ev.key)) { const nr = parseInt(ev.key, 10); if (Z.detail.versionen.some((v) => v.nr === nr) && nr !== Z.versionNr) geheZu(Z.route.kunde, Z.route.projekt, Z.route.video, nr); }
    }
  });

  // ---------- Autor, NAS, Start ----------------------------------------------------------------------------------
  function autorAnzeigen() { $("#autor-knopf").textContent = Z.autor || "Name wählen"; }
  function autorDialog() {
    const dialog = $("#autor-dialog");
    $("#autor-frei").value = ["David", "Jan", "Sergio"].includes(Z.autor) ? "" : Z.autor;
    if (!dialog.open) dialog.showModal();
  }
  $("#autor-form").addEventListener("submit", (ev) => {
    const wert = ev.submitter && ev.submitter.value;
    const name = wert === "__frei" ? $("#autor-frei").value.trim() : wert;
    if (!name) { ev.preventDefault(); $("#autor-frei").focus(); return; }
    Z.autor = name.slice(0, 40);
    try { localStorage.setItem("niroReviewAutor", Z.autor); } catch (e) { /* privat */ }
    autorAnzeigen();
    if (Z.detail && Z.dom.seite) renderSeite();
  });
  $("#autor-dialog").addEventListener("cancel", (ev) => { if (!Z.autor) ev.preventDefault(); });
  $("#autor-knopf").addEventListener("click", autorDialog);
  $("#suche").addEventListener("input", (ev) => { Z.suche = ev.target.value; renderBaum(); if (Z.route.kunde && !Z.route.video) renderProjekt(); });

  async function nasPruefen() {
    const nas = $("#nas"), banner = $("#banner");
    try {
      const z = await api("zustand");
      nas.className = "nas " + (z.nas_verbunden ? "ok" : "weg");
      nas.title = (z.nas_verbunden ? "NAS verbunden · " : "NAS nicht verbunden · ") + z.wurzel + " · " + z.mac;
      banner.hidden = z.nas_verbunden;
      banner.textContent = z.nas_verbunden ? "" : "NAS nicht verbunden (" + z.wurzel + ") — Reviews erscheinen, sobald das NAS da ist.";
    } catch (e) { nas.className = "nas weg"; nas.title = "Server antwortet nicht"; }
  }

  async function navigieren() {
    Z.route = route();
    if (Z.pollTimer) { clearInterval(Z.pollTimer); Z.pollTimer = null; }
    if (Z.rvfc && Z.video) { try { Z.video.cancelVideoFrameCallback(Z.rvfc); } catch (e) { /* egal */ } Z.rvfc = null; }
    Z.video = null; Z.detail = null; Z.dom = {};
    if (!Z.index) await ladeIndex();
    renderBaum(); renderKrumen();
    const r = Z.route;
    if (!r.kunde) return renderStart();
    if (!r.video) return renderProjekt();
    await renderPlayer();
  }
  window.addEventListener("hashchange", () => navigieren().catch(fehler));
  autorAnzeigen();
  if (!Z.autor) autorDialog();
  nasPruefen();
  setInterval(nasPruefen, 10000);
  setInterval(() => { if (!Z.route.video) ladeIndex(true).then(() => { renderBaum(); if (Z.route.kunde) renderProjekt(); else renderStart(); }).catch(() => {}); }, 15000);
  navigieren().catch(fehler);
})();
