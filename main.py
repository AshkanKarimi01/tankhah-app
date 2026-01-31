import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها (دیتابیس شما) ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv"
LOG_FILE = "audit_log.csv"

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

# --- بارگذاری داده‌ها ---
def load_data():
    df_e = pd.read_csv(DB_FILE) if os.path.exists(DB_FILE) else pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])
    df_i = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])
    return df_e, df_i

# --- تنظیمات صفحه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
df_exp, df_inc = load_data()

# موجودی
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

st.title("💸 پنل جامع مدیریت تنخواه")
st.info(f"💰 موجودی فعلی: {format_money(balance)}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و فیلتر", "💰 شارژ", "🛠️ ویرایش کامل", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. ثبت فاکتور (با اصلاح نمایش آنی مبلغ)
with tab1:
    c_l, c_r = st.columns(2)
    with c_l:
        d_f = shamsi_date_input("تاریخ فاکتور", "fact_new")
        d_p = shamsi_date_input("تاریخ پرداخت", "pay_new")
        unit_in = st.selectbox("واحد", UNITS)
    with c_r:
        amt_in = st.number_input("مبلغ (ریال)", min_value=0, step=1000, key="new_amt_input")
        # این کد زیر دقیقا همان چیزی است که میخواستی؛ نمایش آنی حروف
        st.markdown(f"✍️ <span style='color:#3498db; font-weight:bold; font-size:18px;'>{format_money(amt_in)}</span>", unsafe_allow_html=True)
        cat_in = st.selectbox("دسته بندی", CATEGORIES)
        pay_in = st.text_input("پرداخت کننده")
    desc_in = st.text_area("توضیحات")
    
    if st.button("🚀 ثبت نهایی فاکتور"):
        if amt_in > 0:
            nid = 1 if df_exp.empty else int(df_exp["شماره فاکتور"].max()) + 1
            new_row = {"شماره فاکتور": nid, "تاریخ": d_f, "تاریخ پرداخت": d_p, "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in), "توضیحات": desc_in, "ثبت کننده": "barjani", "پرداخت کننده": pay_in}
            pd.concat([df_exp, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
            add_log(f"ثبت فاکتور {nid}", "barjani")
            st.success("ثبت شد!"); st.rerun()

# ۲. گزارش با فیلتر تاریخ (بدون تغییر)
with tab2:
    st.subheader("🔍 فیلتر گزارش")
    c1, c2 = st.columns(2)
    with c1: start_date = shamsi_date_input("از تاریخ پرداخت", "f_s")
    with c2: end_date = shamsi_date_input("تا تاریخ پرداخت", "f_e")
    
    mask = (df_exp["تاریخ پرداخت"] >= start_date) & (df_exp["تاریخ پرداخت"] <= end_date)
    st.dataframe(df_exp[mask], use_container_width=True)
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as wr: df_exp[mask].to_excel(wr, index=False)
    st.download_button("📥 دانلود اکسل این گزارش", output.getvalue(), "Report.xlsx")

# ۳. شارژ تنخواه + بازگشت تاریخچه (اصلاح شده)
with tab3:
    st.subheader("➕ شارژ جدید")
    i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0, key="inc_input")
    st.markdown(f"💎 **{format_money(i_amt)}**")
    i_desc = st.text_input("بابت")
    if st.button("ثبت شارژ"):
        new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
        pd.concat([df_inc, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
        add_log(f"شارژ: {i_amt}", "barjani")
        st.success("حساب شارژ شد"); st.rerun()
    
    st.write("---")
    st.subheader("📜 تاریخچه شارژهای قبلی")
    if not df_inc.empty:
        st.dataframe(df_inc.sort_index(ascending=False), use_container_width=True)
    else:
        st.write("تاریخچه‌ای موجود نیست.")

# ۴. ویرایش کامل (بدون تغییر در منطق قبلی)
with tab4:
    if not df_exp.empty:
        edit_id = st.selectbox("انتخاب فاکتور:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره fاکتور"] == edit_id].index[0] if "شماره fاکتور" in df_exp.columns else df_exp[df_exp["شماره فاکتور"] == edit_id].index[0]
        
        ce1, ce2 = st.columns(2)
        with ce1:
            n_f = shamsi_date_input("اصلاح تاریخ فاکتور", "e_f", df_exp.at[idx, "تاریخ"])
            n_p = shamsi_date_input("اصلاح تاریخ پرداخت", "e_p", df_exp.at[idx, "تاریخ پرداخت"])
            n_u = st.selectbox("واحد", UNITS, index=UNITS.index(df_exp.at[idx, "واحد"]) if df_exp.at[idx, "واحد"] in UNITS else 0)
        with ce2:
            n_amt = st.number_input("مبلغ", value=int(df_exp.at[idx, "مبلغ"]), key="edit_amt")
            st.info(format_money(n_amt))
            n_cat = st.selectbox("دسته بندی", CATEGORIES, index=CATEGORIES.index(df_exp.at[idx, "دسته بندی"]) if df_exp.at[idx, "دسته بندی"] in CATEGORIES else 0)
            n_pay = st.text_input("پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
        
        n_desc = st.text_area("توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
        
        b1, b2 = st.columns(2)
        if b1.button("💾 ذخیره تغییرات"):
            df_exp.iloc[idx] = [edit_id, n_f, n_p, n_cat, n_u, n_amt, n_desc, "barjani", n_pay]
            df_exp.to_csv(DB_FILE, index=False)
            add_log(f"ویرایش فاکتور {edit_id}", "barjani")
            st.success("بروزرسانی شد"); st.rerun()
        if b2.button("🗑️ حذف فاکتور"):
            df_exp.drop(idx).to_csv(DB_FILE, index=False)
            add_log(f"حذف فاکتور {edit_id}", "barjani")
            st.rerun()

# ۵. لاگ سیستم (بدون تغییر)
with tab5:
    if os.path.exists(LOG_FILE):
        st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False), use_container_width=True)
