# import calendar
from datetime import datetime
import requests
import io

import pandas as pd
# from dateutil.rrule import rrule, MONTHLY
from flask import current_app
from redminelib import Redmine

from app import db, scheduler
from app.models import Forecast, Dedication_Redmine
from app.utility_functions import try_except_decorator, pivot_table_decorator


@try_except_decorator
def get_redmine_obj():
    return Redmine (current_app.config['REDMINE_URL'], key='48d4b42ac6b432621059e1aa51c234c6119ff1ee',
                    requests={'verify': False})


@try_except_decorator
def get_redmine_project_list(return_dict=False):
    redmine_obj = get_redmine_obj ()
    projects_dict = {prj.name: prj.id for prj in redmine_obj.project.all () if prj.status is not 5}
    projects_name_list = list (projects_dict.keys ())
    if return_dict:
        return projects_dict
    else:
        return projects_name_list


@try_except_decorator
def get_redmine_user_list():
    redmine_obj = get_redmine_obj ()
    users_list = [f'{usr}' for usr in redmine_obj.user.filter (status=1)]
    return users_list

def list2emptydict(lst):
    return {i: '' for i in lst}



@try_except_decorator
def get_redmine_userid(employee_name):
    redmine_obj = get_redmine_obj ()
    usr = redmine_obj.user.filter (name=employee_name)[0]
    try:
        return usr.id
    except:
        return None


@try_except_decorator
def get_redmine_projectid(project_name):
    projects_dict = get_redmine_project_list (True)
    return projects_dict.get (project_name, None)


@try_except_decorator
def get_time_entries(user_id, project_id=None, from_date=None, to_date=None):
    redmine_obj = get_redmine_obj ()
    if from_date and to_date and project_id:
        filtered_time_entries = redmine_obj.time_entry.filter (user_id=user_id, project_id=project_id,
                                                               from_date=from_date, to_date=to_date)
    elif not project_id and from_date and to_date:
        filtered_time_entries = redmine_obj.time_entry.filter (user_id=user_id, from_date=from_date, to_date=to_date)
    else:
        filtered_time_entries = redmine_obj.time_entry.filter (user_id=user_id, limit=100)
    return [t_e.hours for t_e in filtered_time_entries]


def get_query_columns_name():
    return Forecast.__table__.columns.keys ()


def get_available_employees():
    return [r.employee for r in db.session.query (Forecast.employee).distinct ()]


def get_employees_project(employee):
    return [r.project for r in db.session.query (Forecast.project).filter (Forecast.employee == employee).distinct ()]

def get_all_time_entries():
    payload = {'key': '48d4b42ac6b432621059e1aa51c234c6119ff1ee'}
    r = requests.get(f"{current_app.config['REDMINE_URL']}/time_entries.csv", params=payload, verify=False).text
    raw_data = pd.read_csv (io.StringIO (r))
    raw_data.drop (columns=['Activity', 'Issue', 'Comment'], inplace=True)
    raw_data = raw_data[raw_data['Hours'] != 0]
    raw_data['Date'] = pd.to_datetime (raw_data['Date'], format='%m/%d/%Y')
    raw_data.set_index(['Date'], inplace=True)
    raw_data=raw_data.groupby ([pd.Grouper(freq='M'), 'Project', 'User']).sum ()
    raw_data.reset_index(inplace=True)
    raw_data['year']= raw_data['Date'].dt.strftime('%Y')
    raw_data['month'] = raw_data['Date'].dt.strftime ('%m')
    raw_data.rename (columns={"Project": "project", "User": "employee"}, inplace=True)
    raw_data.drop (columns=['Date'], inplace=True)
    raw_data['total_hours']=raw_data.groupby(['year','month','employee'])['Hours'].transform ('sum')
    avg_monthly_hours = float (current_app.config['AVG_MONTHLY_HOURS'])
    raw_data['dedication']=raw_data['Hours']/avg_monthly_hours
    raw_data.drop (columns=['Hours'], inplace=True)
    raw_data['remarks'] = 'Imported from Redmine at ' + datetime.today ().strftime ("%d/%m/%Y %H:%M:%S")
    return raw_data


@scheduler.task('cron', id='do_job_1', minute='5', hour='1-2')
# @scheduler.task ('date', id='do_job_1')
def build_spent_time_matrix():
    with db.app.app_context ():
        dedication_matrix=get_all_time_entries()
        # avg_monthly_hours=float(current_app.config['AVG_MONTHLY_HOURS'])
        # current_date = datetime.today ()
        # this_year = current_date.year
        # previous_year = current_date.year - 1
        # date1 = datetime (this_year, 1, 1)
        # date2 = datetime (this_year, 12, 31)
        # column_names = ['employee', 'project', 'year', 'month', 'dedication', 'total_hours', 'remarks']
        # dedication_list = list ()
        # for current_year in [previous_year, this_year]:
        #     date1 = date1.replace (year=current_year)
        #     date2 = date2.replace (year=current_year)
        #     months = [dt.strftime ("%m") for dt in rrule (MONTHLY, dtstart=date1, until=date2)]
        #     for employee in get_available_employees ():
        #         employee_id = get_redmine_userid (employee)
        #         for membership_project in get_employees_project (employee):
        #             project_id = get_redmine_projectid (membership_project)
        #             for month in months:
        #                 lastday = calendar.monthrange (int (current_year), int (month))[1]
        #                 start_date = f'{current_year}-{month}-01'
        #                 end_date = f'{current_year}-{month}-{lastday}'
        #                 total_hours = sum (get_time_entries (employee_id, None, start_date, end_date))
        #                 dedication = sum (get_time_entries (employee_id, project_id, start_date, end_date))
        #                 # if total_hours > 0.85*avg_monthly_hours :
        #                 #     dedication = dedication / total_hours
        #                 # else:
        #                 dedication = dedication / avg_monthly_hours
        #                 dedication_list.append (
        #                     [employee, membership_project, current_year, int (month), float (dedication),
        #                      float (total_hours),
        #                      'Imported from Redmine at ' + current_date.strftime ("%d/%m/%Y %H:%M:%S")])
        # dedication_matrix = pd.DataFrame (dedication_list, columns=column_names)
        # dedication_matrix.index = range (1, len (dedication_matrix) + 1)
        dedication_matrix.to_sql ('dedication_redmine', con=db.engine, index_label='id', if_exists='replace')


@pivot_table_decorator
def get_spent_time_matrix(selected_year):
    return Dedication_Redmine.query.filter_by (year=selected_year)


def get_spent_time_summary(selected_year, item):
    table = get_spent_time_matrix (selected_year)
    summary_table = table.groupby (item).sum ()
    summary_table['TOTAL'] = summary_table.sum (axis=1)
    return summary_table


def get_spent_time_matrix_for_excel(selected_year):
    try:
        query=Dedication_Redmine.query.filter_by (year=selected_year)
        table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
        table_query.columns = [x.capitalize () for x in table_query.columns]
        table = table_query.pivot_table (values=['Dedication'], index=['Employee', 'Project'], columns=['Month'],
                                         fill_value=0)
        return table.reset_index ()
    except:
        return pd.DataFrame(columns = ['No Data to Show'])