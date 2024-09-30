# Gunakan image Python sebagai base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Salin file requirements.txt dan instal dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi ke dalam container
COPY app1.py .

# Jalankan aplikasi
CMD ["python", "app1.py"]
