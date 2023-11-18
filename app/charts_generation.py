from app import db
from app.models import Forecast, Dedication_Redmine
import pandas as pd


def projects_chart(selected_year, project):
    query_forecast = Forecast.query.filter_by (year=selected_year).filter_by(project=project)
    query_spenttime = Dedication_Redmine.query.filter_by (year=selected_year).filter_by (project=project)
    fg=list()
    for query, df_name in zip([query_forecast, query_spenttime], ['Forecast','Spent Time']):
        table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
        table_query.columns = [x.capitalize () for x in table_query.columns]
        try:
            table = table_query.pivot_table (values='Dedication', index=['Employee'], columns=['Month'],
                                          fill_value=0)
            table=table.transpose ()
            fg.append((table, df_name))
        except:
            pass
    categories=[str(x) for x in list (fg[0][0].index.values)]
    return to_highchart(fg,f'{selected_year} - {project}', 'Month',"chart", "column", categories)

def employee_chart(selected_year, employee):
    query_forecast = Forecast.query.filter_by (year=selected_year).filter_by(employee=employee)
    query_spenttime = Dedication_Redmine.query.filter_by (year=selected_year).filter_by (employee=employee)
    fg=list()
    for query, df_name in zip([query_forecast, query_spenttime], ['Forecast','Spent Time']):
        table_query = pd.read_sql (query.statement, con=db.engine, index_col='id')
        table_query.columns = [x.capitalize () for x in table_query.columns]
        try:
            table = table_query.pivot_table (values='Dedication', index=['Project'], columns=['Month'],
                                          fill_value=0)
            table=table.transpose ()
            fg.append((table, df_name))
        except:
            pass
    categories=[str(x) for x in list (fg[0][0].index.values)]
    return to_highchart(fg,f'{selected_year} - {employee}', 'Month',"chart", "column", categories)

def to_highchart(df_list, title, xAxistitle, renderTo, graphtype, categories):
    series=[{'data': list (value.values), 'name': key, 'stack': df_name} for df, df_name in df_list for key, value in df.items ()]

    formatter = "__function () {return '<br/>' + this.series.options.stack + ' - ' + this.series.name +': ' + Highcharts.numberFormat(this.y, 2) + ' PM <br/>' +'Total:' + Highcharts.numberFormat(this.point.stackTotal,2) + ' PM';}__"

    to_print = {'plotOptions': {'column': {'stacking': 'normal'}}, 'tooltip': {'formatter' : f'{formatter}'} ,
                'series': series, 'chart': {"renderTo": renderTo, "type": graphtype}, "legend": {"enabled": 'true'},
                "title": {"text": title}, "xAxis": {"title": {"text": xAxistitle}}, 'xAxis': {'categories' : categories}}

    return f'{to_print}'.replace ('nan', 'null').replace('"__','').replace('__"','')
