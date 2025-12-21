import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات اولیه دیتابیس و فایل‌ها ---
DB_FILE = "tankhah_data.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# --- سیستم لاگین با دو کاربر ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.set_page_config(page_title="ورود به سیستم", layout="centered")
    st.markdown("<h2 style='text-align: center;'>🔒 ورود به سیستم مدیریت تنخواه</h2>", unsafe_allow_html=True)
    
    with st.container():
        user_input = st.text_input("نام کاربری", key="username")
        password_input = st.text_input("رمز عبور", type="password", key="password")
        
        if st.button("ورود به پنل"):
            # تعریف کاربران بر اساس درخواست شما
            users = {
                "barijani": "1234",
                "talebi": "1234"
            }
            
            if user_input in users and users[user_input] == password_input:
                st.session_state["password_correct"] = True
                st.session_state["current_user"] = user_input
                st.rerun()
            else:
                st.error("❌ نام کاربری یا رمز عبور اشتباه است.")
    return False

# توقف اجرا اگر کاربر لاگین نکرده باشد
if not check_password():
    st.stop()

# --- توابع مدیریت داده‌ها ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return df
        except:
            pass
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر", "ثبت کننده"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- تنظیمات ظاهر برنامه اصلی ---
st.set_page_config(page_title="پنل جامع مدیریت تنخواه", layout="wide")
st.markdown("""
    <style>
    .stButton>button {width: 100%;}
    .main {direction: rtl; text-align: right;}
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# سایدبار برای خروج و نمایش کاربر فعال
with st.sidebar:
    st.write(f"👤 کاربر فعال: **{st.session_state['current_user']}**")
    if st.button("خروج از سیستم"):
        st.session_state["password_correct"] = False
        st.rerun()

st.title("💸 پنل جامع مدیریت تنخواه")

tab1, tab2, tab3 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و خروجی", "🛠️ ویرایش و مدیریت"])

CATEGORIES = [
    "غذا", "اسنپ و آژانس", "پیک", "باربری", 
    "پست و تیپاکس", "نوشت افزار", "کارمزد", 
    "آبدارخانه و پذیرایی", "متفرقه"
]

# --- تب ۱: ثبت فاکتور جدید ---
with tab1:
    with st.form("main_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            today_sh = jdatetime.date.today().strftime("%Y/%m/%d")
            date_in = st.text_input("تاریخ (شمسی)", value=today_sh)
            cat_in = st.selectbox("دسته بندی", CATEGORIES)
        with col2:
            amount_in = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
            desc_in = st.text_area("توضیحات فاکتور")
        
        file_in = st.file_uploader("آپلود عکس فاکتور", type=['jpg', 'jpeg', 'png'])
        submit = st.form_submit_button("ثبت نهایی فاکتور")

    if submit and amount_in > 0:
        df = load_data()
        # تولید شماره فاکتور خودکار از ۱
        next_id = 1 if df.empty else int(df["شماره فاکتور"].max()) + 1
        
        img_path = "بدون تصویر"
        if file_in:
            fname = f"{next_id}_{datetime.now().strftime('%H%M%S')}_{file_in.name}"
            img_path = os.path.join(UPLOAD_DIR, fname)
            with open(img_path, "wb") as f:
                f.write(file_in.getbuffer())
        
        new_row = {
            "شماره فاکتور": int(next_id),
            "تاریخ": date_in,
            "دسته بندی": cat_in,
            "مبلغ": int(amount_in),
            "توضیحات": desc_in,
            "تصویر": img_path,
            "ثبت کننده": st.session_state['current_user']
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"✅ فاکتور شماره {next_id} با موفقیت توسط {st.session_state['current_user']} ثبت شد.")

# --- تب ۲: گزارش، مشاهده عکس و خروجی اکسل ---
with tab2:
    df_rep = load_data()
    if not df_rep.empty:
        # نمایش مبالغ با فرمت سه رقم سه رقم
        display_df = df_rep.copy()
        display_df["مبلغ"] = display_df["مبلغ"].apply(lambda x: f"{int(x):,}")
        
        st.subheader("📋 لیست فاکتورهای ثبت شده")
        st.dataframe(display_df.drop(columns=["تصویر"]), use_container_width=True, hide_index=True)
        
        st.divider()
        col_img, col_exl = st.columns([2, 1])
        
        with col_img:
            st.subheader("🔍 مشاهده عکس فاکتور")
            selected_id = st.selectbox("انتخاب شماره فاکتور:", df_rep["شماره فاکتور"].tolist()[::-1])
            row = df_rep[df_rep["شماره فاکتور"] == selected_id].iloc[0]
            if row["تصویر"] != "بدون تصویر" and os.path.exists(row["تصویر"]):
                st.image(row["تصویر"], caption=f"عکس فاکتور شماره {selected_id}", use_container_width=True)
            else:
                st.warning("این فاکتور عکسی ندارد.")
        
        with col_exl:
            st.subheader("📥 خروجی اکسل")
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_rep.to_excel(writer, index=False, sheet_name='گزارش تنخواه')
            
            st.download_button(
                label="📥 دانلود فایل Excel",
                data=output.getvalue(),
                file_name=f"Report_{jdatetime.date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            if st.button("🗑️ پاکسازی کل دیتای تست"):
                if os.path.exists(DB_FILE): os.remove(DB_FILE)
                st.rerun()
    else:
        st.info("هنوز هیچ فاکتوری ثبت نشده است.")

# --- تب ۳: ویرایش فاکتورها ---
with tab3:
    df_edit = load_data()
    if not df_edit.empty:
        st.subheader("✏️ ویرایش فاکتور موجود")
        edit_id = st.selectbox("شماره فاکتور برای ویرایش:", df_edit["شماره فاکتور"].tolist())
        edit_idx = df_edit[df_edit["شماره fاکتور"] == edit_id].index[0]
        
        with st.form("edit_form"):
            new_amount = st.number_input("اصلاح مبلغ", value=int(df_edit.at[edit_idx, "مبلغ"]))
            new_desc = st.text_area("اصلاح توضیحات", value=df_edit.at[edit_idx, "توضیحات"])
            new_cat = st.selectbox("اصلاح دسته بندی", CATEGORIES, index=CATEGORIES.index(df_edit.at[edit_idx, "دسته بندی"]))
            
            if st.form_submit_button("اعمال تغییرات"):
                df_edit.at[edit_idx, "مبلغ"] = new_amount
                df_edit.at[edit_idx, "توضیحات"] = new_desc
                df_edit.at[edit_idx, "دسته بندی"] = new_cat
                save_data(df_edit)
                st.success("✅ تغییرات ذخیره شد.")
                st.rerun()
    else:
        st.info("دیتایی برای ویرایش وجود ندارد.")
