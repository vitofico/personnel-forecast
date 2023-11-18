import functools
from flask import url_for, redirect, current_app, abort, request, flash
from flask_login import current_user
from flask_admin.contrib import sqla

from app import db, scheduler

from app.models import Changelog, User, ACCESS

import pandas as pd

def try_except_decorator(func):
    @functools.wraps (func)
    def wrapper_decorator(*args, **kwargs):
        try:
            value = func (*args, **kwargs)
        except Exception as e:
            print (e)
            value = None
        # Do something after
        return value

    return wrapper_decorator

def pivot_table_decorator(func):
    @functools.wraps(func)
    def wrapper_pivot_table(*args, **kwargs):
        query = func (*args, **kwargs)
        table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
        if not table_query.empty:
            table_query.columns = [x.capitalize () for x in table_query.columns]
            table = table_query.pivot_table (values='Dedication', index=['Employee', 'Project'], columns=['Month'],
                                     fill_value=0)
            return table.reset_index()
        else:
            return table_query
    return wrapper_pivot_table

@scheduler.task('cron', id='do_job_2', minute='10', hour='2')
def clean_logtable():
    Changelog.delete_expired()

#--------------- ADMIN functions ------------------------#

def requires_access_level(access_level):
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.allowed(access_level):
                flash("You do not have access to that page. Sorry!")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@try_except_decorator
def add_admin_user():
    user = User.query.filter_by (username='admin').first ()
    if not user:
        user = User (username='admin', access=ACCESS['superuser'])
        user.set_password (current_app.config['ADMIN_PASS'])
        db.session.add (user)
        db.session.commit ()

# Create customized model view class
class MyModelView(sqla.ModelView):
    def is_accessible(self):
        return (current_user.is_active and
                current_user.is_authenticated and
                current_user.is_superuser()
        )

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('auth.login', next=request.url))

# -------------- Painting Dataframes ------------------- #

def removekey(d, key_list):
    r = dict (d)
    for key in key_list:
        try:
            del r[key]
        except:
            pass
    return r

def highlight_vals(val, max=1):
    if max < val and val <= 3*max :
        return 'background-color: %s' % 'indianred'
    elif 0.5*max < val and val <= 0.8*max :
        return 'background-color: %s' % 'khaki'
    elif val <= 0.5*max :
        return 'background-color: %s' % 'darkorange'
    # elif val > 14 * max:
    #     return 'background-color: %s' % 'orchid'
    else:
        return ''

def dataframe_to_html(dataframe, frmt='percent'):
    if frmt == 'percent':
        temp = dataframe.style.set_uuid('dataframe').\
            set_table_attributes ('class="table table-striped"'). \
            format ("{:.0%}",subset=[x for x in range(1,13) if x in dataframe.columns]).hide_index()
    elif frmt == 'euro':
        temp = dataframe.style.set_uuid ('dataframe_cost'). \
            set_table_attributes ('class="table table-striped"'). \
            format ("{} €", subset=[x for x in range(1,13) if x in dataframe.columns]). \
            format ("{} €", subset=['TOTAL']). \
            bar(subset=['TOTAL'], color='lavender') \
            .hide_index ()
    elif frmt == 'PM':
        temp = dataframe.style.set_uuid('dataframe_PM').\
            set_table_attributes ('class="table table-striped"'). \
            format ("{:.1f}").format ("{:.1f} PM", subset=['TOTAL']).bar(subset=['TOTAL'], color='lavender')
    elif frmt == 'PM_color':
        temp = dataframe.style.set_uuid('dataframe_PM_color').\
            set_table_attributes ('class="table table-striped"'). \
            format ("{:.1f}").format ("{:.1f} PM", subset=['TOTAL']). \
            applymap (highlight_vals).bar(subset=['TOTAL'], color='lavender')
    return temp.render ()


def create_summary_view(years, get_summary_func):
    data = list ()
    for year in years:
        d = dict ()
        d['year'] = year
        d['summary_project'] = dataframe_to_html (get_summary_func (year, 'Project'), 'PM')
        d['summary_employee'] = dataframe_to_html (get_summary_func (year, 'Employee'), 'PM_color')
        data.append (d)
    return data

