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

# --- توابع کمکی ---
def format_money(amount):
    try:
        val = int(float(amount))
        if val == 0: return "صفر ریال"
        toman = val // 10
        return f"{val:,} ریال (معادل {toman:,} تومان)"
    except: return "۰ ریال"

def add_log(action, user):
    df_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["زمان", "کاربر", "عملیات"])
    new_log = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": user, "عملیات": action}
    pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True).to_csv(LOG_FILE, index=False)

# --- سیستم ورود ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.set_page_config(page_title="ورود به سیستم", layout="centered")
    st.subheader("🔐 ورود به مدیریت تنخواه")
    u_in = st.text_input("نام کاربری")
    p_in = st.text_input("رمز عبور", type="password")
    users = {"admin": "admin123@", "barjani": "1234", "talebi": "1234"}
    
    if st.button("ورود"):
        if u_in in users and users[u_in] == p_in:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u_in
            st.rerun()
        else:
            st.error("نام کاربری یا رمز عبور اشتباه است!")
    st.stop()

# --- بارگذاری داده‌ها ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if "شماره fاکتور" in df.columns:
            df = df.rename(columns={"شماره fاکتور": "شماره فاکتور"})
        # اضافه کردن ستون تاریخ پرداخت اگر وجود نداشت
        if "تاریخ پرداخت" not in df.columns:
            df["تاریخ پرداخت"] = "نامشخص"
        if "مبلغ" in df.columns:
            df["مبلغ"] = pd.to_numeric(df["مبلغ"], errors='coerce').fillna(0)
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])

st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
df_exp = load_data()
df_inc = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# هدر
c_h1, c_h2 = st.columns([5, 1])
with c_h1: st.title("💸 پنل مدیریت تنخواه")
with c_h2: 
    if st.button("خروج"): 
        st.session_state["logged_in"] = False
        st.rerun()

