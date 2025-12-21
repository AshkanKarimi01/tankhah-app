import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
LOG_FILE = "audit_log.csv"  # فایل ثبت لاگ ویرایش‌ها
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- سیستم لاگین ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.set_page_config(page_title="ورود", layout="centered")
    st.markdown("<h2 style='text-align: center;'>🔒 ورود به سیستم</h2>", unsafe_allow_html=True)
    user_input = st.text_input("نام کاربری")
    password_input = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        users = {"barijani": "1234", "talebi": "1234"}
        if user_input in users and users[user_input] == password_input:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = user_input
            st.rerun()
        else:
            st.error("❌ اشتباه است.")
    return False

if not check_password():
    st.stop()

# --- توابع داده ---
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر", "ثبت کننده"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def add_audit_log(invoice_id, action, details):
    """ثبت هرگونه تغییر در فایل جداگانه"""
    new_log = {
        "زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "کاربر": st.session_state['current_user'],
        "شماره فاکتور": invoice_id,
        "عملیات": action,
        "جزئیات": details
    }
    log_df = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=new_log.keys())
    log_df = pd.concat([log_df, pd.DataFrame([new_log])], ignore_index=True)
    log_df.to_csv(LOG_FILE, index=False)

# --- ظاهر برنامه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
with st.sidebar:
    st.write(f"👤 کاربر: **{st.session_state['current_user']}**")
    if st.button("خروج"):
        st.session_state["password_correct"] = False
        st.rerun()

st.title("💸 پنل جامع مدیریت تنخواه")
tab1, tab2, tab3, tab4 = st.tabs(["📝 ثبت", "📊 گزارش", "✏️ ویرایش", "📜 تاریخچه تغییرات"])

CATEGORIES = ["غذا", "اسنپ و آژانس", "پیک", "باربری", "پست و تیپاکس", "نوشت افزار", "کارمزد", "آبدارخانه و پذیرایی", "متفرقه"]

# --- تب ۱: ثبت ---
with tab1:
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        date_in = c1.text_input("تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        cat_in = c1.selectbox("دسته", CATEGORIES)
        amount_in = c2.number_input("مبلغ", min_value=0, step=1000)
        desc_in = c2.text_area("توضیحات")
        file_in = st.file_uploader("عکس", type=['jpg', 'png'])
        if st.form_submit_button("ثبت"):
            df = load_data()
            next_id = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
            path = "بدون تصویر"
            if file_in:
                path = os.path.join(UPLOAD_DIR, f"{next_id}_{file_in.name}")
                with open(path, "wb") as f: f.write(file_in.getbuffer())
            new_row = {"شماره فاکتور": next_id, "تاریخ": date_in, "دسته بندی": cat_in, "مبلغ": amount_in, "توضیحات": desc_in, "تصویر": path, "ثبت کننده": st.session_state['current_user']}
            save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("ثبت شد.")

# --- تب ۲: گزارش ---
with tab2:
    df = load_data()
    if not df.empty:
        st.dataframe(df.drop(columns=["تصویر"]), use_container_width=True, hide_index=True)
        sel_id = st.selectbox("نمایش عکس فاکتور:", df["شماره فاکتور"].tolist()[::-1])
        row = df[df["شماره فاکتور"] == sel_id].iloc[0]
        if row["تصویر"] != "بدون تصویر": st.image(row["تصویر"], width=400)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        st.download_button("📥 دانلود اکسل کل فاکتورها", output.getvalue(), "Report.xlsx")

# --- تب ۳: ویرایش ---
with tab3:
    df_edit = load_data()
    if not df_edit.empty:
        e_id = st.selectbox("شماره فاکتور برای ویرایش:", df_edit["شماره فاکتور"].tolist())
        idx = df_edit[df_edit["شماره فاکتور"] == e_id].index[0]
        old_val = df_edit.at[idx, "مبلغ"]
        with st.form("edit_form"):
            new_amt = st.number_input("اصلاح مبلغ", value=int(df_edit.at[idx, "مبلغ"]))
            new_desc = st.text_area("اصلاح توضیحات", value=df_edit.at[idx, "توضیحات"])
            if st.form_submit_button("اعمال تغییرات"):
                details = f"تغییر مبلغ از {old_val} به {new_amt}"
                add_audit_log(e_id, "ویرایش", details) # ثبت لاگ
                df_edit.at[idx, "مبلغ"] = new_amt
                df_edit.at[idx, "توضیحات"] = new_desc
                save_data(df_edit)
                st.success("تغییرات ثبت و لاگ شد.")
                st.rerun()

# --- تب ۴: لاگ ویرایش‌ها (جدید) ---
with tab4:
    st.subheader("📜 تاریخچه تغییرات و ویرایش‌ها")
    if os.path.exists(LOG_FILE):
        logs = pd.read_csv(LOG_FILE)
        st.table(logs.sort_values(by="زمان", ascending=False))
    else:
        st.info("هنوز هیچ ویرایشی انجام نشده است.")
