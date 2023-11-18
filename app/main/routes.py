import json
import os
from datetime import datetime

from flask import render_template, flash, redirect, url_for, request, g, \
    jsonify, current_app, Response, send_from_directory
from flask_babel import _, get_locale
from flask_login import current_user, login_required
from guess_language import guess_language
from werkzeug.utils import secure_filename

from app import db
from app.charts_generation import projects_chart, employee_chart
from app.costs_functionality import analyse_cost_forecast, build_cost_matrix
from app.forecasts_functionality import build_dedication_matrix, get_available_years, analyse_personnel_forecast, \
    save_forecasts, get_dedication_summary, import_forecast_excel, get_available_projects_year, \
    get_available_employees_year, create_employee_profile_dataframe, update_employee_profile_file
from app.main import bp
from app.main.forms import EditProfileForm, PostForm, SearchForm, ForecastForm, UploadExcel, UploadJSON, CostForm
from app.models import User, Post, Changelog, Dedication_Redmine, ACCESS
from app.redmine_functionality import get_redmine_project_list, get_redmine_user_list, get_spent_time_matrix, \
    get_spent_time_summary, list2emptydict
from app.translate import translate
from app.utility_functions import dataframe_to_html, create_summary_view, add_admin_user, requires_access_level


@bp.before_app_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow ()
        db.session.commit ()
        g.search_form = SearchForm ()
    g.locale = str (get_locale ())
    add_admin_user ()


