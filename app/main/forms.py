from flask import request
from flask_babel import _, lazy_gettext as _l
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from flask_wtf.file import FileField
from wtforms import StringField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import ValidationError, DataRequired, NumberRange

from app.models import User

months_list = [('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'June'),
               ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'), ('11', 'November'),
               ('12', 'December')]
years_list = [(str (x), str (x)) for x in range (2020, 2031)]

concepts_list = [('Subcontracting', 'Subcontracting'), ('Material', 'Material'), ('Travel', 'Travel'), ('Other', 'Other')]

class EditProfileForm (FlaskForm):
    username = StringField (_l ('Username'), validators=[DataRequired ()])
    submit = SubmitField (_l ('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super (EditProfileForm, self).__init__ (*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by (username=self.username.data).first ()
            if user is not None:
                raise ValidationError (_ ('Please use a different username.'))


class PostForm (FlaskForm):
    post = TextAreaField (_l ('Say something'), validators=[DataRequired ()])
    submit = SubmitField (_l ('Submit'))


class SearchForm (FlaskForm):
    q = StringField (_l ('Search'), validators=[DataRequired ()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super (SearchForm, self).__init__ (*args, **kwargs)


class ForecastForm (FlaskForm):
    employee = StringField ('Employee', validators=[DataRequired ()], id='employee_autocomplete')
    project = StringField ('Project', validators=[DataRequired ()], id='project_autocomplete')
    month = SelectField ('Month', choices=months_list, validators=[DataRequired ()])
    year = SelectField ('Year', choices=years_list, validators=[DataRequired ()])
    dedication = IntegerField ('Dedication (%)', validators=[NumberRange (min=0, max=100)])
    remarks = TextAreaField ('Remarks')
    submit = SubmitField ('Save')

class CostForm (FlaskForm):
    concept = SelectField ('Concept', choices=concepts_list, validators=[DataRequired ()])
    project = StringField ('Project', validators=[DataRequired ()], id='project_cost')
    month = SelectField ('Month', choices=months_list, validators=[DataRequired ()])
    year = SelectField ('Year', choices=years_list, validators=[DataRequired ()])
    cost = IntegerField ('Quantity (€)', validators=[NumberRange (min=0)])
    remarks = TextAreaField ('Remarks')
    submit = SubmitField ('Save')


class UploadExcel (FlaskForm):
    spreadsheet_file = FileField ('Spreadsheet File', validators=[FileRequired (),
                                                                  FileAllowed (['xls', 'xlsx'], 'Spreadsheets only!')
                                                                  ])
    submit = SubmitField ('Submit')

class UploadJSON (FlaskForm):
    json_file = FileField ('JSON File', validators=[FileRequired (),
                                                                  FileAllowed (['json'], 'json only!')
                                                                  ])
    submit = SubmitField ('Submit')