import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_bootstrap import Bootstrap4
from flask_ckeditor import CKEditor
from flask_login import UserMixin, LoginManager, login_user, current_user, login_required, logout_user
from flask_modals import Modal
from flask_modals import render_template_modal
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from forms import LoginForm, RegisterForm, CreateListForm, AddItemForm

load_dotenv()

application = Flask(__name__, static_folder='static')
application.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
ckeditor = CKEditor(application)
Bootstrap4(application)
modal = Modal(application)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(application)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


##CONNECT TO DB
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(application)


##CONFIGURE TABLES
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    lists = relationship("List", back_populates="author")
    creation_date = db.Column(db.Date, nullable=False)


class List(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    author = relationship("User", back_populates="lists")
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    title = db.Column(db.String(250), unique=True, nullable=False)
    items = relationship("Item", back_populates="parent_list")
    creation_date = db.Column(db.Date, nullable=False)


class Item(db.Model):
    __tablename__ = "items"
    id = db.Column(db.Integer, primary_key=True)
    parent_list = relationship("List", back_populates="items")
    parent_list_id = db.Column(db.Integer, ForeignKey('lists.id'))
    text = db.Column(db.Text, nullable=False)
    done = db.Column(db.Boolean)
    creation_date = db.Column(db.Date, nullable=False)
    due_date = db.Column(db.Date)
    type = db.Column(db.String(50))


db.create_all()


@application.route('/', methods=["GET", "POST"])
def home():
    form = LoginForm()
    if form.validate_on_submit():
        found_user = User.query.filter_by(email=form.email.data).first()
        if found_user:
            if check_password_hash(found_user.password, form.password.data):
                login_user(found_user)
                return redirect(url_for('show_lists'))
            else:
                flash("The password is incorrect. Try again.")
                return redirect(url_for('home'))
        else:
            flash("The email is not registered.")
            redirect(url_for('home'))
    return render_template("index.html", form=form)


@application.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        found_user = User.query.filter_by(email=form.email.data).first()
        if found_user:
            flash("Email already exists. Log In instead.")
            return redirect(url_for('login'))
        hashed_pw = generate_password_hash(form.password.data)
        new_user = User(
            email=form.email.data,
            password=hashed_pw,
            name=form.name.data,
            creation_date=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        return redirect(url_for('show_lists'))
    return render_template("register.html", form=form)


@application.route('/show-lists', methods=['GET', 'POST'])
@login_required
def show_lists():
    ajax = '_ajax' in request.form
    form = CreateListForm()
    if form.validate_on_submit():
        new_list = List(
            author=current_user,
            author_id=current_user.id,
            title=form.title.data,
            creation_date=datetime.now(),
        )
        db.session.add(new_list)
        db.session.commit()
        if ajax:
            return ''
        return redirect(url_for('show_lists'))
    return render_template_modal("show_lists.html", form=form)


@application.route('/edit-list/<list_id>', methods=['GET', 'POST'])
@login_required
def edit_list(list_id):
    list_to_edit = List.query.get(list_id)
    if not list_to_edit:
        flash(f"Error: List with id {list_id} doesn't exist")
        return redirect(url_for('show_lists'))
    ajax = '_ajax' in request.form
    form = AddItemForm()
    if form.validate_on_submit():
        new_item = Item(
            parent_list=list_to_edit,
            parent_list_id=list_to_edit.id,
            text=form.text.data,
            done=False,
            creation_date=datetime.now(),
            due_date=form.due_date.data,
        )
        db.session.add(new_item)
        db.session.commit()
        if ajax:
            return ''
    return render_template_modal('edit_list.html', list=list_to_edit, form=form)


@application.route('/submit-edit-item/<item_id>', methods=['POST'])
@login_required
def submit_edit_item(item_id):
    item_to_edit = Item.query.get(item_id)
    if request.method == 'POST':
        item_to_edit.done = bool(request.form.get('done', False))
        item_to_edit.text = request.form['text']
        item_to_edit.due_date = datetime.strptime(request.form['due_date'], '%Y-%m-%d')
        db.session.commit()
    return redirect(url_for('edit_list', list_id=item_to_edit.parent_list_id))


@application.route('/delete-list/<list_id>', methods=['GET'])
@login_required
def delete_list(list_id):
    list_to_delete = List.query.get(list_id)
    db.session.delete(list_to_delete)
    delete_q = Item.__table__.delete().where(Item.parent_list_id == list_id)
    db.session.execute(delete_q)
    db.session.commit()
    return redirect(url_for('show_lists'))


@application.route('/delete-item/<item_id>', methods=['GET'])
@login_required
def delete_item(item_id):
    item_to_delete = Item.query.get(item_id)
    list_id = item_to_delete.parent_list_id
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('edit_list', list_id=list_id))


@application.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        user_to_edit = User.query.get(current_user.id)
        if request.args.get('form_id') == 'changeNameForm':
            user_to_edit.name = request.form.get('name')
            db.session.commit()
            flash("Successfully changed name", "info")
            return redirect(url_for('settings'))
        elif request.args.get('form_id') == 'changePasswordForm':
            hashed_pw = generate_password_hash(request.form.get('password'))
            user_to_edit.password = hashed_pw
            db.session.commit()
            flash("Successfully changed password", "info")
            return redirect(url_for('settings'))
        elif request.args.get('form_id') == 'deleteAccForm':
            lists_to_delete = db.session.query(List).filter(List.author_id == user_to_edit.id)
            for ilist in lists_to_delete:
                delete_q = Item.__table__.delete().where(Item.parent_list_id == ilist.id)
                db.session.execute(delete_q)
                db.session.delete(ilist)
            db.session.delete(user_to_edit)
            db.session.commit()
            logout_user()
            flash("Your account was deleted successfully", "info")
            return redirect(url_for('home'))
    return render_template("settings.html")


@application.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    application.run(host='127.0.0.1', port=5000)
