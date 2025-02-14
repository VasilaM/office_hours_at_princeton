from flask import Blueprint, Flask, request, render_template, jsonify, redirect, url_for, make_response, current_app, g
from CASClient import CASClient
from OHDatabase import OHDatabase
from flask_mail import Mail, Message
from mail import mail
import datetime
from datetime import timedelta
import os
from req_lib import ReqLib

events_bp = Blueprint('cal_events', __name__)
_cas = CASClient()
_database = OHDatabase()
colors = ["#4C566A", "#5E81AC", "#788c66", "#bf616a", "#b0715d",
          "#c4aa74", "#8fbcbb", "#b48ead"]
#-----------------------------------------------------------------------
# admin functionality

# Endpoint to add new office hours
@events_bp.route("/createoh", methods=['POST'])
def createoh():
    course_id = request.form.get('courses')
    date = datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%d')
    weekday = date.weekday()
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    location = request.form.get('location')
    instructor = request.form.get('netid')
    is_draft = False
    is_recurring = request.form.get('recurring')

    enddate = datetime.datetime.strptime("2025-01-07", '%Y-%m-%d')
    difference = enddate - date



    if is_recurring:
        for i in range(1, (difference.days // 7) + 1):
            recurring_date = date+timedelta(days=7 * i)
            _database.create_oh(is_draft, starttime, endtime, course_id,
                  instructor, location, weekday, recurring_date, instructor)
    
    return _database.create_oh(is_draft, starttime, endtime, course_id,
                  instructor, location, weekday, date, instructor)

@events_bp.route("/delete-office-hour", methods=['POST'])
def delete_office_hour():
    oh_id = request.form.get('oh_id')
    netid = _cas.authenticate().rstrip()
    mail_obj = mail

    return _database.delete_oh(netid, oh_id, mail_obj)

@events_bp.route('/add_admin', methods=['POST'])
def add_admin():
    netid_to_add = request.form.get("netid")
    course_id = request.form.get('admin-courses')

    return _database.add_admin(netid_to_add, course_id)

@events_bp.route('/approve_office_hours', methods=['POST'])
def approve_office_hours():
    data = request.json.get('items', [])

    return _database.approve_office_hours(data)

@events_bp.route('/fetch_oh_to_approve', methods=['GET'])
def fetch_oh_to_approve():
    netid = _cas.authenticate()
    netid = netid.rstrip()

    return _database.fetch_oh_to_approve(netid)

@events_bp.route('/update-office-hour', methods=['POST'])
def update_office_hour():
    date = datetime.datetime.strptime(request.form.get('editdate'), '%Y-%m-%d')
    starttime = request.form.get('editstarttime')
    endtime = request.form.get('editendtime')
    location = request.form.get('editlocation')
    oh_id = request.form.get('ohid')
    mail_obj = mail
    netid = _cas.authenticate().rstrip()

    return _database.update_office_hour(starttime, endtime, date, 
                            location, oh_id, mail_obj, netid)

#-----------------------------------------------------------------------
# auth functionality

# if user is not logged in with CAS
# or if user is logged in with CAS, but doesn't have entry in DB
def _redirect_landing():
    try:
        # Check if the user is logged in via CAS
        if _cas.is_logged_in():
            req_lib = ReqLib("https://api.princeton.edu:443/active-directory/1.0.5")
            netid = _cas.authenticate().strip()  # Strip whitespace from netid

            user_info = req_lib.getJSON(
                req_lib.configs.USERS,
                uid=netid,
            )
            print(f"Authenticated user: {netid}")

            if not _database.check_user_in_db_from_netid(netid):
                emplid = user_info[0]['universityid']
                if _database.check_user_in_db_from_emplid(emplid):
                    _database.set_instructor_netid(emplid, netid)
                    return False
                return True
            return False
        return True
    except Exception as ex:
        print(f"Error in detecting user: {ex}")
        return "Error in detecting user"


# Home page route
@events_bp.route("/landing-page", methods=['GET'])
def landing_page():
    return render_template('landing-page.html')

@events_bp.route('/team', methods=['GET'])
def team():
    return render_template('team.html')

# Home page route
@events_bp.route("/", methods=['GET'])
def index():
    if _redirect_landing():
        return redirect(url_for('cal_events.landing_page'))

    netid = _cas.authenticate()
    is_admin = False
    admin_for = _database.user_is_admin_for(netid)

    if admin_for:
        is_admin = True

    html_code = render_template('index.html',
        username=_database.get_name_from_netid(netid), netid=netid,
        is_admin=is_admin, admin_for=admin_for)

    return make_response(html_code)

@events_bp.route('/login', methods=['GET'])
def login():
    netid = _cas.authenticate()
    netid = netid.rstrip()

    if _cas.is_logged_in():
        if not _database.user_exists_in_db(netid):
            req_lib = ReqLib("https://api.princeton.edu:443/active-directory/1.0.5")
            netid = _cas.authenticate().strip()  # Strip whitespace from netid

            user_info = req_lib.getJSON(
                req_lib.configs.USERS,
                uid=netid,
            )
            emplid = user_info[0]['universityid']

            if _database.check_user_in_db_from_emplid(emplid):
                    _database.set_instructor_netid(emplid, netid)
            else:
                _database.create_user(netid)

    return redirect(url_for('cal_events.index'))

@events_bp.route('/logoutapp', methods=['GET'])
def logoutapp():
    # Log out of the application.
    _cas.logout()

#-----------------------------------------------------------------------
# cal events functionality

# Endpoint to retrieve events
@events_bp.route("/events", methods=['GET'])
def get_events():
    netid = _cas.authenticate()
    netid = netid.rstrip()

    events_list = _database.get_events(netid)

    return events_list

# Endpoint to add new office hours
@events_bp.route("/sendoh", methods=['POST'])
def sendoh():
    course_id = request.form.get('courses')
    date = datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%d')
    weekday = date.weekday()
    starttime = request.form.get('starttime')
    endtime = request.form.get('endtime')
    location = request.form.get('location')
    instructor = request.form.get('associated-instructors')
    is_recurring = request.form.get('recurring')
    is_draft = True
    netid = _cas.authenticate().rstrip()

    enddate = datetime.datetime.strptime("2025-01-07", '%Y-%m-%d')
    difference = enddate - date

    if is_recurring:
        for i in range(1, (difference.days // 7) + 1):
            recurring_date = date+timedelta(days=7 * i)
            _database.create_oh(is_draft, starttime, endtime, course_id, 
                  instructor, location, weekday, recurring_date, netid)
    
    return _database.create_oh(is_draft, starttime, endtime, course_id, 
                  instructor, location, weekday, date, netid)

@events_bp.route('/save_course', methods=['POST'])
def save_course():
    data = request.get_json()
    course_id = data.get('courseid')
    course_id = course_id.lstrip('p')
    netid = _cas.authenticate()
    netid = netid.rstrip()
    is_admin = False
    is_toggled = True
    semester = os.environ["CUR_SEMESTER"]

    return _database.save_course(netid, course_id, is_toggled, 
                                 is_admin, semester, colors)

@events_bp.route('/remove_saved_course', methods=['POST'])
def remove_saved_course():
    data = request.get_json()
    netid = _cas.authenticate()
    netid = netid.rstrip()
    course_id = data.get('courseid')
    course_id = course_id.lstrip('p')

    return _database.remove_saved_course(netid, course_id)

@events_bp.route('/fetch_saved_courses', methods=['GET'])
def fetch_saved_courses():
    netid = _cas.authenticate()
    netid = netid.rstrip()

    return _database.fetch_saved_courses(netid)

# TODO: frontend help
@events_bp.route("/toggle", methods=['POST'])
def toggle():
    data = request.get_json()
    netid = _cas.authenticate()
    netid = netid.rstrip()
    course_id = data.get('courseid')
    course_id = course_id.lstrip('p')
    print("course id", course_id)
    return _database.toggle_course(netid, course_id)

#-----------------------------------------------------------------------
# search functionality
@events_bp.route("/searchresults", methods=['GET'])
def search_result():
    search_input = request.args.get('searchInput', '')
    netid = _cas.authenticate().rstrip()  # Authenticate the user

    return _database.search_result(netid, search_input)

#-----------------------------------------------------------------------
# switch to student view
@events_bp.route("/student_view", methods=['GET'])
def student_view():
    netid = _cas.authenticate()
    is_admin = False
    admin_for = _database.user_is_admin_for(netid)

    if admin_for:
        is_admin = False

    html_code = render_template('index.html',
        username=_database.get_name_from_netid(netid), netid=netid,
        is_admin=is_admin, admin_for=admin_for)

    return make_response(html_code)