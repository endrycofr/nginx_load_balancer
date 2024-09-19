from flask import Flask

app1 = Flask(__name__)

@app1.route('/')
def hello_world():
    return 'Hi, this is App 2'

if __name__ == '__main__':
    app1.run(debug=True, host='0.0.0.0')

