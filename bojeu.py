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
import json
import config.secret


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function


def coordinator_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if len(current_user.module_coordinated) == 0:
            flash('Vous n\'avez pas les droits pour accéder à cette page', 'error')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
@login_required
def default():
    modules = current_user.module_accessible
    todo = Badge.query.distinct(Badge.timestamp).group_by(Badge.timestamp).filter_by(id_ldap_teacher=current_user.id).filter(Badge.id_module==0).count()
    return render_template('index.html', modules=modules, todo=todo)


@app.route("/coordinateur")
@login_required
@coordinator_required
def coordinateur():
    modules = db.session.query(Module).join(Badge).\
            filter_by(id_module=Module.id).filter(Module.id!=0).all()
    modulesCoordinated = [module for module in modules if module in current_user.module_coordinated]
    return render_template('coordinateur.html', modules=modulesCoordinated)


@app.route("/tablessession")
@login_required
def loadTablesession():
    badges = Badge.query.distinct(Badge.timestamp).group_by(Badge.timestamp).filter_by(id_ldap_teacher=current_user.id)
    data = [(badge, binascii.hexlify(str(badge.timestamp).encode()).decode()) for badge in badges if badge.id_module]
    todo = [(badge, binascii.hexlify(str(badge.timestamp).encode()).decode()) for badge in badges if not badge.id_module]
    distinct_modules = current_user.module_accessible
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
        #for mod in current_user.module_coordinated:
        #    badges += [Badge.query.filter_by(timestamp=timestamp,module=mod).filter(Badge.id_ldap_teacher!=current_user.id).all]
        if request.method == 'POST':
            try:
                if request.form['newModuleId'] in [str(i.id) for i in current_user.module_accessible]: 
                #return redirect('/tablesusers/{}'.format(var))
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
        data['Modules']=db.session.query(Module.nom, Module.id).join(Badge).filter_by(id_ldap_teacher=current_user.id).filter(Module.id!=0).distinct(Module.id)
        data['Modules'] = [(mod.nom, mod.id) for mod in current_user.module_accessible]
        return render_template('tablesusers.html', data=data)
    #except Exception as e:
    #    flash("L'url n'est pas valide",'error')
        return redirect('/tablessession')


@app.route("/update-module", methods=["POST"])
@login_required
def update_session():
    id_module = request.form['module']
    if not(id_module in [str(i.id) for i in current_user.module_accessible]):
        flash('Veuillez sélectionner un module valide', 'error')
    else:
        kw = {'id_ldap_teacher': current_user.id, 
              'timestamp': datetime.datetime.strptime(request.form['timestamp']+ '.000000','%Y-%m-%d %H:%M:%S.%f')}
        badges = Badge.query.filter_by(**kw).all()
        for badge in badges:
            badge.id_module = id_module
        db.session.commit()
        flash('La session du {} a bien été associée au module {}'.format(request.form['timestamp'], Module.query.get(request.form['module']).nom))
    return redirect('/tablessession')



@app.route("/requete",methods=["POST"])
def addsession():
    #try:
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
        #if not(ldap_teacher):
        #    ldap_teacher = LdapUser(id_badge=id_badge_teacher)
        id_ldap_teacher = ldap_teacher.id 
        ldap_student = LdapUser.query.filter_by(id_badge=id_badge_student).first()
        #if ldap_student:
        id_ldap_student = ldap_student.id 
        #else:
            #A Modifier
            #id_ldap_student = LdapUser.query.first().id 
        if not(Badge.query.filter_by(id_ldap_teacher = id_ldap_teacher, id_ldap_student=id_ldap_student, timestamp=date).first()):   
            badge = Badge(id_ldap_teacher=id_ldap_teacher,id_ldap_student=id_ldap_student,timestamp=date,id_module=0)
            db.session.add(badge)
            db.session.commit()
        return render_template('index.html')
    #except:
    #    pass


    
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


@app.route("/coordinateur-module/<id_mod>", methods=["GET", "POST"])
@login_required
@coordinator_required
def coordinateur_module(id_mod): 
    # charge module
    module = db.session.query(Module).get(id_mod)
    
    # charge les intervenants du module
    intervenants = [intervenant for intervenant in LdapUser.query.all() if module in intervenant.module_accessible]
    intervenants_data = [{'user': intervenant, 
                  'nb_sessions': db.session.query(Badge.timestamp).filter_by(id_module=id_mod, id_ldap_teacher=intervenant.id).distinct(Badge.timestamp).count()} for intervenant in intervenants]

    # charge les eleves enregistres du module
    eleves = db.session.query(LdapUser.login).\
            join(Badge, Badge.id_ldap_student==LdapUser.id).filter_by(id_module=id_mod).all()
    eleves = [eleve[0] for eleve in eleves]
    eleves_distinct = list(set([(eleve, eleves.count(eleve)) for eleve in eleves]))
    liste_eleves = [eleve[0] for eleve in eleves_distinct]
    liste_presences = [eleve[1] for eleve in eleves_distinct]

    # cas requete post
    if request.method == "POST":
        intervenant_change = LdapUser.query.get(request.form["id_ldap_intervenant"])
        if intervenant_change in intervenants:
            UserModules.query.filter_by(ldap_user_id=request.form["id_ldap_intervenant"], module_id=id_mod).delete()
        else:
            new_entry = UserModules(ldap_user=LdapUser.query.get(request.form["id_ldap_intervenant"]), module=Module.query.get(id_mod))
            db.session.add(new_entry)
        db.session.commit()

        intervenants = [intervenant for intervenant in LdapUser.query.all() if module in intervenant.module_accessible]
        intervenants_data = [{'user': intervenant, 
                      'nb_sessions': db.session.query(Badge.timestamp).filter_by(id_module=id_mod, id_ldap_teacher=intervenant.id).distinct(Badge.timestamp).count()} for intervenant in intervenants]
    
    # charge intervenants non ajoutes
    intervenants_possibles = [user for user in LdapUser.query.all() if user not in intervenants]
    return render_template('coordinateur-module.html', module=module,
                           intervenants=intervenants_data, 
                           possible=intervenants_possibles, 
                           labels=liste_eleves, data=liste_presences)


@app.route("/intervenant/<id_module>/<id_user>")
@login_required
@coordinator_required
def user_table(id_module, id_user):     
    module = Module.query.get(id_module)
    intervenant = LdapUser.query.get(id_user)
    timestamps = db.session.query(Badge.timestamp).filter_by(id_ldap_teacher=id_user, id_module=id_module).distinct(Badge.timestamp, Badge.id_ldap_teacher).all()
    presences = [db.session.query(Badge).filter_by(timestamp=t[0], id_module=id_module, id_ldap_teacher=id_user).count() for t in timestamps]
    sessions = [{'timestamp': timestamps[i][0], 'presence': presences[i]} for i in range(len(timestamps))]
    return render_template('intervenant.html', module=module, intervenant=intervenant,
                           sessions=sessions)


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
