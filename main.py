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
    u = st.text_input("نام کاربری")
    p = st.text_input("رمز عبور", type="password")
    if st.button("ورود"):
        users = {"barijani": "1234", "talebi": "1234"}
        if u in users and users[u] == p:
            st.session_state["password_correct"] = True
            st.session_state["current_user"] = u
            st.rerun()
        else: st.error("❌ خطا در ورود")
    return False

if not check_password(): st.stop()

# --- توابع داده ---
def load_data():
    if os.path.exists(DB_FILE):
        df = pd.read_csv(DB_FILE)
        cols = ["واحد", "پرداخت کننده", "زمان ثبت سیستم"]
        for c in cols:
            if c not in df.columns: df[c] = "تعریف نشده"
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "واحد", "مبلغ", "توضیحات", "تصویر", "ثبت کننده", "پرداخت کننده", "زمان ثبت سیستم"])

def load_income():
    if os.path.exists(INCOME_FILE): return pd.read_csv(INCOME_FILE)
    return pd.DataFrame(columns=["تاریخ", "مبلغ واریزی", "بابت", "ثبت کننده"])

def save_data(df, filename): df.to_csv(filename, index=False)

def add_audit_log(invoice_id, action, details):
    log_entry = {"زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "کاربر": st.session_state['current_user'], "شماره فاکتور": invoice_id, "عملیات": action, "جزئیات": details}
    ldf = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=log_entry.keys())
    ldf = pd.concat([ldf, pd.DataFrame([log_entry])], ignore_index=True)
    ldf.to_csv(LOG_FILE, index=False)

# --- محاسبات موجودی ---
df_exp = load_data()
df_inc = load_income()
balance = df_inc["مبلغ واریزی"].sum() - df_exp["مبلغ"].sum()

# --- ظاهر برنامه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
st.title("💸 پنل جامع مدیریت تنخواه")

# نوار وضعیت موجودی
st.info(f"💰 **موجودی فعلی تنخواه:** {balance:,} تومان")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش", "💰 شارژ تنخواه", "🛠️ ویرایش و حذف", "📜 تاریخچه"])

CATEGORIES = ["غذا", "اسنپ و آژانس", "پیک", "باربری", "پست و تیپاکس", "نوشت افزار", "کارمزد", "آبدارخانه و پذیرایی", "متفرقه"]
UNITS = ["انبار", "فروش", "مالی", "اداری", "هیات مدیره", "مشاور", "بازرگانی", "ممیز"]

# --- تب ۱: ثبت ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_in = c1.text_input("تاریخ فاکتور", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        unit_in = c1.selectbox("واحد مربوطه", UNITS)
        cat_in = c1.selectbox("دسته بندی", CATEGORIES)
        amt_in = c2.number_input("مبلغ (تومان)", min_value=0, step=1000)
        pay_in = c2.text_input("پرداخت کننده")
        desc_in = st.text_area("توضیحات")
        file_in = st.file_uploader("عکس فاکتور", type=['jpg', 'png', 'jpeg'])
        if st.form_submit_button("ثبت نهایی"):
            df = load_data()
            nid = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
            img_p = "بدون تصویر"
            if file_in:
                img_p = os.path.join(UPLOAD_DIR, f"{nid}_{file_in.name}")
                with open(img_p, "wb") as f: f.write(file_in.getbuffer())
            new_row = {"شماره فاکتور": nid, "تاریخ": d_in, "دسته بندی": cat_in, "واحد": unit_in, "مبلغ": amt_in, "توضیحات": desc_in, "تصویر": img_p, "ثبت کننده": st.session_state['current_user'], "پرداخت کننده": pay_in, "زمان ثبت سیستم": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True), DB_FILE)
            st.success(f"فاکتور {nid} ثبت شد."); st.rerun()

