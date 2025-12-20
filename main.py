import os
import sys
import pandas as pd
import streamlit as st
import jdatetime
from datetime import datetime
import streamlit.web.cli as stcli

# --- بخش خود-اجرا برای لیارا ---
def run_streamlit():
    if "streamlit" not in sys.modules:
        os.environ["STREAMLIT_SERVER_PORT"] = os.environ.get("PORT", "80")
        sys.argv = ["streamlit", "run", __file__, "--server.port", os.environ["STREAMLIT_SERVER_PORT"], "--server.address", "0.0.0.0"]
        sys.exit(stcli.main())

if __name__ == "__main__":
    run_streamlit()

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

# --- ظاهر برنامه ---
st.set_page_config(page_title="تنخواه آنلاین", layout="centered")
st.title("💸 سیستم مدیریت تنخواه")

# ایجاد تب‌ها (این همون بخشیه که توی عکس کد شما نبود)
tab1, tab2 = st.tabs(["📝 ثبت هزینه جدید", "📂 آرشیو و گزارشات"])

with tab1:
    with st.form("tankhah_form", clear_on_submit=True):
        # تنظیم تاریخ شمسی
        now_shamsi = jdatetime.date.today().strftime("%Y/%m/%d")
        date_sh = st.text_input("تاریخ فاکتور (شمسی)", value=now_shamsi)
        
        cat = st.selectbox("دسته بندی", ["خرید اقلام", "ایاب و ذهاب", "تعمیرات", "سایر"])
        price = st.number_input("مبلغ (تومان)", min_value=0, step=1000)
        desc = st.text_area("توضیحات")
        file = st.file_uploader("عکس فاکتور", type=['jpg', 'png', 'jpeg'])
        
        submit = st.form_submit_button("ثبت در سیستم")

    if submit and price > 0:
        img_path = "بدون تصویر"
        if file is not None:
            fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.name}"
            img_path = os.path.join(UPLOAD_DIR, fname)
            with open(img_path, "wb") as f:
                f.write(file.getbuffer())
        
        new_row = {"تاریخ": date_sh, "دسته بندی": cat, "مبلغ": f"{price:,}", "توضیحات": desc, "تصویر": img_path}
        df = load_data()
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        save_data(df)
        st.success("✅ با موفقیت ثبت شد.")

with tab2:
    df_list = load_data()
    if not df_list.empty:
        st.subheader("🖼️ مشاهده عکس فاکتورها")
        # معکوس کردن لیست برای نمایش جدیدترین‌ها در بالا
        options = [f"{i}: {r['تاریخ']} - {r['مبلغ']}" for i, r in df_list.iterrows()]
        sel = st.selectbox("انتخاب فاکتور:", options[::-1])
        
        idx = int(sel.split(":")[0])
        path = df_list.loc[idx, "تصویر"]
        
        if path != "بدون تصویر" and os.path.exists(path):
            st.image(path, use_container_width=True)
        else:
            st.warning("تصویری ندارد")
        
        st.divider()
        st.subheader("📋 جدول کل هزینه‌ها")
        st.dataframe(df_list, use_container_width=True)
        
        # دکمه دانلود
        csv_data = df_list.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 دانلود فایل اکسل", csv_data, "report.csv", "text/csv")
    else:
        st.info("هنوز دیتایی ثبت نشده.")
