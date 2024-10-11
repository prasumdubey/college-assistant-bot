import mysql.connector
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from fuzzywuzzy import process  # Import fuzzy matching module

# Create a function to connect to the MySQL database
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="college_assistant"
    )
    return conn

# Helper function for fuzzy matching
def get_closest_match(input_str, options_list):
    closest_match, score = process.extractOne(input_str, options_list)
    return closest_match if score > 80 else None  # Set threshold for accuracy

class ActionListCourses(Action):

    def name(self) -> str:
        return "action_list_courses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        department = tracker.get_slot('department')

        if department:
            conn = get_db_connection()
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
                dispatcher.utter_message(text=f"Sorry, I couldn’t find a department matching '{department}'.")

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
                dispatcher.utter_message(text=f"Sorry, I couldn’t find a course matching '{course_name}'.")

            cursor.close()
            conn.close()
        else:
            dispatcher.utter_message(text="Please specify a course name.")

        return []


class ActionDepartmentInfo(Action):

    def name(self) -> str:
        return "action_department_info"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        department = tracker.get_slot('department')

        if department:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Get all unique departments for fuzzy matching
            cursor.execute("SELECT DISTINCT department FROM courses")
            all_departments = [dept['department'] for dept in cursor.fetchall()]

            # Find the closest match for the user's input
            department_match = get_closest_match(department, all_departments)

            if department_match:
                # Query to get department information
                query = "SELECT course_name FROM courses WHERE department = %s"
                cursor.execute(query, (department_match,))
                department_info = cursor.fetchall()

                if department_info:
                    courses_list = [course['course_name'] for course in department_info]
                    info = f"Here’s some info about the {department_match} department:\n"
                    info += f"Courses Offered: {', '.join(courses_list)}"
                    dispatcher.utter_message(text=info)
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn’t find any information on the {department_match} department.")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn’t find a department matching '{department}'.")

            cursor.close()
            conn.close()
        else:
            dispatcher.utter_message(text="Please specify a department.")

        return []
    
class ActionFetchFees(Action):

    def name(self) -> str:
        return "action_fetch_fees"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        course_name = tracker.get_slot('course_name')
        semester = tracker.get_slot('semester')
        fee_type = tracker.get_slot('fee_type')  # Added for total fee inquiry

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get all unique course names for fuzzy matching
        cursor.execute("SELECT DISTINCT course_name FROM courses")
        all_courses = [course['course_name'] for course in cursor.fetchall()]

        # Find the closest match for the user's input
        course_match = get_closest_match(course_name, all_courses) if course_name else None

        if course_match:
            if semester == "total fee":
                # Query to get total fees for the matched course
                query = """
                    SELECT SUM(total_semester_fee) as total_fee
                    FROM fees
                    WHERE course_id = (SELECT course_id FROM courses WHERE course_name = %s)
                """
                cursor.execute(query, (course_match,))
                total_fee = cursor.fetchone()

                if total_fee and total_fee['total_fee'] is not None:
                    dispatcher.utter_message(text=f"The total fee for the {course_match} course is {total_fee['total_fee']}.")
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn’t find the total fee for the {course_match} course.")
            else:
                # Query to get all fees for the specific semester
                query = """
                    SELECT tuition_fee, dev_fee, exam_fee, regn_other_charges, job_readiness_fee, total_semester_fee
                    FROM fees
                    WHERE course_id = (SELECT course_id FROM courses WHERE course_name = %s) AND semester = %s
                """
                cursor.execute(query, (course_match, semester))
                fee_details = cursor.fetchone()

                if fee_details:
                    response = f"Here are the fee details for {course_match} in {semester}:\n"
                    response += f"Tuition Fee: {fee_details['tuition_fee']}\n"
                    response += f"Development Fee: {fee_details['dev_fee']}\n"
                    response += f"Exam Fee: {fee_details['exam_fee']}\n"
                    response += f"Registration & Other Charges: {fee_details['regn_other_charges']}\n"
                    response += f"Job Readiness Fee: {fee_details['job_readiness_fee']}\n"
                    response += f"Total Semester Fee: {fee_details['total_semester_fee']}"
                    dispatcher.utter_message(text=response)
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn’t find fee details for {course_match} in {semester}.")
        else:
            dispatcher.utter_message(text=f"Sorry, I couldn’t find a course matching '{course_name}'.")

        cursor.close()
        conn.close()
        return []