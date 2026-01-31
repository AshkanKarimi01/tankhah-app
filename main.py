import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv"
LOG_FILE = "audit_log.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR): os.makedirs(UPLOAD_DIR)

# --- توابع کمکی ---
def format_money(amount):
    try:
        val = int(amount)
        if val == 0: return "صفر ریال"
        toman = val // 10
        return f"{val:,} ریال (معادل {toman:,} تومان)"
    except: return "۰ ریال"

def add_log(action, user):
    df_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["زمان", "کاربر", "عملیات"])
    new_log = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": user, "عملیات": action}
    pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True).to_csv(LOG_FILE, index=False)

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

# --- سیستم ورود ---
if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
if not st.session_state["password_correct"]:
    st.set_page_config(page_title="ورود", layout="centered")
    u = st.text_input("نام کاربری")
    p = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        if u == "barjani" and p == "1234":
            st.session_state["password_correct"], st.session_state["current_user"] = True, u
            st.rerun()
        else: st.error("نام کاربری یا رمز عبور اشتباه است.")
    st.stop()

# --- بارگذاری داده ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        for c in ["واحد", "تاریخ پرداخت"]:
            if c not in df.columns: df[c] = "ثبت نشده"
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])

df_exp = load_data()
df_inc = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی"])
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# --- منوی اصلی ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
st.title("💸 پنل جامع مدیریت تنخواه")
st.info(f"💰 موجودی فعلی: {format_money(balance)}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و فیلتر", "💰 شارژ", "🛠️ ویرایش کامل", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. ثبت فاکتور
with tab1:
    with st.form("f_add", clear_on_submit=True):
        c_l, c_r = st.columns(2)
        with c_l:
            d_f = shamsi_date_input("تاریخ فاکتور", "fact_new")
            d_p = shamsi_date_input("تاریخ پرداخت", "pay_new")
            unit_in = st.selectbox("واحد", UNITS)
        with c_r:
            amt_in = st.number_input("مبلغ (ریال)", min_value=0, step=1000)
            st.write(f"✍️ **{format_money(amt_in)}**")
            cat_in = st.selectbox("دسته بندی", CATEGORIES)
            pay_in = st.text_input("پرداخت کننده")
        desc_in = st.text_area("توضیحات")
        if st.form_submit_button("ثبت"):
            df = load_data()
            nid = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
            new_row = {"شماره فاکتور": nid, "تاریخ": d_f, "تاریخ پرداخت": d_p, "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in), "توضیحات": desc_in, "ثبت کننده": st.session_state['current_user'], "پرداخت کننده": pay_in}
            pd.concat([df, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
            add_log(f"ثبت فاکتور {nid}", st.session_state['current_user'])
            st.success("ثبت شد!"); st.rerun()

# ۲. گزارش با فیلتر کامل
with tab2:
    st.subheader("🔍 فیلتر پیشرفته گزارش")
    c1, c2 = st.columns(2)
    with c1: start_date = shamsi_date_input("از تاریخ (پرداخت)", "filter_start")
    with c2: end_date = shamsi_date_input("تا تاریخ (پرداخت)", "filter_end")
    
    c3, c4, c5 = st.columns(3)
    f_unit = c3.multiselect("واحدها", UNITS)
    f_cat = c4.multiselect("دسته بندی", CATEGORIES)
    search_txt = c5.text_input("جستجو در توضیحات/پرداخت کننده")
    
    filtered_df = df_exp.copy()
    filtered_df = filtered_df[(filtered_df["تاریخ پرداخت"] >= start_date) & (filtered_df["تاریخ پرداخت"] <= end_date)]
    if f_unit: filtered_df = filtered_df[filtered_df["واحد"].isin(f_unit)]
    if f_cat: filtered_df = filtered_df[filtered_df["دسته بندی"].isin(f_cat)]
    if search_txt: filtered_df = filtered_df[filtered_df["توضیحات"].str.contains(search_txt, na=False) | filtered_df["پرداخت کننده"].str.contains(search_txt, na=False)]
    
    st.dataframe(filtered_df, use_container_width=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as wr: filtered_df.to_excel(wr, index=False)
    st.download_button("📥 دانلود اکسل این فیلتر", output.getvalue(), "Filtered_Report.xlsx")

# ۳. شارژ تنخواه
with tab3:
    with st.form("f_inc"):
        i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0)
        st.write(format_money(i_amt))
        i_desc = st.text_input("بابت")
        if st.form_submit_button("ثبت واریز"):
            df_i = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])
            new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
            pd.concat([df_i, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
            add_log(f"شارژ تنخواه: {i_amt}", st.session_state['current_user'])
            st.rerun()

# ۴. ویرایش کامل (تمام فیلدها)
with tab4:
    if not df_exp.empty:
        edit_id = st.selectbox("انتخاب فاکتور برای ویرایش کامل:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره فاکتور"] == edit_id].index[0]
        
        with st.form("full_edit"):
            st.warning(f"در حال ویرایش فاکتور شماره {edit_id}")
            ce1, ce2 = st.columns(2)
            with ce1:
                new_df = shamsi_date_input("اصلاح تاریخ فاکتور", "e_f", df_exp.at[idx, "تاریخ"])
                new_dp = shamsi_date_input("اصلاح تاریخ پرداخت", "e_p", df_exp.at[idx, "تاریخ پرداخت"])
                new_u = st.selectbox("اصلاح واحد", UNITS, index=UNITS.index(df_exp.at[idx, "واحد"]) if df_exp.at[idx, "واحد"] in UNITS else 0)
            with ce2:
                new_amt = st.number_input("اصلاح مبلغ (ریال)", value=int(df_exp.at[idx, "مبلغ"]))
                st.write(format_money(new_amt))
                new_cat = st.selectbox("اصلاح دسته بندی", CATEGORIES, index=CATEGORIES.index(df_exp.at[idx, "دسته بندی"]) if df_exp.at[idx, "دسته بندی"] in CATEGORIES else 0)
                new_pay = st.text_input("اصلاح پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
            
            new_desc = st.text_area("اصلاح توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
            
            cb1, cb2 = st.columns(2)
            if cb1.form_submit_button("💾 ذخیره تغییرات نهایی"):
                df_exp.at[idx, "تاریخ"], df_exp.at[idx, "تاریخ پرداخت"] = new_df, new_dp
                df_exp.at[idx, "واحد"], df_exp.at[idx, "مبلغ"] = new_u, new_amt
                df_exp.at[idx, "دسته بندی"], df_exp.at[idx, "پرداخت کننده"] = new_cat, new_pay
                df_exp.at[idx, "توضیحات"] = new_desc
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"ویرایش کامل فاکتور {edit_id}", st.session_state['current_user'])
                st.success("تغییرات با موفقیت اعمال شد."); st.rerun()
                
            if cb2.form_submit_button("🗑️ حذف این فاکتور"):
                df_exp = df_exp.drop(idx)
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"حذف فاکتور {edit_id}", st.session_state['current_user'])
                st.error("فاکتور حذف شد."); st.rerun()

# ۵. لاگ سیستم
with tab5:
    if os.path.exists(LOG_FILE):
        st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False), use_container_width=True)
