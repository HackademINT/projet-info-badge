#! /usr/bin/python3 
from flask import Flask, render_template, render_template_string, redirect
from flask_sqlalchemy import SQLAlchemy
from flask import abort, flash, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from pathlib import Path 
from functools import wraps
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from config.db_acces import *
from config.functions import *

tokens = ["thesupertoken"]

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
    data = {}
    data['Badge']=Badge.query.filter_by(id_ldap_teacher=current_user.id_badge)
    return render_template('index.html', data=data)

@app.route("/tables")
@login_required
def loadTable(): 
    data = {}
    data['Badge']=Badge.query.filter_by(id_ldap_teacher=current_user.id_badge)
    return render_template('tables.html', data=data)

@app.route("/charts")
@login_required
def loadChart():
    data = {}
    data['Badge']=Badge.query.filter_by(id_ldap_teacher=current_user.id_badge)
    data['Module']=Module.query.all()
    return render_template('charts.html', data=data)

@app.route("/requete",methods=["POST"])
def addsession():
    message = request.form['message'].split(";")
    if len(message) != 4:
        return None
    id_badge_student, id_badge_teacher, date, token = message
    
    if not token in tokens:
        return None
    
    ldap_teacher = LdapUser.query.filter_by(id_badge=id_badge_teacher).first()
    if ldap_teacher:
        id_ldap_teacher = ldap_teacher.id 
    else:
        new_ldap_teacher = LdapUser(login=current_user.login,id_badge=ldap_teacher.id)
    
    ldap_student = LdapUser.query.filter_by(id_badge=id_badge_student).first()
    if ldap_student:
        id_ldap_student = ldap_student.id 
    else:
        #A Modifier
        id_ldap_student = LdapUser.query.all().first().id 

    badge = Badge(id_ldap_prof=id_ldap_teacher,id_ldap_student=id_ldap_student,date=date)
    db.add(badge)
    db.commit()

@app.route("/login",methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        if func_authenticate(request.form['inputLogin'],request.form['inputPassword']):
            ldap_user = LdapUser.query.filter_by(login=request.form['inputLogin']).first()
            if ldap_user is None:
                ldap_user = LdapUser(login=request.form['inputLogin'])
                db.session.add(ldap_user)
                db.session.commit()
            login_user(ldap_user)
            flash('Vous êtes connecté','success')
            return redirect('/')
        flash('Login ou mot de passe incorrect','error')
        return render_template('login.html')
    elif request.method == "GET":
        return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/<var1>")
@login_required
def relocate(var1):     
    if Path('config/templates/{}.html'.format(var1)).is_file():
        return render_template(var1+'.html')
    else:
        abort(404)

@app.errorhandler(404)
def erreur404(error): 
    return redirect(url_for('default'))

if __name__ == "__main__":
    db.create_all()
    app.run(host="0.0.0.0", port=3002, debug=True)
