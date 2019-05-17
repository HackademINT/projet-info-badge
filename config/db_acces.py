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
from config.secret import secretkey
app = Flask(__name__)
db = SQLAlchemy(app)
app.config['SECRET_KEY'] = secretkey
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost/postgres'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)

class Module(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    nom             = db.Column(db.String(80),nullable=False)
    def __repr__(self):
        return self.nom

class Badge(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    
    id_ldap_teacher = db.Column(db.Integer, db.ForeignKey('ldap_user.id'), nullable=False)
    ldap_teacher    = db.relationship('LdapUser', foreign_keys=[id_ldap_teacher])
    
    id_ldap_student = db.Column(db.Integer, db.ForeignKey('ldap_user.id',ondelete='CASCADE'))#, nullable=False)
    ldap_student    = db.relationship('LdapUser', foreign_keys=[id_ldap_student])
    
    timestamp       = db.Column(db.DateTime, nullable=False)
    
    module          = db.relationship('Module')
    id_module       = db.Column(db.Integer(), db.ForeignKey('module.id'), nullable=False)
    def __repr__(self):
        return '<{} {} ({} {}): {} >' .format(self.ldap_teacher.login, self.timestamp,
                                              self.id_module, self.module.nom, 
                                              self.ldap_student.login)


class LdapUser(db.Model, UserMixin):
    id              = db.Column(db.Integer, primary_key=True)
    login           = db.Column(db.String(80), nullable=False)
    id_badge        = db.Column(db.Integer, unique=True)#,nullable=False)
    coordinated_module = db.relationship('Module', secondary='coordinator')
    def __repr__(self):
        return self.login

class Coordinator(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    id_coordinator  = db.Column(db.Integer, db.ForeignKey('ldap_user.id'))
    id_module       = db.Column(db.Integer, db.ForeignKey('module.id'))

# set optional bootswatch theme
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        print("test")
        return self.render('admin/index.html')
    def is_accessible(self):
        return current_user.is_authenticated
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login_page'))
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')

class ModuleModelView(ModelView):                                                 
    page_size = 20                                                               
    column_searchable_list = ['id', 'nom']                         
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):                                                    
        return current_user.is_authenticated                                    
    def inaccessible_callback(self, name, **kwargs):                            
        flash('Accès interdit ! Merci de vous identifier.', 'error')            
        return redirect(url_for('default'))

class BadgeModelView(ModelView):                                                 
    page_size = 20                                                              
    column_searchable_list = ['id_ldap_teacher','id_ldap_student', 'timestamp','id_module'] 
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):                                                    
        return current_user.is_authenticated                                    
    def inaccessible_callback(self, name, **kwargs):                            
        flash('Accès interdit ! Merci de vous identifier.', 'error')            
        return redirect(url_for('default'))

@login_manager.user_loader
def get_user(user_id):
    return LdapUser.query.get(int(user_id))

admin = Admin(app, name='Base de données', template_mode='bootstrap3',index_view=MyAdminView(url='/admin'))                             
admin.add_view(ModuleModelView(Module, db.session))                                 
admin.add_view(BadgeModelView(Badge, db.session))                               
