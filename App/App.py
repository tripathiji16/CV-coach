###### Packages Used ######
import streamlit as st  # core package used in this project
import pandas as pd
import base64, random
import time, datetime
import pymysql
import os
import socket
import platform
import geocoder
import secrets
import io, random
import plotly.express as px  # to create visualisations at the admin session
import plotly.graph_objects as go
from geopy.geocoders import Nominatim
import re  # for email validation

# libraries used to parse the pdf files
from pyresparser import ResumeParser
from pdfminer3.layout import LAParams, LTTextBox
from pdfminer3.pdfpage import PDFPage
from pdfminer3.pdfinterp import PDFResourceManager
from pdfminer3.pdfinterp import PDFPageInterpreter
from pdfminer3.converter import TextConverter
from streamlit_tags import st_tags
from PIL import Image

# pre stored data for prediction purposes
from Courses import (
    ds_course,
    web_course,
    android_course,
    ios_course,
    uiux_course,
    resume_videos,
    interview_videos,
)
import nltk

nltk.download("stopwords")


###### Validation Functions ######
def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def validate_mobile(mobile):
    # Remove any spaces or special characters
    mobile = "".join(filter(str.isdigit, mobile))
    # Check if mobile number has 10 digits
    return len(mobile) == 10


###### Preprocessing functions ######


# Generates a link allowing the data in a given panda dataframe to be downloaded in csv format
def get_csv_download_link(df, filename, text):
    csv = df.to_csv(index=False)
    ## bytes conversions
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">{text}</a>'
    return href


# Reads Pdf file and check_extractable
def pdf_reader(file):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)
    with open(file, "rb") as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)
            print(page)
        text = fake_file_handle.getvalue()

    ## close open handles
    converter.close()
    fake_file_handle.close()
    return text


# show uploaded file path to view pdf_display
def show_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# course recommendations which has data already loaded from Courses.py
def course_recommender(course_list):
    st.subheader("**Courses & Certificates Recommendations 👨‍🎓**")
    c = 0
    rec_course = []
    ## slider to choose from range 1-10
    no_of_reco = st.slider("Choose Number of Course Recommendations:", 1, 10, 5)
    random.shuffle(course_list)
    for c_name, c_link in course_list:
        c += 1
        st.markdown(f"({c}) [{c_name}]({c_link})")
        rec_course.append(c_name)
        if c == no_of_reco:
            break
    return rec_course


###### Database Stuffs ######


# sql connector
connection = pymysql.connect(host="localhost", user="root", password="qwerty", db="cv")
cursor = connection.cursor()


