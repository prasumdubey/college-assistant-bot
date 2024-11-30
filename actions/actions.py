import mysql.connector
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from fuzzywuzzy import process  # Import fuzzy matching module
import os

load_dotenv(dotenv_path='actions/my.env')


host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")

# Create a function to connect to the MySQL database
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database 
        )
        if conn.is_connected():
            return conn
        else:
            print("Database connection failed.")
            return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None


# Helper function for fuzzy matching
def get_closest_match(input_str, options_list):
    closest_match, score = process.extractOne(input_str, options_list)
    return closest_match if score > 80 else None  # Set threshold for accuracy


class ActionProvideDepartment(Action):

    def name(self) -> str:
        return "action_provide_departments"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        conn = get_db_connection()
        if not conn:
            dispatcher.utter_message(text="Sorry, I couldn't connect to the database. Please try again later.")
            return []
        cursor = conn.cursor(dictionary=True)

        # Get all unique departments
        cursor.execute("SELECT DISTINCT department FROM courses")
        unique_departments = cursor.fetchall()

        # Extract department names
        department_names = [dept['department'] for dept in unique_departments]
        total_departments = len(department_names)

        if total_departments > 0:
            # Create a response with total number and department names
            response = f"There are a total of {total_departments} departments in the university:\n"
            response += "\n".join([f"• {dept}" for dept in department_names])
            dispatcher.utter_message(text=response)
        else:
            dispatcher.utter_message(text="Sorry, I couldn’t find any departments in the university.")

        cursor.close()
        conn.close()

        return []

class ActionListCourses(Action):

    def name(self) -> str:
        return "action_list_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        department = tracker.get_slot('department')

        if department:
            conn = get_db_connection()
            if not conn:
                dispatcher.utter_message(text="Sorry, I couldn't connect to the database. Please try again later.")
                return []
            cursor = conn.cursor(dictionary=True)

            # Get all unique departments for fuzzy matching
            cursor.execute("SELECT DISTINCT department FROM courses")
            all_departments = [dept['department'] for dept in cursor.fetchall()]

            # Find the closest match for the user's input
            department_match = get_closest_match(department, all_departments)

            if department_match:
                # Query to get the courses for the matched department
                query = "SELECT course_name FROM courses WHERE department = %s"
                cursor.execute(query, (department_match,))
                courses = cursor.fetchall()

                if courses:
                    course_list = [course['course_name'] for course in courses]
                    courses_str = '\n'.join(course_list)
                    dispatcher.utter_message(
                        text=f"Here are the courses offered by the {department_match} department:\n\n{courses_str}")
                else:
                    dispatcher.utter_message(
                        text=f"Sorry, I couldn’t find any courses for the {department_match} department.")
            else:
                department_list = '\n'.join(all_departments)
                dispatcher.utter_message(
                    text=f"Sorry, there is no such department as '{department}' in the university. Here are the departments that the university offers:\n\n{department_list}")

            cursor.close()
            conn.close()
        else:
            dispatcher.utter_message(text="Please specify a department.")

        return []


class ActionCourseInfo(Action):

    def name(self) -> str:
        return "action_course_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        course_name = tracker.get_slot('course_name')

        if course_name:
            conn = get_db_connection()
            if not conn:
                dispatcher.utter_message(text="Sorry, I couldn't connect to the database. Please try again later.")
                return []
            cursor = conn.cursor(dictionary=True)

            # Get all unique course names for fuzzy matching
            cursor.execute("SELECT DISTINCT course_name FROM courses")
            all_courses = [course['course_name'] for course in cursor.fetchall()]

            # Find the closest match for the user's input
            course_match = get_closest_match(course_name, all_courses)

            if course_match:
                # Query to get course information for the matched course
                query = "SELECT * FROM courses WHERE course_name = %s"
                cursor.execute(query, (course_match,))
                course_info = cursor.fetchone()

                if course_info:
                    response = f"Here's the scoop on the {course_match} course:\n"
                    response += f"Level: {course_info['level']}\n"
                    response += f"Duration: {course_info['duration']}\n"
                    response += f"Intake: {course_info['intake']}\n"
                    response += f"Department: {course_info['department']}"
                    dispatcher.utter_message(text=response)
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn’t find any information on the {course_match} course.")
            else:
                 cursor.execute("SELECT course_name FROM courses")
                 all_courses = [row['course_name'] for row in cursor.fetchall()]
                 suggested_courses = "\n".join(all_courses[:5])  # Show top 5 courses as examples

                 dispatcher.utter_message(
                    text=f"Sorry, I couldn’t find a course matching '{course_name}'. Here are some examples:\n{suggested_courses}"
                 )

            cursor.close()
            conn.close()
        else:
            dispatcher.utter_message(text="Please specify a course name.")

        return []


