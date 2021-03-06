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
from config.superadmins import superadmins
import binascii
import re 
import datetime
import json
import config.secret


def super_admin_required(f):                                                          
    @wraps(f)                                                                   
    def decorated_function(*args, **kwargs):                                    
        if not current_user.login in superadmins:                                   
            flash('Pour ajouter des administrateurs, veiuillez vous référer à un super administrateur','error')
            return redirect('/')                                           
        return f(*args, **kwargs)                                               
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def coordinator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if len(current_user.coordonnated) == 0:
            flash('Vous n\'avez pas les droits pour accéder à cette page', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/nouvel_admin', methods=["GET","POST"])
@login_required
@admin_required
@super_admin_required
def nouvel_admin():
    data = {}
    data['admins'] = LdapUser.query.filter_by(is_admin=1).all()
    if request.method == "POST":
        if not 'admin'in request.form and not "desadmin" in request.form:
            flash('La requête n\'est pas valide','error')
            return render_template("nouvel_admin.html", data=data)

        if 'admin' in request.form:
            user = LdapUser.query.filter_by(login=request.form['admin']).first()
            if user == None:
                nouvel_admin = LdapUser(login=request.form['admin'], is_admin=1)
                db.session.add(nouvel_admin)
                db.session.commit()
                user = LdapUser.query.filter_by(login=request.form['admin']).first()
            else:
                user.is_admin = 1
            modules_id = [ i.id for i in Module.query.all() ]
            for i in modules_id:
                newmodule = CoordonnatorModules(ldap_user_id=user.id, module_id=i)
                db.session.add(newmodule)

            db.session.commit()
            flash('Administrateur ajouté','success')
            return redirect("/nouvel_admin")
        
        if 'desadmin' in request.form:
            try:
                id_admin = int(request.form['desadmin'])
            except:
                flash('Une erreur est survenue','error')
                return render_template("nouvel_admin.html", data=data)
            user = LdapUser.query.get(id_admin)
            if user == None:
                flash('Une erreur est survenue','error')
                return render_template("/nouvel_admin")
            user.is_admin = 0
            for i in CoordonnatorModules.query.filter_by(ldap_user_id=user.id).all():
                db.session.delete(i)

            db.session.commit()
            flash('Administrateur retiré','success')
            return redirect("/nouvel_admin")

    return render_template("nouvel_admin.html", data=data)


@app.route("/")
@login_required
def default():
    data = {}
    data['todo'] = Session.query.filter_by(id_ldap_teacher=current_user.id).filter(Session.id_module==0).count()
    data['modules'] = Session.query.distinct(Session.id_module).filter_by(id_ldap_teacher=current_user.id).group_by(Session.id_module).filter(Session.id_module>0)
    return render_template('index.html', data=data)


@app.route("/coordonnateur")
@login_required
@coordinator_required
def loadCoordonnateur():
    data = {}
    data['modules'] = current_user.coordonnated
    return render_template('coordonnateur.html', data=data)


@app.route("/tablessession", methods=["GET","POST"])
@login_required
def loadTablesession():
    data = {}
    session = Session.query.filter_by(id_ldap_teacher=current_user.id).all()
    data['defined'] = [ses for ses in session if ses.id_module]
    data['undefined'] = [ses for ses in session if not ses.id_module]
    data['modules'] = Module.query.filter(Module.id>0)
    if request.method == 'POST':
        if request.form['type'] == "moduleid":
            if request.form['id_session'] in [str(i.id_session) for i in Session.query.all()] and request.form['newModuleId'] in [str(i.id) for i in Module.query.all()]:
                Session.query.get(int(request.form['id_session'])).id_module = int(request.form['newModuleId'])
                db.session.commit()
                flash('La session a été mise à jour','success') 
            else:
                flash("Les sessions n'existent pas",'error')

        if request.form['type'] == 'description':
            if request.form['id_session'] in [str(i.id_session) for i in Session.query.all()]:
                if len(request.form['newDescription']) <= 100:
                    Session.query.get(int(request.form['id_session'])).description = request.form['newDescription']
                    db.session.commit()
                    flash('La session a été mise à jour','success') 
                else:
                    flash('Le commentaire est trop long','error')
            else: 
                flash('La session n\'existe pas','error')
        return redirect('tablessession')
    return render_template('tablessession.html', data=data)


@app.route("/tablesusers/<var1>", methods=["GET","POST"])
@login_required
def loadTableusers(var1):
    data = {}
    sessions = [ i.id_session for i in Session.query.filter_by(id_ldap_teacher=current_user.id).all() ]
    sessions += [ i.id_session for i in Session.query.all() if i.id_module in [ i.id for i in current_user.coordonnated ]]
    if not int(var1) in sessions:
        flash('Vous n\'avez pas les droits pour accéder à cette page', 'error')
        return redirect('/tablessession')

    try:
        timestamp = Session.query.get(var1).timestamp
        data['Badge']=Badge.query.join(Session).filter_by(id_session=var1).all()
        data['Modules']=db.session.query(Module.nom, Module.id).filter(Module.id!=0).distinct(Module.id)
        if request.method == 'POST':
            if request.form['type'] == 'moduleid':
                if request.form['newModuleId'] in [str(i.id) for i in Module.query.filter(Module.id>0).all()]:
                    Session.query.get(int(var1)).id_module = int(request.form['newModuleId'])
                    db.session.commit()
                    flash('La session a été mise à jour','success') 
                else:
                        flash('Veuillez sélectionner un module valide','error')

            if request.form['type'] == 'description':
                if len(request.form['newDescription']) <= 100:
                    Session.query.get(int(var1)).description = request.form['newDescription']
                    db.session.commit()
                    flash('La session a été mise à jour','success') 
                else:
                        flash('Le commentaire est trop long','error')
        return render_template('tablesusers.html',data=data)
    except Exception as e:
        flash("L'url n'est pas valide",'error')
    return redirect('tablesusers/{}'.format(var1))         

@app.route("/requete",methods=["POST"])
def addsession():
    try:
        premess = hex(pow(int(request.data.decode()), config.secret.d, config.secret.n))[2:]
        if len(premess)%2:
            premess = "0" + premess
        message = binascii.unhexlify(premess).decode().split(";")
        if len(message) != 3:
            return None
        id_badge_student, id_badge_teacher, date = message
        id_badge_student = int(id_badge_student, 16)
        id_badge_teacher = int(id_badge_teacher, 16)
        date=datetime.datetime.strptime(date + '.000000','%Y-%m-%d %H:%M:%S.%f')
        ldap_teacher = LdapUser.query.filter_by(id_badge=id_badge_teacher).first()
        id_ldap_teacher = ldap_teacher.id 
        ldap_student = LdapUser.query.filter_by(id_badge=id_badge_student).first()
        id_ldap_student = ldap_student.id 

        if not(Session.query.filter_by(id_ldap_teacher = id_ldap_teacher, timestamp=date).first()): 
            session = Session(timestamp=date,id_module=0,id_ldap_teacher=id_ldap_teacher)
            db.session.add(session)
            db.session.commit()

        id_session = Session.query.filter_by(id_ldap_teacher=id_ldap_teacher, timestamp=date).first().id_session
        
        if not(Badge.query.filter_by(id_session=id_session, id_ldap_student=id_ldap_student).first()):   
            badge = Badge(id_session=id_session,id_ldap_student=id_ldap_student)
            db.session.add(badge)
            db.session.commit()
        return render_template('index.html')
    except:
        pass

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

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route("/module/<id_mod>")
@login_required
def loadmodule(id_mod): 
    data = {}
    data['module'] = Module.query.get(id_mod)
    data['eleves'] = Badge.query.join(Session).filter_by(id_module=id_mod, id_ldap_teacher=current_user.id)
    noms = [eleve.ldap_student.login for eleve in data['eleves']]
    distinct_eleves = list(set([(eleve,noms.count(eleve)) for eleve in noms]))
    distinct_eleves.sort(key=lambda x:x[1])
    data['labels'] = [i[0] for i in distinct_eleves]
    data['data'] = [i[1] for i in distinct_eleves]
    return render_template('module.html', data=data)

@app.route("/coordonnateur-module/<id_mod>", methods=["GET", "POST"])
@login_required
@coordinator_required
def coordonnateur_module(id_mod): 
    module = db.session.query(Module).get(id_mod)
    if module in current_user.coordonnated:
        data = {}
        data['module'] = module
        intervenants = Session.query.filter_by(id_module=id_mod).distinct(Session.id_ldap_teacher).group_by(Session.id_ldap_teacher)
        data['intervenants'] = [{'user': intervenant, 
                      'nb_sessions': Session.query.filter_by(id_module=id_mod, id_ldap_teacher=intervenant.id_ldap_teacher).count()} for intervenant in intervenants]
        eleves = [i.ldap_student.login for i in Badge.query.join(Session).filter_by(id_module=id_mod)]
        distinct_eleves = list(set([(eleve,eleves.count(eleve)) for eleve in eleves])) 
        distinct_eleves.sort(key=lambda x:x[1])
        data['labels'] = [i[0] for i in distinct_eleves]
        data['data'] = [i[1] for i in distinct_eleves]
        return render_template('coordonnateur-module.html', data=data)
    else:
        flash('Vous n\'avez pas les droits pour accéder à cette page', 'error')
        return redirect('/')


@app.route("/intervenant/<id_module>/<id_user>")
@login_required
@coordinator_required
def user_table(id_module, id_user):
    data = {}
    module = Module.query.get(id_module)
    if module in current_user.coordonnated:
        data['module'] = module
        data['intervenant'] = LdapUser.query.get(id_user)
        list_session = Session.query.filter_by(id_ldap_teacher=id_user, id_module=id_module).distinct(Session.id_session)
        data['presences'] = [Badge.query.filter_by(id_session=i.id_session).count() for i in list_session]
        data['sessions'] = [{'timestamp': list_session[i].timestamp, 'presence': data['presences'][i], 'description': list_session[i].description, 'id_session': list_session[i].id_session} for i in range(len(list_session.all()))]
        return render_template('intervenant.html', data=data)
    else:
        flash('Vous n\'avez pas les droits pour accéder à cette page', 'error')
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
    for superadmin in superadmins:
        newsuperadmin = LdapUser.query.filter_by(login=superadmin).first()
        if newsuperadmin == None:
            newsuperadmin = LdapUser(login=superadmin, is_admin=1)
            db.session.add(newsuperadmin)
            db.session.commit()

            newsuperadmin = LdapUser.query.filter_by(login=superadmin).first()

            modules_id = [ i.id for i in Module.query.all() ]
            for i in modules_id:
                newmodule = CoordonnatorModules(ldap_user_id=newsuperadmin.id, module_id=i)
                db.session.add(newmodule)
            db.session.commit()
    app.run(host="0.0.0.0", port=3002, debug=True)
