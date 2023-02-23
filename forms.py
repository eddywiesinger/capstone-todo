from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[Email(), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In")


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[Email(), DataRequired()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8),
                                                     EqualTo('password_confirm', message='Passwords must match')])
    password_confirm = PasswordField(label='Password confirm', validators=[Length(min=8)])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up")


class CreateListForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired()])
    submit = SubmitField("Create List")


class AddItemForm(FlaskForm):
    text = StringField("Todo", validators=[DataRequired()])
    due_date = DateField("Due Date", default=datetime.now())
    submit = SubmitField("Add Item")

# class AccountSettingsForm(FlaskForm):
#     name = StringField("Name", validators=[DataRequired()], default='Test')
#     email = StringField('Email', render_kw={'readonly': True}, default='asdasd@asdf.de')
#     password = PasswordField("Password", validators=[DataRequired(), Length(min=8),
#                                                      EqualTo('password_confirm', message='Passwords must match')])
#     password_confirm = PasswordField(label='Password confirm', validators=[Length(min=8)])
#     submit = SubmitField("Confirm changes")
