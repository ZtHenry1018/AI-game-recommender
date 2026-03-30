import streamlit as st
import requests

# 🔗 你的后端地址（换成你的）
API_URL = "https://ai-game-recommender-production.up.railway.app"

st.title("🎮 AI游戏推荐器")

# ===== 推荐功能 =====
st.header("🔍 游戏推荐")

user_input = st.text_input("请输入你的游戏需求：")

if st.button("推荐游戏"):

    response = requests.post(
        f"{API_URL}/recommend",
        json={"query": user_input}
    )

    if response.status_code == 200:
        data = response.json()

        for g in data["results"]:
            st.subheader(g["name"])
            st.write(f"评分：{g['score']}")
            st.write(f"理由：{g['reason']}")
            st.write("---")
    else:
        st.error("推荐失败")


# ===== 添加游戏 =====
st.header("➕ 添加游戏")

new_game = st.text_input("输入游戏名称")

if st.button("添加游戏"):

    response = requests.post(
        f"{API_URL}/add_game",
        json={"name": new_game}
    )

    if response.status_code == 200:
        st.success("添加成功！")
        st.json(response.json())
    else:
        st.error("添加失败")