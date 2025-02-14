from flask import jsonify
from CASClient import CASClient
import psycopg2
from psycopg2 import pool
import os
from req_lib import ReqLib
from flask_mail import Mail, Message
#-----------------------------------------------------------------------
class OHDatabase:
    def __init__(self):
        self.connection_pool = None
        try:
            # creating a connection pool for multiple simultaneous
            # queries
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,  # Adjust based on app's needs
            dbname="office_hours_at_princeton",
            user="office_hours_at_princeton_user",
            password=os.environ['OH_DB_PWD'],
            host=os.environ['RENDER_HOST'],
            port="5432"
            )
        except Exception as e:
            print(f"Error initializing connection pool: {e}")
#-----------------------------------------------------------------------
    # Helper functions to manage database connections
    def get_db_connection(self):
        conn = self.connection_pool.getconn()
        conn.autocommit = True  # Enable autocommit if needed
        return conn

    def release_db_connection(self, conn):
        if conn:
            self.connection_pool.putconn(conn)
#-----------------------------------------------------------------------
    # check if the user is in the database using netid
    def check_user_in_db_from_netid(self, netid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Query to check if the user exists in the database
                cursor.execute("SELECT * FROM users WHERE netid = %s",
                                (netid,))
                user = cursor.fetchone()
                # If user does not exist in the database, redirect
                if not user:
                    return False
                return True  # User doesn't exist, redirection needed
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn) # Ensure conn released

#-----------------------------------------------------------------------
    # check if the user is in the database using emplid
    def check_user_in_db_from_emplid(self, emplid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Query to check if the user exists in the database
                cursor.execute("SELECT * FROM users WHERE emplid = %s",
                                (emplid,))
                user = cursor.fetchone()
                # If user does not exist in the database, redirect
                if not user:
                    return False  # Indicates user in db
                return True  # User doesn't exist, redirection needed
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn) # Ensure conn released

#-----------------------------------------------------------------------
    # check if the user is in the database using emplid
    def set_instructor_netid(self, emplid, netid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # Query to check if the user exists in the database
                update_query = """
                    UPDATE users
                    SET netid = %s
                    WHERE emplid = %s
                """
                cursor.execute(update_query, (netid,emplid,))

        except Exception as e:
            err = f"Error occurred setting instructor netid: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn) # Ensure conn released
#-----------------------------------------------------------------------
    # get name from netid
    def get_name_from_netid(self, netid):
        conn = self.get_db_connection()
        # need to handle service accounts separately
        if netid=="cs-officehrs":
            return "OH @ Princeton Admin"

        try:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT name FROM users
                               WHERE netid = %s""", (netid,))
                users = cursor.fetchone()
                if users:
                    return users[0]
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn)

        reqlib = ReqLib("https://api.princeton.edu:443/active-directory/1.0.5")

        user_info = reqlib.getJSON(
            reqlib.configs.USERS,
            uid=netid,
        )
        if not user_info:
            return "does not exist"
        return user_info[0]['displayname']

#-----------------------------------------------------------------------
    # get name from uuid
    def get_netid_from_uuid(self, uuid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT netid FROM users
                               WHERE user_id = %s""", (uuid,))
                users = cursor.fetchone()
                if users:
                    return users[0]
        except Exception as e:
            err = f"Error occurred fetching name from uuid: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # get name from uuid
    def get_name_from_uuid(self, uuid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT name FROM users
                               WHERE user_id = %s""", (uuid,))
                users = cursor.fetchone()
                if users:
                    return users[0]
        except Exception as e:
            err = f"Error occurred fetching name from uuid: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # get uuid from netid
    def get_uuid_from_netid(self, netid):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("""SELECT user_id FROM users
                               WHERE netid = %s""", (netid,))
                users = cursor.fetchone()
                if users:
                    return users[0]

        except Exception as e:
            # Return error message with details for debugging
            err = f"Error occurred while fetching uuid: {str(e)}"
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # get deptnum from netid
    def get_deptnum_from_courseid(self, courseid):
        if not courseid:
            return "LOL101"

        res = ""
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                            SELECT courses.course_id,
                                courses.title,
                                STRING_AGG(crosslistings.dept ||
                                crosslistings.course_num, '/')
                                AS course_info
                            FROM courses
                            JOIN crosslistings
                            ON crosslistings.course_id = %s
                            WHERE courses.course_id = %s
                            GROUP BY courses.course_id, courses.title
                            ORDER BY course_info ASC;
                        """
                cursor.execute(query, (courseid, courseid,))
                course_info = cursor.fetchone()
                res = course_info[2]
        except Exception as e:
            print(f"Database operation failed: {e}")
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn)

        return res
