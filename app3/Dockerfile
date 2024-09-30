# Gunakan image Python sebagai base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Salin file requirements.txt dan instal dependensi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin kode aplikasi ke dalam container
COPY app3.py .

# Jalankan aplikasi
CMD ["python", "app3.py"]
