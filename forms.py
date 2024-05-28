from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, NumberRange

class ClientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    submit = SubmitField('Add Client')

class ServiceForm(FlaskForm):
    description = StringField('Description', validators=[DataRequired()])
    cost = FloatField('Cost', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Service')
