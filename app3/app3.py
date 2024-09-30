from flask import Flask, Response
import prometheus_client

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    # Menghasilkan data metrics untuk Prometheus
    return Response(prometheus_client.generate_latest(), mimetype=prometheus_client.CONTENT_TYPE_LATEST)

@app.route('/')
def hello_world():
    return 'Hello, World! 3'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  # Pastikan portnya sesuai