@bp.route ('/', methods=['GET', 'POST'])
@bp.route ('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm ()
    if form.validate_on_submit ():
        language = guess_language (form.post.data)
        if language == 'UNKNOWN' or len (language) > 5:
            language = ''
        post = Post (body=form.post.data, author=current_user,
                     language=language)
        db.session.add (post)
        db.session.commit ()
        flash (_ ('Your post is now live!'))
        return redirect (url_for ('main.index'))
    page = request.args.get ('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate (
        page, current_app.config['POSTS_PER_PAGE'], False)
    # posts = current_user.followed_posts ().paginate (
    #     page, current_app.config['POSTS_PER_PAGE'], False)
    return render_template ('index.html', title=_ ('Home'), form=form,
                            posts=posts)


# @bp.route ('/explore')
# @login_required
# def explore():
#     page = request.args.get ('page', 1, type=int)
#     posts = Post.query.order_by (Post.timestamp.desc ()).paginate (
#         page, current_app.config['POSTS_PER_PAGE'], False)
#     next_url = url_for ('main.explore', page=posts.next_num) \
#         if posts.has_next else None
#     prev_url = url_for ('main.explore', page=posts.prev_num) \
#         if posts.has_prev else None
#     return render_template ('index.html', title=_ ('Explore'),
#                             posts=posts.items, next_url=next_url,
#                             prev_url=prev_url)


@bp.route ('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by (username=username).first_or_404 ()
    page = request.args.get ('page', 1, type=int)
    posts = user.posts.order_by (Post.timestamp.desc ()).paginate (
        page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for ('main.user', username=user.username,
                        page=posts.next_num) if posts.has_next else None
    prev_url = url_for ('main.user', username=user.username,
                        page=posts.prev_num) if posts.has_prev else None
    return render_template ('user.html', user=user, posts=posts.items,
                            next_url=next_url, prev_url=prev_url)


@bp.route ('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by (username=username).first_or_404 ()
    return render_template ('user_popup.html', user=user)


@bp.route ('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm (current_user.username)
    if form.validate_on_submit ():
        current_user.username = form.username.data
        db.session.commit ()
        flash (_ ('Your changes have been saved.'))
        return redirect (url_for ('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template ('edit_profile.html', title=_ ('Edit Profile'),
                            form=form)


@bp.route ('/follow/<username>')
@login_required
def follow(username):
    user = User.query.filter_by (username=username).first ()
    if user is None:
        flash (_ ('User %(username)s not found.', username=username))
        return redirect (url_for ('main.index'))
    if user == current_user:
        flash (_ ('You cannot follow yourself!'))
        return redirect (url_for ('main.user', username=username))
    current_user.follow (user)
    db.session.commit ()
    flash (_ ('You are following %(username)s!', username=username))
    return redirect (url_for ('main.user', username=username))


@bp.route ('/unfollow/<username>')
@login_required
def unfollow(username):
    user = User.query.filter_by (username=username).first ()
    if user is None:
        flash (_ ('User %(username)s not found.', username=username))
        return redirect (url_for ('main.index'))
    if user == current_user:
        flash (_ ('You cannot unfollow yourself!'))
        return redirect (url_for ('main.user', username=username))
    current_user.unfollow (user)
    db.session.commit ()
    flash (_ ('You are not following %(username)s.', username=username))
    return redirect (url_for ('main.user', username=username))


@bp.route ('/translate', methods=['POST'])
@login_required
def translate_text():
    return jsonify ({'text': translate (request.form['text'],
                                        request.form['source_language'],
                                        request.form['dest_language'])})


@bp.route ('/search')
@login_required
def search():
    if not g.search_form.validate ():
        return redirect (url_for ('main.explore'))
    page = request.args.get ('page', 1, type=int)
    posts, total = Post.search (g.search_form.q.data, page,
                                current_app.config['POSTS_PER_PAGE'])
    next_url = url_for ('main.search', q=g.search_form.q.data, page=page + 1) \
        if total > page * current_app.config['POSTS_PER_PAGE'] else None
    prev_url = url_for ('main.search', q=g.search_form.q.data, page=page - 1) \
        if page > 1 else None
    return render_template ('search.html', title=_ ('Search'), posts=posts,
                            next_url=next_url, prev_url=prev_url)


@bp.route ('/_autocomplete/<item>', methods=['GET'])
def autocomplete(item):
    if item == 'project':
        return Response (json.dumps (get_redmine_project_list ()), mimetype='application/json')
    elif item == 'employee':
        return Response (json.dumps (get_redmine_user_list ()), mimetype='application/json')


@bp.route ('/add_forecast', methods=['GET', 'POST'])
@login_required
def add_forecast():
    form_p = ForecastForm ()
    form_c = CostForm ()
    flag=False
    if form_p.submit.data and form_p.validate_on_submit ():
        data = request.form.to_dict ()
        data['dedication'] = int (data['dedication']) / 100
        change, forecast, flash_message = analyse_personnel_forecast (data, current_user.username)
        flag=True
    elif form_c.validate_on_submit ():
        data = request.form.to_dict ()
        change, forecast, flash_message = analyse_cost_forecast (data, current_user.username)
        flag = True
    if flag:
        try:
            db.session.add (change)
            db.session.add (forecast)
            db.session.commit ()
        except Exception as inst:
            flash_message = f'error! {inst}'
        flash (flash_message)
        return redirect (url_for ('main.add_forecast'))

    return render_template ('add_forecast.html', title='Add Forecast', form_c=form_c, form_p=form_p)


@bp.route ('/select_year')
@login_required
def select_year():
    years = get_available_years ()
    return render_template ('select_year.html', years=years, filename='forecasts.xlsx')


@bp.route ('/forecasts/summary')
@login_required
def forecasts_summary():
    years = get_available_years ()
    data = create_summary_view (years, get_dedication_summary)
    return render_template ('summary.html', data=data)


@bp.route ('/forecasts/<year>')
@login_required
def forecasts_results(year):
    table_p = build_dedication_matrix (year)
    table_p_html = dataframe_to_html (table_p)
    table_c = build_cost_matrix (year)
    table_c_html = dataframe_to_html (table_c, 'euro')
    return render_template ('results.html', table_p=table_p_html, table_c=table_c_html, year=year)

@bp.route ('/changelog')
@login_required
def changelog():
    changes = Changelog.query.order_by (Changelog.timestamp.desc ())
    return render_template ('changelog.html', changes=changes)


@bp.route ('/spent_time/<year>')
@login_required
def spent_time(year):
    table = get_spent_time_matrix (year)
    table_html = dataframe_to_html (table)
    return render_template ('results.html', table=table_html, year=year)


@bp.route ('/spent_time/summary')
@login_required
def spent_time_summary():
    years = get_available_years (Dedication_Redmine)
    data = create_summary_view (years, get_spent_time_summary)
    return render_template ('summary.html', data=data)


@bp.route ('/charts/<year>/<item>')
@login_required
def show_charts(year, item='None'):
    projects = get_available_projects_year (year)
    employees = get_available_employees_year (year)
    if item == 'None':
        return render_template ('charts.html', chart=None, projects=projects, employees=employees, year=year)
    else:
        if item in projects:
            chart = projects_chart (year, item)
        elif item in employees:
            chart = employee_chart (year, item)
        return render_template ('charts.html', chart=chart, projects=projects, employees=employees, year=year)


@bp.route ("/downloads/<path:filename>", methods=['GET', 'POST'])
@login_required
def get_file(filename):
    """Download a file."""
    save_forecasts ()
    uploads = os.path.join (current_app.root_path, current_app.config['DOWNLOAD_FOLDER'])
    return send_from_directory (directory=uploads, filename=filename, as_attachment=True)


@bp.route ("/uploads", methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadExcel ()
    if form.validate_on_submit ():
        if request.method == 'POST':
            # check if the post request has the file part
            f = form.spreadsheet_file.data
            _, file_extension = os.path.splitext (f.filename)
            filename = secure_filename (f'import{file_extension}')
            uploaded_file = os.path.join (current_app.root_path, current_app.config['UPLOAD_FOLDER'], filename)
            f.save (uploaded_file)
            message = import_forecast_excel (uploaded_file, current_user.username)
            flash (message)
            return redirect (url_for ('main.select_year'))
    return render_template ('upload_forecasts.html', form=form, filename='forecasts_template.xlsx')


@bp.route ('/employees_profile', methods=['GET', 'POST'])
@requires_access_level(ACCESS['admin'])
@login_required
def employees_profile():
    filename_orig = 'employee_profile.json'
    uploads = os.path.join (current_app.root_path, current_app.config['DOWNLOAD_FOLDER'], filename_orig)
    datastore = list2emptydict (get_redmine_user_list ())
    if not uploads:
        with open (uploads, 'w', encoding='utf8') as f:
            json.dump (datastore, f, indent=2)
    else:
        with open (uploads, 'r') as f:
            datastore = {**datastore, **json.load (f)}
    form = UploadJSON ()
    if form.validate_on_submit ():
        if request.method == 'POST':
            # check if the post request has the file part
            f = form.json_file.data
            _, file_extension = os.path.splitext (f.filename)
            filename = secure_filename (f'employee_profile{file_extension}')
            uploaded_file = os.path.join (current_app.root_path, current_app.config['UPLOAD_FOLDER'], filename)
            f.save(uploaded_file)
            updated_data=update_employee_profile_file(datastore, uploaded_file)
            directory,result_file,message=create_employee_profile_dataframe(updated_data)
            return send_from_directory (directory=directory, filename=result_file, as_attachment=True)

    return render_template ('employee_profile.html', form=form, filename=filename_orig)
