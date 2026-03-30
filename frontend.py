import streamlit as st
import requests

st.title("🎮 AI游戏推荐助手")

user_input = st.text_input("请输入你的游戏需求")

if st.button("推荐"):

    response = requests.post(
        "http://127.0.0.1:8000/recommend",
        json={"user_input": user_input}
    )

    data = response.json()

    if data["status"] == "invalid":
        st.error(data["reason"])

    elif data["status"] == "no_result":
        st.warning("没有匹配游戏")

    elif data["status"] == "success":

        st.success("推荐结果：")

        for g in data["games"]:
            st.markdown(f"### 🎮 {g['name']}")
            st.write(f"评分：{g['score']}")
            st.write(f"理由：{g['reason']}")
            st.divider()

st.title("➕ 添加游戏")

new_game = st.text_input("输入游戏名")

if st.button("添加到库"):

    response = requests.post(
        "http://127.0.0.1:8000/add_game",
        json={"name": new_game}
    )

    data = response.json()

    if data["status"] == "success":
        st.success(f"已添加：{data['game']['name']}")