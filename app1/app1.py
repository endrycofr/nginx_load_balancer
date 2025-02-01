from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import time
import pytz
import logging
import psutil
import platform  # Missing import for platform version
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter, Histogram, Gauge, Summary
from sqlalchemy.exc import SQLAlchemyError
import threading
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Enhanced Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Enhanced Prometheus Metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application Info', version='1.0.0')

# Enhanced Request Metrics
REQUEST_COUNT = Counter(
    'flask_request_total',
    'Total number of requests',
    ['endpoint', 'method', 'status_code', 'service']
)

REQUEST_LATENCY = Summary(
    'flask_request_latency_seconds',
    'Request latency in seconds',
    ['endpoint', 'method', 'service'],
    percentiles=[0.5, 0.75, 0.90, 0.95, 0.99]
)

# Enhanced Error Metrics
ERROR_COUNT = Counter(
    'flask_error_total',
    'Total number of errors',
    ['endpoint', 'error_type', 'service']
)

# Enhanced Database Metrics
DB_CONNECTION_COUNT = Gauge(
    'flask_db_connections_current',
    'Number of active database connections'
)

DB_OPERATION_LATENCY = Histogram(
    'flask_db_operation_latency_seconds',
    'Database operation latency',
    ['operation', 'table'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

# Enhanced System Metrics
CPU_USAGE_GAUGE = Gauge(
    'system_cpu_usage_percent',
    'CPU usage percentage',
    ['core']
)

MEMORY_METRICS = {
    'total': Gauge('system_memory_total_bytes', 'Total memory in bytes'),
    'available': Gauge('system_memory_available_bytes', 'Available memory in bytes'),
    'used': Gauge('system_memory_used_bytes', 'Used memory in bytes'),
    'cached': Gauge('system_memory_cached_bytes', 'Cached memory in bytes'),
    'percent': Gauge('system_memory_usage_percent', 'Memory usage percentage')
}

DISK_METRICS = {
    'total': Gauge('system_disk_total_bytes', 'Total disk space in bytes'),
    'used': Gauge('system_disk_used_bytes', 'Used disk space in bytes'),
    'free': Gauge('system_disk_free_bytes', 'Free disk space in bytes'),
    'percent': Gauge('system_disk_usage_percent', 'Disk usage percentage')
}

# Application Metrics
APP_INFO = Gauge(
    'flask_app_info',
    'Application information',
    ['version', 'python_version', 'service']
)

REQUEST_IN_PROGRESS = Gauge(
    'flask_requests_in_progress',
    'Number of requests in progress',
    ['endpoint']
)

# Database Configuration
db_uri = os.getenv('DB_URI', 'mysql+mysqlconnector://flask_user:password@mysql/flask_app_db')
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 280,
    'pool_pre_ping': True,
    'pool_size': 20,
    'max_overflow': 5
}

db = SQLAlchemy(app)

# Database Connection Monitoring
@event.listens_for(Engine, 'connect')
def receive_connect(dbapi_connection, connection_record):
    DB_CONNECTION_COUNT.inc()

@event.listens_for(Engine, 'disconnect')
def receive_disconnect(dbapi_connection, connection_record):
    DB_CONNECTION_COUNT.dec()

# Enhanced System Metrics Collection
def update_system_metrics():
    while True:
        try:
            # CPU Metrics
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            for i, percent in enumerate(cpu_percent):
                CPU_USAGE_GAUGE.labels(core=f'core_{i}').set(percent)

            # Memory Metrics
            memory = psutil.virtual_memory()
            MEMORY_METRICS['total'].set(memory.total)
            MEMORY_METRICS['available'].set(memory.available)
            MEMORY_METRICS['used'].set(memory.used)
            MEMORY_METRICS['cached'].set(memory.cached)
            MEMORY_METRICS['percent'].set(memory.percent)

            # Disk Metrics
            disk = psutil.disk_usage('/')
            DISK_METRICS['total'].set(disk.total)
            DISK_METRICS['used'].set(disk.used)
            DISK_METRICS['free'].set(disk.free)
            DISK_METRICS['percent'].set(disk.percent)

            time.sleep(5)  # Update every 5 seconds
        except Exception as e:
            logger.error(f"Error updating system metrics: {e}")
            time.sleep(1)

# Start system metrics collection in background
metrics_thread = threading.Thread(target=update_system_metrics, daemon=True)
metrics_thread.start()

# Database Model with Monitoring
class Absensi(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nrp = db.Column(db.String(20), nullable=False, index=True)
    nama = db.Column(db.String(100), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(pytz.utc), index=True)

    def to_dict(self):
        local_timestamp = self.timestamp.astimezone(pytz.timezone('Asia/Jakarta'))
        return {
            'id': self.id,
            'nrp': self.nrp,
            'nama': self.nama,
            'timestamp': local_timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')
        }

# Enhanced Request Monitoring
@app.before_request
def before_request():
    request.start_time = time.time()
    if request.endpoint:
        REQUEST_IN_PROGRESS.labels(endpoint=request.endpoint).inc()

@app.after_request
def after_request(response):
    if request.endpoint:
        REQUEST_IN_PROGRESS.labels(endpoint=request.endpoint).dec()

    if hasattr(request, 'start_time'):
        latency = time.time() - request.start_time
        REQUEST_LATENCY.labels(
            endpoint=request.endpoint,
            method=request.method,
            service='absensi'
        ).observe(latency)

    REQUEST_COUNT.labels(
        endpoint=request.endpoint,
        method=request.method,
        status_code=response.status_code,
        service='absensi'
    ).inc()

    if response.status_code >= 400:
        ERROR_COUNT.labels(
            endpoint=request.endpoint,
            error_type=f'http_{response.status_code}',
            service='absensi'
        ).inc()

    return response

# Enhanced Error Monitoring for Database Operations
def monitor_db_operation(operation_name, table_name):
    def decorator(f):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                DB_OPERATION_LATENCY.labels(
                    operation=operation_name,
                    table=table_name
                ).observe(time.time() - start_time)
                return result
            except Exception as e:
                ERROR_COUNT.labels(
                    endpoint=request.endpoint,
                    error_type='database_error',
                    service='absensi'
                ).inc()
                raise
        return wrapper
    return decorator

# Routes with Enhanced Monitoring
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/metrics/custom')
def custom_metrics():
    return jsonify({
        'cpu_usage': psutil.cpu_percent(interval=1),
        'memory_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'active_db_connections': DB_CONNECTION_COUNT._value.get()
    })

@app.route('/health')
def health_check():
    try:
        with app.app_context():
            start_time = time.time()
            db.session.execute('SELECT 1')
            query_time = time.time() - start_time
            
            return jsonify({
                'status': 'healthy',
                'database_latency': f'{query_time:.3f}s',
                'app_number': os.getenv('APP_NUMBER', '1')
            }), 200
    except Exception as e:
        logger.error(f'Health check failed: {e}')
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@app.route('/absensi', methods=['POST'])
@monitor_db_operation('create', 'absensi')
def create_absensi():
    try:
        data = request.json
        if not data or 'nrp' not in data or 'nama' not in data:
            return jsonify({'message': 'Input tidak valid'}), 400

        new_absensi = Absensi(nrp=data['nrp'], nama=data['nama'])
        db.session.add(new_absensi)
        db.session.commit()

        return jsonify({
            'message': 'Absensi berhasil ditambahkan',
            'data': new_absensi.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in create_absensi: {e}')
        raise

@app.route("/absensi", methods=["GET"])
def get_absensi():
    try:
        absensi_list = Absensi.query.order_by(Absensi.timestamp.desc()).all()
        return jsonify(
            {
                "message": "Berhasil mengambil data absensi",
                "total": len(absensi_list),
                "data": [absensi.to_dict() for absensi in absensi_list],
            }
        ), 200
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error during get_absensi: {e}")
        return jsonify({"message": "Gagal mengambil data absensi", "error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error during get_absensi: {e}")
        return jsonify({"message": "Terjadi kesalahan tidak terduga", "error": str(e)}), 500

@app.route('/absensi/<int:id>', methods=['PUT'])
def update_absensi(id):
    try:
        absensi = Absensi.query.get(id)
        if not absensi:
            return jsonify({'message': 'Absensi tidak ditemukan'}), 404

        data = request.json
        absensi.nrp = data['nrp'] if 'nrp' in data else absensi.nrp
        absensi.nama = data['nama'] if 'nama' in data else absensi.nama
        db.session.commit()

        return jsonify({
            'message': 'Absensi berhasil diperbarui',
            'data': absensi.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f'Error in update_absensi: {e}')
        return jsonify({'message': 'Gagal memperbarui absensi'}), 500

if __name__ == "__main__":
    # Ensure database is ready before starting the app
    def wait_for_database():
        # Your database wait logic here (e.g., retry connection)
        pass

    # Initialize app and database
    wait_for_database()
    app.run(debug=True, host="0.0.0.0", port=5000)
