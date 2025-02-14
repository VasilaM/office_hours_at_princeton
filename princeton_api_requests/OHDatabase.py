from flask import Flask, request, render_template, jsonify, redirect, url_for, make_response, session
import json
import psycopg2
from psycopg2 import pool
import os
from req_lib import ReqLib
from flask_mail import Mail, Message
import datetime
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
            password="uV5uOuPV3Yxf3bF3tgEGDzr3TJyPeFVZ",
            host=
            "dpg-csc0ts3v2p9s73dmsgd0-a.virginia-postgres.render.com",
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


    def add_emplids(self):
        req_lib = ReqLib()
        fall_2024_term_code = "1252"
        subj = " "
        conn = self.get_db_connection()

        # Returns all courses in COS
        term_info = req_lib.getJSON(
        req_lib.configs.COURSE_COURSES,
        # To return a json version of the return value
        fmt="json",
        term=fall_2024_term_code,
        search=subj,)

        # IF RUNNING IN A FUTURE SEM, REMEMBER TO ALSO SET COLOR
        with conn.cursor() as cursor:
            for term in term_info["term"]:
                for subject in term["subjects"]:
                    for course in subject["courses"]:
                        for instructor in course["instructors"]:
                            print("name: ", instructor['full_name'], ";", "emplid: ", instructor["emplid"])
                            instructor_existence_query = """
                                SELECT user_id FROM users WHERE emplid = %s
                            """
                            cursor.execute(instructor_existence_query, (instructor["emplid"],))

                            existing_instructor = cursor.fetchone()
                            uuid = ""

                            if not existing_instructor:
                                instructor_addition_query = """
                                    INSERT INTO users (user_id, emplid, name)
                                    VALUES (uuid_generate_v4(), %s, %s)
                                    RETURNING user_id
                                """
                                cursor.execute(instructor_addition_query, (instructor["emplid"], instructor['full_name'],))
                                uuid = cursor.fetchone()[0]
                            else:
                                uuid = existing_instructor[0]
            
                            update_admin_query = """
                                INSERT INTO course_user_association 
                                (user_id, course_id, is_toggled, 
                                term, is_admin, is_saved)
                                VALUES (%s, %s, %s, %s, %s, %s)
                            """

                            cursor.execute(update_admin_query, (uuid, course['guid'], False, "1252", True, True,))

if __name__ == "__main__":
    _database = OHDatabase()

    _database.add_emplids()