import streamlit as st
import pandas as pd
import plotly.express as px

# 제목
st.title("칼바람 챔피언 통계 대시보드")

# 데이터 불러오기
df = pd.read_csv("champion_summary.csv")

# 데이터 확인
st.subheader("챔피언별 성과 요약 (앞부분)")
st.write(df.head())

# 승률 Top10 챔피언 시각화
st.subheader("승률 Top 10 챔피언")
top10 = df.sort_values("winrate", ascending=False).head(10)

fig = px.bar(
    top10,
    x="champion",
    y="winrate",
    text="winrate",
    title="칼바람 승률 TOP 10"
)
st.plotly_chart(fig)

# 챔피언 선택해서 상세 확인
champ = st.selectbox("챔피언을 선택하세요", df["champion"].unique())
info = df[df["champion"] == champ].iloc[0]
st.write(f"**{champ}** - 경기 수: {info['games']}, 승률: {info['winrate']}%")
