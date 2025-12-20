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
        
        sys.argv = [
            "streamlit",
            "run",
            __file__,
            "--server.port",
            os.environ["STREAMLIT_SERVER_PORT"],
            "--server.address",
            "0.0.0.0",
        ]
        sys.exit(stcli.main())

if __name__ == "__main__":
    run_streamlit()

# --- کد اصلی برنامه تنخواه ---

# نام فایل دیتابیس (در پوشه متصل به دیسک)
DB_FILE = "tankhah_data.csv"

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["تاریخ", "دسته بندی", "مبلغ", "توضیحات"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

st.set_page_config(page_title="سیستم ثبت تنخواه", layout="centered")

st.title("💸 ثبت هزینه‌های تنخواه")
st.write("لطفاً اطلاعات فاکتور را وارد کنید:")

# فرم ورود اطلاعات
with st.form("tankhah_form", clear_on_submit=True):
    date = st.date_input("تاریخ فاکتور", datetime.now())
    category = st.selectbox("دسته بندی", ["خرید اقلام", "ایاب و ذهاب", "تعمیرات", "سایر"])
    amount = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
    description = st.text_area("توضیحات")
    
    submit_button = st.form_submit_button("ثبت در سیستم")

if submit_button:
    if amount > 0:
        new_data = {
            "تاریخ": str(date),
            "دسته بندی": category,
            "مبلغ": amount,
            "توضیحات": description
        }
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        save_data(df)
        st.success("✅ فاکتور با موفقیت ثبت شد.")
    else:
        st.error("⚠️ لطفا مبلغ را وارد کنید.")

# نمایش لیست هزینه‌های قبلی
st.divider()
st.subheader("📋 لیست هزینه‌های اخیر")
data = load_data()
if not data.empty:
    st.dataframe(data.tail(10), use_container_width=True)
else:
    st.info("هنوز هیچ هزینه‌ای ثبت نشده است.")
