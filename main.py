import os
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import io

# --- تنظیمات دیتابیس و فایل‌ها ---
DB_FILE = "tankhah_data.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            return df
        except:
            pass
    return pd.DataFrame(columns=["شماره فاکتور", "تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ظاهر برنامه ---
st.set_page_config(page_title="مدیریت تنخواه حرفه‌ای", layout="wide")
st.markdown("""<style> .stButton>button {width: 100%;} .main {direction: rtl; text-align: right;} </style>""", unsafe_allow_html=True)

st.title("💸 پنل جامع مدیریت تنخواه")

tab1, tab2, tab3 = st.tabs(["📝 ثبت فاکتور", "📊 گزارش و خروجی", "🛠️ ویرایش و مدیریت"])

# --- لیست کامل ۹تایی دسته‌بندی‌ها ---
CATEGORIES = [
    "غذا", 
    "اسنپ و آژانس", 
    "پیک", 
    "باربری", 
    "پست و تیپاکس", 
    "نوشت افزار", 
    "کارمزد", 
    "آبدارخانه و پذیرایی", 
    "متفرقه"
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
        next_id = 1 if df.empty else df["شماره فاکتور"].max() + 1
        
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
            "تصویر": img_path
        }
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success(f"✅ فاکتور شماره {next_id} با موفقیت ثبت شد.")

# --- تب ۲: گزارش، مشاهده عکس و خروجی اکسل ---
with tab2:
    df_rep = load_data()
    if not df_rep.empty:
        display_df = df_rep.copy()
        display_df["مبلغ"] = display_df["مبلغ"].apply(lambda x: f"{int(x):,}")
        
        st.subheader("📋 لیست فاکتورهای ثبت شده")
        st.dataframe(display_df.drop(columns=["تصویر"]), use_container_width=True, hide_index=True)
        
        st.divider()
        col_img, col_exl = st.columns([2, 1])
        
        with col_img:
            st.subheader("🔍 مشاهده سریع عکس فاکتور")
            selected_id = st.selectbox("انتخاب شماره فاکتور برای مشاهده عکس:", df_rep["شماره فاکتور"].tolist()[::-1])
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
                label="دانلود فایل Excel حرفه‌ای",
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
        edit_id = st.selectbox("شماره فاکتور مورد نظر برای ویرایش:", df_edit["شماره فاکتور"].tolist())
        edit_idx = df_edit[df_edit["شماره فاکتور"] == edit_id].index[0]
        
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
