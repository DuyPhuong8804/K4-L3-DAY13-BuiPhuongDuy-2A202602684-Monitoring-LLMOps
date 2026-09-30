"""Dashboard 6 panel đọc data/logs.jsonl theo config/dashboard.yaml.

Chạy: streamlit run scripts/dashboard.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
PANELS = {p["id"]: p for p in CONFIG["panels"]}
LOG_PATH = ROOT / "data" / "logs.jsonl"

st.set_page_config(page_title=CONFIG["title"], layout="wide")
st.title(CONFIG["title"])


def load_logs() -> pd.DataFrame:
    rows = []
    if LOG_PATH.exists():
        for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    return df


def p(series: pd.Series, q: float) -> float:
    return float(series.quantile(q)) if len(series) else 0.0


def threshold_label(panel: dict) -> str:
    t = panel["threshold"]
    ops = {"lte": "<=", "gte": ">="}
    return f"SLO/threshold: {t['aggregation']} {ops[t['operator']]} {t['value']} {panel['unit']}"


def add_threshold(fig: go.Figure, panel: dict, value: float | None = None) -> None:
    fig.add_hline(
        y=panel["threshold"]["value"] if value is None else value,
        line_dash="dash",
        line_color="red",
        annotation_text=threshold_label(panel),
    )


def header(panel: dict, ok: bool | None, current: str) -> None:
    badge = "" if ok is None else (" ✅" if ok else " 🔴")
    st.subheader(f"{panel['title']} ({panel['unit']}){badge}")
    st.caption(f"{current} · {threshold_label(panel)} · range: last {minutes} min")


def render() -> None:
    df = load_logs()
    if df.empty:
        st.warning("data/logs.jsonl chưa có dữ liệu. Chạy load_test.py trước.")
        return
    if minutes:
        df = df[df["ts"] >= pd.Timestamp.now(tz="UTC") - pd.Timedelta(minutes=minutes)]
    if df.empty:
        st.warning(f"Không có log trong {minutes} phút gần nhất.")
        return

    st.caption(f"Time range: {df['ts'].min():%H:%M:%S} → {df['ts'].max():%H:%M:%S} UTC · {len(df)} log records")
    sent = df[df["event"] == "response_sent"]
    recv = df[df["event"] == "request_received"]
    failed = df[df["event"] == "request_failed"]
    col1, col2 = st.columns(2)

    with col1:
        panel = PANELS["latency"]
        p95 = p(sent["latency_ms"], 0.95)
        header(panel, p95 <= panel["threshold"]["value"],
               f"P50 {p(sent['latency_ms'], .5):.0f} · P95 {p95:.0f} · P99 {p(sent['latency_ms'], .99):.0f} · TTFT P95 {p(sent['ttft_ms'], .95):.0f} ms")
        fig = go.Figure()
        fig.add_scatter(x=sent["ts"], y=sent["latency_ms"], mode="lines+markers", name="latency_ms")
        fig.add_scatter(x=sent["ts"], y=sent["ttft_ms"], mode="lines+markers", name="ttft_ms")
        add_threshold(fig, panel)
        fig.update_layout(yaxis_title="ms", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        panel = PANELS["traffic"]
        per_min = recv.set_index("ts").resample("1min").size()
        rate = float(per_min.mean()) if len(per_min) else 0.0
        header(panel, rate >= panel["threshold"]["value"], f"{len(recv)} requests · avg {rate:.1f}/min")
        fig = go.Figure(go.Bar(x=per_min.index, y=per_min.values, name="requests/min"))
        add_threshold(fig, panel)
        fig.update_layout(yaxis_title="requests/min", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        panel = PANELS["errors"]
        err_rate = len(failed) / len(recv) * 100 if len(recv) else 0.0
        tool = df["tool_success"].dropna() if "tool_success" in df else pd.Series(dtype=bool)
        retrieval_ok = float(tool.astype(bool).mean() * 100) if len(tool) else 100.0
        header(panel, err_rate <= panel["threshold"]["value"],
               f"Error rate {err_rate:.2f}% · Retrieval success {retrieval_ok:.1f}%")
        by_type = failed["error_type"].value_counts() if "error_type" in failed else pd.Series(dtype=int)
        fig = go.Figure()
        fig.add_bar(x=["error_rate_pct", "retrieval_success_pct"], y=[err_rate, retrieval_ok])
        add_threshold(fig, panel)
        fig.update_layout(yaxis_title="percent", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)
        st.write("Errors by type:", by_type.to_dict() or "none")

    with col4:
        panel = PANELS["cost"]
        total = float(sent["cost_usd"].sum())
        header(panel, total <= panel["threshold"]["value"], f"Total {total:.4f} USD")
        per_min = sent.set_index("ts")["cost_usd"].resample("1min").sum()
        fig = go.Figure(go.Bar(x=per_min.index, y=per_min.values, name="cost/min"))
        fig.update_layout(yaxis_title="usd", height=300, margin=dict(t=20))
        add_threshold(fig, panel)
        st.plotly_chart(fig, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        panel = PANELS["tokens"]
        tin, tout = int(sent["tokens_in"].sum()), int(sent["tokens_out"].sum())
        header(panel, tin + tout <= panel["threshold"]["value"], f"in {tin} · out {tout} · total {tin + tout} tokens")
        fig = go.Figure(go.Bar(x=["tokens_in", "tokens_out"], y=[tin, tout]))
        add_threshold(fig, panel)
        fig.update_layout(yaxis_title="tokens", height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)

    with col6:
        panel = PANELS["quality"]
        mean_q = float(sent["quality_score"].mean()) if len(sent) else 0.0
        header(panel, mean_q >= panel["threshold"]["value"], f"Mean {mean_q:.2f}")
        fig = go.Figure(go.Scatter(x=sent["ts"], y=sent["quality_score"], mode="lines+markers"))
        add_threshold(fig, panel)
        fig.update_layout(yaxis_title="score 0-1", yaxis_range=[0, 1], height=300, margin=dict(t=20))
        st.plotly_chart(fig, use_container_width=True)


minutes = st.sidebar.slider("Time range (minutes)", 5, 1440, CONFIG["time_range_minutes"], step=5)
refresh = st.sidebar.slider("Refresh (seconds)", 5, 120, CONFIG["refresh_seconds"], step=5)
render()
time.sleep(refresh)
st.rerun()
