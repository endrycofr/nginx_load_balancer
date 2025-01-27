<<<<<<< HEAD
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

=======
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
>>>>>>> 29b4750f76282410e5b7952fdb20a63756a5fc0e
CMD ["python", "app1.py"]
