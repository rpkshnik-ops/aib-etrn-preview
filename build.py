"""Deterministic static build. Python 3.11+, no third-party build dependencies."""
import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

from src.deployment import settings
from src.render import render_page

ROOT = Path(__file__).resolve().parent


def write_atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temp = Path(handle.name)
        try:
            handle.write(content)
        except BaseException:
            handle.close()
            temp.unlink(missing_ok=True)
            raise
    try:
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def build(output, options=None):
    options = settings(options)
    output = Path(output).resolve()
    if output in (ROOT, ROOT / "src", ROOT / "deploy", ROOT / "backend"):
        raise ValueError("Use a separate build directory")
    assets = {
        "styles.css": (ROOT / "src/styles.css").read_bytes(),
        "app.js": (ROOT / "src/app.js").read_bytes(),
        "assets/aib-logo.png": (ROOT / "src/assets/aib-site.png").read_bytes(),
    }
    version = hashlib.sha256(b"".join(assets.values())).hexdigest()[:12]
    for name in ('offer.pdf', 'confidentiality.pdf'):
        assets['assets/documents/' + name] = (ROOT / 'src/assets/documents' / name).read_bytes()
    html = '\n'.join(line.rstrip() for line in render_page(options, version).splitlines()) + '\n'
    production = options["mode"] == "production"
    robots = "User-agent: *\nAllow: /\nSitemap: " + options["site_url"] + "sitemap.xml\n" if production else "User-agent: *\nDisallow: /\n"
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    if production:
        sitemap += "<url><loc>" + escape(options["site_url"]) + "</loc></url>"
    sitemap += "</urlset>\n"
    assets.update({
        "index.html": html.encode("utf-8"),
        "robots.txt": robots.encode("utf-8"),
        "sitemap.xml": sitemap.encode("utf-8"),
        ".nojekyll": b"",
        "404.html": '<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Страница не найдена — Компания АиБ</title><body><h1>Страница не найдена</h1><p><a href="./">Вернуться на главную</a></p></body></html>'.encode("utf-8"),
    })
    # Write HTML last so a failed asset write does not publish a partial new page.
    for name, content in assets.items():
        if name != "index.html":
            write_atomic(output / name, content)
    write_atomic(output / "index.html", assets["index.html"])
    print(f"Built {options['mode']}: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path)
    parser.add_argument("--mode", choices=("preview", "staging", "production"))
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    options = json.loads(args.config.read_text(encoding="utf-8-sig")) if args.config else {}
    if args.mode:
        options["mode"] = args.mode
    try:
        build(args.output, options)
    except (ValueError, OSError) as exc:
        parser.exit(1, str(exc) + "\n")
