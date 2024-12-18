# Gunakan Python 3.9 Slim sebagai base image
FROM python:3.9-slim

# Set working directory di dalam container
WORKDIR /app

# Salin file requirements terlebih dahulu
COPY requirements.txt .

# Instal dependencies Python
RUN pip install --no-cache-dir -r requirements.txt

# Salin semua file aplikasi ke dalam container
COPY . .

# Salin script wait-for-it untuk sinkronisasi dengan database
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh  # Berikan izin eksekusi pada script

# Tambahkan user non-root untuk keamanan (opsional)
RUN useradd -ms /bin/bash appuser
USER appuser

# Jalankan aplikasi hanya setelah database siap
CMD ["sh", "-c", "/wait-for-it.sh db:3306 -- python app1.py"]
