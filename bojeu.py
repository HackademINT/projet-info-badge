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
import binascii
import re 
import datetime

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
    modules = db.session.query(Module).join(Badge).\
            filter_by(id_ldap_teacher=current_user.id, 
                      id_module=Module.id).filter(Module.id!=0).all()
    todo = Badge.query.distinct(Badge.timestamp).group_by(Badge.timestamp).filter_by(id_ldap_teacher=current_user.id).filter(Badge.id_module==0).count()
    return render_template('index.html', modules=modules, todo=todo)

@app.route("/tablessession")
@login_required
def loadTablesession():
    badges = Badge.query.distinct(Badge.timestamp).group_by(Badge.timestamp).filter_by(id_ldap_teacher=current_user.id)
    data = [(badge, binascii.hexlify(str(badge.timestamp).encode()).decode()) for badge in badges if badge.id_module]
    todo = [(badge, binascii.hexlify(str(badge.timestamp).encode()).decode()) for badge in badges if not badge.id_module]
    distinct_modules = db.session.query(Module).join(Badge).filter_by(id_ldap_teacher=current_user.id).filter(Badge.id_module!=0)
    return render_template('tablessession.html', data=data, todo=todo, modules=distinct_modules)

@app.route("/tablesusers/<var1>", methods=["GET","POST"])
@login_required
def loadTableusers(var1):
        data = {}
    #try:
        var=var1
        var1 = binascii.unhexlify(var1)
        tmp = re.findall(b'([1-9][0-9]*-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1]) (2[0-3]|[01][0-9]):[0-5][0-9]:[0-5][0-9])',var1)[0][0].decode()
        timestamp=datetime.datetime.strptime(tmp + '.000000','%Y-%m-%d %H:%M:%S.%f')
        badges = Badge.query.filter_by(timestamp=timestamp,id_ldap_teacher=current_user.id)
        if request.method == 'POST':
            try:
                #badge = Badge.query.filter_by(id=badges[0].module.id).first()
                for badge in list(badges):
                    badge.id_module = request.form['newModuleId']
                    db.session.commit()
                return redirect('/tablesusers/{}'.format(var))
            except Exception as e:
                flash("La base n'a pas pu être modifiée",'error')
                data['Badge']=badges
                data['Modules']=db.session.query(Module.nom, Module.id).join(Badge).filter_by(id_ldap_teacher=current_user.id).distinct(Module.id)
                return render_template('/tablesusers/{}'.format(var), data=data)
        data['Badge']=badges
        data['Modules']=db.session.query(Module.nom, Module.id).join(Badge).filter_by(id_ldap_teacher=current_user.id).distinct(Module.id)
        return render_template('tablesusers.html', data=data)
    #except Exception as e:
    #    flash("Le timestamp n'est pas valide",'error')
    #    return redirect('/tablessession')

@app.route("/charts")
@login_required
def loadChart():
    data = {}
    data['Badge']=Badge.query.filter_by(id_ldap_teacher=current_user.id)
    data['Module']=Module.query.all()
    return render_template('charts.html', data=data)

@app.route("/update-module", methods=["POST"])
@login_required
def update_session():
    kw = {'id_ldap_teacher': current_user.id, 'timestamp': request.form['timestamp']}
    badges = Badge.query.filter_by(**kw).all()
    for badge in badges:
        badge.id_module = request.form['module']
    db.session.commit()
    flash('La session du {} a bien été associée au module {}'.format(request.form['timestamp'], 
                 Module.query.get(request.form['module']).nom))
    return redirect('/tablessession')

@app.route("/requete",methods=["POST"])
def addsession():
    message = request.data.decode()
    print(message)
    message = message.split(";")
    if len(message) != 4:
        return None
    id_badge_student, id_badge_teacher, date, token = message
    id_badge_student = int(id_badge_student, 16)
    id_badge_teacher = int(id_badge_teacher, 16)
    date=datetime.datetime.strptime(date + '.000000','%Y-%m-%d %H:%M:%S.%f')
    ldap_teacher = LdapUser.query.filter_by(id_badge=id_badge_teacher).first()
    #if not(ldap_teacher):
    #    ldap_teacher = LdapUser(id_badge=id_badge_teacher)
    id_ldap_teacher = ldap_teacher.id 
    ldap_student = LdapUser.query.filter_by(id_badge=id_badge_student).first()
    if ldap_student:
        id_ldap_student = ldap_student.id 
    else:
        #A Modifier
        id_ldap_student = LdapUser.query.first().id 
    badge = Badge(id_ldap_teacher=id_ldap_teacher,id_ldap_student=id_ldap_student,timestamp=date,id_module=0)
    db.session.add(badge)
    db.session.commit()

@app.route("/login",methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        if func_authenticate(request.form['inputLogin'],request.form['inputPassword']):
            login = request.form['inputLogin'].lower()
            ldap_user = LdapUser.query.filter_by(login=login).first()
            if ldap_user is None:
                ldap_user = LdapUser(login=login)
                ldap_user.id_badge = ldap_user.id
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

@app.route("/module/<id_mod>")
@login_required
def module(id_mod): 
    nomModule = db.session.query(Module).get(id_mod).nom
    eleves = db.session.query(LdapUser.login).\
            join(Badge, Badge.id_ldap_student==LdapUser.id).filter_by(id_module=id_mod).all()
    eleves = [eleve[0] for eleve in eleves]
    eleves_distinct = list(set([(eleve, eleves.count(eleve)) for eleve in eleves]))
    liste_eleves = [eleve[0] for eleve in eleves_distinct]
    liste_presences = [eleve[1] for eleve in eleves_distinct]
    return render_template('module.html', nomModule=nomModule,
                           labels=liste_eleves, data=liste_presences)

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
    app.run(host="0.0.0.0", port=8083, debug=True)
