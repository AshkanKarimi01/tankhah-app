FROM python:3.9-slim

WORKDIR /app

# کپی کردن لیست کتابخانه‌ها و نصب آن‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کردن کل کدهای برنامه
COPY . .

# باز کردن پورت ۸۰
EXPOSE 80

# دستور اجرای مستقیم استریم‌لیت
CMD ["streamlit", "run", "main.py", "--server.port=80", "--server.address=0.0.0.0"]
