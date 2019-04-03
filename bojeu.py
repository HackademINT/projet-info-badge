#! /usr/bin/python3 
from flask import Flask, render_template, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import abort
from flask import request
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path 
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'LIncroyableCleDuBoJeu'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class Module(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    nom       = db.Column(db.String(80),nullable=False)

class Badge(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    id_badge  = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    id_module = db.Column(db.Integer(), db.ForeignKey('module.id', ondelete='CASCADE'))

class User(UserMixin,db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    email     = db.Column(db.String(80),nullable=False)
    password  = db.Column(db.String(255),unique=True,nullable=False)
    role      = db.relationship('Role', secondary='user_roles')

class Role(db.Model):
    id        = db.Column(db.Integer(), primary_key=True)
    name      = db.Column(db.String(50), unique=True)

class UserRoles(db.Model):
    id        = db.Column(db.Integer(), primary_key=True)
    user_id   = db.Column(db.Integer(), db.ForeignKey('user.id', ondelete='CASCADE'))
    role_id   = db.Column(db.Integer(), db.ForeignKey('role.id', ondelete='CASCADE'))

@login_manager.user_loader
def load_user(user_id):
        return User.query.get(int(user_id))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
@login_required
def default():
    return render_template('index.html')

@app.route("/tables")
@login_required
def loadTable(): 
    return render_template('tables.html', Badge=Badge.query.all())

@app.route("/charts")
@login_required
def loadChart():
    return render_template('charts.html', Badge=Badge.query.all(), Module = Module.query.all())


@app.route("/login",methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form['inputEmail']).first()
        if user:
            if check_password_hash(user.password,request.form['inputPassword']):
                login_user(user)
                return redirect('/')
        return render_template('login.html', error=True)
    elif request.method == "GET":
        return render_template('login.html')

@app.route("/forgot-password", methods=["GET","POST"])
def forgot_page():
    if request.method == "POST":
        pass
    elif request.method == "GET":
        return render_template('forgot-password.html')
@app.route("/logout")
@login_required
def logout():
        logout_user()
        return redirect('/')

@app.route("/<var1>")
@login_required
def relocate(var1):     
    if Path('templates/{}.html'.format(var1)).is_file():
        return render_template(var1+'.html')
    else:
        abort(404)

@app.errorhandler(404)
def erreur404(error): 
    return render_template('404.html')

if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0",port=3002)
