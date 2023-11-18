import json
import os

import pandas as pd
from flask import current_app

from app import db
from app.models import Cost, Changelog
from app.utility_functions import pivot_table_decorator, removekey


def get_available_years(table=Cost):
    return [r.year for r in db.session.query (table.year).distinct ()]


def get_available_projects_year(year, table=Cost):
    return [r.project for r in db.session.query (table.project).filter (table.year == year).distinct ()]


def get_available_concepts_year(year, table=Cost):
    return [r.concept for r in db.session.query (table.concept).filter (table.year == year).distinct ()]


def query_existing(data):
    key_list = ['csrf_token', 'cost', 'remarks', 'submit']
    data_cleaned = removekey (data, key_list)
    my_filters = data_cleaned
    query = db.session.query (Cost)
    for attr, value in my_filters.items ():
        query = query.filter (getattr (Cost, attr) == value)
    # now we can run the query
    return query.first ()

def build_cost_matrix(selected_year):
    query = Cost.query.filter_by (year=selected_year)
    table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
    if not table_query.empty:
        table_query.columns = [x.capitalize () for x in table_query.columns]
        table = table_query.pivot_table (values='Cost', index=['Project', 'Concept'], columns=['Month'],
                                         fill_value=0)
        table=table.reset_index ()
        table['TOTAL'] = table.sum (axis=1)
        return table
    else:
        return table_query


def analyse_cost_forecast(data, change_author):
    forecast = query_existing (data)
    if forecast:
        change = Changelog (author=change_author, action='update', concept=forecast.concept,
                            project=forecast.project, month=forecast.month,
                            year=forecast.year, cost_old=forecast.cost,
                            dedication_new=data['cost'], remarks=data['remarks'])
        forecast.cost = data['cost']
        forecast.remarks = data['remarks']
        flash_message = 'Your cost forecast has been updated!'
    else:
        change = Changelog (author=change_author, action='add', concept=data['concept'],
                            project=data['project'], month=int (data['month']),
                            year=int (data['year']), cost_old=int ('0'),
                            cost_new=data['cost'], remarks=data['remarks'])
        forecast = Cost (concept=data['concept'], project=data['project'], month=int (data['month']),
                             year=int (data['year']), cost=data['cost'], remarks=data['remarks'])
        flash_message = 'Your cost forecast has been added!'

    return change, forecast, flash_message
