from flask import *

app = Flask(__name__)

@app.route('/')
@app.route('/homepage')
def home():
    return render_template("home.html")

if __name__ == '__main__':
    app.run(debug=True)