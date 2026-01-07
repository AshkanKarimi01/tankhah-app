import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات فایل‌ها ---
DB_FILE = "tankhah_data.csv"
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
        users = {"barjani": "1234", "talebi": "1234"}
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
        # اطمینان از وجود ستون‌های جدید در صورت قدیمی بودن فایل
        for col in ["پرداخت کننده", "زمان ثبت سیستم"]:
            if col not in df.columns:
                df[col] = "نامشخص"
        return df
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر", "ثبت کننده", "پرداخت کننده", "زمان ثبت سیستم"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

def add_audit_log(invoice_id, action, details):
    log_entry = {
        "زمان": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "کاربر": st.session_state['current_user'],
        "شماره فاکتور": invoice_id,
        "عملیات": action,
        "جزئیات": details
    }
    ldf = pd.read_csv(LOG_FILE) if os.path.exists(LOG_FILE) else pd.DataFrame(columns=log_entry.keys())
    ldf = pd.concat([ldf, pd.DataFrame([log_entry])], ignore_index=True)
    ldf.to_csv(LOG_FILE, index=False)

# --- ظاهر برنامه ---
st.set_page_config(page_title="مدیریت تنخواه", layout="wide")
st.title("💸 پنل جامع مدیریت تنخواه")

with st.sidebar:
    st.write(f"👤 کاربر: **{st.session_state['current_user']}**")
    if st.button("خروج"):
        st.session_state["password_correct"] = False
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و خروجی", "✏️ ویرایش و حذف", "📜 تاریخچه تغییرات"])

CATEGORIES = ["غذا", "اسنپ و آژانس", "پیک", "باربری", "پست و تیپاکس", "نوشت افزار", "کارمزد", "آبدارخانه و پذیرایی", "متفرقه"]

# --- تب ۱: ثبت ---
with tab1:
    with st.form("f1", clear_on_submit=True):
        c1, c2 = st.columns(2)
        d_in = c1.text_input("تاریخ فاکتور (شمسی)", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        cat_in = c1.selectbox("دسته بندی", CATEGORIES)
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
                
                new_row = {
                    "شماره فاکتور": next_id, "تاریخ": d_in, "دسته بندی": cat_in, 
                    "مبلغ": int(amt_in), "توضیحات": desc_in, "تصویر": img_p, 
                    "ثبت کننده": st.session_state['current_user'], 
                    "پرداخت کننده": pay_in,
                    "زمان ثبت سیستم": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                save_data(pd.concat([df, pd.DataFrame([new_row])], ignore_index=True))
                st.success(f"✅ فاکتور شماره {next_id} با موفقیت ثبت شد.")
            else:
                st.warning("⚠️ وارد کردن مبلغ و پرداخت‌کننده الزامی است.")

# --- تب ۲: گزارش (با فیلتر بازه زمانی) ---
with tab2:
    df_rep = load_data()
    if not df_rep.empty:
        st.subheader("🔍 فیلتر گزارش")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        with f_col1:
            start_date = st.text_input("از تاریخ:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        with f_col2:
            end_date = st.text_input("تا تاریخ:", value=jdatetime.date.today().strftime("%Y/%m/%d"))
        with f_col3:
            all_payers = ["همه"] + sorted(df_rep["پرداخت کننده"].unique().tolist())
            sel_payer = st.selectbox("توسط پرداخت کننده:", all_payers)

        # فیلتر کردن دیتا
        mask = (df_rep["تاریخ"] >= start_date) & (df_rep["تاریخ"] <= end_date)
        filtered_df = df_rep.loc[mask]
        if sel_payer != "همه":
            filtered_df = filtered_df[filtered_df["پرداخت کننده"] == sel_payer]

        st.divider()
        
        if not filtered_df.empty:
            total = filtered_df["مبلغ"].sum()
            st.metric("جمع کل هزینه‌های فیلتر شده", f"{total:,} تومان")
            
            # نمایش جدول
            disp_df = filtered_df.copy()
            disp_df["مبلغ"] = disp_df["مبلغ"].apply(lambda x: f"{int(x):,}")
            st.dataframe(disp_df.drop(columns=["تصویر", "زمان ثبت سیستم"]), use_container_width=True, hide_index=True)
            
            # خروجی اکسل
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                filtered_df.to_excel(writer, index=False)
            st.download_button("📥 دانلود اکسلِ این لیست", output.getvalue(), f"Report_{start_date.replace('/','_')}.xlsx")
            
            st.divider()
            sel_id = st.selectbox("مشاهده عکس فاکتور شماره:", filtered_df["شماره فاکتور"].tolist()[::-1])
            img_row = filtered_df[filtered_df["شماره فاکتور"] == sel_id].iloc[0]
            if img_row["تصویر"] != "بدون تصویر" and os.path.exists(img_row["تصویر"]):
                st.image(img_row["تصویر"], width=500)
        else:
            st.info("در این بازه زمانی هیچ فاکتوری یافت نشد.")

# --- تب ۳: ویرایش و حذف ---
with tab3:
    df_m = load_data()
    if not df_m.empty:
        mid = st.selectbox("انتخاب فاکتور برای تغییر:", df_m["شماره فاکتور"].tolist())
        idx = df_m[df_m["شماره فاکتور"] == mid].index[0]
        c_edit, c_del = st.columns(2)
        with c_edit:
            with st.form("f_edit"):
                n_amt = st.number_input("اصلاح مبلغ", value=int(df_m.at[idx, "مبلغ"]))
                n_pay = st.text_input("اصلاح پرداخت کننده", value=str(df_m.at[idx, "پرداخت کننده"]))
                n_desc = st.text_area("اصلاح توضیحات", value=str(df_m.at[idx, "توضیحات"]))
                if st.form_submit_button("ذخیره تغییرات"):
                    add_audit_log(mid, "ویرایش", f"مبلغ به {n_amt} و پرداخت‌کننده به {n_pay} تغییر کرد.")
                    df_m.at[idx, "مبلغ"], df_m.at[idx, "پرداخت کننده"], df_m.at[idx, "توضیحات"] = n_amt, n_pay, n_desc
                    save_data(df_m)
                    st.success("تغییرات با موفقیت اعمال شد.")
                    st.rerun()
        with c_del:
            st.write("---")
            if st.button("❌ حذف قطعی این فاکتور"):
                add_audit_log(mid, "حذف", "فاکتور به طور کامل حذف شد.")
                if df_m.at[idx, "تصویر"] != "بدون تصویر" and os.path.exists(df_m.at[idx, "تصویر"]):
                    os.remove(df_m.at[idx, "تصویر"])
                df_m = df_m.drop(idx)
                save_data(df_m)
                st.error("فاکتور از سیستم حذف شد.")
                st.rerun()

# --- تب ۴: تاریخچه ---
with tab4:
    if os.path.exists(LOG_FILE):
        st.subheader("📜 گزارش فعالیت‌های کاربران")
        st.table(pd.read_csv(LOG_FILE).sort_values(by="زمان", ascending=False))

