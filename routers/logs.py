import json
import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.security.api_key import APIKeyHeader

import config
from logger.transaction_log import transaction_log

router = APIRouter(tags=["logs"])

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
_http_basic = HTTPBasic(auto_error=False)


def _verify_logs_auth(
    api_key: str = Depends(api_key_header),
    credentials: HTTPBasicCredentials = Depends(_http_basic),
):
    # Allow access via X-API-Key header (bot/curl access)
    if api_key is not None:
        if secrets.compare_digest(api_key, config.API_KEY):
            return
        raise HTTPException(status_code=403, detail="Invalid API key")

    # Allow access via HTTP Basic Auth (browser access)
    logs_user = config.LOGS_USER
    logs_password = config.LOGS_PASSWORD
    if credentials is not None and logs_user and logs_password:
        user_ok = secrets.compare_digest(credentials.username, logs_user)
        pass_ok = secrets.compare_digest(credentials.password, logs_password)
        if user_ok and pass_ok:
            return

    # No valid auth — issue a Basic Auth challenge so browsers prompt for credentials
    raise HTTPException(
        status_code=401,
        detail="Authentication required",
        headers={"WWW-Authenticate": 'Basic realm="commandhub.iot logs"'},
    )


def _fmt_payload(payload) -> str:
    if isinstance(payload, dict):
        return json.dumps(payload)
    return str(payload)


def _status_badge(status_code, timed_out) -> str:
    if status_code is None:
        return '<span style="background:#555;color:#fff;padding:2px 8px;border-radius:3px">in-progress</span>'
    if timed_out or status_code == 408:
        color = "#c0392b"
    elif 200 <= status_code < 300:
        color = "#27ae60"
    else:
        color = "#c0392b"
    return f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:3px">{status_code}</span>'


def _build_transactions_html(transactions) -> str:
    if not transactions:
        return '<p style="color:#666;font-style:italic">No entries yet.</p>'
    parts = []
    for entry in transactions:
        ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        badge = _status_badge(entry.status_code, entry.timed_out)
        dur = f"{entry.duration_ms}ms" if entry.duration_ms is not None else ""
        header = (
            f'<div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
            f'<span style="color:#888">{ts}</span>'
            f'<span style="color:#7ec8e3;font-weight:bold">{entry.method}</span>'
            f'<span style="color:#fff">{entry.path}</span>'
            f"{badge}"
            f'<span style="color:#888">{dur}</span>'
            f"</div>"
        )
        steps_html = ""
        for step in entry.steps:
            if step.direction == "publish":
                arrow = '<span style="color:#f39c12">→ PUBLISH</span>'
            else:
                arrow = '<span style="color:#2ecc71">← RECEIVE</span>'
            steps_html += (
                f'<div style="margin-left:16px;color:#ccc">'
                f"{arrow}"
                f'&nbsp;&nbsp;<span style="color:#aaa">{step.topic}</span>'
                f'&nbsp;&nbsp;<span style="color:#888">{_fmt_payload(step.payload)}</span>'
                f"</div>"
            )
        if entry.timed_out:
            steps_html += (
                '<div style="margin-left:16px;color:#c0392b;font-weight:bold">✗ TIMEOUT</div>'
            )
        parts.append(
            f'<div style="border:1px solid #2a2d36;border-radius:4px;padding:10px 14px;margin-bottom:10px">'
            f"{header}{steps_html}"
            f"</div>"
        )
    return "".join(parts)


def _build_mqtt_html(events) -> str:
    if not events:
        return '<p style="color:#666;font-style:italic">No entries yet.</p>'
    rows = []
    for event in events:
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        rows.append(
            f'<div style="padding:4px 0;border-bottom:1px solid #1e2130;color:#ccc">'
            f'<span style="color:#888;margin-right:12px">{ts}</span>'
            f'<span style="color:#aaa;margin-right:12px">{event.topic}</span>'
            f'<span style="color:#888">{_fmt_payload(event.payload)}</span>'
            f"</div>"
        )
    return "".join(rows)


@router.get("/logs", response_class=HTMLResponse, include_in_schema=False)
def get_logs(_auth=Depends(_verify_logs_auth)):
    transactions = transaction_log.get_transactions()
    mqtt_events = transaction_log.get_mqtt_events()

    transactions_html = _build_transactions_html(transactions)
    mqtt_html = _build_mqtt_html(mqtt_events)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="10">
<title>commandhub.iot — transaction log</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: #0f1117;
    color: #ccc;
    font-family: 'Courier New', Courier, monospace;
    font-size: 13px;
    padding: 20px;
  }}
  h1 {{ color: #7ec8e3; font-size: 18px; margin: 0 0 20px; }}
  h2 {{ color: #aaa; font-size: 14px; margin: 0 0 12px; border-bottom: 1px solid #2a2d36; padding-bottom: 6px; }}
  .columns {{
    display: flex;
    gap: 24px;
    align-items: flex-start;
  }}
  .col {{
    flex: 1 1 0;
    min-width: 0;
  }}
  @media (max-width: 800px) {{
    .columns {{ flex-direction: column; }}
  }}
</style>
</head>
<body>
<h1>commandhub.iot — transaction log</h1>
<div class="columns">
  <div class="col">
    <h2>API Transactions</h2>
    {transactions_html}
  </div>
  <div class="col">
    <h2>MQTT Monitor</h2>
    {mqtt_html}
  </div>
</div>
</body>
</html>"""
    return HTMLResponse(content=html)
