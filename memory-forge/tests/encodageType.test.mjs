// Tests de l'encodage forme/type (ticket wayfinder 0026 — encodage visuel du
// type d'entité). Module pur, zéro DOM : lancé hors du harnais pytest via
// node:test, même patron que adressabilite.test.mjs.
import { test } from "node:test";
import assert from "node:assert/strict";
import { FORMES_PAR_TYPE, formeDuType } from "../app/viz/encodageType.js";

const TYPES_DE_L_ONTOLOGIE = [
  "Activite", "Personne", "Lieu", "Organisation", "Animal", "Bien", "Projet", "Aliment",
];

test("test_couvre_les_huit_types_de_l_ontologie", () => {
  assert.deepEqual(new Set(Object.keys(FORMES_PAR_TYPE)), new Set(TYPES_DE_L_ONTOLOGIE));
});

test("test_chaque_type_a_une_forme_distincte", () => {
  const formes = Object.values(FORMES_PAR_TYPE);
  assert.equal(new Set(formes).size, formes.length);
});

test("test_formeDuType_renvoie_la_forme_associee", () => {
  assert.equal(formeDuType("Personne"), "sphere");
  assert.equal(formeDuType("Activite"), "tore");
});

test("test_formeDuType_renvoie_null_pour_type_absent_ou_inconnu", () => {
  assert.equal(formeDuType(null), null);
  assert.equal(formeDuType(undefined), null);
  assert.equal(formeDuType("Zorglub"), null);
});
