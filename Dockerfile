# استخدام نسخة بايثون خفيفة ومستقرة
FROM python:3.12-slim

# تثبيت مكتبات النظام اللازمة للخرائط (GDAL)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgdal-dev \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# تعيين متغيرات البيئة لـ GDAL
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# مجلد العمل
WORKDIR /app

# نسخ ملف المتطلبات أولاً للاستفادة من الـ Cache
COPY requirements.txt .

# تثبيت مكتبات بايثون
RUN pip install --no-cache-dir -r requirements.txt

# نسخ ملفات التطبيق
COPY . .

# سيتم نسخ البيانات في خطوة الرفع
# COPY assets /app/gis_assets

# تعيين المنفذ الافتراضي (Cloud Run يستخدم 8080)
EXPOSE 8080

# تشغيل Streamlit مع إعدادات السيرفر
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
