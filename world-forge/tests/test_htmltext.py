from app.world.htmltext import extract_text

HTML = """<html><head><title>Mon article</title>
<style>body { color: red }</style></head>
<body>
<nav><a href="/">Accueil</a> | <a href="/contact">Contact</a></nav>
<article>
  <h1>Mon article</h1>
  <p>Premier   paragraphe,
  avec des espaces à normaliser.</p>
  <p>Second paragraphe &amp; entités.</p>
</article>
<script>alert("pub");</script>
<footer>Mentions légales</footer>
</body></html>"""


def test_extrait_titre_et_texte():
    title, text = extract_text(HTML)

    assert title == "Mon article"
    assert "Premier paragraphe, avec des espaces à normaliser." in text
    assert "Second paragraphe & entités." in text


def test_ignore_scripts_styles_et_menus():
    _, text = extract_text(HTML)

    assert "alert" not in text
    assert "color: red" not in text
    assert "Accueil" not in text
    assert "Mentions légales" not in text
