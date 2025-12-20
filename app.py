import streamlit as st
import pandas as pd
from datetime import datetime
import os

# تنظیمات ظاهری (راست‌چین برای فارسی)
st.set_page_config(page_title="سیستم تنخواه", layout="centered")

# استایل دهی برای فونت و جهت متن
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn&display=swap');
    html, body, [class*="css"]  {
        font-family: 'Vazirmatn', sans-serif;
        direction: rtl;
        text-align: right;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📝 ثبت هزینه جدید")

# ایجاد دیتابیس ساده (فایل CSV) اگر وجود نداشته باشد
DB_FILE = "tankhah_db.csv"
if not os.path.exists(DB_FILE):
    df = pd.DataFrame(columns=["تاریخ", "مبلغ", "دسته", "توضیحات", "نام_فایل"])
    df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')

# فرم ثبت اطلاعات
with st.container():
    amount = st.number_input("مبلغ هزینه (ریال):", min_value=0, step=10000)
    category = st.selectbox("نوع هزینه:", ["بنزین/سفر", "خرید قطعات", "پذیرایی/غذا", "ابزارآلات", "سایر"])
    description = st.text_area("توضیحات فاکتور:")
    
    # دکمه دوربین
    img_file = st.camera_input("📸 گرفتن عکس از فاکتور")

    if st.button("ثبت نهایی و ارسال"):
        if img_file is not None and amount > 0:
            # ذخیره عکس در پوشه
            if not os.path.exists("images"): os.makedirs("images")
            img_name = f"images/IMG_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            with open(img_name, "wb") as f:
                f.write(img_file.getbuffer())
            
            # ثبت در دیتابیس
            new_entry = {
                "تاریخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "مبلغ": f"{amount:,}",
                "دسته": category,
                "توضیحات": description,
                "نام_فایل": img_name
            }
            df = pd.read_csv(DB_FILE)
            df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
            df.to_csv(DB_FILE, index=False, encoding='utf-8-sig')
            
            st.success("✅ فاکتور با موفقیت ثبت شد.")
        else:

            st.error("⚠️ لطفاً مبلغ را وارد کرده و عکس فاکتور را بگیرید.")
