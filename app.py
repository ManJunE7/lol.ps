import os
import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

# -----------------------------
# Config
# -----------------------------
st.set_page_config(page_title="ARAM 챔피언 보드", layout="wide")
DATA_DIR = "/content" if os.path.exists("/content") else "."

MASTER_CANDIDATES = ["champion_master_plus.csv", "champion_master.csv"]
SPELL_SUMMARY = os.path.join(DATA_DIR, "spell_summary.csv")
ITEM_SUMMARY  = os.path.join(DATA_DIR, "item_summary.csv")

# -----------------------------
# Loaders
# -----------------------------
@st.cache_data
def load_master():
    for name in MASTER_CANDIDATES:
        path = os.path.join(DATA_DIR, name)
        if os.path.exists(path):
            df = pd.read_csv(path)
            df["champion"] = df["champion"].astype(str)
            return df, name
    raise FileNotFoundError("champion_master(_plus).csv 가 필요합니다.")

@st.cache_data
def load_optional(path):
    if os.path.exists(path):
        try:
            return pd.read_csv(path)
        except:
            return None
    return None

master, master_file = load_master()
spell_summary = load_optional(SPELL_SUMMARY)    # spell_combo, games, wins, winrate
item_summary  = load_optional(ITEM_SUMMARY)     # item, games, wins, winrate

# 유틸
def exists_cols(df, cols):
    return df is not None and all(c in df.columns for c in cols)

# -----------------------------
# Sidebar / Filters
# -----------------------------
st.sidebar.title("⚙️ 필터")
champions = sorted(master["champion"].unique())
search = st.sidebar.text_input("챔피언 검색", "")
if search.strip():
    champions = [c for c in champions if search.lower() in c.lower()]
champ = st.sidebar.selectbox("챔피언", champions, index=0 if champions else None)

if not champ:
    st.stop()

# 현재 선택행
row = master[master["champion"] == champ].iloc[0]

# -----------------------------
# Header
# -----------------------------
st.title(f"칼바람 — {champ} 대시보드")
st.caption(f"데이터 소스: {master_file}")

# 상단 KPI
kpi_cols = st.columns(6)
kpi_cols[0].metric("승률", f"{row.get('winrate', np.nan):.2f}%")
kpi_cols[1].metric("픽률", f"{row.get('pickrate', np.nan):.2f}%")
kpi_cols[2].metric("게임수", f"{int(row.get('games', 0)):,}")
kpi_cols[3].metric("KDA", f"{row.get('kda', np.nan):.2f}")
kpi_cols[4].metric("분당 딜량(DPM)", f"{row.get('avg_dpm', np.nan):.0f}")
kpi_cols[5].metric("분당 골드(GPM)", f"{row.get('avg_gpm', np.nan):.0f}")

if "delta_winrate" in row and not pd.isna(row["delta_winrate"]):
    st.info(f"📈 최근 메타 변화(최근 vs 과거): **{row['delta_winrate']:+.2f}%p**")

st.divider()

# -----------------------------
# 좌측: 추천 빌드 / 룬 / 스펠   |   우측: 페이즈별 DPM 그래프
# -----------------------------
left, right = st.columns([1.1, 1])

with left:
    st.subheader("추천 룬 · 스펠 · 아이템")
    st.markdown(f"**추천 룬**: {row.get('best_rune', '—')}")
    st.markdown(f"**추천 스펠**: {row.get('best_spell_combo', row.get('best_spells','—'))}")
    st.markdown(f"**시작 아이템**: {row.get('best_start', '—')}")
    st.markdown(f"**2티어 신발**: {row.get('best_boots', '—')}")
    st.markdown(f"**코어 3코어**: {row.get('best_core3', '—')}")

    syn = row.get("synergy_top1", "")
    synwr = row.get("synergy_wr", np.nan)
    if isinstance(syn, str) and syn.strip():
        st.markdown(f"**같이하면 좋은 챔피언**: {syn} — {synwr:.2f}%")

    hard = row.get("enemy_hard_top1", "")
    hardwr = row.get("enemy_wr", np.nan)
    if isinstance(hard, str) and hard.strip():
        st.markdown(f"**상대하기 어려운 챔피언**: {hard} — {hardwr:.2f}%")

with right:
    st.subheader("페이즈별 DPM")
    have_phase = any(col in master.columns for col in ["dpm_early","dpm_mid","dpm_late"])
    if have_phase:
        plot_df = pd.DataFrame({
            "phase":["0–8분(Early)","8–16분(Mid)","16+분(Late)"],
            "dpm":[row.get("dpm_early", np.nan),
                   row.get("dpm_mid", np.nan),
                   row.get("dpm_late", np.nan)]
        })
        fig = px.bar(plot_df, x="phase", y="dpm", text="dpm", height=300)
        fig.update_traces(texttemplate="%{text:.0f}", textposition="outside")
        fig.update_layout(yaxis_title=None, xaxis_title=None, margin=dict(t=20,b=0,l=0,r=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("페이즈별 DPM 데이터가 없습니다(선택).")

st.divider()

# -----------------------------
# 기본 스탯
# -----------------------------
st.subheader("챔피언 기본 스탯")
base_cols = [
    ("체력", "hp"), ("레벨당 체력", "hpperlevel"),
    ("마나", "mp"), ("레벨당 마나", "mpperlevel"),
    ("방어력", "armor"), ("레벨당 방어력", "armorperlevel"),
    ("마법저항", "spellblock"), ("레벨당 마저", "spellblockperlevel"),
    ("공격력", "attackdamage"), ("레벨당 공력", "attackdamageperlevel"),
    ("공속", "attackspeed"), ("레벨당 공속", "attackspeedperlevel"),
    ("이동속도", "movespeed"), ("사거리", "attackrange")
]
cols = st.columns(5)
i = 0
for label, key in base_cols:
    if key in master.columns and not pd.isna(row.get(key, np.nan)):
        cols[i%5].metric(label, f"{row[key]:.2f}")
        i += 1

st.divider()

# -----------------------------
# (선택) 전체 스펠/아이템 통계 테이블
# -----------------------------
c1,c2 = st.columns(2)
with c1:
    st.subheader("스펠 조합 통계(전체 샘플)")
    if exists_cols(spell_summary, ["spell_combo","games","wins","winrate"]):
        show = spell_summary.sort_values(["games","winrate"], ascending=[False, False]).head(10)
        show["winrate"] = show["winrate"].map(lambda x: f"{x:.2f}%")
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.caption("스펠 통계 파일(spell_summary.csv)이 없습니다.")

with c2:
    st.subheader("아이템 성과 통계(전체 샘플)")
    if exists_cols(item_summary, ["item","games","wins","winrate"]):
        show = item_summary.sort_values(["games","winrate"], ascending=[False, False]).head(10)
        show["winrate"] = show["winrate"].map(lambda x: f"{x:.2f}%")
        st.dataframe(show, use_container_width=True, hide_index=True)
    else:
        st.caption("아이템 통계 파일(item_summary.csv)이 없습니다.")

# -----------------------------
# 푸터
# -----------------------------
st.caption("© ARAM 분석 대시보드 — 샘플 데이터 기반. 파일만 바꿔 끼우면 최신 데이터로 자동 반영됩니다.")
