import os
import time
from flask import Flask, request, jsonify, Response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
import prometheus_client
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# Prometheus Metrics initialization
metrics = PrometheusMetrics(app)

# Konfigurasi Database dari environment variable
db_uri = os.getenv('DB_URI', 'mysql+mysqlconnector://flask_user:password@db/flask_app_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)

# Model Database Absensi
class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nrp = db.Column(db.String(20), nullable=False)
    nama = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nrp': self.nrp,
            'nama': self.nama,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }

# Fungsi untuk menunggu koneksi database
def wait_for_database(max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            # Coba koneksi dengan database
            with db.engine.connect() as connection:
                return True
        except Exception as e:
            print(f"Database connection attempt {attempt + 1} failed: {e}")
            time.sleep(delay)
    return False

# Create database tables only when database connection is established
def create_tables():
    try:
        db.create_all()
        print("Tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")

# Health Check Route
@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Cek koneksi database
        db.session.execute('SELECT 2')
        return jsonify({
            'status': 'healthy',
            'app_number': os.getenv('APP_NUMBER', '2')
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# Route untuk menambah Absensi
@app.route('/absensi', methods=['POST'])
def create_absensi():
    try:
        app_number = os.getenv('APP_NUMBER', 2)
        ip_address = request.remote_addr
        data = request.json

        if not data or 'nrp' not in data or 'nama' not in data:
            return jsonify({'message': 'Input tidak valid'}), 400

        new_absensi = Absensi(nrp=data['nrp'], nama=data['nama'])
        db.session.add(new_absensi)
        db.session.commit()

        return jsonify({
            'message': 'Absensi berhasil ditambahkan',
            'data': new_absensi.to_dict(),
            'app': app_number,
            'ip_address': ip_address
        }), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'message': 'Gagal menambahkan absensi',
            'error': str(e)
        }), 500

# Route untuk mendapatkan semua Absensi
@app.route('/absensi', methods=['GET'])
def get_absensi():
    try:
        app_number = os.getenv('APP_NUMBER', 2)
        ip_address = request.remote_addr
        absensi_list = Absensi.query.all()

        return jsonify({
            'data': [absensi.to_dict() for absensi in absensi_list],
            'app': app_number,
            'ip_address': ip_address
        }), 200

    except SQLAlchemyError as e:
        return jsonify({
            'message': 'Gagal mengambil data absensi',
            'error': str(e)
        }), 500

# Route untuk memperbarui Absensi
@app.route('/absensi/<int:id>', methods=['PUT'])
def update_absensi(id):
    try:
        app_number = os.getenv('APP_NUMBER', 2)
        ip_address = request.remote_addr
        data = request.json

        absensi = Absensi.query.get(id)
        if not absensi:
            return jsonify({'message': 'Absensi tidak ditemukan'}), 404

        absensi.nrp = data.get('nrp', absensi.nrp)
        absensi.nama = data.get('nama', absensi.nama)
        db.session.commit()

        return jsonify({
            'message': 'Absensi berhasil diperbarui',
            'data': absensi.to_dict(),
            'app': app_number,
            'ip_address': ip_address
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'message': 'Gagal memperbarui absensi',
            'error': str(e)
        }), 500

# Route untuk menghapus Absensi
@app.route('/absensi/<int:id>', methods=['DELETE'])
def delete_absensi(id):
    try:
        app_number = os.getenv('APP_NUMBER', 2)
        ip_address = request.remote_addr

        absensi = Absensi.query.get(id)
        if not absensi:
            return jsonify({'message': 'Absensi tidak ditemukan'}), 404

        db.session.delete(absensi)
        db.session.commit()

        return jsonify({
            'message': 'Absensi berhasil dihapus',
            'app': app_number,
            'ip_address': ip_address
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({
            'message': 'Gagal menghapus absensi',
            'error': str(e)
        }), 500

# Route untuk Prometheus Metrics
@app.route(f'/metrics/{os.getenv("APP_NUMBER", 2)}', methods=['GET'])
def prometheus_metrics():
    # Register custom metrics
    return Response(prometheus_client.generate_latest(), mimetype='text/plain')

if __name__ == '__main__':
    # Tunggu koneksi database dengan timeout
    if wait_for_database():
        create_tables()  # Create tables after database is connected
        app.run(host='0.0.0.0', port=5000)
    else:
        print("Tidak dapat terhubung ke database. Aplikasi berhenti.")
        exit(1)
