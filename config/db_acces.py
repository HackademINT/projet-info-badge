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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///badge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
login_manager = LoginManager()
login_manager.init_app(app)


class Module(db.Model):
    __tablename__   = 'module'
    id              = db.Column(db.Integer, primary_key=True)
    nom             = db.Column(db.String(80),nullable=False)
    def __repr__(self):
        return self.nom


class Badge(db.Model):
    __tablename__   = 'badge'
    id              = db.Column(db.Integer, primary_key=True)
    
    id_ldap_student = db.Column(db.Integer, db.ForeignKey('ldap_user.id', ondelete='CASCADE'))
    ldap_student    = db.relationship('LdapUser', foreign_keys=[id_ldap_student])

    id_session      = db.Column(db.Integer, db.ForeignKey('session.id_session', ondelete='CASCADE'))
    session         = db.relationship('Session', foreign_keys=[id_session])
    def __repr__(self):
        return '<{} {} ({} {}): {} >' .format(self.session.ldap_teacher.login, self.session.timestamp,
                                              self.session.id_module, self.session.module.nom, 
                                              self.ldap_student.login)


class Session(db.Model):
    __tablename__   = 'session'
    
    id_session      = db.Column(db.Integer, primary_key=True)   
    
    timestamp       = db.Column(db.DateTime, nullable=False)

    module          = db.relationship('Module')
    id_module       = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=False)
    
    id_ldap_teacher = db.Column(db.Integer, db.ForeignKey('ldap_user.id'), nullable=False)
    ldap_teacher    = db.relationship('LdapUser', foreign_keys=[id_ldap_teacher])
    
    description     = db.Column(db.String(300))
    def __repr__(self):
        return '<{} ({}:{})>'.format(self.ldap_teacher.login, self.module.nom, self.timestamp)
class LdapUser(db.Model, UserMixin):
    __tablename__     = 'ldap_user'
    id                = db.Column(db.Integer, primary_key=True)
    login             = db.Column(db.String(80), nullable=False)
    id_badge          = db.Column(db.Integer, unique=True)#,nullable=False)
    is_admin          = db.Column(db.Boolean, nullable=False)
    coordonnated      = db.relationship('Module', secondary='coordonnator_modules')

    def __repr__(self):
        return self.login

class CoordonnatorModules(db.Model):
    __tablename__     = 'coordonnator_modules'
    id                = db.Column(db.Integer, primary_key=True)
    
    ldap_user         = db.relationship('LdapUser')
    ldap_user_id      = db.Column(db.Integer, db.ForeignKey('ldap_user.id',ondelete='CASCADE'))
    
    module            = db.relationship('Module')
    module_id         = db.Column(db.Integer, db.ForeignKey('module.id', ondelete='CASCADE'))

# set optional bootswatch theme
# app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'

class MyAdminView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')
            return redirect("/")


class ModuleModelView(ModelView):                                                 
    page_size = 20                                                               
    column_searchable_list = ['nom']                         
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')

class BadgeModelView(ModelView):                                                 
    page_size = 20                                                              
    column_searchable_list = ['session.ldap_teacher.login','ldap_student.login', 'session.timestamp','session.module.nom'] 
    column_default_sort = ('session.timestamp', True)
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')

class SessionModelView(ModelView):                                                 
    page_size = 20                                                              
    column_searchable_list = ['timestamp','ldap_teacher.login','module.nom','description'] 
    column_default_sort = ('timestamp', True)
    column_sortable_list = ['timestamp']
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')

class CoordonnatorModelView(ModelView):                                                 
    page_size = 20                                                              
    column_searchable_list = ['ldap_user.login', 'module.nom'] 
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')


class LdapUserModelView(ModelView):                                                 
    page_size = 20                                                              
    column_searchable_list = ['login', 'id_badge'] 
    column_exclude_list = []                                                    
    form_excluded_columns = []                                                                                                                                  
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    def inaccessible_callback(self, name, **kwargs):
        flash('Accès interdit ! Merci de vous identifier.', 'error')
        return redirect(url_for('login_page'))
    def _handle_view(self, name, *args, **kwargs):
        if not self.is_accessible():
            flash('Accès interdit ! Merci de vous identifier.', 'error')

@login_manager.user_loader
def get_user(user_id):
    return LdapUser.query.get(int(user_id))


admin = Admin(app, name='Base de données', template_mode='bootstrap3',index_view=MyAdminView(url='/admin'))                             
admin.add_view(LdapUserModelView(LdapUser, db.session))
admin.add_view(ModuleModelView(Module, db.session))                                 
admin.add_view(BadgeModelView(Badge, db.session))                               
admin.add_view(SessionModelView(Session, db.session))                               
admin.add_view(CoordonnatorModelView(CoordonnatorModules, db.session))