st.info(f"💰 موجودی فعلی: {format_money(balance)} | 👤 کاربر: {st.session_state['user']}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و فیلتر", "💰 شارژ", "🛠️ ویرایش و حذف", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. تب ثبت (با فیلد تاریخ پرداخت)
with tab1:
    c_l, c_r = st.columns(2)
    with c_l:
        dfac = st.text_input("تاریخ فاکتور", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        dpay = st.text_input("تاریخ پرداخت", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        unit_in = st.selectbox("واحد مربوطه", UNITS)
    with c_r:
        amt_in = st.number_input("مبلغ فاکتور (ریال)", min_value=0, step=1000)
        st.markdown(f"👈 **{format_money(amt_in)}**")
        cat_in = st.selectbox("دسته‌بندی", CATEGORIES)
        pay_in = st.text_input("پرداخت کننده")
    desc_in = st.text_area("توضیحات")
    if st.button("🚀 ثبت نهایی"):
        nid = 1 if df_exp.empty else int(df_exp["شماره فاکتور"].max()) + 1
        new_row = {
            "شماره فاکتور": nid, "تاریخ": dfac, "تاریخ پرداخت": dpay,
            "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in),
            "توضیحات": desc_in, "ثبت کننده": st.session_state['user'], "پرداخت کننده": pay_in
        }
        pd.concat([df_exp, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
        add_log(f"ثبت فاکتور {nid}", st.session_state['user'])
        st.success("فاکتور ثبت شد."); st.rerun()

# ۲. تب گزارش
with tab2:
    st.subheader("🔍 فیلتر گزارش بر اساس تاریخ")
    c1, c2 = st.columns(2)
    s_date = c1.text_input("از تاریخ (مثل 1404/09/01)", value="1404/09/01", key="s_rep")
    e_date = c2.text_input("تا تاریخ (مثل 1404/11/30)", value="1404/11/30", key="e_rep")
    
    col_show1, col_show2 = st.columns(2)
    btn_filter = col_show1.button("🔍 نمایش گزارش فیلتر شده")
    btn_all = col_show2.button("📋 نمایش کل فاکتورها")

    final_report = pd.DataFrame()
    if btn_filter:
        final_report = df_exp[(df_exp["تاریخ"] >= s_date) & (df_exp["تاریخ"] <= e_date)]
    elif btn_all:
        final_report = df_exp

    if not final_report.empty:
        st.dataframe(final_report, use_container_width=True)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
            final_report.to_excel(wr, index=False)
        st.download_button("📥 دانلود اکسل خروجی", out.getvalue(), "Tankhah_Report.xlsx")

# ۳. تب شارژ
with tab3:
    i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0)
    st.info(format_money(i_amt))
    i_desc = st.text_input("بابت")
    if st.button("ثبت واریز"):
        new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
        pd.concat([df_inc, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
        add_log(f"شارژ {i_amt}", st.session_state['user'])
        st.rerun()
    st.dataframe(df_inc.sort_index(ascending=False), use_container_width=True)

# ۴. تب ویرایش و حذف
with tab4:
    if not df_exp.empty:
        e_id = st.selectbox("انتخاب شماره فاکتور:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره فاکتور"] == e_id].index[0]
        with st.expander("📝 اصلاح", expanded=True):
            v_f = st.text_input("تاریخ فاکتور", value=str(df_exp.at[idx, "تاریخ"]))
            v_p = st.text_input("تاریخ پرداخت", value=str(df_exp.at[idx, "تاریخ پرداخت"]))
            v_a = st.number_input("مبلغ", value=int(df_exp.at[idx, "مبلغ"]), key="edit_amt")
            v_pay = st.text_input("پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
            v_desc = st.text_area("توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
            
            b1, b2 = st.columns(2)
            if b1.button("💾 ذخیره تغییرات"):
                df_exp.at[idx, "تاریخ"] = v_f
                df_exp.at[idx, "تاریخ پرداخت"] = v_p
                df_exp.at[idx, "مبلغ"] = int(v_a)
                df_exp.at[idx, "توضیحات"] = v_desc
                df_exp.at[idx, "پرداخت کننده"] = v_pay
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"ویرایش فاکتور {e_id}", st.session_state['user'])
                st.success("اصلاح شد."); st.rerun()
            if b2.button("🗑️ حذف فاکتور"):
                df_exp.drop(idx).to_csv(DB_FILE, index=False)
                add_log(f"حذف فاکتور {e_id}", st.session_state['user'])
                st.rerun()

# ۵. لاگ سیستم
with tab5:
    if os.path.exists(LOG_FILE): 
        st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False), use_container_width=True)import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
INCOME_FILE = "income_data.csv"
LOG_FILE = "audit_log.csv"

# --- توابع کمکی ---
def format_money(amount):
    try:
        val = int(float(amount))
        if val == 0: return "صفر ریال"
        toman = val // 10
        return f"{val:,} ریال (معادل {toman:,} تومان)"
    except: return "۰ ریال"

def add_log(action, user):
    df_log = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=["زمان", "کاربر", "عملیات"])
    new_log = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": user, "عملیات": action}
    pd.concat([df_log, pd.DataFrame([new_log])], ignore_index=True).to_csv(LOG_FILE, index=False)

# --- سیستم ورود ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.set_page_config(page_title="ورود به سیستم", layout="centered")
    st.subheader("🔐 ورود به مدیریت تنخواه")
    u_in = st.text_input("نام کاربری")
    p_in = st.text_input("رمز عبور", type="password")
    users = {"admin": "admin123@", "barjani": "1234", "talebi": "1234"}
    
    if st.button("ورود"):
        if u_in in users and users[u_in] == p_in:
            st.session_state["logged_in"] = True
            st.session_state["user"] = u_in
            st.rerun()
        else:
            st.error("نام کاربری یا رمز عبور اشتباه است!")
    st.stop()

# --- بارگذاری داده‌ها ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        if "شماره fاکتور" in df.columns:
            df = df.rename(columns={"شماره fاکتور": "شماره فاکتور"})
        # اضافه کردن ستون تاریخ پرداخت اگر وجود نداشت
        if "تاریخ پرداخت" not in df.columns:
            df["تاریخ پرداخت"] = "نامشخص"
        if "مبلغ" in df.columns:
            df["مبلغ"] = pd.to_numeric(df["مبلغ"], errors='coerce').fillna(0)
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "تاریخ پرداخت", "دسته بندی", "واحد", "مبلغ", "توضیحات", "ثبت کننده", "پرداخت کننده"])

st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
df_exp = load_data()
df_inc = pd.read_csv(INCOME_FILE) if os.path.exists(INCOME_FILE) else pd.DataFrame(columns=["مبلغ واریزی", "تاریخ", "بابت"])
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# هدر
c_h1, c_h2 = st.columns([5, 1])
with c_h1: st.title("💸 پنل مدیریت تنخواه")
with c_h2: 
    if st.button("خروج"): 
        st.session_state["logged_in"] = False
        st.rerun()

st.info(f"💰 موجودی فعلی: {format_money(balance)} | 👤 کاربر: {st.session_state['user']}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و فیلتر", "💰 شارژ", "🛠️ ویرایش و حذف", "📜 لاگ سیستم"])

UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز", "فناوری اطلاعات"]
CATEGORIES = ["غذا", "اسنپ", "پیک", "باربری", "پست", "نوشت افزار", "کارمزد", "آبدارخانه", "متفرقه"]

