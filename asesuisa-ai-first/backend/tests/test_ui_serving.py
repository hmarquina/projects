import importlib
import mimetypes

from fastapi.testclient import TestClient


def test_js_mime_is_forced_even_if_registry_says_text_plain() -> None:
    """Windows toma .js del registro; con text/plain el navegador bloquea el modulo y la UI queda en blanco."""
    import app.main as main

    mimetypes.add_type("text/plain", ".js")
    importlib.reload(main)
    assert mimetypes.guess_type("index-abc.js")[0] == "text/javascript"
    assert mimetypes.guess_type("style.css")[0] == "text/css"


def test_root_serves_html_or_explains_missing_ui() -> None:
    import app.main as main

    response = TestClient(main.app).get("/")
    assert response.headers["content-type"].startswith("text/html")
    if response.status_code == 503:  # sin frontend/dist: aviso explicito, no pagina en blanco
        assert "interfaz no compilada" in response.text
    else:
        assert response.status_code == 200
        assert '<div id="root"' in response.text


def test_built_assets_have_javascript_content_type() -> None:
    import re

    import app.main as main

    index = TestClient(main.app).get("/")
    if index.status_code != 200:
        return
    match = re.search(r'src="(/assets/[^"]+\.js)"', index.text)
    assert match, "index.html no referencia un bundle JS"
    asset = TestClient(main.app).get(match.group(1))
    assert asset.status_code == 200
    assert "javascript" in asset.headers["content-type"]
