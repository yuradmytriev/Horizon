"""Read-only local viewer for generated summaries: python -m src.viewer"""

import html
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .services.email import _prepare_email_markdown, _render_email_markdown

SUMMARIES = Path(os.environ.get("HORIZON_SUMMARIES_DIR", "data/summaries"))
# Only plain summary filenames: blocks path traversal and other files in data/.
NAME_RE = re.compile(r"horizon-\d{4}-\d{2}-\d{2}-[a-z]{2}\.md")

CSS = (
    "body{max-width:760px;margin:40px auto;padding:0 16px;font:16px/1.6 -apple-system,system-ui,sans-serif;"
    "color:#222;background:#fff}a{color:#0a5bd8}h1,h2,h3{line-height:1.25}"
    "code{background:#f2f2f2;padding:1px 4px;border-radius:3px}nav{margin-bottom:24px}"
    "@media(prefers-color-scheme:dark){body{color:#ddd;background:#161616}a{color:#6ea8ff}code{background:#2a2a2a}}"
)


def page(title: str, body: str) -> bytes:
    return (
        f"<!doctype html><meta charset=utf-8><meta name=viewport content='width=device-width'>"
        f"<title>{html.escape(title)}</title><style>{CSS}</style>{body}"
    ).encode()


def summary_path(name: str) -> Path | None:
    return SUMMARIES / name if NAME_RE.fullmatch(name) and (SUMMARIES / name).is_file() else None


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        name = self.path.lstrip("/").split("?", 1)[0]
        if name == "":
            files = sorted((p.name for p in SUMMARIES.glob("*.md") if NAME_RE.fullmatch(p.name)), reverse=True)
            items = "".join(f"<li><a href='/{n}'>{n[8:-3]}</a></li>" for n in files) or "<li>No summaries yet</li>"
            return self.send(200, page("Horizon", f"<h1>Horizon</h1><ul>{items}</ul>"))
        path = summary_path(name)
        if path is None:
            return self.send(404, page("Not found", "<p>Not found. <a href='/'>Back</a></p>"))
        rendered = _render_email_markdown(_prepare_email_markdown(path.read_text(encoding="utf-8")))
        self.send(200, page(name[8:-3], f"<nav><a href='/'>← All digests</a></nav>{rendered}"))

    def send(self, status: int, content: bytes):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; img-src https:")
        self.end_headers()
        self.wfile.write(content)


def main():
    port = int(os.environ.get("PORT", "8000"))
    print(f"Horizon viewer on port {port}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
