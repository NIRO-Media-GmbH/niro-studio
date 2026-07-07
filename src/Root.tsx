// ============================================================
// NIRO Motion Graphics — Root Composition Registry
// All compositions (templates + client projects) are registered here
// ============================================================

import React from "react";
import { Composition, Folder } from "remotion";
import { getCalculateMetadata } from "./core/format-utils";

const REVIEW_DEFAULTS = {
  showGuides: false,
  showSafeZone: true,
  showFaceZone: true,
  showGrid: false,
  guideOpacity: 0.35,
} as const;

// Template imports
import {
  socialPostSchema,
  logoIntroSchema,
  textSlideshowSchema,
  productShowcaseSchema,
  minimalTypographySchema,
} from "./core/schemas";
import { SocialPost } from "./templates/SocialPost";
import { LogoIntro } from "./templates/LogoIntro";
import { TextSlideshow } from "./templates/TextSlideshow";
import { ProductShowcase } from "./templates/ProductShowcase";
import { MinimalTypography } from "./templates/MinimalTypography";

// Client imports
import { LaunchAd, launchAdSchema } from "./clients/niro-demo/projects/launch-ad/Composition";
import { LandhausWolfFischZerlegen, landhausWolfFischZerlegenSchema } from "./clients/landhaus-wolf/projects/fisch-zerlegen/Composition";
import { LandhausWolfKartoffelgratinPart1, landhausWolfKartoffelgratinPart1Schema, LandhausWolfKartoffelgratinPart2, landhausWolfKartoffelgratinPart2Schema } from "./clients/landhaus-wolf/projects/kartoffelgratin/Composition";
import { LandhausWolfKartoffelschaum, landhausWolfKartoffelschaumSchema } from "./clients/landhaus-wolf/projects/kartoffelschaum/Composition";
import { LandhausWolfDasPerfekteDessert, landhausWolfDasPerfekteDessertSchema } from "./clients/landhaus-wolf/projects/das-perfekte-dessert/Composition";
import { LandhausWolfMuschelnRichtigKochen, landhausWolfMuschelnRichtigKochenSchema } from "./clients/landhaus-wolf/projects/muscheln-richtig-kochen/Composition";
import { LandhausWolfChicoree, landhausWolfChicoreeSchema } from "./clients/landhaus-wolf/projects/chicoree/Composition";
import { LandhausWolfDiePerfekteBeilage, landhausWolfDiePerfekteBeilageSchema } from "./clients/landhaus-wolf/projects/die-perfekte-beilage/Composition";
import { LandhausWolfPetrischale, landhausWolfPetrischaleSchema } from "./clients/landhaus-wolf/projects/petrischale/Composition";
import { SWSolarVerkaeufer, swSolarVerkaeuferSchema } from "./clients/sw-projektentwicklung/projects/solar-verkaeufer/Composition";
import { PraktikantReel, praktikantReelSchema } from "./clients/niro-demo/projects/praktikant-reel/Composition";
import { BremsenSchneiderCta, bremsenSchneiderCtaSchema } from "./clients/bremsen-schneider/projects/cta-endslide/Composition";
import { BremsenSchneiderAzubi, azubiOverlaySchema, azubiOverlayDefaults } from "./clients/bremsen-schneider/projects/azubi-overlay/Composition";
import { BremsenSchneiderFachkraft, fachkraftOverlaySchema, fachkraftOverlayDefaults } from "./clients/bremsen-schneider/projects/fachkraft-overlay/Composition";
import { BremsenSchneiderMeister, meisterOverlaySchema, meisterOverlayDefaults } from "./clients/bremsen-schneider/projects/meister-overlay/Composition";
import { BremsenSchneiderImagefilm, imagefilmOverlaySchema, imagefilmOverlayDefaults } from "./clients/bremsen-schneider/projects/imagefilm-overlay/Composition";
import { SauberEntsorgenLeistungen, leistungenOverlaySchema, leistungenOverlayDefaults } from "./clients/sauber-entsorgen/projects/leistungen-overlay/Composition";
import { SauberEntsorgenErklaervideo, erklaervideoSchema, erklaervideoDefaults } from "./clients/sauber-entsorgen/projects/erklaervideo/Composition";
import { SauberEntsorgenReel1, reel1Schema, reel1Defaults } from "./clients/sauber-entsorgen/projects/reel-1/Composition";
import { SauberEntsorgenReel2, reel2Schema, reel2Defaults } from "./clients/sauber-entsorgen/projects/reel-2/Composition";
import { PflegefachkraftOverlay, pflegefachkraftSchema, pflegefachkraftDefaults } from "./clients/seniorenstiftung/projects/pflegefachkraft/Composition";
import { PflegeAzubisOverlay, pflegeAzubisSchema, pflegeAzubisDefaults } from "./clients/seniorenstiftung/projects/pflege-azubis/Composition";
import { KuechenhilfeOverlay, kuechenhilfeSchema, kuechenhilfeDefaults } from "./clients/seniorenstiftung/projects/kuechenhilfe/Composition";
import { PutzfachkraftOverlay, putzfachkraftSchema, putzfachkraftDefaults } from "./clients/seniorenstiftung/projects/putzfachkraft/Composition";
import { AllgemeinesOverlay, allgemeinesSchema, allgemeinesDefaults } from "./clients/seniorenstiftung/projects/allgemeines/Composition";
import { TopFotografieSchulleiterTypen, schulleiterTypenSchema, schulleiterTypenDefaults } from "./clients/top-fotografie/projects/schulleiter-typen/Composition";
import { TopFotografieDreiVersprechen, dreiVersprechenSchema, dreiVersprechenDefaults } from "./clients/top-fotografie/projects/drei-versprechen/Composition";
import { TopFotografieKeineFotos, keineFotosSchema, keineFotosDefaults } from "./clients/top-fotografie/projects/keine-fotos/Composition";
import { TopFototagBlur, fototagBlurSchema, fototagBlurDefaults } from "./clients/top-fotografie/projects/fototag-teaser-blur/Composition";
import { TopFototagRedacted, fototagRedactedSchema, fototagRedactedDefaults } from "./clients/top-fotografie/projects/fototag-teaser-redacted/Composition";
import { TopFototagGlitch, fototagGlitchSchema, fototagGlitchDefaults } from "./clients/top-fotografie/projects/fototag-teaser-glitch/Composition";
import { TopFototagSchritte, fototagSchritteSchema, fototagSchritteDefaults } from "./clients/top-fotografie/projects/fototag-schritte/Composition";
import { TopJobEndscreen, jobEndscreenSchema, fotografEndscreenDefaults, vertrieblerEndscreenDefaults } from "./clients/top-fotografie/projects/endscreen-job/Composition";
import { TopHookSchulenKitas, hookSchulenKitasSchema, hookSchulenKitasDefaults } from "./clients/top-fotografie/projects/hook-schulen-kitas/Composition";
import { TopFotografieDreiFragen, dreiFragenSchema, dreiFragenDefaults } from "./clients/top-fotografie/projects/drei-fragen/Composition";
import { TopFotografieDreiTipps, dreiTippsSchema, dreiTippsDefaults } from "./clients/top-fotografie/projects/drei-tipps/Composition";
import { TopFotografieDreiProbleme, dreiProblemeSchema, dreiProblemeDefaults } from "./clients/top-fotografie/projects/drei-probleme/Composition";
import { RemDachbeschichtung, remDachbeschichtungSchema, remDachbeschichtungDefaults } from "./clients/rem-maler/projects/dachbeschichtung/Composition";
import { RemDachbeschichtungV2, remDachV2Schema, remDachV2Defaults } from "./clients/rem-maler/projects/dachbeschichtung-v2/Composition";
import { RemDachbeschichtungV2Premium, remDachV2PremiumSchema, remDachV2PremiumDefaults } from "./clients/rem-maler/projects/dachbeschichtung-v2-premium/Composition";
import { ManLagerCta, manLagerCtaSchema, manLagerCtaDefaults } from "./clients/man/projects/lager-ausbildung-cta/Composition";
import { WTNErsterTag, ersterTagSchema, ersterTagDefaults } from "./clients/wtn/projects/erster-tag/Composition";
import { WTNTechnik, technikSchema, technikDefaults } from "./clients/wtn/projects/technik/Composition";
import { WTNTeamSicherheit, teamSicherheitSchema, teamSicherheitDefaults } from "./clients/wtn/projects/team-sicherheit/Composition";
import { WTNArbeitsbedingungen, arbeitsbedingungenSchema, arbeitsbedingungenDefaults } from "./clients/wtn/projects/arbeitsbedingungen/Composition";
import { WTNMotivationAufstieg, motivationAufstiegSchema, motivationAufstiegDefaults } from "./clients/wtn/projects/motivation-aufstieg/Composition";


