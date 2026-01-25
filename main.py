import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv" # فایل جدید برای ورودی‌ها
LOG_FILE = "audit_log.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- سیستم لاگین ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.set_page_config(page_title="ورود به سیستم", layout="centered")
    st.markdown("<h2 style='text-align: center;'>🔒 ورود به سیستم مدیریت تنخواه</h2>", unsafe_allow_html=True)
    u_in = st.text_input("نام کاربری")
    p_in = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        users = {"barijani": "1234", "talebi": "1234"}
        if u_in in users and users[u_in] == p_in:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u_in
            st.rerun()
        else:
            st.error("❌ نام کاربری یا رمز عبور اشتباه است.")
    return False

if not check_password():
    st.stop()

# --- توابع داده ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        for col in ["پرداخت کننده", "زمان ثبت سیستم"]:
            if col not in df.columns: df[col] = "نامشخص"
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر", "ثبت کننده", "پرداخت کننده", "زمان ثبت سیستم"])

def load_income():
    if os.path.exists(INCOME_FILE):
        return pd.read_csv(INCOME_FILE)
    return pd.DataFrame(columns=["تاریخ", "مبلغ واریزی", "بابت", "ثبت کننده"])

def save_data(df, filename):
    df.to_csv(filename, index=False)

def add_audit_log(invoice_id, action, details):
    log_entry = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": st.session_state['current_user'], "شماره فاکتور": invoice_id, "عملیات": action, "جزئیات": details}
    ldf = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=log_entry.keys())
    ldf = pd.concat([ldf, pd.DataFrame([log_entry])], ignore_index=True)
    ldf.to_csv(LOG_FILE, index=False)

# --- محاسبه موجودی ---
df_exp = load_data()
df_inc = load_income()
total_expenses = df_exp["مبلغ"].sum()
total_income = df_inc["مبلغ واریزی"].sum()
current_balance = total_income - total_expenses

# --- ظاهر برنامه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
st.title("💸 پنل جامع مدیریت تنخواه")

# نمایش موجودی در بالای صفحه
col_b1, col_b2, col_b3 = st.columns(3)
col_b1.metric("📥 کل واریزی‌ها", f"{total_income:,} تومان")
col_b2.metric("📤 کل مخارج", f"{total_expenses:,} تومان", delta=f"-{total_expenses:,}", delta_color="inverse")
col_b3.metric("💰 موجودی فعلی تنخواه", f"{current_balance:,} تومان")

st.divider()

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و خروجی", "💰 شارژ تنخواه", "✏️ ویرایش و حذف", "📜 تاریخچه"])

# --- تب ۱: ثبت فاکتور (بدون تغییر) ---
with tab1:
    with st.form("f1", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_in = c1.text_input("تاریخ فاکتور (شمسی)", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        cat_in = c1.selectbox("دسته بندی", ["غذا", "اسنپ و آژانس", "پیک", "باربری", "پست و تیپاکس", "نوشت افزار", "کارمزد", "آبدارخانه و پذیرایی", "متفرقه"])
        pay_in = c1.text_input("پرداخت کننده (نام شخص یا منبع)")
        amt_in = c2.number_input("مبلغ (تومان)", min_value=0, step=1000)
        desc_in = c2.text_area("توضیحات")
        file_in = st.file_uploader("عکس فاکتور", type=['jpg', 'png', 'jpeg'])
        if st.form_submit_button("ثبت نهایی"):
            if amt_in > 0 and pay_in.strip() != "":
                df = load_data()
                next_id = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
                img_p = "بدون تصویر"
                if file_in:
                    img_p = os.path.join(UPLOAD_DIR, f"{next_id}_{file_in.name}")
                    with open(img_p, "wb") as f: f.write(file_in.getbuffer())
                new_row = {"شماره فاکتور": next_id, "تاریخ": d_in, "دسته بندی": cat_in, "مبلغ": int(amt_in), "توضیحات": desc_in, "تصویر": img_p, "ثبت کننده": st.session_state['current_user'], "پرداخت کننده": pay_in, "زمان ثبت سیستم": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), DB_FILE)
                st.success(f"✅ فاکتور شماره {next_id} ثبت شد.")
                st.rerun()

# --- تب ۲: گزارش (بدون تغییر) ---
with tab2:
    if not df_exp.empty:
        st.subheader("🔍 فیلتر گزارش مخارج")
        f_col1, f_col2 = st.columns(2)
        start_date = f_col1.text_input("از تاریخ:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        end_date = f_col2.text_input("تا تاریخ:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        mask = (df_exp["تاریخ"] >= start_date) & (df_exp["تاریخ"] <= end_date)
        filtered_df = df_exp.loc[mask]
        st.dataframe(filtered_df.drop(columns=["تصویر", "زمان ثبت سیستم"]), use_container_width=True, hide_index=True)
        # دکمه اکسل
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer: filtered_df.to_excel(writer, index=False)
        st.download_button("📥 دانلود اکسل مخارج فیلتر شده", output.getvalue(), "Expenses.xlsx")

# --- تب ۳: شارژ تنخواه (جدید) ---
with tab3:
    st.subheader("➕ ثبت ورودی جدید به تنخواه")
    with st.form("income_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        inc_date = c1.text_input("تاریخ واریز", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        inc_amount = c2.number_input("مبلغ واریزی (تومان)", min_value=0, step=10000)
        inc_note = st.text_input("بابت (مثلاً: شارژ تنخواه دی ماه)")
        if st.form_submit_button("ثبت واریزی"):
            if inc_amount > 0:
                df_i = load_income()
                new_inc = {"تاریخ": inc_date, "مبلغ واریزی": int(inc_amount), "بابت": inc_note, "ثبت کننده": st.session_state['current_user']}
                save_data(pd.concat([df_i, pd.DataFrame([new_inc])], ignore_index=True), INCOME_FILE)
                st.success("✅ حساب تنخواه شارژ شد.")
                st.rerun()
    
    st.divider()
    st.subheader("📜 لیست واریزی‌های اخیر")
    st.table(df_inc.sort_index(ascending=False))

# --- تب ۴ و ۵: ویرایش و تاریخچه (مشابه قبل) ---
with tab4:
    if not df_exp.empty:
        mid = st.selectbox("انتخاب فاکتور برای تغییر:", df_exp["شماره فاکتور"].tolist())
        # ... کدهای ویرایش مشابه قبل ...
        if st.button("❌ حذف قطعی"):
            # کد حذف مشابه قبل
            st.rerun()

with tab5:
    if os.path.exists(LOG_FILE):
        st.table(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False))