# ۱. تب ثبت (با فیلد تاریخ پرداخت)
with tab1:
    c_l, c_r = st.columns(2)
    with c_l:
        dfac = st.text_input("تاریخ فاکتور", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        dpay = st.text_input("تاریخ پرداخت", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        unit_in = st.selectbox("واحد مربوطه", UNITS)
    with c_r:
        amt_in = st.number_input("مبلغ فاکتور (ریال)", min_value=0, step=1000)
        st.markdown(f"👈 **{format_money(amt_in)}**")
        cat_in = st.selectbox("دسته‌بندی", CATEGORIES)
        pay_in = st.text_input("پرداخت کننده")
    desc_in = st.text_area("توضیحات")
    if st.button("🚀 ثبت نهایی"):
        nid = 1 if df_exp.empty else int(df_exp["شماره فاکتور"].max()) + 1
        new_row = {
            "شماره فاکتور": nid, "تاریخ": dfac, "تاریخ پرداخت": dpay,
            "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": int(amt_in),
            "توضیحات": desc_in, "ثبت کننده": st.session_state['user'], "پرداخت کننده": pay_in
        }
        pd.concat([df_exp, pd.DataFrame([new_row])], ignore_index=True).to_csv(DB_FILE, index=False)
        add_log(f"ثبت فاکتور {nid}", st.session_state['user'])
        st.success("فاکتور ثبت شد."); st.rerun()

# ۲. تب گزارش
with tab2:
    st.subheader("🔍 فیلتر گزارش بر اساس تاریخ")
    c1, c2 = st.columns(2)
    s_date = c1.text_input("از تاریخ (مثل 1404/09/01)", value="1404/09/01", key="s_rep")
    e_date = c2.text_input("تا تاریخ (مثل 1404/11/30)", value="1404/11/30", key="e_rep")
    
    col_show1, col_show2 = st.columns(2)
    btn_filter = col_show1.button("🔍 نمایش گزارش فیلتر شده")
    btn_all = col_show2.button("📋 نمایش کل فاکتورها")

    final_report = pd.DataFrame()
    if btn_filter:
        final_report = df_exp[(df_exp["تاریخ"] >= s_date) & (df_exp["تاریخ"] <= e_date)]
    elif btn_all:
        final_report = df_exp

    if not final_report.empty:
        st.dataframe(final_report, use_container_width=True)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr:
            final_report.to_excel(wr, index=False)
        st.download_button("📥 دانلود اکسل خروجی", out.getvalue(), "Tankhah_Report.xlsx")

# ۳. تب شارژ
with tab3:
    i_amt = st.number_input("مبلغ واریزی (ریال)", min_value=0)
    st.info(format_money(i_amt))
    i_desc = st.text_input("بابت")
    if st.button("ثبت واریز"):
        new_i = {"مبلغ واریزی": i_amt, "تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "بابت": i_desc}
        pd.concat([df_inc, pd.DataFrame([new_i])], ignore_index=True).to_csv(INCOME_FILE, index=False)
        add_log(f"شارژ {i_amt}", st.session_state['user'])
        st.rerun()
    st.dataframe(df_inc.sort_index(ascending=False), use_container_width=True)

# ۴. تب ویرایش و حذف
with tab4:
    if not df_exp.empty:
        e_id = st.selectbox("انتخاب شماره فاکتور:", df_exp["شماره فاکتور"].tolist()[::-1])
        idx = df_exp[df_exp["شماره فاکتور"] == e_id].index[0]
        with st.expander("📝 اصلاح", expanded=True):
            v_f = st.text_input("تاریخ فاکتور", value=str(df_exp.at[idx, "تاریخ"]))
            v_p = st.text_input("تاریخ پرداخت", value=str(df_exp.at[idx, "تاریخ پرداخت"]))
            v_a = st.number_input("مبلغ", value=int(df_exp.at[idx, "مبلغ"]), key="edit_amt")
            v_pay = st.text_input("پرداخت کننده", value=str(df_exp.at[idx, "پرداخت کننده"]))
            v_desc = st.text_area("توضیحات", value=str(df_exp.at[idx, "توضیحات"]))
            
            b1, b2 = st.columns(2)
            if b1.button("💾 ذخیره تغییرات"):
                df_exp.at[idx, "تاریخ"] = v_f
                df_exp.at[idx, "تاریخ پرداخت"] = v_p
                df_exp.at[idx, "مبلغ"] = int(v_a)
                df_exp.at[idx, "توضیحات"] = v_desc
                df_exp.at[idx, "پرداخت کننده"] = v_pay
                df_exp.to_csv(DB_FILE, index=False)
                add_log(f"ویرایش فاکتور {e_id}", st.session_state['user'])
                st.success("اصلاح شد."); st.rerun()
            if b2.button("🗑️ حذف فاکتور"):
                df_exp.drop(idx).to_csv(DB_FILE, index=False)
                add_log(f"حذف فاکتور {e_id}", st.session_state['user'])
                st.rerun()

# ۵. لاگ سیستم
with tab5:
    if os.path.exists(LOG_FILE): 
        st.dataframe(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False), use_container_width=True)
