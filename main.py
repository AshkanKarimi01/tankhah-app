import os
import sys
import pandas as pd
import streamlit as st
from datetime import datetime
import streamlit.web.cli as stcli

# --- بخش خود-اجرا برای لیارا ---
def run_streamlit():
    if "streamlit" not in sys.modules:
        if "STREAMLIT_SERVER_PORT" not in os.environ:
            os.environ["STREAMLIT_SERVER_PORT"] = os.environ.get("PORT", "8000")
        sys.argv = ["streamlit", "run", __file__, "--server.port", os.environ["STREAMLIT_SERVER_PORT"], "--server.address", "0.0.0.0"]
        sys.exit(stcli.main())

if __name__ == "__main__":
    run_streamlit()

# --- تنظیمات دیتابیس و پوشه عکس‌ها ---
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

# --- ظاهر برنامه ---
st.set_page_config(page_title="تنخواه آنلاین", layout="centered")
st.title("💸 ثبت هزینه‌های تنخواه با تصویر")

# --- فرم ورود اطلاعات ---
with st.form("tankhah_form", clear_on_submit=True):
    date = st.date_input("تاریخ فاکتور", datetime.now())
    category = st.selectbox("دسته بندی", ["خرید اقلام", "ایاب و ذهاب", "تعمیرات", "سایر"])
    amount = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
    description = st.text_area("توضیحات")
    
    # اضافه شدن بخش آپلود عکس
    uploaded_file = st.file_uploader("عکس فاکتور را انتخاب کنید", type=['jpg', 'jpeg', 'png'])
    
    submit_button = st.form_submit_button("ثبت نهایی")

if submit_button:
    if amount > 0:
        image_path = "بدون تصویر"
        if uploaded_file is not None:
            # ذخیره عکس با نام منحصر به فرد (بر اساس زمان)
            file_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uploaded_file.name}"
            image_path = os.path.join(UPLOAD_DIR, file_name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        new_data = {
            "تاریخ": str(date),
            "دسته بندی": category,
            "مبلغ": amount,
            "توضیحات": description,
            "تصویر": image_path
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        save_data(df)
        st.success(f"✅ فاکتور با مبلغ {amount:,} تومان ثبت شد.")
    else:
        st.error("⚠️ مبلغ نمی‌تواند صفر باشد.")

# --- نمایش لیست هزینه‌ها ---
st.divider()
st.subheader("📋 لیست آخرین ثبت‌ها")
data = load_data()
if not data.empty:
    # نمایش جدول (بدون ستون مسیر فایل برای زیبایی بیشتر)
    st.dataframe(data.tail(10), use_container_width=True)
    
    # قابلیت مشاهده عکس آخرین فاکتور
    last_row = data.iloc[-1]
    if last_row["تصویر"] != "بدون تصویر" and os.path.exists(last_row["تصویر"]):
        with st.expander("👁️ مشاهده عکس آخرین فاکتور"):
            st.image(last_row["تصویر"])
else:
    st.info("هنوز موردی ثبت نشده است.")