#-----------------------------------------------------------------------
    # get number of toggled courses from netid
    def get_num_toggled_courses_from_netid(self, netid):
        if not netid:
            return 0

        uuid = self.get_uuid_from_netid(netid)
        res = 0
        conn = self.get_db_connection()

        try:
            with conn.cursor() as cursor:
                query = """
                            SELECT course_id
                            FROM course_user_association
                            WHERE user_id = %s AND is_toggled = %s
                        """
                cursor.execute(query, (uuid, True,))
                courses = cursor.fetchall()
                res = len(courses)
        except Exception as e:
            print(f"Database operation failed: {e}")
            return jsonify({"error": "Database error"}), 500
        finally:
            self.release_db_connection(conn)

        return res
#-----------------------------------------------------------------------
    # get instructors from course ID
    def get_instructors_from_course_id(self, course_id):
        conn = self.get_db_connection()
        if not course_id:
            return ["ProfessorX"]
        instructors = []

        try:
            with conn.cursor() as cursor:
                query = """
                    SELECT user_id
                    FROM course_user_association
                    WHERE course_id = %s AND is_admin = %s
                """
                cursor.execute(query, (course_id, True,))
                uuids = cursor.fetchall()
                for uuid in uuids:
                    uuid = uuid[0]
                    instructors.append(uuid)

            return instructors

        except Exception as e:
            # Return error message with details for debugging
            err = f"Error occurred creating getting instructors: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # returns an array of courses the current users is an admin for
    def user_is_admin_for(self, netid):
        admin_for = []
        conn = self.get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE netid = %s",
                                (netid,))
                users = cursor.fetchall()
                cursor.execute("""SELECT course_id
                            FROM course_user_association
                            WHERE user_id = %s AND is_admin = %s""",
                              (users[0][0], True,))
                course_id = cursor.fetchall()
                if course_id:
                    for course in course_id:
                        admin_for.append(course[0])

            return admin_for
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # returns false if user doesn't exist, true if does
    def user_exists_in_db(self, netid):
        conn = self.get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE netid = %s",
                               (netid,))
                users = cursor.fetchall()
                if not users:
                    return False
                return True
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # create a new user in our database if they do not exist
    def create_user(self, netid):
        conn = self.get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM users WHERE netid = %s",
                                (netid,))
                users = cursor.fetchall()
                if not users:
                    name = self.get_name_from_netid(netid)
                    if name == "does not exist":
                        return name
                    query = """
                            INSERT INTO users (user_id, netid, name)
                            VALUES (uuid_generate_v4(), %s, %s)
                            """
                    cursor.execute(query, (netid,name,))
        except Exception as e:
            return jsonify({"status": "error", "message": e}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # helper function to get rgba for draft events
    def _hex_to_rgba(self, hex):
        hex = hex.lstrip("#")
        rgb_tuple = str(tuple(int(hex[i:i+2],16) for i in (0, 2, 4)))
        rgb_tuple = rgb_tuple.rstrip(")")
        rgb_tuple = "rgba" + rgb_tuple
        rgb_tuple += ", 0.5)"
        return rgb_tuple

#-----------------------------------------------------------------------
    # get list of users' saved events as json to add to display
    # on calendar, do correct coloring
    def get_events(self, netid):
        user_id = self.get_uuid_from_netid(netid)
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                # List of toggled courses
                toggled_courses_query = """
                    SELECT * FROM course_user_association
                    WHERE user_id = %s AND is_toggled = %s
                """
                cursor.execute(toggled_courses_query, (user_id, True,))
                saved_course_ids = []
                saved_colors = {}

                # associating courses with colors from the DB
                for row in cursor.fetchall():
                    saved_course_ids.append(row[1])
                    saved_colors[row[1]] = row[5] if row[5] else "#3688D8"

                if (len(saved_course_ids) > 0):
                    course_filter = f"AND course_id IN %s"
                else:
                    course_filter = f""

                query = f"""
                        SELECT * FROM office_hours
                        WHERE is_draft = %s
                        {course_filter}
                    """
                cursor.execute(query, (False, tuple(saved_course_ids),))
                events = cursor.fetchall()

                # list of draft office hours
                proposed_oh_query = """
                    SELECT oh_id FROM oh_user_association
                    WHERE user_id = %s
                """
                cursor.execute(proposed_oh_query, (user_id,))
                proposed_oh_ids = []
                draft_events = []

                for row in cursor.fetchall():
                    proposed_oh_ids.append(row[0])
                if len(proposed_oh_ids) > 0:
                    query = f"""
                            SELECT * FROM office_hours
                            WHERE is_draft = %s
                            AND oh_id IN %s
                        """
                    cursor.execute(query, (True, tuple(proposed_oh_ids),))
                    draft_events = cursor.fetchall()

                # Transform the data to JSON format required by FullCalendar
                event_list = [
                    {
                        "oh_id" : event[10],
                        "title": self.get_name_from_uuid(event[6]),
                        "start": f"{event[9]}T{event[1]}",
                        "end": f"{event[9]}T{event[2]}",
                        "location":event[7],
                        "course": self.get_deptnum_from_courseid(event[5]),
                        "color": saved_colors[event[5]],
                        "is_draft":event[0],
                    }
                    for event in events
                ]

                for event in draft_events:
                    event_list.append(
                        {
                            "oh_id" : event[10],
                            "title": self.get_name_from_uuid(event[6]),
                            "start": f"{event[9]}T{event[1]}",
                            "end": f"{event[9]}T{event[2]}",
                            "location":event[7],
                            "course":
                            self.get_deptnum_from_courseid(event[5]),
                            "backgroundColor":
                            self._hex_to_rgba(saved_colors[event[5]]),
                            "borderColor": saved_colors[event[5]],
                            "is_draft":event[0],
                        }
                    )
                return jsonify(event_list)
        except Exception as e:
            err = f"Error occurred while fetching events: {str(e)}"
            print(err)
            return jsonify([])
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # create an OH in the backend with the given parameters
    # returns a json status depending on whether the operation was
    # successful
    def create_oh(self, is_draft, starttime, endtime, course_id, 
                  instructor, location, weekday, date, netid):
        conn = self.get_db_connection()
        if not is_draft:
            instructor = self.get_uuid_from_netid(instructor)
        try:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO office_hours (is_draft, 
                    starttime, endtime, course_id, instructor, 
                    location, weekday, date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING oh_id;
                """
                cursor.execute(query, (is_draft, starttime, endtime, 
                    course_id, instructor, location, weekday, date,))
                
                if is_draft:
                    oh_id = cursor.fetchone()[0]
                    uuid = self.get_uuid_from_netid(netid)
                    draft_query = """
                            INSERT INTO oh_user_association
                            (user_id, oh_id)
                            VALUES (%s, %s)
                            """
                    cursor.execute(draft_query, (uuid, oh_id,))
                """
                One issue with how our code is right now is that when
                someone creates a new OH, that OH should be added into the
                course_user_association table for users who have already
                added the given course to their calendar. Right now, I think
                our code is only doing so when someone adds the course?

                To fix this, I think we can use the following queries:

                First, check which course this office hour is associated with:
                SELECT user_id
                FROM course_user_association
                WHERE course_id = %s

                INSERT INTO oh_user_association (user_id, oh_id)
                VALUES (%s, %s)
                """
            return jsonify({"status": "success"}), 200

        except Exception as e:
            # Return error message with details for debugging
            err = f"Error occurred while creating OH: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # deletes the requested OH if the user is an admin for the course
    def delete_oh(self, netid, oh_id, mail_obj):
        conn = self.get_db_connection()
        uuid = self.get_uuid_from_netid(netid)
        student_emails = []

        try:
        # TODO: CLEAN UP THIS CODE, PASS STUFF IN INSTEAD
            with conn.cursor() as cursor:
                query = """
                        SELECT * FROM office_hours
                        WHERE oh_id = %s
                    """
                cursor.execute(query, (oh_id,))
                result = cursor.fetchall()

                editor = self.get_name_from_uuid(result[0][6])
                date = result[0][9]
                starttime = result[0][1]
                course_id = result[0][5]

                query = """
                        SELECT user_id FROM course_user_association
                        WHERE course_id = %s
                    """
                cursor.execute(query, (course_id,))

                user_ids = cursor.fetchall()

                for user_id_tuple in user_ids:
                    user_id = user_id_tuple[0]
                    query = """
                            SELECT netid FROM users
                            WHERE user_id = %s
                        """

                    cursor.execute(query, (user_id,))

                    user_profile_result = cursor.fetchall()

                    if user_profile_result[0][0]:
                        netid = user_profile_result[0][0]
                        if netid:
                            student_emails.append(f"{netid}@princeton.edu")

                can_delete_query = """
                    SELECT is_admin
                    FROM course_user_association
                    WHERE course_id = %s AND user_id = %s
                """
                cursor.execute(can_delete_query, (course_id, uuid,))
                can_delete = cursor.fetchall()

                if not can_delete:
                    return jsonify({"status": "error", "message": "You do not have permission to delete this office hour."}), 500
                can_delete = can_delete[0][0]
                if not can_delete:
                    return jsonify({"status": "error", "message": "You do not have permission to delete this office hour."}), 500

                delete_assocation_query = """
                    DELETE FROM oh_user_association
                    WHERE oh_id = %s
                """
                cursor.execute(delete_assocation_query,
                                (oh_id,))
                delete_query = """
                    DELETE FROM office_hours
                    WHERE oh_id = %s
                """
                cursor.execute(delete_query, (oh_id,))

            subject = f"Office Hours Cancelled by {editor}"

            body = f"""
Dear Student,

I hope this message finds you well.

{editor} has cancelled their office hour on {date} at {starttime.strftime('%H:%M')}

Should you have any further questions or concerns regarding this change, please feel free to reach out to your instructor.

Best regards,
Office Hours At Princeton
            """
            if self.send_email_notification(subject, student_emails, body, mail_obj):
                return jsonify({"message": "Emails sent successfully"}), 200
            else:
                return jsonify({"error": "Failed to send emails"}), 500
        except Exception as e:
        # Return error message with details for debugging
            err = f"Error occurred while deleting OH: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # FUNCTION TO TRUNCATE ALL EVENTS
    # WARNING: GOING TO THIS URL WILL DELETE ALL EVENTS, USE FOR DEV
    # PURPOSES ONLY
    def truncate_oh(self):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                    TRUNCATE office_hours CASCADE
                """
                cursor.execute(query)

            return jsonify({"status": "success"}), 201

        except Exception as e:
            # Return error message with details for debugging
            err = f"Error occurred while truncating OH: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # save the given course
    def save_course(self, netid, course_id, is_toggled, 
                    is_admin, semester, colors):
        conn = self.get_db_connection()
        user_id = self.get_uuid_from_netid(netid)
        admin_for_course = False

        try:
            with conn.cursor() as cursor:
                course_query = """
                    SELECT * FROM course_user_association
                    WHERE user_id = %s
                    AND course_id = %s
                """
                cursor.execute(course_query, (user_id, course_id,))
                results = cursor.fetchone()
                color = colors.pop(0)
                colors.append(color)
                if not results:
                    if netid == "cs-officehrs":
                        is_admin = True
                    course_query = """
                        INSERT INTO course_user_association 
                        (user_id, course_id, is_toggled, 
                        term, is_admin, color, is_saved)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(course_query, (user_id, course_id, 
                            is_toggled, semester, is_admin, color, True,))
                    admin_for_course = is_admin
                else:
                    query = """
                        UPDATE course_user_association
                        SET is_toggled = %s, color = %s, is_saved = %s
                        WHERE course_id = %s AND user_id = %s
                    """
                    cursor.execute(query, 
                            (is_toggled, color, True, results[1], results[0],))
                    admin_for_course = results[4]

                data_query = """
                    SELECT courses.course_id, 
                        courses.title, 
                        STRING_AGG(crosslistings.dept 
                        || crosslistings.course_num, '/') 
                        AS course_info
                    FROM courses
                    JOIN crosslistings 
                    ON crosslistings.course_id = %s
                    WHERE courses.course_id = %s
                    GROUP BY courses.course_id, courses.title
                """
                cursor.execute(data_query, (course_id,course_id))
                course_data = cursor.fetchone()
                instructor_uuids = self.get_instructors_from_course_id(course_id)
                instructor_names = []
                for uuid in instructor_uuids:
                    instructor_names.append(self.get_name_from_uuid(uuid))

                result_data  = {
                    "courseid": course_data[0],
                    "title": course_data[1],
                    "dept_num": course_data[2],
                    "is_admin": admin_for_course,
                    "color": color,
                    "is_toggled": is_toggled,
                    "instructor_names": instructor_names,
                    "instructor_netids": instructor_uuids,
                }
            return jsonify(status="success",
                            message="Course saved successfully.", 
                            data=result_data), 200
        except Exception as e:
            err = f"Error occurred while saving course: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # remove the given course for the given user
    def remove_saved_course(self, netid, course_id):
        conn = self.get_db_connection()
        user_id = self.get_uuid_from_netid(netid)
        try:
            with conn.cursor() as cursor:
                query = """
                        SELECT is_admin FROM course_user_association
                        WHERE course_id = %s AND user_id = %s
                    """
                cursor.execute(query, (course_id, user_id))
                query_result = cursor.fetchall()
                is_admin = query_result[0][0]
                if is_admin:
                    query = """
                            UPDATE course_user_association
                            SET is_saved = %s, is_toggled = %s
                            WHERE course_id = %s AND user_id = %s
                        """
                    cursor.execute(query, (False, False, course_id, user_id))
                # if theyre not an admin, we don't need to save them in course_user_association
                else:
                    query = """
                            DELETE FROM course_user_association
                            WHERE course_id = %s AND user_id = %s
                        """
                    cursor.execute(query, (course_id, user_id))
            return jsonify({"status": "success", "is_admin": is_admin}), 200
        except Exception as e:
            err = f"Error while removing saved course: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # fetch saved courses for the given user
    def fetch_saved_courses(self, netid):
        user_id = self.get_uuid_from_netid(netid)
        conn = self.get_db_connection()

        try:
            result_data = []
            with conn.cursor() as cursor:
                course_query = """
                    SELECT course_id, is_admin, color, is_toggled 
                    FROM course_user_association
                    WHERE course_user_association.user_id = %s
                    AND course_user_association.is_saved = %s
                """
                cursor.execute(course_query, (user_id, True,))
                results = cursor.fetchall()
                for result in results:
                    query = """
                        SELECT courses.course_id, 
                            courses.title, 
                            STRING_AGG(crosslistings.dept 
                            || crosslistings.course_num, '/') 
                            AS course_info
                        FROM courses
                        JOIN crosslistings 
                        ON crosslistings.course_id = %s
                        WHERE courses.course_id = %s
                        GROUP BY courses.course_id, courses.title
                        ORDER BY course_info ASC;
                    """
                    cursor.execute(query, (result[0],result[0]))
                    course_results = cursor.fetchall()

                    for course_result in course_results:
                        instructor_uuids = self.get_instructors_from_course_id(course_result[0])
                        instructor_names = []
                        for uuid in instructor_uuids:
                            instructor_names.append(self.get_name_from_uuid(uuid))

                        result_data.append({
                            "courseid": course_result[0],
                            "title": course_result[1],
                            "dept_num": course_result[2],
                            "is_admin": result[1],
                            "color": result[2],
                            "is_toggled": result[3],
                            "instructor_names": instructor_names,
                            "instructor_netids": instructor_uuids,
                        })

            return jsonify({"status": "success",
                             "results": result_data}), 200
        except Exception as e:
            err = f"Error while fetching saved courses: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    def toggle_course(self, netid, course_id):
        conn = self.get_db_connection()
        user_id = self.get_uuid_from_netid(netid)
        try:
            with conn.cursor() as cursor:
                query = """
                            UPDATE course_user_association
                            SET is_toggled = NOT is_toggled
                            WHERE user_id = %s AND course_id = %s
                        """
                cursor.execute(query, (user_id, course_id))
                # user_profile_result = cursor.fetchall()

                # if user_profile_result:
                #     netid = user_profile_result[0][0]

                return jsonify(status="success", message="Course toggled successfully."), 200
        except Exception as e:
            err = f"Error while toggling course: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # make user admin for given course by netid
    def add_admin(self, netid_to_add, course_id):
        conn = self.get_db_connection()
        if not self.check_user_in_db_from_netid(netid_to_add):
            if self.create_user(netid_to_add) == "does not exist":
                return jsonify({"status": "error", 
                                "message": "Invalid netid."}), 500

        user_id = self.get_uuid_from_netid(netid_to_add)

        try:
            with conn.cursor() as cursor:
                course_query = """
                    SELECT * FROM course_user_association
                    WHERE course_user_association.user_id = %s
                    AND course_user_association.course_id = %s
                """
                cursor.execute(course_query, (user_id, course_id,))
                results = cursor.fetchone()
                if not results:
                    query = """
                    INSERT INTO course_user_association 
                    (user_id, course_id, is_toggled, is_saved, term, is_admin)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(query, (user_id, course_id, 
                        False, False, os.environ["CUR_SEMESTER"], True,))
                else:
                    query = """
                        UPDATE course_user_association
                        SET is_admin = %s
                        WHERE course_user_association.course_id = %s 
                        AND course_user_association.user_id = %s
                    """
                    cursor.execute(query, (True, course_id, user_id,))

            return jsonify({"status": "success"}), 200
        except Exception as e:
            err = f"Error while adding admin: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)

#-----------------------------------------------------------------------
    # approve the list of office hours read in from data
    def approve_office_hours(self, data):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                for item in data:
                    if item['status'] == 'approve':
                        update_query = """
                            UPDATE office_hours
                            SET is_draft = %s
                            WHERE oh_id = %s
                        """
                        cursor.execute(update_query, (False, item['id'],))
                    elif item['status'] == 'reject':
                        delete_assocation_query = """
                            DELETE FROM oh_user_association
                            WHERE oh_id = %s
                        """
                        cursor.execute(delete_assocation_query,
                                       (item['id'],))
                        delete_query = """
                            DELETE FROM office_hours
                            WHERE oh_id = %s
                        """
                        cursor.execute(delete_query, (item['id'],))
            return jsonify({"status": "success"}), 200
        except Exception as e:
            err = f"Error while approving OH: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)

#-----------------------------------------------------------------------
    # fetches the office hours the user can approve
    def fetch_oh_to_approve(self, netid):
        conn = self.get_db_connection()
        user_id = self.get_uuid_from_netid(netid)
        
        try:
            result_data = []
            with conn.cursor() as cursor:
                course_query = """
                    SELECT course_id, color FROM course_user_association
                    WHERE user_id = %s
                    AND is_admin = %s
                """
                cursor.execute(course_query, (user_id, True,))
                results = cursor.fetchall()
                # JOIN crosslistings 
                # ON crosslistings.course_id = courses.course_id
                # STRING_AGG(crosslistings.dept 
                # || crosslistings.course_num, '/') AS course_info,
                for result in results:
                    query = """
                        SELECT courses.course_id, 
                            courses.title,
                            STRING_AGG(crosslistings.dept 
                            || crosslistings.course_num, '/') 
                            AS course_info,
                            office_hours.oh_id, 
                            office_hours.starttime, 
                            office_hours.endtime,
                            office_hours.instructor, 
                            office_hours.location,
                            office_hours.date
                        FROM courses
                        LEFT JOIN crosslistings 
                        ON crosslistings.course_id = courses.course_id
                        LEFT JOIN office_hours 
                        ON office_hours.course_id = %s
                        WHERE courses.course_id = %s 
                        AND office_hours.is_draft = %s
                        GROUP BY courses.course_id, courses.title, 
                        office_hours.oh_id
                    """
                    cursor.execute(query, (result[0], result[0], True,))
                    oh_results = cursor.fetchall()
                    for oh_result in oh_results:
                        result_data.append({
                            "courseid": oh_result[0],
                            "title": oh_result[1],
                            "dept_num": oh_result[2],
                            "oh_id": oh_result[3],
                            "oh_starttime": str(oh_result[4]),
                            "oh_endtime": str(oh_result[5]),
                            "oh_instructor": 
                            self.get_name_from_uuid(oh_result[6]),
                            "oh_location": oh_result[7],
                            "oh_date": str(oh_result[8])
                        })
            return jsonify({"status": "success",
                            "results": result_data}), 200    
        except Exception as e:
            err = f"Error while fetching OH to approve: {str(e)}"
            print(err)
            return jsonify({"status": "error", "message": err}), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # helper function used for a one-time fix of the database
    def set_colors_where_null(self):
        conn = self.get_db_connection()
        try:
            with conn.cursor() as cursor:
                query = """
                        UPDATE course_user_association
                        SET color = %s
                        WHERE color IS NULL
                    """
                cursor.execute(query, ("#4C566A",))
        except Exception as e:
                print(e)
                return jsonify(status="error", message=str(e))
        finally:
                self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # updates office hours for all subscribed, sends an email to
    # users with course toggled
    def update_office_hour(self, starttime, endtime, date,
                           location, oh_id, mail_obj, netid):
        conn = self.get_db_connection()
        attempted_editor_uuid = self.get_uuid_from_netid(netid)
        student_emails = []
        try:
            with conn.cursor() as cursor:
                query = """
                        SELECT * FROM office_hours
                        WHERE oh_id = %s
                    """
                cursor.execute(query, (oh_id,))
                result = cursor.fetchall()



                editor = self.get_name_from_uuid(result[0][6])
                prevdate = result[0][9]
                prevstarttime = result[0][1]
                prevendtime = result[0][2]
                prevlocation = result[0][7]

                can_delete_query = """
                    SELECT is_admin
                    FROM course_user_association
                    WHERE course_id = %s AND user_id = %s
                """
                cursor.execute(can_delete_query, (result[0][5], attempted_editor_uuid,))
                can_delete = cursor.fetchall()

                if not can_delete:
                    return jsonify({"status": "error", "message": "You do not have permission to edit this office hour."}), 500
                can_delete = can_delete[0][0]
                if not can_delete:
                    return jsonify({"status": "error", "message": "You do not have permission to edit this office hour."}), 500

                query = """
                        SELECT user_id FROM course_user_association
                        WHERE course_id = %s
                    """
                cursor.execute(query, (result[0][5],))
                user_ids = cursor.fetchall()

                for user_id_tuple in user_ids:
                    user_id = user_id_tuple[0]
                    query = """
                            SELECT netid FROM users
                            WHERE user_id = %s
                        """
                    cursor.execute(query, (user_id,))
                    user_profile_result = cursor.fetchall()

                    if user_profile_result:
                        netid = user_profile_result[0][0]
                        if netid:
                            student_emails.append(f"{netid}@princeton.edu")

                query = """
                        UPDATE office_hours
                        SET starttime = %s, endtime = %s, date = %s, location = %s
                        WHERE oh_id = %s
                    """
                # temporarily removing this line to fix editing 
                cursor.execute(query, (starttime, endtime, date, location, oh_id,))

            subject = f"Office Hours Update by {editor}"

            body = f"""
Dear Student,

I hope this message finds you well.

Please note the update to the office hours as outlined below:

Old Information:
- Date: {prevdate}
- Start Time: {prevstarttime.strftime('%H:%M')}
- End Time: {prevendtime.strftime('%H:%M')}
- Location: {prevlocation}

New Information:
- Date: {date.strftime('%Y-%m-%d')}
- Start Time: {starttime}
- End Time: {endtime}
- Location: {location}

Should you have any further questions or concerns regarding this change, please feel free to reach out to your instructor.

Best regards,
Office Hours At Princeton
            """

            if self.send_email_notification(subject, student_emails, body, mail_obj):
                return jsonify({"message": "Emails sent successfully"}), 200
            else:
                err = f"Failed to send emails: {str(e)}"
                print(err)
                return jsonify({"status": "error", "message": err}), 500
        except Exception as e:
            print(e)
            return jsonify(status="error", message=str(e)), 500
        finally:
            self.release_db_connection(conn)
#-----------------------------------------------------------------------
    # helper function to send email notifications
    def send_email_notification(self, subject, recipients, body, mail_obj):
        try:
            if not recipients:
                print("No recipients found")
                return False
            
            msg = Message(
                subject,
                sender=('cs-officehrs@princeton.edu'),
                recipients=recipients
            )
            msg.body = body
            mail_obj.send(msg)
            print(f"Email sent successfully to: {', '.join(recipients)}")
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
#-----------------------------------------------------------------------
    def search_result(self, netid, searchInput):
        conn = self.get_db_connection()
        user_id = self.get_uuid_from_netid(netid)

        if searchInput:
            searchInput = searchInput.replace('%', '\\%').replace('_', '\\_')

            try:
                result_data = []
                with conn.cursor() as cursor:
                    # List of saved courses
                    saved_courses_query = """
                        SELECT course_id FROM course_user_association
                        WHERE user_id = %s AND is_saved = TRUE
                    """
                    cursor.execute(saved_courses_query, (user_id,))
                    saved_course_ids = [row[0] for row in cursor.fetchall()]

                    # Check if saved_course_ids is empty and
                    # adjust query accordingly
                    if saved_course_ids:
                        course_filter = f"AND courses.course_id NOT IN %s"
                        params = (tuple(saved_course_ids),)
                    else:
                        course_filter = ""
                        params = ()
                    
                    stmt_str = """
                        SELECT user_id FROM users
                        WHERE name ILIKE %s
                    """

                    search_pattern = f"%{searchInput}%"

                    cursor.execute(stmt_str, (search_pattern,))

                    # Fetch all user_ids
                    rows = cursor.fetchall()

                    # Initialize an empty list to store course_ids
                    prof_matches = []

                    for row in rows:
                        user_id = row[0]
                        stmt_str = """
                            SELECT course_id
                            FROM course_user_association
                            WHERE user_id = %s AND is_admin = True
                        """
                        cursor.execute(stmt_str, (user_id,))
                        
                        # Fetch all course_ids for this user
                        course_rows = cursor.fetchall()
                        
                        # Append course_ids to the prof_matches list
                        for course_row in course_rows:
                            prof_matches.append(course_row[0])

                    # Print the resulting list of course_ids
                    print("prof_matches:", prof_matches)

                    stmt_str = f"""
                        SELECT courses.course_id,
                            courses.title,
                            STRING_AGG(DISTINCT crosslistings.dept || crosslistings.course_num, '/') AS course_info
                        FROM courses
                        JOIN crosslistings 
                            ON crosslistings.course_id = courses.course_id
                        LEFT JOIN office_hours 
                            ON office_hours.course_id = courses.course_id
                        WHERE (
                            courses.course_id IN (
                                SELECT courses.course_id
                                FROM courses
                                JOIN crosslistings 
                                    ON crosslistings.course_id = courses.course_id
                                WHERE (
                                    REPLACE(courses.title, ' ', '') 
                                    ILIKE REPLACE(%s, ' ', '') ESCAPE '\\'
                                    OR REPLACE(crosslistings.dept || crosslistings.course_num, ' ', '') 
                                    ILIKE REPLACE(%s, ' ', '') ESCAPE '\\'
                                )
                            )
                            OR courses.course_id = ANY (%s)
                        )
                        {course_filter}
                        GROUP BY courses.course_id, courses.title
                        ORDER BY 
                            MIN(CAST(REGEXP_REPLACE(crosslistings.course_num, '[^0-9]', '', 'g') AS INT)) ASC,
                            courses.title ASC;
                    """
                    cursor.execute(stmt_str, (search_pattern, search_pattern, prof_matches) + params)
                    results = cursor.fetchall()

                    # Process results
                    for result in results:
                        result_data.append({
                            "courseid": result[0],
                            "title": result[1],
                            "dept_num": result[2]
                        })

                return jsonify({"status": "success", "results": result_data}), 200

            except Exception as e:
                err = f"Error occurred while searching classes: {str(e)}"
                print(err)  # Log error to console for debugging
                return jsonify({"status": "error", "message": err}), 500
            finally:
                self.release_db_connection(conn)
        else:
            return jsonify({"status": "error", "message": "No search input provided"}), 400
#-----------------------------------------------------------------------
def main():
    print("OHDatabase does not run standalone")
    # database = OHDatabase()
    # database.set_colors_where_null()

if __name__ == "__main__":
    main()