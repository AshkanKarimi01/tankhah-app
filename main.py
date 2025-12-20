import os
import sys
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import streamlit.web.cli as stcli

# --- تنظیمات دیتابیس ---
DB_FILE = "tankhah_data.csv"
UPLOAD_DIR = "uploaded_images"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

def load_data():
    if os.path.exists(DB_FILE):
        try: return pd.read_csv(DB_FILE)
        except: return pd.DataFrame(columns=["تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر"])
    return pd.DataFrame(columns=["تاریخ", "دسته بندی", "مبلغ", "توضیحات", "تصویر"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# --- ظاهر برنامه و CSS برای پرینت ---
st.set_page_config(page_title="تنخواه آنلاین", layout="centered")

# مخفی کردن المان‌های اضافی موقع پرینت
st.markdown("""
    <style>
    @media print {
        .stButton, .stFileUploader, .stForm, header, footer {
            display: none !important;
        }
        .main {
            background-color: white !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💸 مدیریت و آرشیو تنخواه")

# --- منوی اصلی (تب‌بندی) ---
tab1, tab2 = st.tabs(["📝 ثبت فاکتور جدید", "📂 آرشیو و گزارش"])

with tab1:
    with st.form("tankhah_form", clear_on_submit=True):
        today = jdatetime.date.today().strftime("%Y/%m/%d")
        date = st.text_input("تاریخ (شمسی)", value=today)
        category = st.selectbox("دسته بندی", ["خرید اقلام", "ایاب و ذهاب", "تعمیرات", "سایر"])
        amount = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
        description = st.text_area("توضیحات")
        uploaded_file = st.file_uploader("عکس فاکتور", type=['jpg', 'jpeg', 'png'])
        submit_button = st.form_submit_button("ثبت فاکتور")

    if submit_button and amount > 0:
        image_path = "بدون تصویر"
        if uploaded_file is not None:
            file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
            image_path = os.path.join(UPLOAD_DIR, file_name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        new_data = {"تاریخ": date, "دسته بندی": category, "مبلغ": f"{amount:,}", "توضیحات": description, "تصویر": image_path}
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        save_data(df)
        st.success("✅ فاکتور با موفقیت ثبت شد.")

with tab2:
    data = load_data()
    if not data.empty:
        # --- بخش مشاهده عکس‌های قبلی ---
        st.subheader("🖼️ مشاهده تصاویر فاکتورها")
        options = [f"{idx}: {row['تاریخ']} - {row['مبلغ']} تومان" for idx, row in data.iterrows()]
        selected_option = st.selectbox("فاکتور مورد نظر را انتخاب کنید:", options[::-1]) # نمایش از جدید به قدیم
        
        idx_to_view = int(selected_option.split(":")[0])
        img_url = data.loc[idx_to_view, "تصویر"]
        
        if img_url != "بدون تصویر" and os.path.exists(img_url):
            st.image(img_url, caption=f"تصویر فاکتور {data.loc[idx_to_view, 'تاریخ']}", use_container_width=True)
        else:
            st.warning("برای این فاکتور تصویری ثبت نشده است.")

        st.divider()
        
        # --- بخش جدول و پرینت ---
        st.subheader("📋 لیست کل هزینه‌ها")
        st.dataframe(data, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            csv = data.to_csv(index=False).encode('utf-8-sig')
            st.download_button("📥 دانلود فایل اکسل (CSV)", data=csv, file_name="report.csv", mime='text/csv')
        
        with col2:
            if st.button("🖨️ آماده‌سازی برای پرینت"):
                st.info("حالا دکمه Ctrl+P را بزنید تا فقط لیست چاپ شود.")
    else:
        st.info("هنوز موردی ثبت نشده است.")
