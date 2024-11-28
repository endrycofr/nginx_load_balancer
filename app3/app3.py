import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Konfigurasi Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://flask_user:password@db/flask_app_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model Database Absensi
class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nrp = db.Column(db.String(20), nullable=False)  # Nomor Registrasi Pegawai
    nama = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Buat Database dan Tabel
@app.before_first_request
def create_tables():
    db.create_all()

# Route untuk CRUD Absensi
@app.route('/absensi', methods=['POST'])
def create_absensi():
    app_number = os.getenv('APP_NUMBER', 3)  # Dynamically fetch the app number
    ip_address = request.remote_addr
    data = request.json
    new_absensi = Absensi(nrp=data['nrp'], nama=data['nama'])
    db.session.add(new_absensi)
    db.session.commit()
    return jsonify({
        'message': 'Absensi berhasil ditambahkan',
        'app': app_number,
        'ip_address': ip_address
    }), 201

@app.route('/absensi', methods=['GET'])
def get_absensi():
    app_number = os.getenv('APP_NUMBER', 3)  # Dynamically fetch the app number
    ip_address = request.remote_addr
    absensi_list = Absensi.query.all()
    return jsonify([{
        'id': absensi.id,
        'nrp': absensi.nrp,
        'nama': absensi.nama,
        'timestamp': absensi.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        'app': app_number,
        'ip_address': ip_address
    } for absensi in absensi_list])

@app.route('/absensi/<int:id>', methods=['PUT'])
def update_absensi(id):
    app_number = os.getenv('APP_NUMBER', 3)  # Dynamically fetch the app number
    ip_address = request.remote_addr
    data = request.json
    absensi = Absensi.query.get(id)
    if not absensi:
        return jsonify({'message': 'Absensi tidak ditemukan'}), 404
    absensi.nrp = data['nrp']
    absensi.nama = data['nama']
    db.session.commit()
    return jsonify({
        'message': 'Absensi berhasil diperbarui',
        'app': app_number,
        'ip_address': ip_address
    })

@app.route('/absensi/<int:id>', methods=['DELETE'])
def delete_absensi(id):
    app_number = os.getenv('APP_NUMBER', 3)  # Dynamically fetch the app number
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
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
