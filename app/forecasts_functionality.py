import json
import os

import pandas as pd
from flask import current_app

from app import db
from app.costs_functionality import build_cost_matrix
from app.models import Forecast, Changelog
from app.redmine_functionality import get_spent_time_matrix_for_excel, get_spent_time_matrix
from app.utility_functions import pivot_table_decorator, removekey


def get_available_years(table=Forecast):
    return [r.year for r in db.session.query (table.year).distinct ()]


def get_available_projects_year(year, table=Forecast):
    return [r.project for r in db.session.query (table.project).filter (table.year == year).distinct ()]


def get_available_employees_year(year, table=Forecast):
    return [r.employee for r in db.session.query (table.employee).filter (table.year == year).distinct ()]


def query_existing(data):
    key_list = ['csrf_token', 'dedication', 'remarks', 'submit']
    data_cleaned = removekey (data, key_list)
    my_filters = data_cleaned
    query = db.session.query (Forecast)
    for attr, value in my_filters.items ():
        query = query.filter (getattr (Forecast, attr) == value)
    # now we can run the query
    return query.first ()


@pivot_table_decorator
def build_dedication_matrix(selected_year):
    return Forecast.query.filter_by (year=selected_year)


def get_changelog(selected_year, last_n):
    query = Changelog.query.filter_by (year=selected_year).order_by (Changelog.timestamp.desc ()).limit (last_n)
    table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
    table_query.columns = [x.capitalize () for x in table_query.columns]
    return table_query


def get_dedication_summary(selected_year, item):
    table = build_dedication_matrix (selected_year)
    summary_table = table.groupby (item).sum ()
    summary_table['TOTAL'] = summary_table.sum (axis=1)
    return summary_table


def analyse_personnel_forecast(data, change_author):
    forecast = query_existing (data)
    if forecast:
        change = Changelog (author=change_author, action='update', employee=forecast.employee,
                            project=forecast.project, month=forecast.month,
                            year=forecast.year, dedication_old=forecast.dedication,
                            dedication_new=data['dedication'], remarks=data['remarks'])
        forecast.dedication = data['dedication']
        forecast.remarks = data['remarks']
        flash_message = 'Your forecast has been updated!'
    else:
        change = Changelog (author=change_author, action='add', employee=data['employee'],
                            project=data['project'], month=int (data['month']),
                            year=int (data['year']), dedication_old=int ('0'),
                            dedication_new=data['dedication'], remarks=data['remarks'])
        forecast = Forecast (employee=data['employee'], project=data['project'], month=int (data['month']),
                             year=int (data['year']), dedication=data['dedication'], remarks=data['remarks'])
        flash_message = 'Your forecast has been added!'

    return change, forecast, flash_message


def save_forecasts():
    years = get_available_years ()
    filepath = os.path.join (current_app.root_path, current_app.config['DOWNLOAD_FOLDER'], 'forecasts.xlsx')
    with pd.ExcelWriter (filepath) as writer:
        for year in years:
            table = build_dedication_matrix (year)
            table_c = build_cost_matrix(year)
            summary_p = get_dedication_summary (year, 'Project')
            summary_e = get_dedication_summary (year, 'Employee')
            changelog = get_changelog (year, 120)
            spent_time = get_spent_time_matrix_for_excel (year)
            #
            changelog.to_excel (writer, sheet_name=f'Changelog {year}')
            table.to_excel (writer, sheet_name=f'Personnel Forecasts {year}')
            table_c.to_excel (writer, sheet_name=f'Costs Forecasts {year}')
            spent_time.to_excel (writer, sheet_name=f'Spent Time {year}')
            summary_p.to_excel (writer, sheet_name=f'Summary Projects {year}')
            summary_e.to_excel (writer, sheet_name=f'Summary Employees {year}')


def import_forecast_excel(filename, change_author):
    df = pd.read_excel (filename).fillna ('')
    for entry in df.to_dict ('records'):
        change, forecast, flash_message = analyse_personnel_forecast (entry, change_author)
        db.session.add (forecast)
        db.session.add (change)
        db.session.commit ()
    return 'Your forecast has been added!'


# -------------------------- Generate Employees Profile Dataframe ---------------------------

def update_employee_profile_file(data, uploaded_file):
    with open (uploaded_file, 'r') as f:
        datastore = {**data, **json.load (f)}
    if datastore:
        with open (uploaded_file, 'w', encoding='utf8') as f:
            json.dump (datastore, f, indent=2)
    return datastore

def create_employee_profile_dataframe(datastore):
    years = get_available_years ()
    directory = os.path.join (current_app.root_path, current_app.config['DOWNLOAD_FOLDER'])
    result_file = 'admin_temp.xlsx'
    filepath = os.path.join (directory, result_file)
    with pd.ExcelWriter (filepath) as writer:
        for year in years:
            dedication_df = build_dedication_matrix (year)
            spent_time_df = get_spent_time_matrix (year)
            costs_df = build_cost_matrix(year)
            di = datastore
            for df, sheet_name in zip([dedication_df, spent_time_df],['forecast','spent_time']):
                if not df.empty:
                    df['Profile'] = df['Employee']
                    df["Profile"].replace (di, inplace=True)
                    df_temp=df.groupby(['Project', 'Profile']).sum().reset_index()
                    df_temp.to_excel (writer, sheet_name=f'{sheet_name} - {year}', index=False)
            if not costs_df.empty:
                costs_df.to_excel (writer, sheet_name=f'costs - {year}', index=False)
    return directory, result_file, 'Success!'