export const RemotionRoot: React.FC = () => {
  return (
    <>
      {/* ===== TEMPLATES ===== */}
      <Folder name="Templates">
        <Composition
          id="SocialPost"
          component={SocialPost}
          schema={socialPostSchema}
          defaultProps={{
            format: "portrait" as const,
            fps: 30 as const,
            durationInSeconds: 8,
            transparent: false,
            review: REVIEW_DEFAULTS,
            headline: "Your Headline Here",
            bodyText: "Supporting text with key details for your audience.",
            ctaText: "Learn More",
            backgroundType: "gradient" as const,
          }}
          calculateMetadata={({ props }) => getCalculateMetadata(props)}
        />

        <Composition
          id="LogoIntro"
          component={LogoIntro}
          schema={logoIntroSchema}
          defaultProps={{
            format: "landscape" as const,
            fps: 30 as const,
            durationInSeconds: 5,
            transparent: false,
            review: REVIEW_DEFAULTS,
            companyName: "BRAND",
            tagline: "Your tagline here",
            revealMode: "scale" as const,
            showParticles: true,
          }}
          calculateMetadata={({ props }) => getCalculateMetadata(props)}
        />

        <Composition
          id="TextSlideshow"
          component={TextSlideshow}
          schema={textSlideshowSchema}
          defaultProps={{
            format: "portrait" as const,
            fps: 30 as const,
            durationInSeconds: 9,
            transparent: false,
            review: REVIEW_DEFAULTS,
            slides: [
              { text: "First Slide", subtext: "Supporting text" },
              { text: "Second Slide", subtext: "More details" },
              { text: "Third Slide", subtext: "Final thoughts" },
            ],
            transitionType: "fade" as const,
          }}
          calculateMetadata={({ props }) => getCalculateMetadata(props)}
        />

        <Composition
          id="ProductShowcase"
          component={ProductShowcase}
          schema={productShowcaseSchema}
          defaultProps={{
            format: "landscape" as const,
            fps: 30 as const,
            durationInSeconds: 10,
            transparent: false,
            review: REVIEW_DEFAULTS,
            productName: "Product Name",
            tagline: "The best solution for your needs",
            features: ["Fast & Reliable", "Easy to Use", "Beautifully Designed"],
            backgroundType: "gradient" as const,
          }}
          calculateMetadata={({ props }) => getCalculateMetadata(props)}
        />

        <Composition
          id="MinimalTypography"
          component={MinimalTypography}
          schema={minimalTypographySchema}
          defaultProps={{
            format: "portrait" as const,
            fps: 30 as const,
            durationInSeconds: 6,
            transparent: false,
            review: REVIEW_DEFAULTS,
            lines: ["Think", "Create", "Inspire"],
            fontWeight: "900",
            animationStyle: "fade" as const,
          }}
          calculateMetadata={({ props }) => getCalculateMetadata(props)}
        />
      </Folder>

      {/* ===== CLIENTS ===== */}
      <Folder name="Clients">
        <Folder name="NIRO-Demo">
          <Composition
            id="NiroDemo-LaunchAd"
            component={LaunchAd}
            schema={launchAdSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 8,
              transparent: false,
              review: REVIEW_DEFAULTS,
              headline: "Motion Graphics\nMade Simple",
              subheadline: "Create stunning animations with code",
              ctaText: "Get Started Today",
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="NiroDemo-PraktikantReel"
            component={PraktikantReel}
            schema={praktikantReelSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 35.8,
              transparent: false,
              review: REVIEW_DEFAULTS,
              hook:        { startSec: 0,    durationSec: 4.5, mainWord: "PRAKTIKUM", subtitle: "Eine Woche Marketingagentur", wordPos: { x: 0, y: 0 }, subtitlePos: { x: 0, y: 0 } },
              montag:      { startSec: 4.5,  durationSec: 3.5, dayLabel: "MONTAG", activityIcon: "\u{1F4DE}", activityName: "Cold Calling", activityDesc: "Vertrieb wie Jordan Belfort", cardPos: { x: 0, y: 0 } },
              dienstag:    { startSec: 8,    durationSec: 4.5, dayLabel: "DIENSTAG", activityIcon: "\u{1F3AC}", activityName: "Filmdreh", activityDesc: "Kfz-Werkstatt \u00b7 Selber filmen", cardPos: { x: 0, y: 0 } },
              mittwoch:    { startSec: 12.5, durationSec: 4.3, dayLabel: "MITTWOCH", activityIcon: "\u{1F3A8}", activityName: "Canva Design", activityDesc: "Behind-the-Scenes Post", cardPos: { x: 0, y: 0 } },
              donnerstag:  { startSec: 16.8, durationSec: 5.2, dayLabel: "DONNERSTAG", activityIcon: "\u2702\uFE0F", activityName: "Video schneiden", activityDesc: "Kreativer Freiraum", cardPos: { x: 0, y: 0 } },
              freitag:     { startSec: 22,   durationSec: 7,   dayLabel: "FREITAG", activityIcon: "\u{1F916}", activityName: "Marketing & AI", activityDesc: "KI-Nutzen im Marketing gelernt", cardPos: { x: 0, y: 0 } },
              outro:       { startSec: 29,   durationSec: 4,   mainText: "RICHTIG COOL!", subText: "Danke ans Team", textPos: { x: 0, y: 0 } },
              cta:         { startSec: 33,   durationSec: 2.8, brandName: "NeuroMedia", ctaText: "Jetzt bewerben", brandPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="LandhausWolf">
          <Composition
            id="LandhausWolf-FischZerlegen"
            component={LandhausWolfFischZerlegen}
            schema={landhausWolfFischZerlegenSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 140,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-KartoffelgratinPart1"
            component={LandhausWolfKartoffelgratinPart1}
            schema={landhausWolfKartoffelgratinPart1Schema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 85,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-KartoffelgratinPart2"
            component={LandhausWolfKartoffelgratinPart2}
            schema={landhausWolfKartoffelgratinPart2Schema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 85,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-Kartoffelschaum"
            component={LandhausWolfKartoffelschaum}
            schema={landhausWolfKartoffelschaumSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 150,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-DasPerfekteDessert"
            component={LandhausWolfDasPerfekteDessert}
            schema={landhausWolfDasPerfekteDessertSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 190,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-MuschelnRichtigKochen"
            component={LandhausWolfMuschelnRichtigKochen}
            schema={landhausWolfMuschelnRichtigKochenSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 134,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-Chicoree"
            component={LandhausWolfChicoree}
            schema={landhausWolfChicoreeSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 75,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-DiePerfekteBeilage"
            component={LandhausWolfDiePerfekteBeilage}
            schema={landhausWolfDiePerfekteBeilageSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 94,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LandhausWolf-Petrischale"
            component={LandhausWolfPetrischale}
            schema={landhausWolfPetrischaleSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 25 as const,
              durationInSeconds: 88,
              transparent: true,
              review: REVIEW_DEFAULTS,
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="SW-Projektentwicklung">
          <Composition
            id="SW-SolarVerkaeufer"
            component={SWSolarVerkaeufer}
            schema={swSolarVerkaeuferSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 47,
              transparent: false,
              review: REVIEW_DEFAULTS,
              hook:            { startSec: 0,    durationSec: 5,   hookWord: "SOLAR", hookSuffix: "?", wordPos: { x: 0, y: 0 }, subtitle: "Jeder will dir was verkaufen", subtitlePos: { x: 0, y: 0 } },
              problem:         { startSec: 5,    durationSec: 4,   item1: "Falsche Berater", item1Pos: { x: 0, y: 0 }, item2: "Keine Erfahrung", item2Pos: { x: 0, y: 0 }, item3: "Keine Transparenz", item3Pos: { x: 0, y: 0 } },
              lowerThird:      { startSec: 9,    durationSec: 3.9, name: "Fabrice Stradinger", title: "Gründer & Geschäftsführer · SW Projektentwicklung", cardPos: { x: 0, y: 0 } },
              statCounter:     { startSec: 12.9, durationSec: 5,   statNumber: 180, statSuffix: "+", numberPos: { x: 0, y: 0 }, statLabel: "Projekte", labelPos: { x: 0, y: 0 }, statSublabel: "erfolgreich in der Region", sublabelPos: { x: 0, y: 0 } },
              threeComponents: { startSec: 20,   durationSec: 9,   titleNumber: "3", titleSubtext: "Bauteile — mehr nicht.", titlePos: { x: 0, y: 0 }, comp1Icon: "☀️", comp1Label: "Solarmodul", comp1Desc: "Strom erzeugen", comp1Pos: { x: 0, y: 0 }, comp2Icon: "🔋", comp2Label: "Stromspeicher", comp2Desc: "Energie speichern", comp2Pos: { x: 0, y: 0 }, comp3Icon: "⚡", comp3Label: "Wechselrichter", comp3Desc: "Strom umwandeln", comp3Pos: { x: 0, y: 0 } },
              geldSparen:      { startSec: 29,   durationSec: 5.5, symbol: "€", symbolPos: { x: 0, y: 0 }, mainText: "Jeden Monat sparen", mainTextPos: { x: 0, y: 0 }, subText: "Bares Geld mit Solar", subTextPos: { x: 0, y: 0 } },
              fullService:     { startSec: 34.5, durationSec: 6.2, title: "Full Service", titlePos: { x: 0, y: 0 }, item1: "Alles aus einer Hand", item1Pos: { x: 0, y: 0 }, item2: "Keine Subunternehmer", item2Pos: { x: 0, y: 0 }, item3: "Persönliche Beratung", item3Pos: { x: 0, y: 0 }, item4: "Volle Betreuung nach Montage", item4Pos: { x: 0, y: 0 } },
              cta:             { startSec: 40.7, durationSec: 6.3, introText: "Schreib uns einfach", introPos: { x: 0, y: 0 }, bubbleText: "SOLAR", bubblePos: { x: 0, y: 0 }, arrowSymbol: "↓", arrowPos: { x: 0, y: 0 }, brandName: "SW Projektentwicklung", brandPos: { x: 0, y: 0 }, website: "sw-projektentwicklung.com", websitePos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="BremsenSchneider">
          <Composition
            id="BremsenSchneider-CTA"
            component={BremsenSchneiderCta}
            schema={bremsenSchneiderCtaSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 10,
              transparent: false,
              review: REVIEW_DEFAULTS,
              logoPos: { x: 0, y: 0 },
              headerText: "Wir suchen",
              headerPos: { x: 0, y: 0 },
              job1: "Azubi",
              job2: "Fachkraft",
              job3: "Meister",
              jobsPos: { x: 0, y: 0 },
              ctaText: "Jetzt bewerben!",
              ctaPos: { x: 0, y: 0 },
              website: "bremsen-schneider.de",
              websitePos: { x: 0, y: 0 },
              phone: "07907 9888-0",
              phonePos: { x: 0, y: 0 },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="BremsenSchneider-CTA-Transparent"
            component={BremsenSchneiderCta}
            schema={bremsenSchneiderCtaSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 10,
              transparent: true,
              review: REVIEW_DEFAULTS,
              logoPos: { x: 0, y: 0 },
              headerText: "Wir suchen",
              headerPos: { x: 0, y: 0 },
              job1: "Azubi",
              job2: "Fachkraft",
              job3: "Meister",
              jobsPos: { x: 0, y: 0 },
              ctaText: "Jetzt bewerben!",
              ctaPos: { x: 0, y: 0 },
              website: "bremsen-schneider.de",
              websitePos: { x: 0, y: 0 },
              phone: "07907 9888-0",
              phonePos: { x: 0, y: 0 },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="BremsenSchneider-Azubi"
            component={BremsenSchneiderAzubi}
            schema={azubiOverlaySchema}
            defaultProps={azubiOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="BremsenSchneider-Fachkraft"
            component={BremsenSchneiderFachkraft}
            schema={fachkraftOverlaySchema}
            defaultProps={fachkraftOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="BremsenSchneider-Meister"
            component={BremsenSchneiderMeister}
            schema={meisterOverlaySchema}
            defaultProps={meisterOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="BremsenSchneider-Imagefilm"
            component={BremsenSchneiderImagefilm}
            schema={imagefilmOverlaySchema}
            defaultProps={imagefilmOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="SauberEntsorgen">
          <Composition
            id="SauberEntsorgen-Erklaervideo"
            component={SauberEntsorgenErklaervideo}
            schema={erklaervideoSchema}
            defaultProps={erklaervideoDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SauberEntsorgen-Reel1"
            component={SauberEntsorgenReel1}
            schema={reel1Schema}
            defaultProps={reel1Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SauberEntsorgen-Reel2"
            component={SauberEntsorgenReel2}
            schema={reel2Schema}
            defaultProps={reel2Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SauberEntsorgen-Leistungen"
            component={SauberEntsorgenLeistungen}
            schema={leistungenOverlaySchema}
            defaultProps={leistungenOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="TopFotografie">
          <Composition
            id="TopFotografie-SchulleiterTypen"
            component={TopFotografieSchulleiterTypen}
            schema={schulleiterTypenSchema}
            defaultProps={schulleiterTypenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-DreiVersprechen"
            component={TopFotografieDreiVersprechen}
            schema={dreiVersprechenSchema}
            defaultProps={dreiVersprechenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-KeineFotos"
            component={TopFotografieKeineFotos}
            schema={keineFotosSchema}
            defaultProps={keineFotosDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-FototagBlur"
            component={TopFototagBlur}
            schema={fototagBlurSchema}
            defaultProps={fototagBlurDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-FototagRedacted"
            component={TopFototagRedacted}
            schema={fototagRedactedSchema}
            defaultProps={fototagRedactedDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-FototagGlitch"
            component={TopFototagGlitch}
            schema={fototagGlitchSchema}
            defaultProps={fototagGlitchDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-FototagSchritte"
            component={TopFototagSchritte}
            schema={fototagSchritteSchema}
            defaultProps={fototagSchritteDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-DreiFragen"
            component={TopFotografieDreiFragen}
            schema={dreiFragenSchema}
            defaultProps={dreiFragenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-DreiTipps"
            component={TopFotografieDreiTipps}
            schema={dreiTippsSchema}
            defaultProps={dreiTippsDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-DreiProbleme"
            component={TopFotografieDreiProbleme}
            schema={dreiProblemeSchema}
            defaultProps={dreiProblemeDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-EndscreenFotograf"
            component={TopJobEndscreen}
            schema={jobEndscreenSchema}
            defaultProps={fotografEndscreenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-EndscreenVertriebler"
            component={TopJobEndscreen}
            schema={jobEndscreenSchema}
            defaultProps={vertrieblerEndscreenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="TopFotografie-HookSchulenKitas"
            component={TopHookSchulenKitas}
            schema={hookSchulenKitasSchema}
            defaultProps={hookSchulenKitasDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="REM-Maler">
          <Composition
            id="REM-Dachbeschichtung"
            component={RemDachbeschichtung}
            schema={remDachbeschichtungSchema}
            defaultProps={remDachbeschichtungDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="REM-Dachbeschichtung-V2"
            component={RemDachbeschichtungV2}
            schema={remDachV2Schema}
            defaultProps={remDachV2Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="REM-Dachbeschichtung-V2-Premium"
            component={RemDachbeschichtungV2Premium}
            schema={remDachV2PremiumSchema}
            defaultProps={remDachV2PremiumDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="MAN">
          <Composition
            id="MAN-LagerCTA"
            component={ManLagerCta}
            schema={manLagerCtaSchema}
            defaultProps={manLagerCtaDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="Seniorenstiftung">
          <Composition
            id="Seniorenstiftung-Pflegefachkraft"
            component={PflegefachkraftOverlay}
            schema={pflegefachkraftSchema}
            defaultProps={pflegefachkraftDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Seniorenstiftung-PflegeAzubis"
            component={PflegeAzubisOverlay}
            schema={pflegeAzubisSchema}
            defaultProps={pflegeAzubisDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Seniorenstiftung-Kuechenhilfe"
            component={KuechenhilfeOverlay}
            schema={kuechenhilfeSchema}
            defaultProps={kuechenhilfeDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Seniorenstiftung-Putzfachkraft"
            component={PutzfachkraftOverlay}
            schema={putzfachkraftSchema}
            defaultProps={putzfachkraftDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Seniorenstiftung-Allgemeines"
            component={AllgemeinesOverlay}
            schema={allgemeinesSchema}
            defaultProps={allgemeinesDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="WTN">
          <Composition
            id="WTN-ErsterTag"
            component={WTNErsterTag}
            schema={ersterTagSchema}
            defaultProps={ersterTagDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WTN-Technik"
            component={WTNTechnik}
            schema={technikSchema}
            defaultProps={technikDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WTN-TeamSicherheit"
            component={WTNTeamSicherheit}
            schema={teamSicherheitSchema}
            defaultProps={teamSicherheitDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WTN-Arbeitsbedingungen"
            component={WTNArbeitsbedingungen}
            schema={arbeitsbedingungenSchema}
            defaultProps={arbeitsbedingungenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WTN-MotivationAufstieg"
            component={WTNMotivationAufstieg}
            schema={motivationAufstiegSchema}
            defaultProps={motivationAufstiegDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>
      </Folder>
    </>
  );
};
