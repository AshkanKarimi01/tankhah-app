import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات دیتابیس ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv"
LOG_FILE = "audit_log.csv"

# --- تابع تبدیل عدد به حروف ---
def format_money(amount):
    try:
        val = int(amount)
        if val == 0: return "صفر ریال"
        toman = val // 10
        return f"{val:,} ریال (معادل {toman:,} تومان)"
    except: return "۰ ریال"

# --- تابع ثبت لاگ ---
def add_log(action, user):
    df_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["زمان", "کاربر", "عملیات"])
    new_log = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": user, "عملیات": action}
    pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True).to_csv(LOG_FILE, index=False)

# --- ورودی تاریخ شمسی ---
def shamsi_date_input(label_prefix, key_id, default_date=None):
    st.write(f"📅 {label_prefix}")
    if default_date and "/" in str(default_date):
        parts = str(default_date).split("/")
        d_y, d_m, d_d = int(parts[0]), int(parts[1]), int(parts[2])
    else:
        today = jdatetime.date.today()
        d_y, d_m, d_d = today.year, today.month, today.day
    
    c1, c2, c3 = st.columns(3)
    y = c1.selectbox("سال", [1404, 1403, 1402], index=[1404, 1403, 1402].index(d_y) if d_y in [1404, 1403, 1402] else 1, key=f"y_{key_id}")
    m = c2.selectbox("ماه", list(range(1, 13)), index=d_m - 1, key=f"m_{key_id}")
    d = c3.selectbox("روز", list(range(1, 32)), index=min(d_d - 1, 30), key=f"d_{key_id}")
    return f"{y}/{m:02d}/{d:02d}"

# --- سیستم ورود (Login) ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.set_page_config(page_title="ورود به سیستم", layout="centered")
    st.subheader("🔐 ورود به مدیریت تنخواه")
    user_input = st.text_input("نام کاربری")
    pass_input = st.text_input("رمز عبور", type="password")
    
    users = {
        "admin": "admin123@",
        "barjani": "1234",
        "talebi": "1234"
    }
    
    if st.button("ورود"):
        if user_input in users and users[user_input] == pass_input:
            st.session_state["logged_in"] = True
            st.session_state["user"] = user_input
            st.rerun()
        else:
            st.error("نام کاربری یا رمز عبور اشتباه است!")
    st.stop()

# --- بارگذاری داده‌ها (بعد از لاگین) ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        cols = ["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"]
        for c in cols:
            if c not in df.columns: df[c] = "ثبت نشده" if "تاریخ" in c else 0
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])

st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
df_exp = load_data()
df_inc = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# هدر برنامه
c_h1, c_h2 = st.columns([4, 1])
with c_h1: st.title("💸 پنل جامع مدیریت تنخواه")
with c_h2: 
    if st.button("خروج"): 
        st.session_state["logged_in"] = False
        st.rerun()

st.info(f"💰 موجودی فعلی: {format_money(balance)} | 👤 کاربر: {st.session_state['user']}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش", "💰 شارژ", "🛠️ ویرایش و حذف", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. ثبت فاکتور
with tab1:
    col_l, col_r = st.columns(2)
    with col_l:
        d_f = shamsi_date_input("تاریخ فاکتور", "new_f")
        d_p = shamsi_date_input("تاریخ پرداخت", "new_p")
        u_in = st.selectbox("واحد", UNITS)
    with col_r:
        a_in = st.number_input("مبلغ (ریال)", min_value=0, step=1000, key="amt_reg")
        st.markdown(f"👈 **{format_money(a_in)}**")
        c_in = st.selectbox("دسته بندی", CATEGORIES)
        p_in = st.text_input("پرداخت کننده")
    desc_in = st.text_area("توضیحات")
    if st.button("🚀 ثبت نهایی"):
        nid = 1 if df_exp.empty else int(df_exp["شماره فاکتور"].max()) + 1
        new_row = {"شماره فاکتور": nid, "تاریخ": d_f, "تاریخ پرداخت": d_p, "دسته بندی": c_in, "واحد": u_in, "مبلغ": int(a_in), "توضیحات": desc_in, "ثبت کننده": st.session_state['user'], "پرداخت کننده": p_in}
        pd.concat([df_exp, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
        add_log(f"ثبت فاکتور {nid}", st.session_state['user'])
        st.success("ثبت شد!"); st.rerun()

# ۲. گزارش
with tab2:
    c1, c2 = st.columns(2)
    with c1: start_d = shamsi_date_input("از تاریخ", "rep_s")
    with c2: end_d = shamsi_date_input("تا تاریخ", "rep_e")
    f_df = df_exp[(df_exp["تاریخ پرداخت"] >= start_d) & (df_exp["تاریخ پرداخت"] <= end_d)]
    st.dataframe(f_df, use_container_width=True)
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine='xlsxwriter') as wr: f_df.to_excel(wr, index=False)
    st.download_button("📥 دانلود اکسل", out.getvalue(), "Report.xlsx")

# ۳. شارژ و تاریخچه
with tab3:
    i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0, key="inc_f")
    st.info(format_money(i_amt))
    i_desc = st.text_input("بابت")
    if st.button("ثبت شارژ"):
        new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
        pd.concat([df_inc, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
        add_log(f"شارژ حساب {i_amt}", st.session_state['user'])
        st.rerun()
    st.write("---")
    st.subheader("📜 تاریخچه شارژ")
    st.dataframe(df_inc.sort_index(ascending=False), use_container_width=True)

# ۴. ویرایش و حذف
with tab4:
    if not df_exp.empty:
        e_id = st.selectbox("فاکتور:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره فاکتور"] == e_id].index[0]
        with st.expander("فرم اصلاح", expanded=True):
            ca, cb = st.columns(2)
            with ca:
                v_f = shamsi_date_input("تاریخ فاکتور", "ed_f", df_exp.at[idx, "تاریخ"])
                v_p = shamsi_date_input("تاریخ پرداخت", "ed_p", df_exp.at[idx, "تاریخ پرداخت"])
            with cb:
                v_a = st.number_input("مبلغ", value=int(df_exp.at[idx, "مبلغ"]), key="ed_a")
                st.warning(format_money(v_a))
                v_pay = st.text_input("پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
            v_desc = st.text_area("توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
            
            b1, b2 = st.columns(2)
            if b1.button("💾 ذخیره تغییرات"):
                df_exp.at[idx, "تاریخ"], df_exp.at[idx, "تاریخ پرداخت"], df_exp.at[idx, "مبلغ"] = v_f, v_p, int(v_a)
                df_exp.at[idx, "توضیحات"], df_exp.at[idx, "پرداخت کننده"] = v_desc, v_pay
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"ویرایش فاکتور {e_id}", st.session_state['user'])
                st.success("ذخیره شد"); st.rerun()
            if b2.button("🗑️ حذف این فاکتور"):
                df_exp.drop(idx).to_csv(DB_FILE, index=False)
                add_log(f"حذف فاکتور {e_id}", st.session_state['user'])
                st.rerun()

# ۵. لاگ
with tab5:
    if os.path.exists(LOG_FILE): st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False))
