"""Web app: python app.py  (dev)  |  gunicorn app:app  (production)"""
from __future__ import annotations

import csv
import os

from flask import Flask, jsonify, render_template, request, send_from_directory

import service
from config import ROOT

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024  # payload JSON nhỏ, chặn request lớn
OUT = ROOT / "outputs"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def healthz():
    return jsonify(status="ok", models={d: service.load_model(d) is not None for d in service.AGENTS})


@app.get("/api/schema")
def schema():
    return jsonify(schema=service.SCHEMA, agents={d: service.AGENT_LABEL[d] for d in service.AGENTS})


@app.post("/api/predict")
def predict():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="Body phải là JSON object."), 400
    try:
        return jsonify(service.predict(payload))
    except ValueError as e:
        return jsonify(error=str(e)), 400


@app.get("/api/report")
def report():
    rows, f = [], OUT / "metrics_summary.csv"
    if f.exists():
        with f.open(encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append({k: (float(v) if k not in ("ds", "best") and v not in ("", None) else v) for k, v in r.items()})
    figs = sorted(p.name for p in (OUT / "figures").glob("*.png")) if (OUT / "figures").exists() else []
    return jsonify(metrics=rows, figures=figs)


@app.get("/figures/<path:name>")
def figures(name):
    return send_from_directory(OUT / "figures", name)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=os.environ.get("DEBUG") == "1")
