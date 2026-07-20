// Tests de la grammaire de hash (ticket wayfinder 0025 — adressabilité de la
// vue). Module pur, zéro DOM : lancé hors du harnais pytest via node:test.
import { test } from "node:test";
import assert from "node:assert/strict";
import { serialiser, analyser } from "../app/viz/adressabilite.js";

test("test_serialiser_omet_tout_quand_par_defaut", () => {
  assert.equal(
    serialiser({ focus: null, surligner: [], prof: "2", ponts: null, deuxD: false }),
    ""
  );
});

test("test_serialiser_encode_focus_et_profondeur", () => {
  assert.equal(
    serialiser({ focus: "Léa", surligner: [], prof: "3", ponts: null, deuxD: false }),
    "focus=L%C3%A9a&prof=3"
  );
});

test("test_serialiser_liste_ponts_et_2d_dans_l_ordre", () => {
  assert.equal(
    serialiser({ focus: null, surligner: ["Léa", "Max"], prof: "2", ponts: 3, deuxD: true }),
    "surligner=L%C3%A9a,Max&ponts=3&2d=1"
  );
});

test("test_analyser_tolere_le_diese_et_les_cles_inconnues", () => {
  const etat = analyser("#focus=Léa&zzz=1");
  assert.equal(etat.focus, "Léa");
  assert.deepEqual(etat.surligner, []);
  assert.equal(etat.prof, "2");
  assert.equal(etat.ponts, null);
  assert.equal(etat.deuxD, false);
});

test("test_analyser_defauts_sur_hash_vide", () => {
  assert.deepEqual(analyser(""), {
    focus: null,
    surligner: [],
    prof: "2",
    ponts: null,
    deuxD: false,
  });
});

test("test_ponts_present_vaut_mode_actif_avec_seuil", () => {
  assert.equal(analyser("#ponts=5").ponts, 5);
  assert.equal(analyser("#").ponts, null);
});

test("test_le_round_trip_preserve_un_etat_riche", () => {
  const e = { focus: "Léa", surligner: ["Max", "Zoé"], prof: "3", ponts: 4, deuxD: true };
  assert.deepEqual(analyser(serialiser(e)), e);
});

test("test_surligner_gere_une_virgule_dans_un_nom", () => {
  const e = { focus: null, surligner: ["a,b", "c"], prof: "2", ponts: null, deuxD: false };
  assert.deepEqual(analyser(serialiser(e)).surligner, ["a,b", "c"]);
});
