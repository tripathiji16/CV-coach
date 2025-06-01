# CV Coach

> **An AI-powered resume analysis and career guidance tool**

---

## Table of Contents
- [About CV Coach](#about-cv-coach)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [How It Works](#how-it-works)
  - [Installation](#installation)
  - [Usage](#usage)
- [About Pyresparser](#about-pyresparser)
- [Developers](#developers)


---

## About CV Coach
CV Coach is an intelligent, AI-powered resume analysis and career guidance tool designed to help job seekers enhance their CVs, understand their strengths, and prepare effectively for job roles. Powered by Natural Language Processing (NLP), this project bridges the gap between job seekers and industry expectations by providing personalized, actionable feedback.

---

## Features
- **Resume Parsing:** Extracts key sections like education, skills, experience, and achievements using NLP.
- **Job Role Prediction:** Suggests suitable job roles based on your profile and skills.
- **Resume Scoring:** Provides a score based on clarity, structure, keyword usage, and relevance.
- **Skill Recommendations:** Personalized suggestions to enhance your profile.
- **Course Recommendations:** Curated courses to upskill for your target field.
- **Feedback & Analytics:** Collects user feedback and provides admin analytics.
- **User-Friendly Interface:** Clean, modern UI with responsive design.

---

## Tech Stack
- **Python** (core language)
- **Streamlit** (web app framework)
- **Pyresparser** (resume parsing)
- **NLTK** (natural language processing)
- **Pandas, NumPy** (data handling)
- **MySQL** (database)
- **Plotly** (visualizations)
- **Other libraries:** pdfminer3, geopy, PIL, etc.

---

## How It Works
### Installation
1. **Download the code:**
   ```bash
   git clone https://github.com/tripathiji16/CV-coach
   ```

2. **Set up virtual environment:**
   ```bash
   # Navigate to project directory
   cd CV-coach
   
   # Create virtual environment
   python -m venv venvapp
   
   # Activate virtual environment
   cd venvapp/Scripts
   activate
   ```

3. **Install dependencies:**
   ```bash
   # Navigate to App directory
   cd ../..
   cd App
   
   # Install required packages
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Database Setup:**
   - Create a MySQL database named `cv`
   - Update database credentials in `App/App.py`:
     ```python
     connection = pymysql.connect(
         host='localhost',
         user='root',
         password='root@MySQL4admin',
         db='cv'
     )
     ```
5. Go to the `venvapp\Lib\site-packages\pyresparser` folder

And replace the `resume_parser.py` with `resume_parser.py`

which is provided above inside pyresparser folder.

6. **Run the app:**
   ```bash
   streamlit run App.py
   ```

### Usage
- Fill in your details and upload your resume (PDF).
- The app will analyze your resume, provide a score, recommend skills and courses, and offer improvement tips.
- Jump to the feedback page to rate the experience.
- Login to admin side with given credentials: userid `admin` and password `admin@resume-analyzer`.
- Admins can view analytics and user feedback.
- for preview go to screenshots.

---

## About Pyresparser
[pyresparser](https://github.com/OmkarPathak/pyresparser) is an open-source Python library for extracting information from resumes. It uses NLP techniques to parse PDF and DOCX files and extract fields like name, email, phone, education, skills, and more. CV Coach uses pyresparser to power its resume analysis and extraction features. We sincerely thank Omkar Pathak for his open-source contribution — the pyresparser library. It played a crucial role in the development of CV Coach by enabling efficient and accurate resume parsing using Natural Language Processing.

---

## Developers
- **Vaishnavi Tripathi**
- **Jai Srivastava**

---

