import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. 網頁基本配置與外觀隱藏
st.set_page_config(page_title="爽超肥每日紀錄", page_icon="🐷", layout="centered")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# 2. 建立 Google Sheets 資料庫連線
# 這裡使用 Streamlit 官方封裝的連線工具
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 初始化登入狀態 (Session State)
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# 4. 側邊欄：管理員登入系統
with st.sidebar:
    st.header("🔑 管理員系統")
    if not st.session_state["admin_logged_in"]:
        password = st.text_input("請輸入管理員密碼", type="password")
        if st.button("登入後台"):
            # 優先從雲端 Secrets 讀取密碼，若沒設定則預設為 'admin123'
            secure_password = st.secrets.get("admin_password", "admin123")
            if password == secure_password:
                st.session_state["admin_logged_in"] = True
                st.success("管理員認證成功！")
                st.rerun()
            else:
                st.error("密碼錯誤，請再試一次。")
    else:
        st.write("🟢 目前權限：系統管理員")
        if st.button("登出後台"):
            st.session_state["admin_logged_in"] = False
            st.success("已安全登出")
            st.rerun()

# 5. 主頁面邏輯分流：根據登入狀態決定顯示填寫表單還是後台數據
if st.session_state["admin_logged_in"]:
    # ==================== 管理員後台數據顯示 ====================
    st.title("📊 健康紀錄管理後台")
    st.write("此區域僅限管理員查看，一般用戶無法存取。")
    
    try:
        # ttl="0d" 代表快取時間為 0，每次重新整理都會強迫抓取雲端最新資料
        df = conn.read(ttl="0d")
        
        if df.empty:
            st.info("目前雲端資料庫中尚無任何紀錄。")
        else:
            st.subheader("📋 歷史全數據流")
            st.dataframe(df, use_container_width=True)
            
            # 自動生成體重趨勢圖
            if "日期" in df.columns and "今日體重 (kg)" in df.columns:
                st.subheader("📈 體重變化趨勢動態圖")
                df_sorted = df.sort_values(by="日期")
                st.line_chart(data=df_sorted, x="日期", y="今日體重 (kg)")
    except Exception as e:
        st.error(f"從雲端資料庫讀取數據時失敗：{e}")
        st.info("請檢查 Streamlit Secrets 中的雲端試算表網址與權限設定。")

else:
    # ==================== 一般用戶數據輸入表單 ====================
    st.title("每日運動與健康紀錄")
    st.write("請在下方輸入今日數據，完成後點擊送出按鈕存入後台。")
    
    st.header("基本資料")
    record_date = st.date_input("選擇日期", date.today())
    weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=150.0, value=65.0, step=0.1)

    st.header("🏃‍♂️ 任務追蹤")
    st.write("有達成請打勾 ✅，未達成則保持空白 ❌")
    morning_ex = st.checkbox("早上運動")
    noon_fat_burn = st.checkbox("中午燃脂運動")
    night_run = st.checkbox("晚上跑步")
    meals_planned = st.checkbox("三餐照規劃")

    if st.button("送出今日紀錄"):
        # 整理新輸入的數據行
        new_row = pd.DataFrame([{
            "日期": str(record_date),
            "今日體重 (kg)": float(weight),
            "早上運動": "✅" if morning_ex else "❌",
            "中午燃脂運動": "✅" if noon_fat_burn else "❌",
            "晚上跑步": "✅" if night_run else "❌",
            "三餐照規劃": "✅" if meals_planned else "❌"
        }])
        
        try:
            # 讀取現有雲端數據並與新數據合併
            try:
                existing_df = conn.read(ttl="0d")
                updated_df = pd.concat([existing_df, new_row], ignore_index=True)
            except:
                updated_df = new_row
                
            # 將合併後的完整表格推回 Google Sheets
            conn.update(data=updated_df)
            st.success(f"🎉 紀錄已成功自動寫入雲端數據庫！({record_date})")
        except Exception as e:
            st.error(f"寫入雲端失敗，請確認資料庫設定。錯誤代碼：{e}")