# class ActionDepartmentInfo(Action):

#     def name(self) -> str:
#         return "action_department_info"

#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: dict) -> list:

#         department = tracker.get_slot('department')

#         if department:
#             conn = get_db_connection()
#             cursor = conn.cursor(dictionary=True)

#             # Get all unique departments for fuzzy matching
#             cursor.execute("SELECT DISTINCT department FROM courses")
#             all_departments = [dept['department'] for dept in cursor.fetchall()]

#             # Find the closest match for the user's input
#             department_match = get_closest_match(department, all_departments)

#             if department_match:
#                 # Query to get department information
#                 query = "SELECT course_name FROM courses WHERE department = %s"
#                 cursor.execute(query, (department_match,))
#                 department_info = cursor.fetchall()

#                 if department_info:
#                     courses_list = [course['course_name'] for course in department_info]
#                     info = f"Here’s some info about the {department_match} department:\n"
#                     info += f"Courses Offered: {', '.join(courses_list)}"
#                     dispatcher.utter_message(text=info)
#                 else:
#                     dispatcher.utter_message(text=f"Sorry, I couldn’t find any information on the {department_match} department.")
#             else:
#                 dispatcher.utter_message(text=f"Sorry, I couldn’t find a department matching '{department}'.")

#             cursor.close()
#             conn.close()
#         else:
#             dispatcher.utter_message(text="Please specify a department.")

#         return []
    
class ActionGetFee(Action):
    def name(self) -> str:
        return "action_get_fee"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        course_name = tracker.get_slot('course_name')
        semester = tracker.get_slot('semester')

        if course_name:
            conn = get_db_connection()
            if conn is None:
                dispatcher.utter_message(text="Sorry, I couldn't connect to the database.")
                return []

            cursor = conn.cursor(dictionary=True)

            # Get all unique course names for fuzzy matching
            cursor.execute("SELECT DISTINCT course_name FROM courses")
            all_courses = [course['course_name'] for course in cursor.fetchall()]

            # Find the closest match for the user's input
            course_match = get_closest_match(course_name, all_courses)

            if course_match:
                # Fetch course_id for the matched course
                cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course_match,))
                course_id_result = cursor.fetchone()
                
                if course_id_result:
                    course_id = course_id_result['course_id']
                    
                    if semester is not None:  # If semester is provided
                        # Fetch fees for the specified semester
                        cursor.execute("SELECT total_semester_fee FROM fees WHERE course_id = %s AND semester = %s", (course_id, semester))
                        fee_result = cursor.fetchone()

                        if fee_result:
                            semester_fee = fee_result['total_semester_fee']
                            dispatcher.utter_message(text=f"The fee for {course_match} in semester {semester} is ₹{semester_fee}.")
                        else:
                            dispatcher.utter_message(text=f"Sorry, I couldn’t find the fee details for {course_match} in semester {semester}.")
                    else:  # If no semester is provided, fetch total fee
                        cursor.execute("SELECT SUM(total_semester_fee) AS total_fee FROM fees WHERE course_id = %s", (course_id,))
                        total_fee_result = cursor.fetchone()

                        if total_fee_result and total_fee_result['total_fee']:
                            total_fee = total_fee_result['total_fee']
                            dispatcher.utter_message(text=f"The total fee for {course_match} is ₹{total_fee}.")
                        else:
                            dispatcher.utter_message(text=f"Sorry, I couldn’t find the total fee details for {course_match}.")
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn’t find the course ID for {course_match}.")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn’t find a course matching '{course_name}'.")

            cursor.close()
            conn.close()
        else:
            dispatcher.utter_message(text="Please specify a course name.")

        return []