# --- تب ۲: گزارش ---
with tab2:
    if not df_exp.empty:
        c1, c2 = st.columns(2)
        s_d = c1.text_input("از تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        e_d = c2.text_input("تا تاریخ", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        f_df = df_exp[(df_exp["تاریخ"] >= s_d) & (df_exp["تاریخ"] <= e_d)]
        st.dataframe(f_df.drop(columns=["تصویر"]), use_container_width=True, hide_index=True)
        # دانلود اکسل
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='xlsxwriter') as wr: f_df.to_excel(wr, index=False)
        st.download_button("📥 دانلود اکسل", out.getvalue(), "Report.xlsx")

# --- تب ۳: شارژ تنخواه ---
with tab3:
    with st.form("inc_form", clear_on_submit=True):
        st.subheader("افزایش موجودی")
        c1, c2 = st.columns(2)
        i_amt = c1.number_input("مبلغ واریزی", min_value=0)
        i_note = c2.text_input("بابت")
        if st.form_submit_button("ثبت واریزی"):
            df_i = load_income()
            new_i = {"تاریخ": jdatetime.date.today().strftime("%Y/%m/%d"), "مبلغ واریزی": i_amt, "بابت": i_note, "ثبت کننده": st.session_state['current_user']}
            save_data(pd.concat([df_i, pd.DataFrame([new_i])], ignore_index=True), INCOME_FILE)
            st.success("موجودی افزایش یافت."); st.rerun()
    st.table(df_inc.sort_index(ascending=False))

# --- تب ۴: ویرایش و حذف (اصلاح شده) ---
with tab4:
    st.subheader("🛠️ مدیریت فاکتورهای ثبت شده")
    df_m = load_data()
    if not df_m.empty:
        # ۱. انتخاب فاکتور
        selected_id = st.selectbox("شماره فاکتور را برای ویرایش یا حذف انتخاب کنید:", df_m["شماره فاکتور"].tolist()[::-1])
        idx = df_m[df_m["شماره فاکتور"] == selected_id].index[0]
        
        # ۲. فرم ویرایش
        st.markdown("---")
        with st.form("edit_form_final"):
            st.write(f"📝 ویرایش فاکتور شماره {selected_id}")
            col1, col2 = st.columns(2)
            e_amt = col1.number_input("مبلغ", value=int(df_m.at[idx, "مبلغ"]))
            e_unit = col1.selectbox("واحد", UNITS, index=UNITS.index(df_m.at[idx, "واحد"]) if df_m.at[idx, "واحد"] in UNITS else 0)
            e_pay = col2.text_input("پرداخت کننده", value=str(df_m.at[idx, "پرداخت کننده"]))
            e_desc = st.text_area("توضیحات", value=str(df_m.at[idx, "توضیحات"]))
            
            submit_edit = st.form_submit_button("💾 ذخیره تغییرات")
            if submit_edit:
                add_audit_log(selected_id, "ویرایش", "تغییر اطلاعات فاکتور")
                df_m.at[idx, "مبلغ"], df_m.at[idx, "واحد"], df_m.at[idx, "پرداخت کننده"], df_m.at[idx, "توضیحات"] = e_amt, e_unit, e_pay, e_desc
                save_data(df_m, DB_FILE)
                st.success("✅ تغییرات با موفقیت ذخیره شد.")
                st.rerun()

        # ۳. دکمه حذف (جدا از فرم برای امنیت)
        st.markdown("---")
        st.warning("⚠️ بخش حذف فاکتور")
        if st.button("❌ حذف قطعی این فاکتور"):
            add_audit_log(selected_id, "حذف", f"حذف فاکتور به مبلغ {df_m.at[idx, 'مبلغ']}")
            if df_m.at[idx, "تصویر"] != "بدون تصویر" and os.path.exists(df_m.at[idx, "تصویر"]):
                os.remove(df_m.at[idx, "تصویر"])
            df_m = df_m.drop(idx)
            save_data(df_m, DB_FILE)
            st.error(f"🗑️ فاکتور شماره {selected_id} حذف شد.")
            st.rerun()
    else:
        st.info("دیتایی برای ویرایش وجود ندارد.")

# --- تب ۵: تاریخچه ---
with tab5:
    if os.path.exists(LOG_FILE):
        st.table(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False))
