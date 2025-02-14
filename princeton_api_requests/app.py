from flask import Flask, request, render_template, redirect, url_for
import psycopg2
from req_lib import ReqLib

app = Flask(__name__)

# Database connection
conn = psycopg2.connect(
    host="dpg-csc0ts3v2p9s73dmsgd0-a.virginia-postgres.render.com",
    database="office_hours_at_princeton",
    user="office_hours_at_princeton_user",
    password="uV5uOuPV3Yxf3bF3tgEGDzr3TJyPeFVZ",
    port="5432"  # Default port for PostgreSQL
)

# Sample route for POST request
@app.route('/submit', methods=['POST'])
def submit():
    req_lib = ReqLib()
    fall_2024_term_code = "1252"
    subj = " "

    term_info = req_lib.getJSON(
        req_lib.configs.COURSE_COURSES,
        # To return a json version of the return value
        fmt="json",
        term=fall_2024_term_code,
        search=subj,
    )
    with conn.cursor() as cursor:
        for term in term_info["term"]:
            for subject in term["subjects"]:
                code = subject["code"]
                for course in subject["courses"]:

                    # prints each individual course returned
                    # by the endpoint. Each course has the
                    # following parameters:

                    # guid (string of the term code and course id concatenated. Unique each term)
                    # course_id (course id according to the course registrar. Not unique each term)
                    # catalog_number (catalog number of the course. So, for COS 126 this would be 126)
                    # title (Title of the course)
                    # detail (detailed information about the course [start/end date, track, description])
                    # instructors 
                    # crosslistings (any crosslistings, if they exist)
                    # classes (class meetings, each section that is within the class)
                    # WARNING: DO NOT RUN THIS UNLESS YOU ARE A BACKEND PERSON AND KNOW WHAT YOU
                    # ARE DOING
                    guid = int(course['guid'])
                    catalog_number = course['catalog_number']
                    query = "INSERT INTO crosslistings ("
                    query += "course_id, dept, course_num"
                    query += ") VALUES (%s, %s, %s)"
                    cursor.execute(query, [guid, code, catalog_number])

                    for crosslisting in course['crosslistings']:
                        catalog_number = crosslisting['catalog_number']
                        code = crosslisting['subject']
                        query = "INSERT INTO crosslistings ("
                        query += "course_id, dept, course_num"
                        query += ") VALUES (%s, %s, %s)"
                        cursor.execute(query, [guid, code, catalog_number])

        conn.commit()
        return redirect(url_for('index'))

@app.route('/')
def index():
    return render_template('index.html')