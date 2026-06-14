import streamlit as st
import pandas as pd
from datetime import date

# 設定網頁標題
st.set_page_config(page_title="每日運動與健康紀錄", page_icon="💪")
st.title("每日運動與健康紀錄")

hide_streamlit_style = """
            <style>
            /* 隱藏右上角選單與頂部裝飾 */
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            
            /* 隱藏預設的 footer */
            footer {visibility: hidden;}
            
            /* 隱藏右下角的 Hosted with Streamlit 徽章 */
            .viewerBadge_container__1QSob {display: none !important;}
            .viewerBadge_link__1S137 {display: none !important;}
            a[href^="https://streamlit.io/cloud"] {display: none !important;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 日期與體重輸入
st.header("基本資料")
record_date = st.date_input("選擇日期", date.today())
weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=150.0, value=65.0, step=0.1)

# 運動與飲食打勾區塊
st.header("🏃‍♂️ 任務追蹤")
st.write("有達成請打勾 ✅，未達成則保持空白 ❌")

morning_ex = st.checkbox("早上運動")
noon_fat_burn = st.checkbox("中午燃脂運動")
night_run = st.checkbox("晚上跑步")
meals_planned = st.checkbox("三餐照規劃")

# 送出按鈕
if st.button("送出今日紀錄"):
    st.success(f"🎉 已成功送出 {record_date} 的紀錄！")
    
    # 顯示結果預覽
    st.write("### 📌 今日總結")
    st.write(f"**體重：** {weight} kg")
    st.write(f"**早上運動：** {'✅' if morning_ex else '❌'}")
    st.write(f"**中午燃脂：** {'✅' if noon_fat_burn else '❌'}")
    st.write(f"**晚上跑步：** {'✅' if night_run else '❌'}")
    st.write(f"**三餐規劃：** {'✅' if meals_planned else '❌'}")