# inserting miscellaneous data, fetched results, prediction and recommendation into user_data table
def insert_data(
    sec_token,
    ip_add,
    host_name,
    dev_user,
    os_name_ver,
    latlong,
    city,
    state,
    country,
    act_name,
    act_mail,
    act_mob,
    name,
    email,
    res_score,
    timestamp,
    no_of_pages,
    reco_field,
    cand_level,
    skills,
    recommended_skills,
    courses,
    pdf_name,
):
    DB_table_name = "user_data"
    insert_sql = (
        "insert into "
        + DB_table_name
        + """
    values (0,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
    )
    rec_values = (
        str(sec_token),
        str(ip_add),
        host_name,
        dev_user,
        os_name_ver,
        str(latlong),
        city,
        state,
        country,
        act_name,
        act_mail,
        act_mob,
        name,
        email,
        str(res_score),
        timestamp,
        str(no_of_pages),
        reco_field,
        cand_level,
        skills,
        recommended_skills,
        courses,
        pdf_name,
    )
    cursor.execute(insert_sql, rec_values)
    connection.commit()


# inserting feedback data into user_feedback table
def insertf_data(feed_name, feed_email, feed_score, comments, Timestamp):
    DBf_table_name = "user_feedback"
    insertfeed_sql = (
        "insert into "
        + DBf_table_name
        + """
    values (0,%s,%s,%s,%s,%s)"""
    )
    rec_values = (feed_name, feed_email, feed_score, comments, Timestamp)
    cursor.execute(insertfeed_sql, rec_values)
    connection.commit()


###### Setting Page Configuration (favicon, Logo, Title) ######


st.set_page_config(
    page_title="CV coach",
    page_icon="./Logo/3.png",
)


###### Main function run() ######


def run():

    # (Logo, Heading, Sidebar etc)
    img = Image.open("./Logo/1.png")
    st.image(img, use_column_width=True)

    # Sidebar styling
    st.sidebar.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        [data-testid="stSidebar"] > div:first-child {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .custom-sidebar-footer {
            margin-top: auto;
            padding-bottom: 1.5rem;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    st.sidebar.markdown("# Choose Activity:")
    activities = ["User", "Feedback", "About", "Admin"]
    choice = st.sidebar.selectbox("Select an option:", activities)

    # Footer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div class="custom-sidebar-footer">
            <div style='text-align: center; color: #021659; font-size: 1.05rem; margin-top: 1.5rem;'>
                <span style='font-weight: 600;'>Built with 🫶🏻 by</span>
                <ul style='list-style: none; padding: 0; margin: 0.5rem 0 0 0; text-align: center;'>
                    <li style='margin-bottom: 0.3rem;'><span style='background: #e5d4ed; border-radius: 8px; padding: 0.2rem 0.7rem; display: inline-block;'>Vaishnavi Tripathi</span></li>
                    <li><span style='background: #bfd7ed; border-radius: 8px; padding: 0.2rem 0.7rem; display: inline-block;'>Jai Srivastava</span></li>
                </ul>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    ###### Creating Database and Table ######

    # Create the DB
    db_sql = """CREATE DATABASE IF NOT EXISTS CV;"""
    cursor.execute(db_sql)

    # Create table user_data and user_feedback
    DB_table_name = "user_data"
    table_sql = (
        "CREATE TABLE IF NOT EXISTS "
        + DB_table_name
        + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                    sec_token varchar(20) NOT NULL,
                    ip_add varchar(50) NULL,
                    host_name varchar(50) NULL,
                    dev_user varchar(50) NULL,
                    os_name_ver varchar(50) NULL,
                    latlong varchar(50) NULL,
                    city varchar(50) NULL,
                    state varchar(50) NULL,
                    country varchar(50) NULL,
                    act_name varchar(50) NOT NULL,
                    act_mail varchar(50) NOT NULL,
                    act_mob varchar(20) NOT NULL,
                    Name varchar(500) NOT NULL,
                    Email_ID VARCHAR(500) NOT NULL,
                    resume_score VARCHAR(8) NOT NULL,
                    Timestamp VARCHAR(50) NOT NULL,
                    Page_no VARCHAR(5) NOT NULL,
                    Predicted_Field BLOB NOT NULL,
                    User_level BLOB NOT NULL,
                    Actual_skills BLOB NOT NULL,
                    Recommended_skills BLOB NOT NULL,
                    Recommended_courses BLOB NOT NULL,
                    pdf_name varchar(50) NOT NULL,
                    PRIMARY KEY (ID)
                    );
                """
    )
    cursor.execute(table_sql)

    DBf_table_name = "user_feedback"
    tablef_sql = (
        "CREATE TABLE IF NOT EXISTS "
        + DBf_table_name
        + """
                    (ID INT NOT NULL AUTO_INCREMENT,
                        feed_name varchar(50) NOT NULL,
                        feed_email VARCHAR(50) NOT NULL,
                        feed_score VARCHAR(5) NOT NULL,
                        comments VARCHAR(100) NULL,
                        Timestamp VARCHAR(50) NOT NULL,
                        PRIMARY KEY (ID)
                    );
                """
    )
    cursor.execute(tablef_sql)

    ###### CODE FOR CLIENT SIDE (USER) ######

    if choice == "User":

        # User form with enhanced styling
        st.markdown(
            """
            <div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
                <h2 style='color: #021659; margin-bottom: 1.5rem;'>User Information</h2>
                <p style='color: #666; margin-bottom: 1rem;'>Please fill in your details to proceed with resume analysis.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("user_details_form"):
            col1, col2 = st.columns(2)
            with col1:
                act_name = st.text_input(
                    "Full Name*", placeholder="Enter your full name"
                )
            with col2:
                act_mail = st.text_input(
                    "Email Address*", placeholder="Enter your email"
                )

            act_mob = st.text_input(
                "Mobile Number*", placeholder="Enter your 10-digit mobile number"
            )

            submitted = st.form_submit_button("Submit Details")

            if submitted:
                # Validation logic remains the same
                if not act_name:
                    st.error("Name is required!")
                    st.stop()

                if not act_mail:
                    st.error("Email is required!")
                    st.stop()
                elif not validate_email(act_mail):
                    st.error("Please enter a valid email address!")
                    st.stop()

                if not act_mob:
                    st.error("Mobile number is required!")
                    st.stop()
                elif not validate_mobile(act_mob):
                    st.error("Please enter a valid 10-digit mobile number!")
                    st.stop()

                st.success(
                    "Details submitted successfully! You can now upload your resume."
                )

                # Store user details in session state
                st.session_state.user_details = {
                    "name": act_name,
                    "email": act_mail,
                    "mobile": act_mob,
                }

                # Collect system information
                sec_token = secrets.token_urlsafe(12)
                host_name = socket.gethostname()
                ip_add = socket.gethostbyname(host_name)
                dev_user = os.getlogin()
                os_name_ver = platform.system() + " " + platform.release()
                g = geocoder.ip("me")
                latlong = g.latlng
                geolocator = Nominatim(user_agent="http")
                location = geolocator.reverse(latlong, language="en")
                address = location.raw["address"]
                cityy = address.get("city", "")
                statee = address.get("state", "")
                countryy = address.get("country", "")
                city = cityy
                state = statee
                country = countryy

                st.session_state.system_info = {
                    "sec_token": sec_token,
                    "host_name": host_name,
                    "ip_add": ip_add,
                    "dev_user": dev_user,
                    "os_name_ver": os_name_ver,
                    "latlong": latlong,
                    "city": city,
                    "state": state,
                    "country": country,
                }

        if "user_details" in st.session_state and "system_info" in st.session_state:
            st.markdown(
                """
                <div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
                    <h2 style='color: #021659; margin-bottom: 1.5rem;'>Resume Upload</h2>
                    <p style='color: #666; margin-bottom: 1rem;'>Upload your resume in PDF format to get started with the analysis.</p>
                </div>
            """,
                unsafe_allow_html=True,
            )

            pdf_file = st.file_uploader("Select Your Resume", type=["pdf"])
            if pdf_file is not None:
                with st.spinner("Analyzing your resume..."):
                    time.sleep(4)

                save_image_path = "./Uploaded_Resumes/" + pdf_file.name
                pdf_name = pdf_file.name
                with open(save_image_path, "wb") as f:
                    f.write(pdf_file.getbuffer())
                show_pdf(save_image_path)

                resume_data = ResumeParser(save_image_path).get_extracted_data()
                if resume_data:
                    resume_text = pdf_reader(save_image_path)

                    # Improved Resume validation: check for essential sections, email, phone, and length
                    section_headers = [
                        "summary",
                        "objective",
                        "profile",
                        "education",
                        "degree",
                        "university",
                        "college",
                        "school",
                        "skills",
                        "experience",
                        "work experience",
                        "employment",
                        "internship",
                        "projects",
                        "certifications",
                        "achievements",
                        "awards",
                        "languages",
                        "interests",
                        "hobbies",
                        "reference",
                    ]
                    found_sections = [
                        header
                        for header in section_headers
                        if re.search(
                            rf"^\s*{header}\b",
                            resume_text,
                            re.IGNORECASE | re.MULTILINE,
                        )
                    ]
                    # Email and phone regex
                    email_found = re.search(
                        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", resume_text
                    )
                    phone_found = re.search(
                        r"\b(\+\d{1,3}[-.\s]?)?(\d{10}|\d{3}[-.\s]\d{3}[-.\s]\d{4})\b",
                        resume_text,
                    )
                    # Minimum text length
                    min_length = 500
                    if (
                        len(found_sections) < 3
                        or not email_found
                        or not phone_found
                        or len(resume_text) < min_length
                    ):
                        st.error(
                            "The uploaded PDF does not appear to be a valid resume. Please upload a resume containing relevant sections (like Education, Experience, Skills,a valid email,a phone number, etc.)"
                        )
                        return

                    st.markdown(
                        """
                        <div style='background-color: #e8f5e9; padding: 1.5rem; border-radius: 10px; margin: 1rem 0;'>
                            <h3 style='color: #021659; margin-bottom: 1rem;'>Welcome, {}</h3>
                        </div>
                    """.format(
                            resume_data["name"]
                        ),
                        unsafe_allow_html=True,
                    )

                    st.markdown(
                        """
                        <div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin: 1rem 0;'>
                            <h3 style='color: #021659; margin-bottom: 1rem;'>Resume Analysis Report</h3>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Display basic info in a cleaner format
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Name:** {resume_data['name']}")
                        st.markdown(f"**Email:** {resume_data['email']}")
                    with col2:
                        st.markdown(f"**Contact:** {resume_data['mobile_number']}")
                        st.markdown(f"**Degree:** {resume_data['degree']}")
                        st.markdown(f"**Pages:** {resume_data['no_of_pages']}")

                    ## Predicting Candidate Experience Level
                    ### Trying with different possibilities
                    cand_level = ""
                    if resume_data["no_of_pages"] < 1:
                        cand_level = "NA"
                        st.markdown(
                            """<h4 style='text-align: left; color: #d73b5c;'>You are at Fresher level!</h4>""",
                            unsafe_allow_html=True,
                        )

                    #### if internship then intermediate level
                    elif "INTERNSHIP" in resume_text:
                        cand_level = "Intermediate"
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "INTERNSHIPS" in resume_text:
                        cand_level = "Intermediate"
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Internship" in resume_text:
                        cand_level = "Intermediate"
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Internships" in resume_text:
                        cand_level = "Intermediate"
                        st.markdown(
                            """<h4 style='text-align: left; color: #1ed760;'>You are at intermediate level!</h4>""",
                            unsafe_allow_html=True,
                        )

                    #### if Work Experience/Experience then Experience level
                    elif "EXPERIENCE" in resume_text:
                        cand_level = "Experienced"
                        st.markdown(
                            """<h4 style='text-align: left; color: #fba171;'>You are at experience level!""",
                            unsafe_allow_html=True,
                        )
                    elif "WORK EXPERIENCE" in resume_text:
                        cand_level = "Experienced"
                        st.markdown(
                            """<h4 style='text-align: left; color: #fba171;'>You are at experience level!""",
                            unsafe_allow_html=True,
                        )
                    elif "Experience" in resume_text:
                        cand_level = "Experienced"
                        st.markdown(
                            """<h4 style='text-align: left; color: #fba171;'>You are at experience level!""",
                            unsafe_allow_html=True,
                        )
                    elif "Work Experience" in resume_text:
                        cand_level = "Experienced"
                        st.markdown(
                            """<h4 style='text-align: left; color: #fba171;'>You are at experience level!""",
                            unsafe_allow_html=True,
                        )
                    else:
                        cand_level = "Fresher"
                        st.markdown(
                            """<h4 style='text-align: left; color: #fba171;'>You are at Fresher level!!""",
                            unsafe_allow_html=True,
                        )

                    ## Skills Analyzing and Recommendation
                    st.subheader("**💡Skills Recommendation:**")

                    ### Current Analyzed Skills
                    keywords = st_tags(
                        label="### Your Current Skills",
                        text="See CVcoach's skills recommendation below",
                        value=resume_data["skills"],
                        key="1  ",
                    )

                    ### Keywords for Recommendations
                    ds_keyword = [
                        "tensorflow",
                        "keras",
                        "pytorch",
                        "machine learning",
                        "deep learning",
                        "flask",
                        "streamlit",
                        "python",
                        "data science",
                        "data analysis",
                        "statistics",
                        "numpy",
                        "pandas",
                        "scikit-learn",
                        "artificial intelligence",
                        "ai",
                        "ml",
                        "data visualization",
                        "matplotlib",
                        "seaborn",
                    ]
                    web_keyword = [
                        "react",
                        "django",
                        "node js",
                        "react js",
                        "php",
                        "laravel",
                        "magento",
                        "wordpress",
                        "javascript",
                        "angular js",
                        "c#",
                        "asp.net",
                        "flask",
                        "html",
                        "css",
                        "bootstrap",
                        "frontend",
                        "backend",
                        "full stack",
                        "web development",
                        "rest api",
                        "graphql",
                    ]
                    android_keyword = [
                        "android",
                        "android development",
                        "flutter",
                        "kotlin",
                        "xml",
                        "kivy",
                        "java",
                        "mobile development",
                        "android studio",
                        "firebase",
                        "material design",
                        "android sdk",
                        "gradle",
                        "android jetpack",
                    ]
                    ios_keyword = [
                        "ios",
                        "ios development",
                        "swift",
                        "cocoa",
                        "cocoa touch",
                        "xcode",
                        "objective-c",
                        "swiftui",
                        "core data",
                        "core animation",
                        "autolayout",
                        "storyboard",
                        "interface builder",
                    ]
                    uiux_keyword = [
                        "ux",
                        "adobe xd",
                        "figma",
                        "zeplin",
                        "balsamiq",
                        "ui",
                        "prototyping",
                        "wireframes",
                        "storyframes",
                        "adobe photoshop",
                        "photoshop",
                        "editing",
                        "adobe illustrator",
                        "illustrator",
                        "adobe after effects",
                        "after effects",
                        "adobe premier pro",
                        "premier pro",
                        "adobe indesign",
                        "indesign",
                        "wireframe",
                        "solid",
                        "grasp",
                        "user research",
                        "user experience",
                        "design thinking",
                        "interaction design",
                        "visual design",
                    ]
                    n_any = [
                        "english",
                        "communication",
                        "writing",
                        "microsoft office",
                        "leadership",
                        "customer management",
                        "social media",
                    ]
                    ### Skill Recommendations Starts
                    recommended_skills = []
                    reco_field = ""
                    rec_course = ""

                    # Convert skills to lowercase for better matching
                    user_skills = [skill.lower() for skill in resume_data["skills"]]

                    # Count matches for each field
                    field_matches = {
                        "Data Science": sum(
                            1 for skill in user_skills if skill in ds_keyword
                        ),
                        "Web Development": sum(
                            1 for skill in user_skills if skill in web_keyword
                        ),
                        "Android Development": sum(
                            1 for skill in user_skills if skill in android_keyword
                        ),
                        "IOS Development": sum(
                            1 for skill in user_skills if skill in ios_keyword
                        ),
                        "UI-UX Development": sum(
                            1 for skill in user_skills if skill in uiux_keyword
                        ),
                    }

                    # Get the field with most matches
                    max_matches = max(field_matches.values())
                    if max_matches > 0:
                        reco_field = max(field_matches.items(), key=lambda x: x[1])[0]

                        # Get recommendations based on the field
                        if reco_field == "Data Science":
                            recommended_skills = [
                                "Data Visualization",
                                "Predictive Analysis",
                                "Statistical Modeling",
                                "Data Mining",
                                "Clustering & Classification",
                                "Data Analytics",
                                "Quantitative Analysis",
                                "Web Scraping",
                                "ML Algorithms",
                                "Keras",
                                "Pytorch",
                                "Probability",
                                "Scikit-learn",
                                "Tensorflow",
                                "Flask",
                                "Streamlit",
                                "Python",
                                "SQL",
                                "Big Data",
                                "Deep Learning",
                            ]
                            st.success(
                                "** Our analysis suggests you are looking for Data Science Jobs.**"
                            )
                            rec_course = course_recommender(ds_course)

                        elif reco_field == "Web Development":
                            recommended_skills = [
                                "React",
                                "Django",
                                "Node JS",
                                "React JS",
                                "PHP",
                                "Laravel",
                                "Magento",
                                "WordPress",
                                "JavaScript",
                                "Angular JS",
                                "C#",
                                "Flask",
                                "SDK",
                                "HTML5",
                                "CSS3",
                                "Bootstrap",
                                "REST API",
                                "GraphQL",
                                "MongoDB",
                                "MySQL",
                                "PostgreSQL",
                            ]
                            st.success(
                                "** Our analysis suggests you are looking for Web Development Jobs **"
                            )
                            rec_course = course_recommender(web_course)

                        elif reco_field == "Android Development":
                            recommended_skills = [
                                "Android",
                                "Android Development",
                                "Flutter",
                                "Kotlin",
                                "XML",
                                "Java",
                                "Kivy",
                                "GIT",
                                "SDK",
                                "SQLite",
                                "Firebase",
                                "Material Design",
                                "Android Jetpack",
                                "MVVM",
                                "REST API",
                            ]
                            st.success(
                                "** Our analysis suggests you are looking for Android App Development Jobs **"
                            )
                            rec_course = course_recommender(android_course)

                        elif reco_field == "IOS Development":
                            recommended_skills = [
                                "IOS",
                                "IOS Development",
                                "Swift",
                                "Cocoa",
                                "Cocoa Touch",
                                "Xcode",
                                "Objective-C",
                                "SQLite",
                                "Plist",
                                "StoreKit",
                                "UI-Kit",
                                "AV Foundation",
                                "Auto-Layout",
                                "SwiftUI",
                                "Core Data",
                                "Core Animation",
                            ]
                            st.success(
                                "** Our analysis suggests you are looking for IOS App Development Jobs **"
                            )
                            rec_course = course_recommender(ios_course)

                        elif reco_field == "UI-UX Development":
                            recommended_skills = [
                                "UI",
                                "User Experience",
                                "Adobe XD",
                                "Figma",
                                "Zeplin",
                                "Balsamiq",
                                "Prototyping",
                                "Wireframes",
                                "Storyframes",
                                "Adobe Photoshop",
                                "Editing",
                                "Illustrator",
                                "After Effects",
                                "Premier Pro",
                                "Indesign",
                                "Wireframe",
                                "Solid",
                                "Grasp",
                                "User Research",
                                "Design Thinking",
                                "Interaction Design",
                            ]
                            st.success(
                                "** Our analysis suggests you are looking for UI-UX Development Jobs **"
                            )
                            rec_course = course_recommender(uiux_course)
                    else:
                        # If no specific field matches, provide general recommendations
                        recommended_skills = [
                            "Python",
                            "JavaScript",
                            "SQL",
                            "Git",
                            "Problem Solving",
                            "Communication",
                            "Team Collaboration",
                            "Project Management",
                            "Agile Methodologies",
                            "Data Analysis",
                            "Critical Thinking",
                        ]
                        st.warning(
                            "** Based on your skills, we recommend focusing on these fundamental skills to enhance your profile **"
                        )
                        rec_course = "General Development Skills"

                    # Display recommended skills
                    recommended_keywords = st_tags(
                        label="### Recommended skills for you.",
                        text="Recommended skills generated from System",
                        value=recommended_skills,
                        key="2",
                    )
                    st.markdown(
                        """<h5 style='text-align: left; color: #1ed760;'>Adding these skills to your resume will boost🚀 your chances of getting a Job</h5>""",
                        unsafe_allow_html=True,
                    )

                    ## Resume Scorer & Resume Writing Tips
                    st.subheader("**Resume Tips & Ideas **")
                    resume_score = 0

                    ### Predicting Whether these key points are added to the resume
                    if "Objective" or "Summary" in resume_text:
                        resume_score = resume_score + 6
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Objective/Summary</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add your career objective, it will give your career intension to the Recruiters.</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "Education" or "School" or "College" in resume_text:
                        resume_score = resume_score + 12
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Education Details</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Education. It will give Your Qualification level to the recruiter</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "EXPERIENCE" in resume_text:
                        resume_score = resume_score + 16
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Experience" in resume_text:
                        resume_score = resume_score + 16
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Experience</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Experience. It will help you to stand out from crowd</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "INTERNSHIPS" in resume_text:
                        resume_score = resume_score + 6
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "INTERNSHIP" in resume_text:
                        resume_score = resume_score + 6
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Internships" in resume_text:
                        resume_score = resume_score + 6
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Internship" in resume_text:
                        resume_score = resume_score + 6
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Internships</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Internships. It will help you to stand out from crowd</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "SKILLS" in resume_text:
                        resume_score = resume_score + 7
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "SKILL" in resume_text:
                        resume_score = resume_score + 7
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Skills" in resume_text:
                        resume_score = resume_score + 7
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Skill" in resume_text:
                        resume_score = resume_score + 7
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added Skills</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Skills. It will help you a lot</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "HOBBIES" in resume_text:
                        resume_score = resume_score + 4
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Hobbies" in resume_text:
                        resume_score = resume_score + 4
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Hobbies</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Hobbies. It will show your personality to the Recruiters and give the assurance that you are fit for this role or not.</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "INTERESTS" in resume_text:
                        resume_score = resume_score + 5
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Interests" in resume_text:
                        resume_score = resume_score + 5
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Interest</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Interest. It will show your interest other that job.</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "ACHIEVEMENTS" in resume_text:
                        resume_score = resume_score + 13
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Achievements" in resume_text:
                        resume_score = resume_score + 13
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Achievements </h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Achievements. It will show that you are capable for the required position.</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "CERTIFICATIONS" in resume_text:
                        resume_score = resume_score + 12
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Certifications" in resume_text:
                        resume_score = resume_score + 12
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Certification" in resume_text:
                        resume_score = resume_score + 12
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Certifications </h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Certifications. It will show that you have done some specialization for the required position.</h4>""",
                            unsafe_allow_html=True,
                        )

                    if "PROJECTS" in resume_text:
                        resume_score = resume_score + 19
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "PROJECT" in resume_text:
                        resume_score = resume_score + 19
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Projects" in resume_text:
                        resume_score = resume_score + 19
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>""",
                            unsafe_allow_html=True,
                        )
                    elif "Project" in resume_text:
                        resume_score = resume_score + 19
                        st.markdown(
                            """<h5 style='text-align: left; color: #1ed760;'>[+] Awesome! You have added your Projects</h4>""",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            """<h5 style='text-align: left; color: #000000;'>[-] Please add Projects. It will show that you have done work related the required position or not.</h4>""",
                            unsafe_allow_html=True,
                        )

                    st.subheader("**Resume Score 📝**")

                    # Custom styling for the score section
                    st.markdown(
                        """
                        <style>
                            .score-container {
                                background-color: #f8f9fa;
                                padding: 2rem;
                                border-radius: 10px;
                                margin: 1rem 0;
                                text-align: center;
                            }
                            .score-value {
                                font-size: 2.5rem;
                                font-weight: bold;
                                color: #021659;
                                margin: 1rem 0;
                            }
                            .score-label {
                                color: #424242;
                                font-size: 1.1rem;
                                margin-bottom: 1rem;
                            }
                            .score-progress {
                                margin: 1rem 0;
                            }
                            .score-tip {
                                background-color: #e8f5e9;
                                padding: 1rem;
                                border-radius: 5px;
                                margin-top: 1rem;
                                border-left: 4px solid #4caf50;
                            }
                        </style>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Score display container
                    st.markdown(
                        """
                        <div class="score-container">
                            <div class="score-label">Your Resume Writing Score</div>
                            <div class="score-value">{}</div>
                            <div class="score-progress">
                    """.format(
                            resume_score
                        ),
                        unsafe_allow_html=True,
                    )

                    # Progress bar
                    my_bar = st.progress(0)
                    score = 0
                    for percent_complete in range(resume_score):
                        score += 1
                        time.sleep(0.1)
                        my_bar.progress(percent_complete + 1)

                    # Score explanation and tips
                    st.markdown(
                        """
                        </div>
                        <div class="score-tip">
                            <strong>💡 Tip:</strong> This score is calculated based on the content and structure of your resume. 
                            Higher scores indicate better resume quality and completeness.
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Score breakdown
                    st.markdown(
                        """
                        <div style='margin-top: 2rem;'>
                            <h4 style='color: #021659; margin-bottom: 1rem;'>Score Breakdown</h4>
                            <div style='display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;'>
                                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px;'>
                                    <h5 style='color: #021659; margin-bottom: 0.5rem;'>Content Quality</h5>
                                    <p style='color: #424242; font-size: 0.9rem;'>Based on completeness and relevance of information</p>
                                </div>
                                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px;'>
                                    <h5 style='color: #021659; margin-bottom: 0.5rem;'>Structure</h5>
                                    <p style='color: #424242; font-size: 0.9rem;'>Organization and formatting of resume sections</p>
                                </div>
                                <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 8px;'>
                                    <h5 style='color: #021659; margin-bottom: 0.5rem;'>Skills Match</h5>
                                    <p style='color: #424242; font-size: 0.9rem;'>Alignment with industry requirements</p>
                                </div>
                            </div>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Score interpretation
                    st.markdown(
                        """
                        <div style='margin-top: 2rem; padding: 1rem; background-color: #e3f2fd; border-radius: 8px; border-left: 4px solid #2196f3;'>
                            <h4 style='color: #021659; margin-bottom: 0.5rem;'>What Your Score Means</h4>
                            <ul style='color: #424242; margin: 0; padding-left: 1.5rem;'>
                                <li><strong>80-100:</strong> Excellent resume with comprehensive content</li>
                                <li><strong>60-79:</strong> Good resume with room for improvement</li>
                                <li><strong>40-59:</strong> Basic resume that needs enhancement</li>
                                <li><strong>Below 40:</strong> Resume needs significant improvement</li>
                            </ul>
                        </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    st.warning(
                        "** Note: This score is calculated based on the content that you have in your Resume. **"
                    )

                    ### Getting Current Date and Time
                    ts = time.time()
                    cur_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                    cur_time = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                    timestamp = str(cur_date + "_" + cur_time)

                    # Check for required fields in resume_data before inserting into DB
                    required_resume_fields = ["name", "email", "mobile_number"]
                    missing_fields = [
                        field
                        for field in required_resume_fields
                        if not resume_data.get(field)
                    ]
                    if missing_fields:
                        st.error(
                            f"The following required fields are missing in your resume: {', '.join(missing_fields)}. Please upload a resume with all necessary information."
                        )
                        return

                    ## Calling insert_data to add all the data into user_data
                    insert_data(
                        str(st.session_state.system_info["sec_token"]),
                        str(st.session_state.system_info["ip_add"]),
                        st.session_state.system_info["host_name"],
                        st.session_state.system_info["dev_user"],
                        st.session_state.system_info["os_name_ver"],
                        str(st.session_state.system_info["latlong"]),
                        st.session_state.system_info["city"],
                        st.session_state.system_info["state"],
                        st.session_state.system_info["country"],
                        st.session_state.user_details["name"],
                        st.session_state.user_details["email"],
                        st.session_state.user_details["mobile"],
                        resume_data["name"],
                        resume_data["email"],
                        str(resume_score),
                        timestamp,
                        str(resume_data["no_of_pages"]),
                        reco_field,
                        cand_level,
                        str(resume_data["skills"]),
                        str(recommended_skills),
                        str(rec_course),
                        pdf_name,
                    )

                    ## Recommending Resume Writing Video
                    st.header("**Bonus Video for Resume Writing Tips💡**")
                    resume_vid = random.choice(resume_videos)
                    st.video(resume_vid)

                    ## Recommending Interview Preparation Video
                    st.header("**Bonus Video for Interview Tips💡**")
                    interview_vid = random.choice(interview_videos)
                    st.video(interview_vid)

                    ## On Successful Result
                    st.balloons()

                else:
                    st.error("Something went wrong..")
        else:
            st.info(
                "Please fill in your details above to proceed with resume analysis."
            )

    ###### CODE FOR FEEDBACK SIDE ######
    elif choice == "Feedback":
        st.markdown(
            """
            <div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
                <h2 style='color: #021659; margin-bottom: 1.5rem;'>Feedback Form</h2>
                <p style='color: #666; margin-bottom: 1rem;'>Your feedback helps us improve our service.</p>
            </div>
        """,
            unsafe_allow_html=True,
        )

        with st.form("feedback_form"):
            col1, col2 = st.columns(2)
            with col1:
                feed_name = st.text_input("Name", placeholder="Enter your name")
            with col2:
                feed_email = st.text_input("Email", placeholder="Enter your email")

            feed_score = st.slider(
                "Rate Us", 1, 5, 3, help="Rate your experience from 1 to 5"
            )
            comments = st.text_area(
                "Comments", placeholder="Share your thoughts with us"
            )

            submitted = st.form_submit_button("Submit Feedback")

            if submitted:
                ts = time.time()
                cur_date = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
                cur_time = datetime.datetime.fromtimestamp(ts).strftime("%H:%M:%S")
                timestamp = str(cur_date + "_" + cur_time)

                insertf_data(feed_name, feed_email, feed_score, comments, timestamp)
                st.success("Thank you for your feedback! We appreciate your input.")
                st.balloons()

        # query to fetch data from user feedback table
        query = "select * from user_feedback"
        plotfeed_data = pd.read_sql(query, connection)

        # fetching feed_score from the query and getting the unique values and total value count
        labels = plotfeed_data.feed_score.unique()
        values = plotfeed_data.feed_score.value_counts()

        # plotting pie chart for user ratings
        st.subheader("**Past User Rating's**")
        fig = px.pie(
            values=values,
            names=labels,
            title="Chart of User Rating Score From 1 - 5",
            color_discrete_sequence=px.colors.sequential.Aggrnyl,
        )
        st.plotly_chart(fig)

        #  Fetching Comment History
        cursor.execute("select feed_name, comments from user_feedback")
        plfeed_cmt_data = cursor.fetchall()

        st.subheader("**User Comment's**")
        dff = pd.DataFrame(plfeed_cmt_data, columns=["User", "Comment"])
        st.dataframe(dff, width=1000)

    ###### CODE FOR ABOUT PAGE ######
    elif choice == "About":
        st.markdown(
            """
            <div style='background-color: #f8f9fa; padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
                <h2 style='color: #021659; margin-bottom: 1.5rem; text-align: center;'>About CV Coach</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div style='background-color: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); max-width: 800px; margin: 0 auto;'>
                <p style='color: #424242; line-height: 1.8; margin-bottom: 2rem; text-align: justify;'>
                    <b>CV Coach</b> is an intelligent resume analysis and career guidance tool designed to help job seekers enhance their CVs, understand their strengths, and prepare effectively for job roles.<br>
                    Powered by Natural Language Processing (NLP), this project bridges the gap between job seekers and industry expectations by providing personalized, actionable feedback.
                </p>
                <h3 style='color: #021659; margin-bottom: 1rem; border-bottom: 2px solid #021659; padding-bottom: 0.5rem;'>Key Features</h3>
                <ul style='color: #424242; line-height: 1.7; margin-bottom: 2rem;'>
                    <li><b>📊 Resume Analysis:</b> Advanced parsing of resumes using NLP to extract key information and provide detailed insights.</li>
                    <li><b>🎯 Job Role Prediction:</b> AI-powered matching of your skills and experience with suitable job roles.</li>
                    <li><b>💡 Skills Recommendation:</b> Personalized suggestions for skills to enhance your profile and career prospects.</li>
                    <li><b>📝 Resume Scoring:</b> Comprehensive evaluation of your resume with actionable improvement tips.</li>
                </ul>
                <h3 style='color: #021659; margin-bottom: 1rem; border-bottom: 2px solid #021659; padding-bottom: 0.5rem;'>How It Works</h3>
                <ol style='color: #424242; line-height: 1.7; margin-bottom: 2rem;'>
                    <li>Upload your resume in PDF format</li>
                    <li>Our AI analyzes your resume content</li>
                    <li>Receive personalized recommendations</li>
                    <li>Get interview preparation resources</li>
                </ol>
                <h3 style='color: #021659; margin-bottom: 1rem; border-bottom: 2px solid #021659; padding-bottom: 0.5rem;'>Our Team</h3>
                <div style='display: flex; gap: 2rem; flex-wrap: wrap; justify-content: center; margin-bottom: 2rem;'>
                    <div style='text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 8px; min-width: 200px;'>
                        <h4 style='color: #021659; margin-bottom: 0.5rem;'>Vaishnavi Tripathi</h4>
                        <p style='color: #424242; font-size: 0.9rem; margin: 0;'>Developer | UI Designer</p>
                    </div>
                    <div style='text-align: center; padding: 1rem; background-color: #f8f9fa; border-radius: 8px; min-width: 200px;'>
                        <h4 style='color: #021659; margin-bottom: 0.5rem;'>Jai Srivastava</h4>
                        <p style='color: #424242; font-size: 0.9rem; margin: 0;'>Developer | NLP Engineer</p>
                    </div>
                </div>
                <div style='margin: 2rem 0; text-align: center;'>
                    <h3 style='color: #021659; margin-bottom: 1rem;'>Our Mission</h3>
                    <p style='color: #424242; line-height: 1.8; font-style: italic;'>
                        "To empower individuals in their job search journey with actionable insights, role-specific guidance, and resume-building confidence — all in one tool."
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    ###### CODE FOR ADMIN SIDE (ADMIN) ######
    else:
        st.success("Welcome to Admin Side")

        #  Admin Login
        ad_user = st.text_input("Username", placeholder="Enter admin username")
        ad_password = st.text_input(
            "Password", type="password", placeholder="Enter admin password"
        )

        if st.button("Login"):

            ## Credentials
            if ad_user == "admin" and ad_password == "admin@resume-analyzer":

                ### Fetch miscellaneous data from user_data(table) and convert it into dataframe
                cursor.execute(
                    """SELECT ID, ip_add, resume_score, convert(Predicted_Field using utf8), convert(User_level using utf8), city, state, country from user_data"""
                )
                datanalys = cursor.fetchall()
                plot_data = pd.DataFrame(
                    datanalys,
                    columns=[
                        "Idt",
                        "IP_add",
                        "resume_score",
                        "Predicted_Field",
                        "User_Level",
                        "City",
                        "State",
                        "Country",
                    ],
                )

                ### Total Users Count with a Welcome Message
                values = plot_data.Idt.count()
                st.success(
                    "Welcome Administrator! Total %d " % values
                    + " User's Have Used Our Tool : )"
                )

                ### Fetch user data from user_data(table) and convert it into dataframe
                cursor.execute(
                    """SELECT ID, sec_token, ip_add, act_name, act_mail, act_mob, convert(Predicted_Field using utf8), Timestamp, Name, Email_ID, resume_score, Page_no, pdf_name, convert(User_level using utf8), convert(Actual_skills using utf8), convert(Recommended_skills using utf8), convert(Recommended_courses using utf8), city, state, country, latlong, os_name_ver, host_name, dev_user from user_data"""
                )
                data = cursor.fetchall()

                st.header("**User's Data**")
                df = pd.DataFrame(
                    data,
                    columns=[
                        "ID",
                        "Token",
                        "IP Address",
                        "Name",
                        "Mail",
                        "Mobile Number",
                        "Predicted Field",
                        "Timestamp",
                        "Predicted Name",
                        "Predicted Mail",
                        "Resume Score",
                        "Total Page",
                        "File Name",
                        "User Level",
                        "Actual Skills",
                        "Recommended Skills",
                        "Recommended Course",
                        "City",
                        "State",
                        "Country",
                        "Lat Long",
                        "Server OS",
                        "Server Name",
                        "Server User",
                    ],
                )

                ### Viewing the dataframe
                st.dataframe(df)

                ### Downloading Report of user_data in csv file
                st.markdown(
                    get_csv_download_link(df, "User_Data.csv", "Download Report"),
                    unsafe_allow_html=True,
                )

                ### Fetch feedback data from user_feedback(table) and convert it into dataframe
                cursor.execute("""SELECT * from user_feedback""")
                data = cursor.fetchall()

                st.header("**User's Feedback Data**")
                df = pd.DataFrame(
                    data,
                    columns=[
                        "ID",
                        "Name",
                        "Email",
                        "Feedback Score",
                        "Comments",
                        "Timestamp",
                    ],
                )
                st.dataframe(df)

                ### query to fetch data from user_feedback(table)
                query = "select * from user_feedback"
                plotfeed_data = pd.read_sql(query, connection)

                ### Analyzing All the Data's in pie charts

                # fetching feed_score from the query and getting the unique values and total value count
                labels = plotfeed_data.feed_score.unique()
                values = plotfeed_data.feed_score.value_counts()

                # Pie chart for user ratings
                st.subheader("**User Rating's**")
                fig = px.pie(
                    values=values,
                    names=labels,
                    title="Chart of User Rating Score From 1 - 5 🤗",
                    color_discrete_sequence=px.colors.sequential.Aggrnyl,
                )
                st.plotly_chart(fig)

                # fetching Predicted_Field from the query and getting the unique values and total value count
                labels = plot_data.Predicted_Field.unique()
                values = plot_data.Predicted_Field.value_counts()

                # Pie chart for predicted field recommendations
                st.subheader("**Pie-Chart for Predicted Field Recommendation**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Predicted Field according to the Skills 👽",
                    color_discrete_sequence=px.colors.sequential.Aggrnyl_r,
                )
                st.plotly_chart(fig)

                # fetching User_Level from the query and getting the unique values and total value count
                labels = plot_data.User_Level.unique()
                values = plot_data.User_Level.value_counts()

                # Pie chart for User's👨‍💻 Experienced Level
                st.subheader("**Pie-Chart for User's Experienced Level**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Pie-Chart 📈 for User's 👨‍💻 Experienced Level",
                    color_discrete_sequence=px.colors.sequential.RdBu,
                )
                st.plotly_chart(fig)

                # fetching resume_score from the query and getting the unique values and total value count
                labels = plot_data.resume_score.unique()
                values = plot_data.resume_score.value_counts()

                # Pie chart for Resume Score
                st.subheader("**Pie-Chart for Resume Score**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="From 1 to 100 💯",
                    color_discrete_sequence=px.colors.sequential.Agsunset,
                )
                st.plotly_chart(fig)

                # fetching IP_add from the query and getting the unique values and total value count
                labels = plot_data.IP_add.unique()
                values = plot_data.IP_add.value_counts()

                # Pie chart for Users
                st.subheader("**Pie-Chart for Users App Used Count**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Usage Based On IP Address 👥",
                    color_discrete_sequence=px.colors.sequential.matter_r,
                )
                st.plotly_chart(fig)

                # fetching City from the query and getting the unique values and total value count
                labels = plot_data.City.unique()
                values = plot_data.City.value_counts()

                # Pie chart for City
                st.subheader("**Pie-Chart for City**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Usage Based On City 🌆",
                    color_discrete_sequence=px.colors.sequential.Jet,
                )
                st.plotly_chart(fig)

                # fetching State from the query and getting the unique values and total value count
                labels = plot_data.State.unique()
                values = plot_data.State.value_counts()

                # Pie chart for State
                st.subheader("**Pie-Chart for State**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Usage Based on State 🚉",
                    color_discrete_sequence=px.colors.sequential.PuBu_r,
                )
                st.plotly_chart(fig)

                # fetching Country from the query and getting the unique values and total value count
                labels = plot_data.Country.unique()
                values = plot_data.Country.value_counts()

                # Pie chart for Country
                st.subheader("**Pie-Chart for Country**")
                fig = px.pie(
                    df,
                    values=values,
                    names=labels,
                    title="Usage Based on Country 🌏",
                    color_discrete_sequence=px.colors.sequential.Purpor_r,
                )
                st.plotly_chart(fig)

            ## For Wrong Credentials
            else:
                st.error("Wrong ID & Password Provided")


# Calling the main (run()) function to make the whole process run
run()
