// Tests de la lecture temporelle (ticket wayfinder 0027 — curseur « à cette
// date » sur valid_at/invalid_at). Module pur, zéro DOM : lancé hors du
// harnais pytest via node:test, même patron que encodageType.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  bornesTemporelles, presentALaDate, etatTemporel, decompteTemporel,
  COULEUR_FUTUR, COULEUR_REVOLU,
} from "../app/viz/lectureTemporelle.js";

const FAIT_TOUJOURS = { valid_at: null, invalid_at: null };
const FAIT_DEPUIS_JUIN = { valid_at: "2026-06-01", invalid_at: null };
const FAIT_REVOLU_EN_MAI = { valid_at: "2026-01-01", invalid_at: "2026-05-01" };
const FAIT_FUTUR = { valid_at: "2027-01-01", invalid_at: null };

test("test_bornesTemporelles_cas_nominal_prend_le_min_et_le_max_de_toutes_les_dates", () => {
  const bornes = bornesTemporelles([FAIT_DEPUIS_JUIN, FAIT_REVOLU_EN_MAI, FAIT_FUTUR]);

  assert.equal(bornes.min.toISOString().slice(0, 10), "2026-01-01");
  assert.equal(bornes.max.toISOString().slice(0, 10), "2027-01-01");
});

test("test_bornesTemporelles_renvoie_null_si_aucune_date", () => {
  assert.equal(bornesTemporelles([FAIT_TOUJOURS, FAIT_TOUJOURS]), null);
  assert.equal(bornesTemporelles([]), null);
});

test("test_bornesTemporelles_min_egale_max_avec_une_seule_date", () => {
  const bornes = bornesTemporelles([FAIT_DEPUIS_JUIN]);

  assert.equal(bornes.min.getTime(), bornes.max.getTime());
  assert.equal(bornes.min.toISOString().slice(0, 10), "2026-06-01");
});

test("test_presentALaDate_vrai_avant_toute_borne_pour_un_fait_sans_dates", () => {
  assert.equal(presentALaDate(FAIT_TOUJOURS, "2000-01-01"), true);
  assert.equal(presentALaDate(FAIT_TOUJOURS, "2099-01-01"), true);
});

test("test_presentALaDate_faux_avant_valid_at", () => {
  assert.equal(presentALaDate(FAIT_DEPUIS_JUIN, "2026-05-01"), false);
  assert.equal(presentALaDate(FAIT_DEPUIS_JUIN, "2026-06-15"), true);
});

test("test_presentALaDate_faux_a_partir_de_invalid_at", () => {
  assert.equal(presentALaDate(FAIT_REVOLU_EN_MAI, "2026-03-01"), true);
  assert.equal(presentALaDate(FAIT_REVOLU_EN_MAI, "2026-05-01"), false);
  assert.equal(presentALaDate(FAIT_REVOLU_EN_MAI, "2026-06-01"), false);
});

test("test_etatTemporel_distingue_present_futur_revolu", () => {
  assert.equal(etatTemporel(FAIT_DEPUIS_JUIN, "2026-06-15"), "present");
  assert.equal(etatTemporel(FAIT_FUTUR, "2026-06-15"), "futur");
  assert.equal(etatTemporel(FAIT_REVOLU_EN_MAI, "2026-06-15"), "revolu");
});

test("test_etatTemporel_present_pour_un_fait_sans_dates_a_toute_date", () => {
  assert.equal(etatTemporel(FAIT_TOUJOURS, "1900-01-01"), "present");
  assert.equal(etatTemporel(FAIT_TOUJOURS, "2100-01-01"), "present");
});

test("test_accepte_des_dates_deja_en_objet_Date_sans_planter", () => {
  const fait = { valid_at: new Date("2026-06-01"), invalid_at: null };

  assert.equal(presentALaDate(fait, new Date("2026-07-01")), true);
  assert.equal(etatTemporel(fait, new Date("2026-01-01")), "futur");
});

// L'absence se dit par la TEINTE, jamais par la transparence (l'estompage par
// alpha s'est révélé illisible à l'usage). Ces deux valeurs sont validées :
// séparation en vision normale et en daltonisme au-dessus des seuils, sur le
// fond #0e1013 — ne pas les retoucher sans repasser le validateur.
test("test_les_deux_couleurs_d_absence_sont_distinctes_et_figees", () => {
  assert.equal(COULEUR_FUTUR, "#3a4150");
  assert.equal(COULEUR_REVOLU, "#b5533c");
  assert.notEqual(COULEUR_FUTUR, COULEUR_REVOLU);
});

test("test_decompteTemporel_compte_les_trois_etats", () => {
  const aretes = [FAIT_TOUJOURS, FAIT_DEPUIS_JUIN, FAIT_REVOLU_EN_MAI, FAIT_FUTUR];

  const d = decompteTemporel(aretes, new Date("2026-07-01"));

  assert.deepEqual(d, { present: 2, futur: 1, revolu: 1 });
});

test("test_decompteTemporel_a_la_borne_basse_ne_voit_presque_rien", () => {
  const aretes = [FAIT_DEPUIS_JUIN, FAIT_REVOLU_EN_MAI, FAIT_FUTUR];

  const d = decompteTemporel(aretes, new Date("2025-01-01"));

  assert.deepEqual(d, { present: 0, futur: 3, revolu: 0 });
});

test("test_decompteTemporel_totalise_toujours_le_nombre_d_aretes", () => {
  const aretes = [FAIT_TOUJOURS, FAIT_DEPUIS_JUIN, FAIT_REVOLU_EN_MAI, FAIT_FUTUR];

  for (const jour of ["2025-01-01", "2026-03-01", "2026-07-01", "2027-06-01"]) {
    const d = decompteTemporel(aretes, new Date(jour));
    assert.equal(d.present + d.futur + d.revolu, aretes.length, jour);
  }
});

// Invariant de non-régression : au curseur maximum (borne max des dates),
// tout fait visible aujourd'hui (present) le reste — aucun fait qui était
// « present » ne bascule en « futur » ou « revolu » aux bornes.
test("test_au_curseur_maximum_tout_ce_qui_est_present_aujourd_hui_le_reste", () => {
  const aretes = [FAIT_TOUJOURS, FAIT_DEPUIS_JUIN, FAIT_REVOLU_EN_MAI, FAIT_FUTUR];
  const bornes = bornesTemporelles(aretes);

  for (const arete of aretes) {
    if (arete === FAIT_REVOLU_EN_MAI || arete === FAIT_FUTUR) continue;
    assert.equal(presentALaDate(arete, bornes.max), true);
    assert.equal(etatTemporel(arete, bornes.max), "present");
  }
});
