import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io
from streamlit_jalali_date_picker import date_picker

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv"
LOG_FILE = "audit_log.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- تابع تبدیل ریال به تومان و حروف ---
def format_money(amount):
    if amount == 0: return "صفر ریال"
    toman = amount // 10
    return f"{amount:,} ریال (معادل {toman:,} تومان)"

# --- سیستم لاگین ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True
    st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
    st.markdown("<h2 style='text-align: center;'>🔒 ورود به سیستم</h2>", unsafe_allow_html=True)
    u = st.text_input("نام کاربری")
    p = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        users = {"barjani": "1234", "talebi": "1234"}
        if u in users and users[u] == p:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            st.rerun()
        else: st.error("❌ نام کاربری یا رمز عبور اشتباه است.")
    return False

if not check_password(): st.stop()

# --- توابع داده ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        cols = ["واحد", "تاریخ پرداخت", "زمان ثبت سیستم"]
        for c in cols:
            if c not in df.columns: df[c] = "تعریف نشده"
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "تصویر", "ثبت کننده", "پرداخت کننده", "زمان ثبت سیستم"])

def load_income():
    if os.path.exists(INCOME_FILE): return pd.read_csv(INCOME_FILE)
    return pd.DataFrame(columns=["تاریخ", "مبلغ واریزی", "بابت", "ثبت کننده"])

def save_data(df, filename): df.to_csv(filename, index=False)

# --- محاسبات موجودی ---
df_exp = load_data()
df_inc = load_income()
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# --- ظاهر برنامه ---
st.title("💸 پنل جامع مدیریت تنخواه")
st.info(f"💰 **موجودی فعلی:** {format_money(balance)}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش", "💰 شارژ تنخواه", "🛠️ ویرایش و حذف", "📜 تاریخچه"])

CATEGORIES = ["غذا", "اسنپ و آژانس", "پیک", "باربری", "پست و تیپاکس", "نوشت افزار", "کارمزد", "آبدارخانه و پذیرایی", "متفرقه"]
UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]

# --- تب ۱: ثبت ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.write("📅 تاریخ فاکتور:")
            d_fact = date_picker(key='fact_date')
            st.write("📅 تاریخ پرداخت:")
            d_pay = date_picker(key='pay_date')
            unit_in = st.selectbox("واحد مربوطه", UNITS)
            cat_in = st.selectbox("دسته بندی", CATEGORIES)
        with c2:
            amt_in = st.number_input("مبلغ (ریال)", min_value=0, step=1000)
            st.caption(f"✍️ {format_money(amt_in)}")
            pay_in = st.text_input("پرداخت کننده")
            desc_in = st.text_area("توضیحات")
            file_in = st.file_uploader("عکس فاکتور", type=['jpg', 'png', 'jpeg'])

        if st.form_submit_button("ثبت نهایی"):
            if amt_in > 0:
                df = load_data()
                nid = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
                img_p = "بدون تصویر"
                if file_in:
                    img_p = os.path.join(UPLOAD_DIR, f"{nid}_{file_in.name}")
                    with open(img_p, "wb") as f: f.write(file_in.getbuffer())
                new_row = {"شماره فاکتور": nid, "تاریخ": d_fact, "تاریخ پرداخت": d_pay, "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in), "توضیحات": desc_in, "تصویر": img_p, "ثبت کننده": st.session_state['current_user'], "پرداخت کننده": pay_in, "زمان ثبت سیستم": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), DB_FILE)
                st.success(f"فاکتور {nid} ثبت شد."); st.rerun()

# --- تب ۲: گزارش ---
with tab2:
    if not df_exp.empty:
        st.subheader("🔍 فیلتر بر اساس تاریخ پرداخت")
        c1, c2 = st.columns(2)
        with c1: start_d = date_picker(key='start_rep')
        with c2: end_d = date_picker(key='end_rep')
        f_df = df_exp[(df_exp["تاریخ پرداخت"] >= start_d) & (df_exp["تاریخ پرداخت"] <= end_d)]
        
        disp_df = f_df.copy()
        disp_df["مبلغ"] = disp_df["مبلغ"].apply(lambda x: f"{int(x):,} ریال")
        st.dataframe(disp_df.drop(columns=["تصویر"]), use_container_width=True, hide_index=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            f_df.to_excel(writer, index=False)
        st.download_button(label="📥 دانلود اکسل این گزارش", data=output.getvalue(), file_name=f"Report_{d_pay}.xlsx")

# --- تب ۳: شارژ تنخواه ---
with tab3:
    with st.form("inc_form", clear_on_submit=True):
        i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0)
        st.caption(format_money(i_amt))
        i_note = st.text_input("بابت")
        if st.form_submit_button("ثبت واریزی"):
            df_i = load_income()
            new_i = {"تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "مبلغ واریزی": int(i_amt), "بابت": i_note, "ثبت کننده": st.session_state['current_user']}
            save_data(pd.concat([df_i, pd.DataFrame([new_i])], ignore_index=True), INCOME_FILE)
            st.success("حساب شارژ شد."); st.rerun()
    st.table(df_inc.sort_index(ascending=False))

# --- تب ۴: ویرایش و حذف ---
with tab4:
    df_m = load_data()
    if not df_m.empty:
        sel_id = st.selectbox("انتخاب فاکتور:", df_m["شماره فاکتور"].tolist()[::-1])
        idx = df_m[df_m["شماره فاکتور"] == sel_id].index[0]
        with st.form("e_form"):
            e_amt = st.number_input("مبلغ (ریال)", value=int(df_m.at[idx, "مبلغ"]))
            st.caption(format_money(e_amt))
            e_unit = st.selectbox("واحد", UNITS, index=UNITS.index(df_m.at[idx, "واحد"]) if df_m.at[idx, "واحد"] in UNITS else 0)
            e_desc = st.text_area("توضیحات", value=str(df_m.at[idx, "توضیحات"]))
            if st.form_submit_button("ذخیره تغییرات"):
                df_m.at[idx, "مبلغ"], df_m.at[idx, "واحد"], df_m.at[idx, "توضیحات"] = e_amt, e_unit, e_desc
                save_data(df_m, DB_FILE)
                st.success("ویرایش شد."); st.rerun()
        if st.button("❌ حذف این فاکتور"):
            df_m = df_m.drop(idx)
            save_data(df_m, DB_FILE)
            st.error("حذف شد."); st.rerun()

# --- تب ۵: تاریخچه ---
with tab5:
    if os.path.exists(LOG_FILE):
        st.table(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False))
