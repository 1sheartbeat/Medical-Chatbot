from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return '<h1 style="color: blue; font-size: 48px;">Hello! Server is working!</h1><p style="font-size: 20px;">If you see this, Flask is running correctly.</p>'

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)