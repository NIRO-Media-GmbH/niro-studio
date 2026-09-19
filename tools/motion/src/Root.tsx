// ============================================================
// NIRO Motion Graphics — Root Composition Registry
// All compositions (templates + client projects) are registered here
// ============================================================

import React from "react";
import { Composition, Folder } from "remotion";
import { getCalculateMetadata } from "./core/format-utils";
import {
  AeternaMesseScreen, messeScreenSchema, messeScreenDefaults,
} from "./clients/aeterna-weddings/projects/messe-screen/Composition";
import {
  MekZertifikat, zertifikatSchema, zertifikatCacDefaults, zertifikatWeaningDefaults,
} from "./clients/mek/projects/imagefilm/Zertifikate";
import {
  MekImagefilmGrafikKomplett, grafikKomplettSchema, grafikKomplettDefaults, calculateGrafikKomplett,
} from "./clients/mek/projects/imagefilm/Grafikebene";
import {
  TaxodiaGrafikebene, grafikSchema as taxodiaGrafikSchema, grafikDefaults as taxodiaGrafikDefaults, calculateGrafik as calculateTaxodiaGrafik,
} from "./clients/taxodia/projects/erklaervideo/Grafikebene";

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
import { RemocnShowcase, remocnShowcaseSchema, remocnShowcaseDefaults } from "./clients/niro-demo/projects/remocn-showcase/Composition";
import { RecruitingOverlayTest, recruitingOverlayTestSchema, recruitingOverlayTestDefaults } from "./clients/niro-demo/projects/recruiting-overlay-test/Composition";
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
import { RemGewerbedachReinigung, remGewerbedachSchema, remGewerbedachDefaults } from "./clients/rem-maler/projects/gewerbedach-reinigung/Composition";
import { RemGewerbedachOverlay, remGewerbedachOverlaySchema, remGewerbedachOverlayDefaults } from "./clients/rem-maler/projects/gewerbedach-overlay/Composition";
import { ManLagerCta, manLagerCtaSchema, manLagerCtaDefaults } from "./clients/man/projects/lager-ausbildung-cta/Composition";
import { ManLagerCtaWeb, manLagerCtaWebSchema, manLagerCtaWebDefaults } from "./clients/man/projects/lager-ausbildung-cta/CompositionWeb";
import {
  ManWzFrame, manWzFrameSchema,
  manWzFrameSoloDefaults, manWzFrameVersetztDefaults, manWzFrameDuoDefaults,
  ManWzOpener, manWzOpenerSchema, manWzOpenerDefaults,
  ManWzTrenner, manWzTrennerSchema, manWzTrennerDefaults,
  ManWzInsert, manWzInsertSchema, manWzInsertDefaults,
  ManWzEndcard, manWzEndcardSchema, manWzEndcardDefaults,
  ManWz169Master, manWz169MasterSchema, manWz169MasterDefaults,
} from "./clients/man/projects/wartezimmervideo/Composition";
import { WTNErsterTag, ersterTagSchema, ersterTagDefaults } from "./clients/wtn/projects/erster-tag/Composition";
import { FoerchRecOverlay, foerchRecOverlaySchema, foerchRecOverlayDefaults } from "./clients/foerch/projects/messevideos/RecOverlay";
import {
  WlcV6WortBattle, wlcWortBattleSchema, wlcWortBattleDefaults,
  WlcV6Trio, wlcTrioSchema, wlcTrioDefaults,
  WlcV6BeweisCard, wlcBeweisCardSchema, wlcBeweisCardDefaults,
  WlcV6Outro, wlcOutroSchema, wlcOutroDefaults,
} from "./clients/wlc/projects/recruiting-v6/Composition";
import {
  WlcTalkOverlay, wlcTalkOverlaySchema, wlcV4OverlayDefaults, wlcV5OverlayDefaults,
  WlcJobEndcard, wlcJobEndcardSchema, wlcJobEndcardDefaults,
} from "./clients/wlc/projects/recruiting-v4-v5/Composition";
import {
  WlcAzubiOverlay, wlcAzubiOverlaySchema, wlcV1OverlayDefaults, wlcV2OverlayDefaults,
  WlcReporterOverlay, wlcReporterOverlaySchema, wlcV3OverlayDefaults,
  WlcV7Overlay, wlcV7OverlaySchema, wlcV7OverlayDefaults,
} from "./clients/wlc/projects/recruiting-v1-v3/Composition";
import { WTNTechnik, technikSchema, technikDefaults } from "./clients/wtn/projects/technik/Composition";
import { WTNTeamSicherheit, teamSicherheitSchema, teamSicherheitDefaults } from "./clients/wtn/projects/team-sicherheit/Composition";
import { WTNArbeitsbedingungen, arbeitsbedingungenSchema, arbeitsbedingungenDefaults } from "./clients/wtn/projects/arbeitsbedingungen/Composition";
import { WTNMotivationAufstieg, motivationAufstiegSchema, motivationAufstiegDefaults } from "./clients/wtn/projects/motivation-aufstieg/Composition";
import {
  BumbleCleanMesseMaster, bumbleCleanMesseSchema, bumbleCleanMesseDefaults,
} from "./clients/bumble-clean/projects/messevideo/Composition";
import {
  BumbleCleanV1LackEdit, v1LackEditSchema, v1LackEditDefaults,
} from "./clients/bumble-clean/projects/schnittplan-social/V1LackEdit";
import {
  BumbleCleanV2Interior, v2InteriorSchema, v2InteriorDefaults,
} from "./clients/bumble-clean/projects/schnittplan-social/V2InteriorDeepClean";
import {
  BumbleCleanAdZeit, adZeitSchema, adZeitDefaults,
} from "./clients/bumble-clean/projects/cinematic-ad/AdZeit";
import {
  HblSaeulenGrafik, saeulenGrafikSchema, saeulenGrafikDefaults,
  HblSaeulenFokus, saeulenFokusSchema, saeulenFokus01Defaults, saeulenFokus02Defaults,
  HblOpener, openerSchema, openerDefaults,
  HblTitelBadge, titelBadgeSchema, titel01Defaults, titel02Defaults,
  HblZahl40, zahl40Schema, zahl40Defaults,
  HblErgebnisseM1, ergebnisseM1Schema, ergebnisseM1Defaults,
  HblCaption, captionSchema, captionOhneHblDefaults,
  HblPraxisfallTransition, praxisfallTransitionSchema, praxisfallTransitionDefaults,
  HblSplitBlende, splitBlendeSchema, splitBlendeDefaults,
  HblCheckliste, checklisteSchema, checklisteS3Defaults,
  HblSubMitUns, subMitUnsSchema, subMitUnsDefaults,
  HblBauchbinde, bauchbindeSchema, bauchbindeAndreDefaults, bauchbindeBreitenfeldDefaults, bauchbindeHblTeamDefaults,
  HblEndcard, endcardSchema, endcardDefaults,
  HblScreenFenster, screenFensterSchema, screenFensterDefaults,
  HblImagefilmMaster, imagefilmMasterSchema, imagefilmMasterDefaults,
} from "./clients/hbl/projects/imagefilm/Composition";
import { NiroCutterAd, niroCutterAdSchema, niroCutterAdDefaults } from "./clients/niro/projects/cutter-ad/Composition";
import {
  LohiBwAd1, LohiBwAd2, LohiBwAd3, LohiBwAd4,
  lohiBwUntertitelSchema,
  lohiBwAd1Defaults, lohiBwAd2Defaults, lohiBwAd3Defaults, lohiBwAd4Defaults,
} from "./clients/lohi-bw/projects/untertitel/Composition";
import {
  SetzerFleischkaeseVsLeberkaese,
  setzerFleischkaeseSchema,
  setzerFleischkaeseDefaults,
} from "./clients/setzer/projects/fleischkaese-vs-leberkaese/Composition";
import {
  SetzerPfefferbeisser,
  setzerPfefferbeisserSchema,
  setzerPfefferbeisserDefaults,
} from "./clients/setzer/projects/pfefferbeisser/Composition";
import {
  SetzerFleischsalatZutaten,
  setzerFleischsalatZutatenSchema,
  setzerFleischsalatZutatenDefaults,
} from "./clients/setzer/projects/fleischsalat-zutaten/Composition";
import {
  CraissArbeitsalltag, craissArbeitsalltagSchema, craissArbeitsalltagDefaults, craissArbeitsalltagPreviewDefaults,
} from "./clients/craiss/projects/arbeitsalltag/Composition";
import {
  CraissErsterTag, craissErsterTagSchema, craissErsterTagDefaults, craissErsterTagPreviewDefaults,
} from "./clients/craiss/projects/erster-tag/Composition";
import {
  CraissFunnel, craissFunnelSchema, craissFunnelDefaults, craissFunnelPreviewDefaults,
} from "./clients/craiss/projects/funnel/Composition";
import {
  CraissTestimonial, craissTestimonialSchema, craissTestimonialDefaults, craissTestimonialPreviewDefaults,
} from "./clients/craiss/projects/testimonial/Composition";
import {
  CraissVieleJahre, craissVieleJahreSchema, craissVieleJahreDefaults, craissVieleJahrePreviewDefaults,
} from "./clients/craiss/projects/viele-jahre/Composition";
import { CraissErsterTagSubtitled, craissErsterTagSubtitledSchema, craissErsterTagSubtitledDefaults } from "./clients/craiss/projects/erster-tag/CompositionSubtitled";
import { CraissArbeitsalltagSubtitled, craissArbeitsalltagSubtitledSchema, craissArbeitsalltagSubtitledDefaults } from "./clients/craiss/projects/arbeitsalltag/CompositionSubtitled";
import { CraissVieleJahreSubtitled, craissVieleJahreSubtitledSchema, craissVieleJahreSubtitledDefaults } from "./clients/craiss/projects/viele-jahre/CompositionSubtitled";
import { CraissFunnelSubtitled, craissFunnelSubtitledSchema, craissFunnelSubtitledDefaults } from "./clients/craiss/projects/funnel/CompositionSubtitled";
import { CraissTestimonialSubtitled, craissTestimonialSubtitledSchema, craissTestimonialSubtitledDefaults } from "./clients/craiss/projects/testimonial/CompositionSubtitled";
import { CraissVorschau, craissVorschauSchema, craissVorschauDefaults, craissAlphaDefaults } from "./clients/craiss/projects/vorschau/Composition";
import { DoldEndcard, doldEndcardSchema, doldEndcardDefaults } from "./clients/dold/projects/recruiting-endcard/Composition";
import { SWBifazialeModule, swBifazialeModuleSchema } from "./clients/sw-projektentwicklung/projects/bifaziale-module/Composition";
import { SWGottwollshausen, swGottwollshausenSchema } from "./clients/sw-projektentwicklung/projects/gottwollshausen/Composition";
import { SWFlachdach, swFlachdachSchema } from "./clients/sw-projektentwicklung/projects/flachdach/Composition";
import { SWBauerSolar, swBauerSolarSchema } from "./clients/sw-projektentwicklung/projects/bauer-solar/Composition";
import { SWSmartino, swSmartinoSchema } from "./clients/sw-projektentwicklung/projects/smartino/Composition";
import { SWRecruiting, swRecruitingSchema } from "./clients/sw-projektentwicklung/projects/recruiting/Composition";
import { SUBTITLE_DEFAULTS as SW_SUBTITLES } from "./clients/sw-projektentwicklung/Subtitles";
import { SchmittNeuerSpielstand, schmittNeuerSpielstandSchema, schmittNeuerSpielstandDefaults, schmittNeuerSpielstandMetadata } from "./clients/schmitt/projects/neuer-spielstand/Composition";


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
          <Composition
            id="NiroDemo-RemocnShowcase"
            component={RemocnShowcase}
            schema={remocnShowcaseSchema}
            defaultProps={remocnShowcaseDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="NiroDemo-RecruitingOverlayTest"
            component={RecruitingOverlayTest}
            schema={recruitingOverlayTestSchema}
            defaultProps={recruitingOverlayTestDefaults}
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

          {/* Solar-Wissen — Reels 01/02/03/04/05/07 (06 existiert nicht). Preview-Konfiguration:
              transparent:false + echtes footageFile, zum Weiterarbeiten (z.B. Untertitel) gegen
              echtes Material. Fuer den reinen Overlay-Export (wie ausgeliefert): transparent auf
              true, footageFile auf "" setzen. */}
          <Composition
            id="SW-Gottwollshausen"
            component={SWGottwollshausen}
            schema={swGottwollshausenSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 53.53,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "01_Projekt-Gottwolfshausen_V1.mp4",
              subtitles: SW_SUBTITLES,
              hook:     { startSec: 1.3,  durationSec: 4.0,  line1: "Der Netzbetreiber kann", line2: "deine Anlage drosseln!", linesPos: { x: 0, y: 0 } },
              projekt:  { startSec: 6.2,  durationSec: 4.0,  title: "Bauvorhaben", titlePos: { x: 0, y: 0 }, subline: "Gottwollshausen", sublinePos: { x: 0, y: 0 } },
              anlage:   { startSec: 10.9, durationSec: 2.9,  moduleCount: "", wattLabel: "460 Watt", caption: "pro Solarmodul", captionPos: { x: 0, y: 0 }, modulePos: { x: 0, y: 0 } },
              speicher: { startSec: 14.2, durationSec: 2.8,  value: "18", unit: "kWh", label: "Stromspeicher", labelPos: { x: 0, y: 0 }, batteryPos: { x: 0, y: 0 } },
              ertrag:   { startSec: 18.9, durationSec: 3.3,  toValue: 24000, numberPos: { x: 0, y: 0 }, label: "pro Jahr", labelPos: { x: 0, y: 0 }, sublabel: "", sublabelPos: { x: 0, y: 0 } },
              grenze:   { startSec: 22.2, durationSec: 2.0,  limitLabel: "25 kWp", title: "Bewusst darunter geplant", titlePos: { x: 0, y: 0 }, caption: "", captionPos: { x: 0, y: 0 } },
              folgen:   { startSec: 25.6, durationSec: 15.9, heading: "Ab 25 kWp gilt", headingPos: { x: 0, y: 0 }, row1: "Rundsteuer-Empfänger nötig", row1Sub: "pauschal ab ca. 600 €", row2: "Netzbetreiber darf drosseln", row2Sub: "auch deinen Eigenverbrauch", row3: "Höhere Montagekosten", row3Sub: "zusätzlicher Aufwand am Bau", rowsPos: { x: 0, y: 0 } },
              ctaFrage: { startSec: 41.8, durationSec: 4.4,  line1: "Frisst dir die Stromrechnung", line2: "die Haare vom Kopf?", linesPos: { x: 0, y: 0 } },
              endkarte: { startSec: 46.8, durationSec: 6.7,  analyseText: "Komplette Analyse", analysePos: { x: 0, y: 0 }, pillText: "MIND. 70 % AUTARKIE", pillPos: { x: 0, y: 0 }, logoPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SW-BifazialeModule"
            component={SWBifazialeModule}
            schema={swBifazialeModuleSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 35.967,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "02_Bifaziale_Solarmodule_V1.mp4",
              subtitles: SW_SUBTITLES,
              hook:        { startSec: 0,    durationSec: 2.4, word: "STREIT", wordPos: { x: 0, y: 0 }, subline: "im Solarmarkt", sublinePos: { x: 0, y: 0 } },
              streit:      { startSec: 3.4,  durationSec: 3.2, contraText: "„Bringt gar nichts.“", contraPos: { x: 0, y: 0 }, proText: "„Bringt richtig was.“", proPos: { x: 0, y: 0 } },
              titel:       { startSec: 8.0,  durationSec: 5.0, title: "BIFAZIAL", titlePos: { x: 0, y: 0 }, subline: "Module mit zwei aktiven Seiten", sublinePos: { x: 0, y: 0 } },
              beideSeiten: { startSec: 14.0, durationSec: 2.4, leftLabel: "Sonne", rightLabel: "Reflexion", caption: "Strom von beiden Seiten", captionPos: { x: 0, y: 0 }, modulePos: { x: 0, y: 0 } },
              zaun:        { startSec: 18.6, durationSec: 5.4, title: "Modul als Gartenzaun", titlePos: { x: 0, y: 0 }, caption: "Ertrag von vorne und hinten", captionPos: { x: 0, y: 0 }, fencePos: { x: 0, y: 0 } },
              ertrag:      { startSec: 25.0, durationSec: 6.3, fromValue: 5, toValue: 20, suffix: "%", numberPos: { x: 0, y: 0 }, label: "Mehrertrag", labelPos: { x: 0, y: 0 }, sublabel: "je nach Untergrund & Installation", sublabelPos: { x: 0, y: 0 } },
              empfehlung:  { startSec: 32.8, durationSec: 3.2, pillText: "IMMER BIFAZIAL", pillPos: { x: 0, y: 0 }, subline: "Kann man nichts falsch machen.", sublinePos: { x: 0, y: 0 }, logoPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SW-BauerSolar"
            component={SWBauerSolar}
            schema={swBauerSolarSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 56.0,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "03_BauSolar-Modul_V1.mp4",
              subtitles: SW_SUBTITLES,
              brand:       { startSec: 3.1,  durationSec: 3.3, name: "Bauer Solar", namePos: { x: 0, y: 0 }, caption: "German Brand", captionPos: { x: 0, y: 0 } },
              leistung:    { startSec: 7.4,  durationSec: 3.0, value: "460", unit: "Watt", caption: "pro Modul", captionPos: { x: 0, y: 0 }, blockPos: { x: 0, y: 0 } },
              glas:        { startSec: 10.9, durationSec: 3.6, title: "Glas-Glas-Bifazial", titlePos: { x: 0, y: 0 }, caption: "Zellen zwischen zwei Scheiben", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              zellen:      { startSec: 15.2, durationSec: 2.9, title: "Zellen direkt sichtbar", titlePos: { x: 0, y: 0 }, caption: "durch das Glas erkennbar", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              zaun:        { startSec: 18.6, durationSec: 5.8, row1: "Auch als Solar-Zaun", row1Sub: "Module stehen senkrecht", row2: "Ertrag von beiden Seiten", row2Sub: "die Rückseite ist aktiv", rowsPos: { x: 0, y: 0 } },
              stecker:     { startSec: 25.1, durationSec: 4.6, heading: "Stecker", headingPos: { x: 0, y: 0 }, goodText: "Stäubli-Stecker", goodSub: "Markenstecker ab Werk", badText: "Kein Standard-MC4", badSub: "", rowsPos: { x: 0, y: 0 } },
              staerke:     { startSec: 29.7, durationSec: 5.4, value: "2 mm", valueCaption: "Glasstärke", klasseText: "Hagelwiderstandsklasse", klasseValue: "3", blockPos: { x: 0, y: 0 } },
              vergleich:   { startSec: 36.3, durationSec: 3.4, heading: "Im Vergleich", headingPos: { x: 0, y: 0 }, ownLabel: "Bauer Solar", ownValue: "2 mm", otherLabel: "Andere", otherValue: "1,6 mm", barsPos: { x: 0, y: 0 } },
              brandschutz: { startSec: 40.0, durationSec: 3.6, title: "Brandschutzklasse", value: "A", blockPos: { x: 0, y: 0 } },
              beweis:      { startSec: 43.8, durationSec: 5.9, title: "Wirklich so robust?", titlePos: { x: 0, y: 0 }, caption: "Wir haben es getestet", captionPos: { x: 0, y: 0 } },
              tests:       { startSec: 49.9, durationSec: 4.1, heading: "Bestanden", headingPos: { x: 0, y: 0 }, test1: "Härte", test2: "Feuer", test3: "Schlag", rowPos: { x: 0, y: 0 } },
              endkarte:    { startSec: 54.0, durationSec: 2.0, fazitText: "", fazitPos: { x: 0, y: 0 }, pillText: "LINK UNTEN DRIN", pillPos: { x: 0, y: 0 }, logoPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SW-Flachdach"
            component={SWFlachdach}
            schema={swFlachdachSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 79.47,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "04_Flachdach-Erklaerung_V1.mp4",
              subtitles: SW_SUBTITLES,
              dicht:        { startSec: 0.9,  durationSec: 6.2, headline: "Kein Dichtigkeitsproblem", headlinePos: { x: 0, y: 0 }, caption: "Die erste Frage überhaupt", captionPos: { x: 0, y: 0 } },
              ostWest:      { startSec: 10.9, durationSec: 5.6, title: "Ost-West-Aufständerung", titlePos: { x: 0, y: 0 }, leftLabel: "OST", rightLabel: "WEST", caption: "wie ein kleines Zelt", captionPos: { x: 0, y: 0 }, dachPos: { x: 0, y: 0 } },
              winkel:       { startSec: 18.8, durationSec: 3.6, value: "10°", caption: "Module aufgewinkelt", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              schiene:      { startSec: 25.6, durationSec: 3.6, title: "Nur eine Schiene", titlePos: { x: 0, y: 0 }, caption: "Steine als Ballast — mehr nicht", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              durchstossen: { startSec: 29.2, durationSec: 2.4, title: "Keine Dachdurchdringung", subline: "nichts wird durchstoßen", blockPos: { x: 0, y: 0 } },
              auflegen:     { startSec: 32.4, durationSec: 5.0, title: "Unterkonstruktion", titlePos: { x: 0, y: 0 }, caption: "Module werden aufgelegt", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              klemmen:      { startSec: 39.3, durationSec: 6.4, heading: "Befestigung", headingPos: { x: 0, y: 0 }, row1: "Mittelklemme", row1Sub: "zwischen zwei Modulen", row2: "Endklemme", row2Sub: "am Ende jeder Reihe", rowsPos: { x: 0, y: 0 } },
              fertig:       { startSec: 46.9, durationSec: 4.6, line1: "Module verkabeln", line1Pos: { x: 0, y: 0 }, pillText: "ANLAGE FERTIG", pillPos: { x: 0, y: 0 } },
              sued:         { startSec: 53.6, durationSec: 5.6, title: "Süd-Aufständerung", titlePos: { x: 0, y: 0 }, caption: "eine Reihe, nach Süden ausgerichtet", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              unterschied:  { startSec: 60.9, durationSec: 4.4, heading: "Der einzige Unterschied", headingPos: { x: 0, y: 0 }, caption: "Angriffsfläche für Wind", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              windfang:     { startSec: 67.6, durationSec: 4.2, title: "Windfangblech", titlePos: { x: 0, y: 0 }, caption1: "Wind kommt hinten nicht durch", caption2: "bei Ost-West nicht nötig", captionPos: { x: 0, y: 0 }, diagramPos: { x: 0, y: 0 } },
              endkarte:     { startSec: 76.3, durationSec: 3.2, fazitText: "", fazitPos: { x: 0, y: 0 }, pillText: "FRAGEN? GERNE MELDEN", pillPos: { x: 0, y: 0 }, logoPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SW-Smartino"
            component={SWSmartino}
            schema={swSmartinoSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 49.25,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "05_Hotel-Smartino_V1.mp4",
              subtitles: SW_SUBTITLES,
              autarkie:  { startSec: 2.3,  durationSec: 2.9, value: "60 %", unit: "Autarkie", caption: "in den ersten 6 Monaten", captionPos: { x: 0, y: 0 }, blockPos: { x: 0, y: 0 } },
              prognose:  { startSec: 6.3,  durationSec: 3.0, value: "65–70 %", unit: "", caption: "Prognose aufs ganze Jahr", captionPos: { x: 0, y: 0 }, blockPos: { x: 0, y: 0 } },
              objekt:    { startSec: 10.5, durationSec: 5.4, name: "Hotel Smartino", namePos: { x: 0, y: 0 }, ort: "Schwäbisch Hall", caption: "PV-Anlage seit 6 Monaten in Betrieb", captionPos: { x: 0, y: 0 } },
              anlage:    { startSec: 16.15, durationSec: 3.7, heading: "Die Anlage", headingPos: { x: 0, y: 0 }, value1: "144", label1: "Module", value2: "63", label2: "kWp", rowPos: { x: 0, y: 0 } },
              verbrauch: { startSec: 21.4, durationSec: 3.4, value: "70.000", unit: "kWh", caption: "Stromverbrauch pro Jahr", captionPos: { x: 0, y: 0 }, blockPos: { x: 0, y: 0 } },
              netz:      { startSec: 27.2, durationSec: 4.3, heading: "Nur noch", headingPos: { x: 0, y: 0 }, oldLabel: "Vorher", oldValue: "70.000 kWh", newLabel: "Jetzt", newValue: "25.000 kWh", caption: "Netzbezug in diesem Jahr", captionPos: { x: 0, y: 0 }, barsPos: { x: 0, y: 0 } },
              fazit:     { startSec: 35.3, durationSec: 3.1, heading: "Richtig gelungenes Projekt", headingPos: { x: 0, y: 0 }, chip1: "63 kWp", chip2: "144 Module", chip3: "60 % Autarkie", rowPos: { x: 0, y: 0 }, caption: "perfekt ausgelegt", captionPos: { x: 0, y: 0 } },
              cta:       { startSec: 39.4, durationSec: 6.5, heading: "Du hast ein Gewerbeobjekt?", headingPos: { x: 0, y: 0 }, row1: "Analyse deines Dachs", row1Sub: "wir schauen es uns an", row2: "Wie viel Autarkie geht?", row2Sub: "konkret für dein Objekt", rowsPos: { x: 0, y: 0 } },
              endkarte:  { startSec: 46.0, durationSec: 3.25, pillText: "MELD DICH GERN", pillPos: { x: 0, y: 0 }, logoPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="SW-Recruiting"
            component={SWRecruiting}
            schema={swRecruitingSchema}
            defaultProps={{
              format: "portrait" as const,
              fps: 30 as const,
              durationInSeconds: 25.63,
              transparent: false,
              review: REVIEW_DEFAULTS,
              footageFile: "07_Recruiting-Elektromeister_V1.mp4",
              subtitles: SW_SUBTITLES,
              hook:     { startSec: 0.3,   durationSec: 2.3,  word: "Elektromeister?", wordPos: { x: 0, y: 0 } },
              satt:     { startSec: 2.6,   durationSec: 5.7,  heading: "Hast du's satt?", headingPos: { x: 0, y: 0 }, row1: "Nur PV am Einfamilienhaus", row1Sub: "immer dasselbe", row2: "Überspannungsschutz", row2Sub: "das Komplizierteste am Ganzen", rowsPos: { x: 0, y: 0 } },
              richtig:  { startSec: 8.45,  durationSec: 2.9,  line1: "Dann bist du", line2: "bei uns richtig", linesPos: { x: 0, y: 0 } },
              gewerbe:  { startSec: 11.6,  durationSec: 4.7,  heading: "Bei uns machst du", headingPos: { x: 0, y: 0 }, row1: "Gewerbeanlagen", row1Sub: "nicht nur Einfamilienhäuser", row2: "NA-Schutz & Tarifschaltgeräte", row2Sub: "richtige Elektrotechnik", rowsPos: { x: 0, y: 0 } },
              rolle:    { startSec: 16.55, durationSec: 2.9,  headline: "Wir suchen dich", headlinePos: { x: 0, y: 0 }, role: "ALS TEAMLEITER", rolePos: { x: 0, y: 0 } },
              cta:      { startSec: 19.6,  durationSec: 3.15, pillText: "MELD DICH GERN", pillPos: { x: 0, y: 0 }, caption: "Schauen wir, ob du ins Team passt", captionPos: { x: 0, y: 0 } },
              endkarte: { startSec: 22.8,  durationSec: 2.83, headline: "Komm ins Team", role: "ELEKTROMEISTER", roleSuffix: "als Teamleiter (m/w/d)", pillText: "JETZT BEWERBEN", contact: "sw-projektentwicklung.com", blockPos: { x: 0, y: 0 } },
            }}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="Craiss">
          <Composition
            id="Craiss-Arbeitsalltag"
            component={CraissArbeitsalltag}
            schema={craissArbeitsalltagSchema}
            defaultProps={craissArbeitsalltagDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-Arbeitsalltag-Preview"
            component={CraissArbeitsalltag}
            schema={craissArbeitsalltagSchema}
            defaultProps={craissArbeitsalltagPreviewDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-ErsterTag"
            component={CraissErsterTag}
            schema={craissErsterTagSchema}
            defaultProps={craissErsterTagDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-ErsterTag-Preview"
            component={CraissErsterTag}
            schema={craissErsterTagSchema}
            defaultProps={craissErsterTagPreviewDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-Funnel"
            component={CraissFunnel}
            schema={craissFunnelSchema}
            defaultProps={craissFunnelDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-Funnel-Preview"
            component={CraissFunnel}
            schema={craissFunnelSchema}
            defaultProps={craissFunnelPreviewDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-Testimonial"
            component={CraissTestimonial}
            schema={craissTestimonialSchema}
            defaultProps={craissTestimonialDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-Testimonial-Preview"
            component={CraissTestimonial}
            schema={craissTestimonialSchema}
            defaultProps={craissTestimonialPreviewDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-VieleJahre"
            component={CraissVieleJahre}
            schema={craissVieleJahreSchema}
            defaultProps={craissVieleJahreDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Craiss-VieleJahre-Preview"
            component={CraissVieleJahre}
            schema={craissVieleJahreSchema}
            defaultProps={craissVieleJahrePreviewDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          {/* Untertitel-Spuren auf den fertigen Schnitten (01 V3, 02 V3, 03 V3, 04 V4, 05 V2):
              Studio zeigt den Schnitt darunter, Render = Alpha-Overlay 2160×3840.
              Eigener Unterordner, damit sie nicht mit den alten Hook/CTA-„-Preview"-Comps
              (V1/V2-Footage, ohne Untertitel) verwechselt werden. */}
          <Folder name="Untertitel-Final">
            <Composition
              id="Craiss-ErsterTag-Untertitel"
              component={CraissErsterTagSubtitled}
              schema={craissErsterTagSubtitledSchema}
              defaultProps={craissErsterTagSubtitledDefaults}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Arbeitsalltag-Untertitel"
              component={CraissArbeitsalltagSubtitled}
              schema={craissArbeitsalltagSubtitledSchema}
              defaultProps={craissArbeitsalltagSubtitledDefaults}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-VieleJahre-Untertitel"
              component={CraissVieleJahreSubtitled}
              schema={craissVieleJahreSubtitledSchema}
              defaultProps={craissVieleJahreSubtitledDefaults}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Funnel-Untertitel"
              component={CraissFunnelSubtitled}
              schema={craissFunnelSubtitledSchema}
              defaultProps={craissFunnelSubtitledDefaults}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Testimonial-Untertitel"
              component={CraissTestimonialSubtitled}
              schema={craissTestimonialSubtitledSchema}
              defaultProps={craissTestimonialSubtitledDefaults}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
          </Folder>
          {/* Abnahme-Vorschau: Schnitt ohne Animation + aktuelle Animationen + Untertitel */}
          <Folder name="Vorschau-Neu">
            <Composition
              id="Craiss-Vorschau-01-ErsterTag"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissVorschauDefaults("01")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Vorschau-02-Arbeitsalltag"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissVorschauDefaults("02")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Vorschau-03-VieleJahre"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissVorschauDefaults("03")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Vorschau-04-Funnel"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissVorschauDefaults("04")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Vorschau-05-Testimonial"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissVorschauDefaults("05")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
          </Folder>
          {/* Lieferung: pro Video eine Alpha-Datei (alle Animationen + Untertitel), 2160×3840 */}
          <Folder name="Alpha-Komplett">
            <Composition
              id="Craiss-Alpha-01-ErsterTag"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissAlphaDefaults("01")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Alpha-02-Arbeitsalltag"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissAlphaDefaults("02")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Alpha-03-VieleJahre"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissAlphaDefaults("03")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Alpha-04-Funnel"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissAlphaDefaults("04")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
            <Composition
              id="Craiss-Alpha-05-Testimonial"
              component={CraissVorschau}
              schema={craissVorschauSchema}
              defaultProps={craissAlphaDefaults("05")}
              calculateMetadata={({ props }) => getCalculateMetadata(props)}
            />
          </Folder>
        </Folder>

        <Folder name="Dold">
          <Composition
            id="Dold-RecruitingEndcard"
            component={DoldEndcard}
            schema={doldEndcardSchema}
            defaultProps={doldEndcardDefaults}
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
          <Composition
            id="REM-Gewerbedach-Reinigung"
            component={RemGewerbedachReinigung}
            schema={remGewerbedachSchema}
            defaultProps={remGewerbedachDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="REM-Gewerbedach-Overlay"
            component={RemGewerbedachOverlay}
            schema={remGewerbedachOverlaySchema}
            defaultProps={remGewerbedachOverlayDefaults}
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
          <Composition
            id="MAN-LagerCTA-Web"
            component={ManLagerCtaWeb}
            schema={manLagerCtaWebSchema}
            defaultProps={manLagerCtaWebDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Frame-Solo"
            component={ManWzFrame}
            schema={manWzFrameSchema}
            defaultProps={manWzFrameSoloDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Frame-Versetzt"
            component={ManWzFrame}
            schema={manWzFrameSchema}
            defaultProps={manWzFrameVersetztDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Frame-Duo"
            component={ManWzFrame}
            schema={manWzFrameSchema}
            defaultProps={manWzFrameDuoDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Opener"
            component={ManWzOpener}
            schema={manWzOpenerSchema}
            defaultProps={manWzOpenerDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Trenner"
            component={ManWzTrenner}
            schema={manWzTrennerSchema}
            defaultProps={manWzTrennerDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Insert"
            component={ManWzInsert}
            schema={manWzInsertSchema}
            defaultProps={manWzInsertDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MAN-WZ-Endcard"
            component={ManWzEndcard}
            schema={manWzEndcardSchema}
            defaultProps={manWzEndcardDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="man-wz-169-master"
            component={ManWz169Master}
            schema={manWz169MasterSchema}
            defaultProps={manWz169MasterDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="BumbleClean">
          <Composition
            id="bumble-clean-messe-master"
            component={BumbleCleanMesseMaster}
            schema={bumbleCleanMesseSchema}
            defaultProps={bumbleCleanMesseDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="bumble-clean-v1-lack-edit"
            component={BumbleCleanV1LackEdit}
            schema={v1LackEditSchema}
            defaultProps={v1LackEditDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="bumble-clean-v2-interior-deep-clean"
            component={BumbleCleanV2Interior}
            schema={v2InteriorSchema}
            defaultProps={v2InteriorDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="bumble-clean-ad-zeit"
            component={BumbleCleanAdZeit}
            schema={adZeitSchema}
            defaultProps={adZeitDefaults}
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

        <Folder name="WLC">
          <Composition
            id="WlcV6-WortBattle"
            component={WlcV6WortBattle}
            schema={wlcWortBattleSchema}
            defaultProps={wlcWortBattleDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV6-Trio"
            component={WlcV6Trio}
            schema={wlcTrioSchema}
            defaultProps={wlcTrioDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV6-BeweisCard"
            component={WlcV6BeweisCard}
            schema={wlcBeweisCardSchema}
            defaultProps={wlcBeweisCardDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV6-Outro"
            component={WlcV6Outro}
            schema={wlcOutroSchema}
            defaultProps={wlcOutroDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV1-Overlay"
            component={WlcAzubiOverlay}
            schema={wlcAzubiOverlaySchema}
            defaultProps={wlcV1OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV2-Overlay"
            component={WlcAzubiOverlay}
            schema={wlcAzubiOverlaySchema}
            defaultProps={wlcV2OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV3-Overlay"
            component={WlcReporterOverlay}
            schema={wlcReporterOverlaySchema}
            defaultProps={wlcV3OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV7-Overlay"
            component={WlcV7Overlay}
            schema={wlcV7OverlaySchema}
            defaultProps={wlcV7OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV4-Overlay"
            component={WlcTalkOverlay}
            schema={wlcTalkOverlaySchema}
            defaultProps={wlcV4OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcV5-Overlay"
            component={WlcTalkOverlay}
            schema={wlcTalkOverlaySchema}
            defaultProps={wlcV5OverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="WlcJob-Endcard"
            component={WlcJobEndcard}
            schema={wlcJobEndcardSchema}
            defaultProps={wlcJobEndcardDefaults}
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

        <Folder name="Foerch">
          <Composition
            id="Foerch-RecOverlay"
            component={FoerchRecOverlay}
            schema={foerchRecOverlaySchema}
            defaultProps={foerchRecOverlayDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="HBL">
          <Composition
            id="HBL-Imagefilm-Komplett"
            component={HblImagefilmMaster}
            schema={imagefilmMasterSchema}
            defaultProps={imagefilmMasterDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-BauchbindeHBLTeam"
            component={HblBauchbinde}
            schema={bauchbindeSchema}
            defaultProps={bauchbindeHblTeamDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-SaeulenGrafik"
            component={HblSaeulenGrafik}
            schema={saeulenGrafikSchema}
            defaultProps={saeulenGrafikDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Opener"
            component={HblOpener}
            schema={openerSchema}
            defaultProps={openerDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Saeulen-Fokus01"
            component={HblSaeulenFokus}
            schema={saeulenFokusSchema}
            defaultProps={saeulenFokus01Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Saeulen-Fokus02"
            component={HblSaeulenFokus}
            schema={saeulenFokusSchema}
            defaultProps={saeulenFokus02Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Titel01"
            component={HblTitelBadge}
            schema={titelBadgeSchema}
            defaultProps={titel01Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Titel02"
            component={HblTitelBadge}
            schema={titelBadgeSchema}
            defaultProps={titel02Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Zahl40"
            component={HblZahl40}
            schema={zahl40Schema}
            defaultProps={zahl40Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-ErgebnisseM1"
            component={HblErgebnisseM1}
            schema={ergebnisseM1Schema}
            defaultProps={ergebnisseM1Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-PraxisfallTransition"
            component={HblPraxisfallTransition}
            schema={praxisfallTransitionSchema}
            defaultProps={praxisfallTransitionDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-ChecklisteS3"
            component={HblCheckliste}
            schema={checklisteSchema}
            defaultProps={checklisteS3Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-SplitBlende"
            component={HblSplitBlende}
            schema={splitBlendeSchema}
            defaultProps={splitBlendeDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-SubMitUns"
            component={HblSubMitUns}
            schema={subMitUnsSchema}
            defaultProps={subMitUnsDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-ScreenFenster"
            component={HblScreenFenster}
            schema={screenFensterSchema}
            defaultProps={screenFensterDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-CaptionOhneHBL"
            component={HblCaption}
            schema={captionSchema}
            defaultProps={captionOhneHblDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-BauchbindeAndre"
            component={HblBauchbinde}
            schema={bauchbindeSchema}
            defaultProps={bauchbindeAndreDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-BauchbindeBreitenfeld"
            component={HblBauchbinde}
            schema={bauchbindeSchema}
            defaultProps={bauchbindeBreitenfeldDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="HBL-Endcard"
            component={HblEndcard}
            schema={endcardSchema}
            defaultProps={endcardDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="LohiBW">
          <Composition
            id="LohiBW-Untertitel-1"
            component={LohiBwAd1}
            schema={lohiBwUntertitelSchema}
            defaultProps={lohiBwAd1Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LohiBW-Untertitel-2"
            component={LohiBwAd2}
            schema={lohiBwUntertitelSchema}
            defaultProps={lohiBwAd2Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LohiBW-Untertitel-3"
            component={LohiBwAd3}
            schema={lohiBwUntertitelSchema}
            defaultProps={lohiBwAd3Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="LohiBW-Untertitel-4"
            component={LohiBwAd4}
            schema={lohiBwUntertitelSchema}
            defaultProps={lohiBwAd4Defaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="Setzer">
          <Composition
            id="Setzer-Fleischkaese-vs-Leberkaese"
            component={SetzerFleischkaeseVsLeberkaese}
            schema={setzerFleischkaeseSchema}
            defaultProps={setzerFleischkaeseDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Setzer-Pfefferbeisser"
            component={SetzerPfefferbeisser}
            schema={setzerPfefferbeisserSchema}
            defaultProps={setzerPfefferbeisserDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="Setzer-Fleischsalat-Zutaten"
            component={SetzerFleischsalatZutaten}
            schema={setzerFleischsalatZutatenSchema}
            defaultProps={setzerFleischsalatZutatenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="NIRO">
          <Composition
            id="Niro-CutterAd"
            component={NiroCutterAd}
            schema={niroCutterAdSchema}
            defaultProps={niroCutterAdDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="Schmitt">
          <Composition
            id="Schmitt-NeuerSpielstand"
            component={SchmittNeuerSpielstand}
            schema={schmittNeuerSpielstandSchema}
            defaultProps={schmittNeuerSpielstandDefaults}
            calculateMetadata={schmittNeuerSpielstandMetadata}
          />
        </Folder>

        <Folder name="AeternaWeddings">
          <Composition
            id="Aeterna-MesseScreen"
            component={AeternaMesseScreen}
            schema={messeScreenSchema}
            defaultProps={messeScreenDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
        </Folder>

        <Folder name="MEK">
          <Composition
            id="MEK-Imagefilm-Zertifikat-CAC"
            component={MekZertifikat}
            schema={zertifikatSchema}
            defaultProps={zertifikatCacDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MEK-Imagefilm-Zertifikat-Weaning"
            component={MekZertifikat}
            schema={zertifikatSchema}
            defaultProps={zertifikatWeaningDefaults}
            calculateMetadata={({ props }) => getCalculateMetadata(props)}
          />
          <Composition
            id="MEK-Imagefilm-Grafik-Komplett"
            component={MekImagefilmGrafikKomplett}
            schema={grafikKomplettSchema}
            defaultProps={grafikKomplettDefaults}
            calculateMetadata={calculateGrafikKomplett}
          />
        </Folder>

        <Folder name="Taxodia">
          <Composition
            id="Taxodia-Erklaervideo-Grafikebene"
            component={TaxodiaGrafikebene}
            schema={taxodiaGrafikSchema}
            defaultProps={taxodiaGrafikDefaults}
            calculateMetadata={calculateTaxodiaGrafik}
          />
        </Folder>
      </Folder>
    </>
  );
};
