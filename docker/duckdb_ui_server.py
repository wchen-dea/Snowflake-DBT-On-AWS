import os
import secrets
import threading
from html import escape
from typing import Any

import duckdb
from flask import Flask, Response, jsonify, request


app = Flask(__name__)
DB_PATH = os.getenv("DUCKDB_PATH", "/opt/dbt/warehouse/banking_vault.duckdb")
APP_PORT = int(os.getenv("APP_PORT", "4213"))
MAX_ROWS = int(os.getenv("DUCKDB_UI_MAX_ROWS", "200"))
QUERY_TIMEOUT_MS = int(os.getenv("DUCKDB_UI_QUERY_TIMEOUT_MS", "10000"))
UI_USERNAME = os.getenv("DUCKDB_UI_USERNAME", "")
UI_PASSWORD = os.getenv("DUCKDB_UI_PASSWORD", "")
HEALTH_TOKEN = os.getenv("DUCKDB_UI_HEALTH_TOKEN", "")


def auth_enabled() -> bool:
    return bool(UI_USERNAME or UI_PASSWORD)


def unauthorized() -> Response:
    return Response(
        "Authentication required",
        401,
        {"WWW-Authenticate": 'Basic realm="DuckDB UI"'},
    )


def check_auth() -> Response | None:
    if not auth_enabled():
        return None

    auth = request.authorization
    if not auth:
        return unauthorized()

    user_ok = secrets.compare_digest(auth.username or "", UI_USERNAME)
    pass_ok = secrets.compare_digest(auth.password or "", UI_PASSWORD)
    if user_ok and pass_ok:
        return None
    return unauthorized()


def check_health_access() -> Response | None:
    remote = request.remote_addr or ""
    if remote in {"127.0.0.1", "::1"}:
        return None

    if HEALTH_TOKEN:
        provided = request.headers.get("X-Health-Token", "")
        if secrets.compare_digest(provided, HEALTH_TOKEN):
            return None

    return Response("Forbidden", 403)


def run_query(sql: str) -> tuple[list[str], list[tuple[Any, ...]]]:
    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        outcome: dict[str, Any] = {}
        error: dict[str, BaseException] = {}

        def worker_fn() -> None:
            try:
                result = conn.execute(sql)
                outcome["columns"] = [desc[0] for desc in (result.description or [])]
                outcome["rows"] = result.fetchmany(MAX_ROWS)
            except BaseException as exc:  # pragma: no cover - worker path
                error["exception"] = exc

        worker = threading.Thread(target=worker_fn, daemon=True)
        worker.start()
        worker.join(max(QUERY_TIMEOUT_MS, 1) / 1000.0)

        if worker.is_alive():
            try:
                conn.interrupt()
            except Exception:
                pass
            worker.join(1.0)
            raise TimeoutError(f"Query timed out after {QUERY_TIMEOUT_MS} ms")

        if "exception" in error:
            raise error["exception"]

        columns = outcome.get("columns") or []
        rows = outcome.get("rows") or []
        return columns, rows
    finally:
        conn.close()


@app.get("/health")
def health():
    health_access_error = check_health_access()
    if health_access_error is not None:
        return health_access_error

    if not os.path.exists(DB_PATH):
        return jsonify({"status": "error", "message": f"Database not found at {DB_PATH}"}), 503

    try:
        cols, rows = run_query("select 1 as ok")
        ok = int(rows[0][0]) if rows else 0
        return jsonify({"status": "ok", "db_path": DB_PATH, "probe": dict(zip(cols, [ok]))})
    except Exception as exc:  # pragma: no cover - defensive path
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.get("/")
def index():
    auth_error = check_auth()
    if auth_error is not None:
        return auth_error

    default_sql = "show tables;"
    sql = request.args.get("q", default_sql).strip() or default_sql

    if not os.path.exists(DB_PATH):
        return (
            f"""
            <html><body style=\"font-family: sans-serif; margin: 2rem;\">
              <h2>DuckDB UI</h2>
              <p>Database file is missing:</p>
              <pre>{escape(DB_PATH)}</pre>
              <p>Wait for <code>dbt-runner</code> to finish, then refresh.</p>
            </body></html>
            """,
            503,
        )

    try:
        columns, rows = run_query(sql)
        table_header = "".join(f"<th>{escape(str(c))}</th>" for c in columns)
        table_rows = "".join(
            "<tr>" + "".join(f"<td>{escape(str(cell))}</td>" for cell in row) + "</tr>"
            for row in rows
        )
        return f"""
        <html>
          <head>
            <title>DuckDB UI</title>
            <style>
              body {{ font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; margin: 1.5rem; }}
              textarea {{ width: 100%; min-height: 140px; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
              button {{ margin-top: 0.75rem; padding: 0.4rem 0.8rem; }}
              table {{ border-collapse: collapse; margin-top: 1rem; width: 100%; }}
              th, td {{ border: 1px solid #ddd; padding: 0.4rem; text-align: left; }}
              th {{ background: #f5f5f5; }}
              code {{ background: #f5f5f5; padding: 0.1rem 0.3rem; }}
            </style>
          </head>
          <body>
            <h2>DuckDB UI (Stable Service)</h2>
            <p><code>{escape(DB_PATH)}</code></p>
            <form method="get" action="/">
              <textarea name="q">{escape(sql)}</textarea>
              <br/>
              <button type="submit">Run Query</button>
            </form>
            <p>Showing up to {MAX_ROWS} row(s). Timeout: {QUERY_TIMEOUT_MS} ms.</p>
            <table>
              <thead><tr>{table_header}</tr></thead>
              <tbody>{table_rows}</tbody>
            </table>
          </body>
        </html>
        """
    except Exception as exc:
        return (
            f"""
            <html><body style=\"font-family: sans-serif; margin: 1.5rem;\">
              <h2>DuckDB UI Error</h2>
              <pre>{escape(str(exc))}</pre>
              <p><a href=\"/\">Back</a></p>
            </body></html>
            """,
            400,
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=APP_PORT)
