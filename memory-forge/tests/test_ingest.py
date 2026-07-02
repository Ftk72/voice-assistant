"""Phase 4 — ingestion documentaire : chunker (markdown/PDF) et watcher par polling."""

import os
import time

from fastapi.testclient import TestClient

from app.config import Settings
from app.ingest.chunker import chunk_document
from app.ingest.watcher import DocumentWatcher
from app.main import create_app


def make_pdf(pages: list[str]) -> bytes:
    """PDF minimal valide, une ligne de texte par page (pypdf ne sait qu'écrire
    des pages vierges)."""
    objects: list[bytes] = []
    font_num = 3 + 2 * len(pages)
    kids = " ".join(f"{3 + 2 * i} 0 R" for i in range(len(pages)))
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    for i, text in enumerate(pages):
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Contents {4 + 2 * i} 0 R "
            f"/Resources << /Font << /F1 {font_num} 0 R >> >> >>".encode()
        )
        stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
        objects.append(
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream
            + b"\nendstream"
        )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for num, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += f"{num} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_at = len(out)
    out += f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_at}\n%%EOF\n".encode()
    )
    return bytes(out)


class TestChunkMarkdown:
    def test_decoupe_par_sections(self, tmp_path):
        doc = tmp_path / "judo-club.md"
        doc.write_text(
            "# Judo Club\n\nAdresse : 12 rue des Sports.\n\n"
            "## Horaires\n\nMercredi 17h pour les enfants.\n\n"
            "## Tarifs\n\n120 € l'année.\n",
            encoding="utf-8",
        )

        episodes = chunk_document(doc)

        assert [e.name for e in episodes] == [
            "judo-club.md § Judo Club",
            "judo-club.md § Horaires",
            "judo-club.md § Tarifs",
        ]
        assert all(e.source == "document" for e in episodes)
        assert "Mercredi 17h" in episodes[1].content

    def test_sans_titre_donne_un_seul_episode(self, tmp_path):
        doc = tmp_path / "note.md"
        doc.write_text("Léa fait du judo.\nLe club est rue des Sports.\n", encoding="utf-8")

        episodes = chunk_document(doc)

        assert len(episodes) == 1
        assert episodes[0].name == "note.md"
        assert "Léa fait du judo." in episodes[0].content


class TestChunkPdf:
    def test_decoupe_par_page(self, tmp_path):
        doc = tmp_path / "reglement.pdf"
        doc.write_bytes(make_pdf(["Horaires du judo : mercredi 17h.", "Tarif : 120 euros."]))

        episodes = chunk_document(doc)

        assert [e.name for e in episodes] == ["reglement.pdf p.1", "reglement.pdf p.2"]
        assert all(e.source == "document" for e in episodes)
        assert "mercredi 17h" in episodes[0].content
        assert "120 euros" in episodes[1].content


class TestDocumentWatcher:
    def test_premier_scan_ingere_les_fichiers_supportes(self, tmp_path):
        (tmp_path / "judo.md").write_text("# Judo\n\nMercredi 17h.\n", encoding="utf-8")
        (tmp_path / "photo.jpg").write_bytes(b"\xff\xd8pas un document")

        episodes = DocumentWatcher(tmp_path).scan_once()

        assert [e.name for e in episodes] == ["judo.md § Judo"]

    def test_rescan_sans_changement_ne_reingere_rien(self, tmp_path):
        (tmp_path / "judo.md").write_text("# Judo\n\nMercredi 17h.\n", encoding="utf-8")

        assert DocumentWatcher(tmp_path).scan_once() != []
        # L'état est persisté : même un watcher relancé (redémarrage) ne ré-ingère pas.
        assert DocumentWatcher(tmp_path).scan_once() == []

    def test_fichier_modifie_est_reingere(self, tmp_path):
        doc = tmp_path / "judo.md"
        doc.write_text("# Judo\n\nMercredi 17h.\n", encoding="utf-8")
        watcher = DocumentWatcher(tmp_path)
        watcher.scan_once()

        doc.write_text("# Judo\n\nJeudi 18h désormais.\n", encoding="utf-8")
        os.utime(doc, (doc.stat().st_atime, doc.stat().st_mtime + 1))

        episodes = watcher.scan_once()

        assert len(episodes) == 1
        assert "Jeudi 18h" in episodes[0].content


class TestIngestionDansLApp:
    def test_document_depose_devient_des_faits(self, tmp_path):
        (tmp_path / "judo-club.md").write_text(
            "# Judo Club\n\nLes cours enfants ont lieu mercredi à 17h.\n", encoding="utf-8"
        )
        settings = Settings(
            backend="fake", documents_dir=tmp_path, documents_poll_seconds=0.05
        )

        with TestClient(create_app(settings)) as client:
            deadline = time.monotonic() + 5
            facts = []
            while time.monotonic() < deadline and not facts:
                facts = client.get("/search", params={"q": "mercredi"}).json()["facts"]
                time.sleep(0.05)

        assert facts, "le document déposé n'a jamais été ingéré"
        assert facts[0]["provenance"] == {"source": "document", "name": "judo-club.md § Judo Club"}
