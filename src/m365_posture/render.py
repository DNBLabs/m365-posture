"""Render standardized posture reports as HTML."""

from __future__ import annotations

from typing import Any

from jinja2 import Environment, select_autoescape

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>{{ title }}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 1.5rem; max-width: 60rem; }
    h1 { font-size: 1.25rem; }
    .meta { color: #444; font-size: 0.9rem; margin-bottom: 1rem; }
    .summary { margin: 1rem 0; }
    section { border-top: 1px solid #ccc; padding-top: 0.75rem; margin-top: 0.75rem; }
    .status-ok { color: #0a0; }
    .status-degraded { color: #a60; }
    .finding { margin: 0.35rem 0 0 1rem; font-size: 0.9rem; }
    .severity-info { color: #06c; }
    .severity-warn { color: #c60; }
    .err { color: #a00; font-size: 0.85rem; }
  </style>
</head>
<body>
  <h1>{{ title }}</h1>
  <div class="meta">
    <div><strong>Generated:</strong> {{ generated_at }}</div>
    <div><strong>Schema version:</strong> {{ schema_version }}</div>
  </div>
  <div class="summary">
    <strong>Summary:</strong>
    <span class="status-ok">{{ summary_ok }} OK</span>,
    <span class="status-degraded">{{ summary_degraded }} degraded</span>
  </div>
  {% for chapter_id, ch in chapters %}
  <section id="chapter-{{ chapter_id }}">
    <h2>{{ chapter_id }} <span class="status-{{ ch.status|lower }}">{{ ch.status }}</span></h2>
    {% if ch.error_summary %}
    <p class="err">Error: {{ ch.error_summary }}</p>
    {% endif %}
    {% if ch.findings %}
    <ul>
      {% for f in ch.findings %}
      <li class="finding severity-{{ f.severity|lower }}">
        <strong>{{ f.severity }}</strong> {{ f.code }} — {{ f.message }}
      </li>
      {% endfor %}
    </ul>
    {% else %}
    <p class="meta">No findings.</p>
    {% endif %}
  </section>
  {% endfor %}
</body>
</html>
"""

_env = Environment(
    autoescape=select_autoescape(enabled_extensions=("html", "xml")),
)


def render_html(report: dict[str, Any]) -> str:
    """Render a `build_report` envelope to an HTML document string."""
    chapters_dict: dict[str, Any] = report.get("chapters") or {}
    chapters_sorted = sorted(chapters_dict.items(), key=lambda kv: kv[0])
    summary = report.get("summary") or {}
    title = report.get("title") or "Microsoft 365 security posture report"
    return _env.from_string(_HTML_TEMPLATE).render(
        title=title,
        generated_at=report.get("generatedAt", ""),
        schema_version=report.get("schemaVersion", ""),
        summary_ok=summary.get("ok", 0),
        summary_degraded=summary.get("degraded", 0),
        chapters=chapters_sorted,
    )
