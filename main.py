from flask import Flask
from public import public
from admin import admin
from user import user
from worker import worker


app = Flask(__name__)
app.secret_key = "multiflex123"

app.register_blueprint(public)
app.register_blueprint(admin)
app.register_blueprint(user)
app.register_blueprint(worker)

if __name__ == "__main__":
    app.run(debug=True, port=5000)

