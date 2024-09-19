# Gunakan image dasar Python 3.8
FROM python:3

# Salin file requirements.txt ke direktori root di dalam image
COPY requirements.txt /requirements.txt

# Atur direktori kerja
WORKDIR /app

# Install dependensi dari requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Salin seluruh kode aplikasi ke direktori kerja
COPY . /app

# Tentukan perintah untuk menjalankan aplikasi
ENTRYPOINT ["python3"]
CMD ["app3.py"]
