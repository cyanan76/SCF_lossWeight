import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# 1. 網頁基本配置與外觀隱藏
st.set_page_config(page_title="每日運動與健康紀錄", page_icon="💪", layout="centered")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# 2. 初始化狀態管理 (Session State)
# role 可以是 None (未登入), "user" (一般用戶), "admin" (管理員)
if "role" not in st.session_state:
    st.session_state["role"] = None

# 從系統 secrets 取得密碼，若未讀取到則預設為 I071128trade
if "current_admin_password" not in st.session_state:
    st.session_state["current_admin_password"] = st.secrets.get("admin_password", "I071128trade")

# 3. 建立強制登入的彈窗 (Dialog)
@st.dialog("🔒 系統登入", width="small")
def login_modal():
    st.write("請輸入您的帳號密碼以進入系統")
    username = st.text_input("帳號 (使用者名稱)")
    password = st.text_input("密碼", type="password")
    
    if st.button("確認登入", use_container_width=True):
        if username == "" or password == "":
            st.error("帳號與密碼不能為空白！")
        elif username == "admin" and password == st.session_state["current_admin_password"]:
            # 帳號為 admin 且密碼正確 ➔ 給予管理員權限
            st.session_state["role"] = "admin"
            st.rerun()
        else:
            # 任何非 admin 的輸入 ➔ 皆給予一般用戶權限
            st.session_state["role"] = "user"
            st.rerun()

# 4. 閘門邏輯：如果尚未登入，就呼叫彈窗並停止渲染後面的畫面
if st.session_state["role"] is None:
    login_modal()
    st.stop() 

# ==========================================
# 以下為登入後才會顯示的主程式區塊
# ==========================================

# 建立 Google Sheets 資料庫連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 側邊欄：顯示當前身分與登出按鈕
with st.sidebar:
    st.success(f"🟢 當前身分：{'管理員' if st.session_state['role'] == 'admin' else '一般用戶'}")
    if st.button("登出系統"):
        st.session_state["role"] = None
        st.rerun()

# 5. 根據身分分流畫面
if st.session_state["role"] == "admin":
    # ------------------ 管理員專屬後台 ------------------
    st.title("📊 健康紀錄管理後台")
    
    # 密碼修改區塊
    with st.expander("⚙️ 管理員設定 (暫時修改密碼)"):
        st.write("注意：此處修改僅為暫時生效 (重啟網頁會恢復)，永久修改請至 Streamlit Secrets。")
        new_password = st.text_input("輸入新密碼", type="password")
        if st.button("更新密碼"):
            if new_password:
                st.session_state["current_admin_password"] = new_password
                st.success("密碼已暫時更新！")
            else:
                st.error("新密碼不能為空。")
                
    st.divider()
    
    try:
        # 讀取試算表資料
        df = conn.read(ttl="0d")
        if df.empty:
            st.info("目前雲端資料庫中尚無任何紀錄。")
        else:
            st.subheader("📋 歷史全數據流")
            st.dataframe(df, use_container_width=True)
            
            # 繪製體重趨勢圖
            if "日期" in df.columns and "今日體重 (kg)" in df.columns:
                st.subheader("📈 體重變化趨勢動態圖")
                df_sorted = df.sort_values(by="日期")
                st.line_chart(data=df_sorted, x="日期", y="今日體重 (kg)")
    except Exception as e:
        st.error(f"從雲端資料庫讀取數據時失敗：{e}")

elif st.session_state["role"] == "user":
    # ------------------ 一般用戶填寫畫面 ------------------
    st.title("💪 每日運動與健康紀錄")
    st.write("請在下方輸入今日數據，完成後點擊送出按鈕。")
    
    st.header("📝 基本資料")
    record_date = st.date_input("選擇日期", date.today())
    weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=150.0, value=65.0, step=0.1)

    st.header("🏃‍♂️ 任務追蹤")
    st.write("有達成請打勾 ✅，未達成則保持空白 ❌")
    morning_ex = st.checkbox("早上運動")
    noon_fat_burn = st.checkbox("中午燃脂運動")
    night_run = st.checkbox("晚上跑步")
    meals_planned = st.checkbox("三餐照規劃")

    if st.button("送出今日紀錄"):
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
                
            # 更新回 Google Sheets
            conn.update(data=updated_df)
            st.success(f"🎉 紀錄已成功存入資料庫！({record_date})")
        except Exception as e:
            st.error(f"寫入失敗，請通知管理員檢查連線狀態。")
