from __future__ import annotations

import html
import streamlit as st

NAVY = "#12344D"
CORAL = "#E9856A"
TEAL = "#247B73"
BEIGE = "#F4EFE6"
CREAM = "#FBF8F2"
INK = "#20313E"


def inject_css() -> None:
    st.markdown(
        f"""
<style>
:root {{
  --navy: {NAVY}; --coral: {CORAL}; --teal: {TEAL}; --beige: {BEIGE}; --cream: {CREAM}; --ink: {INK};
}}
.stApp {{ background: var(--cream); color: var(--ink); }}
[data-testid="stHeader"] {{ background: rgba(251,248,242,.92); }}
[data-testid="stSidebar"] {{ background: #0f2f46; }}
[data-testid="stSidebar"] * {{ color: #f9fbfc; }}
[data-testid="stSidebar"] div[role="radiogroup"] label {{
  border-radius: 10px; padding: .45rem .55rem; margin-bottom: .12rem;
}}
[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: rgba(255,255,255,.08); }}
h1,h2,h3 {{ font-family: Georgia, 'Times New Roman', serif; color: var(--navy); letter-spacing: -.02em; }}
.block-container {{ max-width: 1180px; padding-top: 1.8rem; padding-bottom: 5rem; }}
.hero {{
  background: linear-gradient(135deg,#12344D 0%,#194967 68%,#256B73 100%);
  padding: 2.2rem 2.3rem; border-radius: 24px; color:white; margin-bottom: 1.25rem;
  box-shadow: 0 18px 42px rgba(18,52,77,.14); border: 1px solid rgba(255,255,255,.1);
}}
.hero h1 {{ color:white; font-size: 2.55rem; margin: 0 0 .6rem 0; line-height: 1.05; }}
.hero p {{ color:#eef5f6; font-size: 1.08rem; max-width: 850px; margin: .35rem 0; line-height: 1.6; }}
.hero-meta {{ margin-top:1rem; display:flex; gap:.55rem; flex-wrap:wrap; }}
.pill {{ display:inline-block; border-radius:999px; padding:.38rem .72rem; font-weight:700; font-size:.82rem; }}
.pill-light {{ background:rgba(255,255,255,.13); color:white; border:1px solid rgba(255,255,255,.18); }}
.pill-coral {{ background:var(--coral); color:#122e43; }}
.card {{ background:white; border:1px solid #e6e0d8; border-radius:18px; padding:1.25rem 1.35rem; box-shadow:0 8px 25px rgba(18,52,77,.055); margin-bottom:.85rem; }}
.card-soft {{ background:var(--beige); border-color:#e9dfd1; }}
.section-kicker {{ color:#6d7d88; font-size:.74rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; margin-bottom:.25rem; }}
.step-title {{ font-family:Georgia,'Times New Roman',serif; color:var(--navy); font-size:1.55rem; margin:.1rem 0 .3rem 0; }}
.metric-row {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.75rem; margin:1rem 0; }}
.metric-card {{ background:white; border:1px solid #e6e0d8; border-radius:16px; padding:1rem 1.1rem; }}
.metric-label {{ color:#71808b; font-size:.78rem; font-weight:700; text-transform:uppercase; letter-spacing:.08em; }}
.metric-value {{ color:var(--navy); font-size:1.55rem; font-weight:800; margin-top:.18rem; }}
.result-card {{ background:white; border:1px solid #e3ddd5; border-left:5px solid var(--coral); border-radius:16px; padding:1rem 1.15rem; margin:.7rem 0; }}
.score {{ font-size:1.65rem; font-weight:800; color:var(--navy); }}
.score-caption {{ font-size:.78rem; color:#71808b; }}
.notice {{ background:#fff8e9; border:1px solid #ead59e; border-radius:14px; padding:.9rem 1rem; color:#534823; }}
.success-note {{ background:#eef7f4; border:1px solid #bfdcd5; border-radius:14px; padding:.9rem 1rem; }}
.agent {{ display:flex; align-items:center; gap:.8rem; background:white; border:1px solid #e5ddd4; border-radius:16px; padding:1rem; }}
.agent-orb {{ width:48px; height:48px; border-radius:50%; background:linear-gradient(135deg,var(--coral),#f2b089); display:flex; align-items:center; justify-content:center; font-weight:900; color:var(--navy); }}
.footer {{ margin-top:2rem; padding-top:1rem; border-top:1px solid #ded8cf; color:#6f7d86; font-size:.84rem; }}
a {{ color:#165e72; }}
.stButton > button, .stDownloadButton > button {{ border-radius:10px; min-height:2.7rem; font-weight:700; }}
.stButton > button[kind="primary"] {{ background:var(--navy); border-color:var(--navy); }}
[data-testid="stMetric"] {{ background:white; border:1px solid #e5ded6; padding:.75rem; border-radius:14px; }}
@media(max-width: 760px) {{ .hero h1 {{font-size:2rem}} .metric-row {{grid-template-columns:1fr}} }}
</style>
""",
        unsafe_allow_html=True,
    )


def hero(visitor_count: int) -> None:
    st.markdown(
        f"""
<div class="hero">
  <div class="section-kicker" style="color:#bcd3dc">UK BENEFITS • AI SCREENING • APPLICATION GUIDANCE</div>
  <h1>AI Financial Benefits Consultant</h1>
  <p>Sissie AI reviews household, work, income, savings, debt, housing, caring and health information to prioritise UK benefits and trusted support resources.</p>
  <div class="hero-meta">
    <span class="pill pill-coral">Author: Sissie Ma</span>
    <span class="pill pill-light">Advisor: Dr. Qingyang Xiao</span>
    <span class="pill pill-light">Cumulative app visitors: {int(visitor_count):,}</span>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def sidebar_brand(visitor_count: int, counter_source: str) -> None:
    st.sidebar.markdown("## Sissie AI")
    st.sidebar.caption("UK Financial Benefits Consultant")
    st.sidebar.markdown(f"**👥 Cumulative visitors: {int(visitor_count):,}**")
    st.sidebar.caption(f"Counter: {counter_source}")
    st.sidebar.markdown("---")


def section_header(step: str, title: str, description: str) -> None:
    st.markdown(
        f"""
<div class="card card-soft">
  <div class="section-kicker">{html.escape(step)}</div>
  <div class="step-title">{html.escape(title)}</div>
  <div style="color:#60717d; line-height:1.55">{html.escape(description)}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def footer(visitor_count: int) -> None:
    st.markdown(
        f"""
<div class="footer">
  <strong>AI Financial Benefits Consultant</strong> · Author: Sissie Ma · Advisor: Dr. Qingyang Xiao · Cumulative visitors: {int(visitor_count):,}<br/>
  Screening and educational prototype only. It is not DWP, HMRC, an NHS body, a local authority, Social Security Scotland or the Department for Communities (NI), and it does not make official eligibility decisions.
</div>
""",
        unsafe_allow_html=True,
    )
