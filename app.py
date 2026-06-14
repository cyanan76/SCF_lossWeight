import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# ==========================================
# 1. 網頁基本配置與外觀隱藏
# ==========================================
st.set_page_config(page_title="爽超肥每日紀錄", page_icon="🐷", layout="centered")

hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 2. 初始化狀態管理 (Session State)
# ==========================================
if "role" not in st.session_state:
    st.session_state["role"] = None

# 從系統 secrets 取得密碼，若未讀取到則預設為 I071128trade
if "current_admin_password" not in st.session_state:
    st.session_state["current_admin_password"] = st.secrets.get("admin_password", "I071128trade")

# 用來控制「登入成功」訊息只顯示一次的開關
if "show_login_msg" not in st.session_state:
    st.session_state["show_login_msg"] = False

# ==========================================
# 3. 登入彈窗與驗證邏輯
# ==========================================
@st.dialog("系統登入", width="small")
def login_modal():
    st.write("請輸入您的帳號密碼以進入系統")
    username = st.text_input("帳號")
    password = st.text_input("密碼", type="password")
    
    if st.button("確認登入", use_container_width=True):
        if username == "" or password == "":
            st.error("帳號與密碼不能為空白！")
        # 判斷是否為管理員：帳號必須是 adw，密碼必須吻合
        elif username == "adw" and password == st.session_state["current_admin_password"]:
            st.session_state["role"] = "admin"
            st.session_state["show_login_msg"] = True
            st.rerun()
        # 除此之外的任何輸入，皆為一般使用者
        else:
            st.session_state["role"] = "user"
            st.session_state["show_login_msg"] = True
            st.rerun()

# 閘門邏輯：如果尚未登入，呼叫彈窗並停止渲染後面的畫面
if st.session_state["role"] is None:
    login_modal()
    st.stop() 

# 顯示登入成功訊息 (顯示後立刻關閉開關，避免重複跳出)
if st.session_state["show_login_msg"]:
    role_name = "系統管理員" if st.session_state["role"] == "admin" else "一般使用者"
    st.toast(f"🎉 登入成功！歡迎進入系統 ({role_name})", icon="✅")
    st.session_state["show_login_msg"] = False

# ==========================================
# 以下為登入後的主程式區塊
# ==========================================

# 建立 Google Sheets 資料庫連線
conn = st.connection("gsheets", type=GSheetsConnection)

# 側邊欄：顯示當前身分與登出按鈕
with st.sidebar:
    st.success(f"🟢 當前權限：{'管理員 (Admin)' if st.session_state['role'] == 'admin' else '肥宅 (User)'}")
    if st.button("登出系統"):
        st.session_state["role"] = None
        st.rerun()

# ==========================================
# 管理員介面 (數據分析與修改)
# ==========================================
if st.session_state["role"] == "admin":
    st.title("📊 健康紀錄管理後台")
    
    # 密碼修改區塊
    with st.expander("⚙️ 管理員設定 (修改密碼)"):
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
            # --- 數據修改區塊 ---
            st.subheader("📝 歷史數據管理")
            st.write("💡 你可以直接在下方表格內雙擊修改數據，或是勾選最左側來刪除整列。完成後請點擊下方按鈕存檔。")
            
            # 使用 data_editor 讓表格變成可編輯狀態
            edited_df = st.data_editor(
                df, 
                num_rows="dynamic", # 允許新增與刪除行
                use_container_width=True
            )
            
            if st.button("💾 儲存修改至資料庫", type="primary"):
                conn.update(data=edited_df)
                st.success("✅ 資料庫已成功同步更新！")
                st.rerun()
            
            st.divider()
            
            # --- 數據分析區塊 ---
            st.subheader("📈 數據分析儀表板")
            if "日期" in df.columns and "今日體重 (kg)" in df.columns:
                # 計算簡易數據
                total_records = len(df)
                latest_weight = df["今日體重 (kg)"].iloc[-1] if total_records > 0 else 0
                first_weight = df["今日體重 (kg)"].iloc[0] if total_records > 0 else 0
                weight_diff = round(latest_weight - first_weight, 1)
                
                # 顯示重點指標
                col1, col2, col3 = st.columns(3)
                col1.metric("總紀錄天數", f"{total_records} 天")
                col2.metric("最新體重", f"{latest_weight} kg")
                col3.metric("累積體重變化", f"{weight_diff} kg", delta=weight_diff, delta_color="inverse")
                
                # 繪製體重趨勢圖
                st.line_chart(data=df, x="日期", y="今日體重 (kg)")

    except Exception as e:
        st.error(f"從雲端資料庫讀取數據時失敗：{e}")

# ==========================================
# 一般使用者介面 (資料輸入)
# ==========================================
elif st.session_state["role"] == "user":
    st.title("每日紀錄")
    st.write("請在下方輸入今日數據，完成後點擊送出按鈕。")
    
    st.header("基本資料")
    record_date = st.date_input("選擇日期", date.today())
    weight = st.number_input("今日體重 (kg)", min_value=30.0, max_value=150.0, value=65.0, step=0.1)

    st.header("我腿好痠肚子好痛任務追蹤")
    st.write("有達成請打勾 ✅，未達成則保持空白 ❌")
    morning_ex = st.checkbox("早上運動")
    noon_fat_burn = st.checkbox("中午燃脂運動")
    night_run = st.checkbox("晚上跑步")
    meals_planned = st.checkbox("三餐照規劃")

    if st.button("送出今日紀錄", type="primary"):
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
            st.error(f"寫入失敗，請通知管理員檢查連線狀態。錯誤資訊：{e}")
