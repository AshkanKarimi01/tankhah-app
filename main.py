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

# --- تابع تبدیل عدد به حروف و فرمت پول ---
def format_money(amount):
    try:
        val = int(amount)
        if val == 0: return "صفر ریال"
        toman = val // 10
        return f"{val:,} ریال (معادل {toman:,} تومان)"
    except: return "۰ ریال"

# --- تابع ثبت لاگ تغییرات ---
def add_log(action, user="barjani"):
    df_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["زمان", "کاربر", "عملیات"])
    new_log = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": user, "عملیات": action}
    pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True).to_csv(LOG_FILE, index=False)

# --- ورودی تاریخ شمسی استاندارد ---
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

# --- بارگذاری و اصلاح خودکار ساختار دیتابیس ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        required_columns = ["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"]
        for col in required_columns:
            if col not in df.columns:
                df[col] = "ثبت نشده" if "تاریخ" in col else (0 if col == "مبلغ" else "نامشخص")
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])

def load_income():
    if os.path.exists(INCOME_FILE): return pd.read_csv(INCOME_FILE)
    return pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])

# --- شروع برنامه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
df_exp = load_data()
df_inc = load_income()

# محاسبه موجودی کل
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()
st.title("💸 پنل جامع مدیریت تنخواه")
st.info(f"💰 موجودی فعلی: {format_money(balance)}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و فیلتر", "💰 شارژ", "🛠️ ویرایش کامل", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. تب ثبت فاکتور
with tab1:
    c_l, c_r = st.columns(2)
    with c_l:
        dfac = shamsi_date_input("تاریخ فاکتور", "reg_f")
        dpay = shamsi_date_input("تاریخ پرداخت", "reg_p")
        unit_in = st.selectbox("واحد مربوطه", UNITS)
    with c_r:
        amt_in = st.number_input("مبلغ فاکتور (ریال)", min_value=0, step=1000, key="amt_reg")
        st.markdown(f"👈 **{format_money(amt_in)}**") # نمایش آنی
        cat_in = st.selectbox("دسته‌بندی مخارج", CATEGORIES)
        pay_in = st.text_input("نام شخص پرداخت کننده")
    desc_in = st.text_area("توضیحات تکمیلی")
    if st.button("🚀 ثبت نهایی در سیستم"):
        nid = 1 if df_exp.empty else int(df_exp["شماره فاکتور"].max()) + 1
        row = {"شماره فاکتور": nid, "تاریخ": dfac, "تاریخ پرداخت": dpay, "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in), "توضیحات": desc_in, "ثبت کننده": "barjani", "پرداخت کننده": pay_in}
        pd.concat([df_exp, pd.DataFrame([row])], ignore_index=True).to_csv(DB_FILE, index=False)
        add_log(f"ثبت فاکتور جدید به شماره {nid}")
        st.success("فاکتور با موفقیت ثبت شد."); st.rerun()

# ۲. تب گزارش و فیلتر تاریخ
with tab2:
    st.subheader("🔍 فیلتر و خروجی گزارش")
    c1, c2 = st.columns(2)
    with c1: s_date = shamsi_date_input("از تاریخ پرداخت", "rep_start")
    with c2: e_date = shamsi_date_input("تا تاریخ پرداخت", "rep_end")
    
    # اعمال فیلتر بازه زمانی
    f_df = df_exp[(df_exp["تاریخ پرداخت"] >= s_date) & (df_exp["تاریخ پرداخت"] <= e_date)]
    st.dataframe(f_df, use_container_width=True)
    
    # خروجی اکسل
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as wr: f_df.to_excel(wr, index=False)
    st.download_button("📥 دانلود فایل اکسل (فیلتر شده)", output.getvalue(), "Tankhah_Report.xlsx")

# ۳. تب شارژ تنخواه و تاریخچه
with tab3:
    st.subheader("➕ شارژ جدید حساب")
    i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0, key="inc_amt_field")
    st.info(format_money(i_amt))
    i_desc = st.text_input("شرح واریز (بابت)")
    if st.button("ثبت شارژ تنخواه"):
        new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
        pd.concat([df_inc, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
        add_log(f"شارژ حساب به مبلغ {i_amt}")
        st.success("حساب شارژ شد."); st.rerun()
    st.write("---")
    st.subheader("📜 تاریخچه شارژهای قبلی")
    st.dataframe(df_inc.sort_index(ascending=False), use_container_width=True)

# ۴. تب ویرایش و حذف کامل
with tab4:
    if not df_exp.empty:
        e_id = st.selectbox("انتخاب فاکتور جهت ویرایش یا حذف:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره فاکتور"] == e_id].index[0]
        
        with st.expander("📝 فرم اصلاح جزئیات فاکتور", expanded=True):
            col_a, col_b = st.columns(2)
            with col_a:
                v_df = shamsi_date_input("اصلاح تاریخ فاکتور", "edit_f", df_exp.at[idx, "تاریخ"])
                v_dp = shamsi_date_input("اصلاح تاریخ پرداخت", "edit_p", df_exp.at[idx, "تاریخ پرداخت"])
                v_u = st.selectbox("اصلاح واحد", UNITS, index=UNITS.index(df_exp.at[idx, "واحد"]) if df_exp.at[idx, "واحد"] in UNITS else 0)
            with col_b:
                v_amt = st.number_input("اصلاح مبلغ", value=int(df_exp.at[idx, "مبلغ"]), key="edit_amt_val")
                st.warning(format_money(v_amt))
                v_cat = st.selectbox("اصلاح دسته‌بندی", CATEGORIES, index=CATEGORIES.index(df_exp.at[idx, "دسته بندی"]) if df_exp.at[idx, "دسته بندی"] in CATEGORIES else 0)
                v_pay = st.text_input("اصلاح پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
            v_desc = st.text_area("اصلاح توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
            
            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("💾 ذخیره تغییرات"):
                df_exp.at[idx, "تاریخ"], df_exp.at[idx, "تاریخ پرداخت"] = v_df, v_dp
                df_exp.at[idx, "واحد"], df_exp.at[idx, "مبلغ"] = v_u, int(v_amt)
                df_exp.at[idx, "دسته بندی"], df_exp.at[idx, "پرداخت کننده"] = v_cat, v_pay
                df_exp.at[idx, "توضیحات"] = v_desc
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"ویرایش فاکتور شماره {e_id}")
                st.success("تغییرات با موفقیت ذخیره شد."); st.rerun()
                
            if btn_col2.button("🗑️ حذف این فاکتور"):
                df_exp = df_exp.drop(idx)
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"حذف فاکتور شماره {e_id}")
                st.error(f"فاکتور شماره {e_id} از سیستم حذف شد."); st.rerun()

# ۵. تب لاگ سیستم
with tab5:
    if os.path.exists(LOG_FILE): 
        st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False), use_container_width=True)
