import streamlit as st
from firebase import db
from utils import hash_password, check_password, generate_code
from email_utils import send_verification_email
import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import io

# ---------- Streamlit Config ----------
st.set_page_config(page_title="Resume Builder", layout="wide")
st.title("Professional Resume Builder")

menu = ["Register", "Verify Email", "Login"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------ REGISTER ------------------
if choice == "Register":
    st.subheader("User Registration")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Register"):
        if email and password:
            users_ref = db.collection("users")
            doc = users_ref.document(email).get()
            if doc.exists:
                st.warning("This email is already registered")
            else:
                code = generate_code()
                send_verification_email(email, code)
                users_ref.document(email).set({
                    "email": email,
                    "password_hash": hash_password(password),
                    "is_verified": False,
                    "verification": {
                        "code": code,
                        "expires_at": (datetime.datetime.utcnow() + datetime.timedelta(minutes=15)).isoformat()
                    }
                })
                st.success("Registration successful! Verification code sent to your email.")

# ------------------ VERIFY EMAIL ------------------
elif choice == "Verify Email":
    st.subheader("Email Verification")
    email = st.text_input("Email")
    code = st.text_input("Verification Code")
    if st.button("Verify"):
        users_ref = db.collection("users")
        doc = users_ref.document(email).get()
        if doc.exists:
            data = doc.to_dict()
            if data["is_verified"]:
                st.success("Email already verified.")
            elif data["verification"]["code"] == code:
                expires_at = datetime.datetime.fromisoformat(data["verification"]["expires_at"])
                if datetime.datetime.utcnow() <= expires_at:
                    users_ref.document(email).update({"is_verified": True})
                    st.success("Email verified successfully!")
                else:
                    st.error("Verification code expired.")
            else:
                st.error("Incorrect verification code.")
        else:
            st.error("User not found")

# ------------------ LOGIN ------------------
elif choice == "Login":
    st.subheader("User Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        users_ref = db.collection("users")
        doc = users_ref.document(email).get()
        if doc.exists:
            data = doc.to_dict()
            if not data["is_verified"]:
                st.warning("Please verify your email first.")
            elif check_password(password, data["password_hash"]):
                st.success(f"Welcome back {email}!")

                st.subheader("Create Your Resume")

                # ------------------ HEADER ------------------
                name = st.text_input("Full Name *")
                phone = st.text_input("Phone (optional)")
                email_contact = st.text_input("Email (optional)")
                github = st.text_input("GitHub (optional)")
                linkedin = st.text_input("LinkedIn (optional)")
                website = st.text_input("Personal Website (optional)")
                social = st.text_input("Other Social (optional)")

                # ------------------ ABOUT ME ------------------
                about_me = st.text_area("About Me (optional)")

                # ------------------ EDUCATION ------------------
                if "education_list" not in st.session_state:
                    st.session_state.education_list = []

                st.subheader("Education")
                with st.expander("Add Education"):
                    school = st.text_input("School/University Name", key="school")
                    degree = st.text_input("Degree/Level", key="degree")
                    start = st.text_input("Start Date", key="edu_start")
                    end = st.text_input("End Date", key="edu_end")
                    desc = st.text_area("Description (optional)", key="edu_desc")
                    if st.button("Add Education"):
                        st.session_state.education_list.append({
                            "school": school,
                            "degree": degree,
                            "start": start,
                            "end": end,
                            "description": desc
                        })

                # ------------------ EXPERIENCE ------------------
                if "experience_list" not in st.session_state:
                    st.session_state.experience_list = []

                st.subheader("Experience")
                with st.expander("Add Experience"):
                    position = st.text_input("Position/Role", key="pos")
                    company = st.text_input("Company", key="comp")
                    start_exp = st.text_input("Start Date", key="exp_start")
                    end_exp = st.text_input("End Date", key="exp_end")
                    desc_exp = st.text_area("Description (optional)", key="exp_desc")
                    if st.button("Add Experience"):
                        st.session_state.experience_list.append({
                            "position": position,
                            "company": company,
                            "start": start_exp,
                            "end": end_exp,
                            "description": desc_exp
                        })

                # ------------------ PROJECTS ------------------
                if "project_list" not in st.session_state:
                    st.session_state.project_list = []

                st.subheader("Projects")
                with st.expander("Add Project"):
                    pname = st.text_input("Project Name", key="pname")
                    pdesc = st.text_area("Description (optional)", key="pdesc")
                    pstart = st.text_input("Start Date (optional)", key="pstart")
                    pend = st.text_input("End Date (optional)", key="pend")
                    plink = st.text_input("Link (optional)", key="plink")
                    if st.button("Add Project"):
                        st.session_state.project_list.append({
                            "name": pname,
                            "description": pdesc,
                            "start": pstart,
                            "end": pend,
                            "link": plink
                        })

                # ------------------ SKILLS, LANGUAGES, ACHIEVEMENTS ------------------
                skills = st.text_area("Skills (comma separated, optional)")
                languages = st.text_area("Languages (comma separated, optional)")
                achievements = st.text_area("Achievements / Awards (optional)")

                # ------------------ SAVE & GENERATE PDF ------------------
                if st.button("Generate PDF Resume"):
                    # Save to Firebase
                    resumes_ref = db.collection("resumes")
                    resumes_ref.document(email).set({
                        "name": name,
                        "contact": {
                            "phone": phone,
                            "email": email_contact,
                            "github": github,
                            "linkedin": linkedin,
                            "website": website,
                            "social": social
                        },
                        "about_me": about_me,
                        "education": st.session_state.education_list,
                        "experience": st.session_state.experience_list,
                        "projects": st.session_state.project_list,
                        "skills": skills,
                        "languages": languages,
                        "achievements": achievements,
                        "created_at": datetime.datetime.utcnow().isoformat()
                    })
                    st.success("Resume saved successfully!")

                    # ------------------ Generate Professional PDF ------------------
                    buffer = io.BytesIO()
                    c = canvas.Canvas(buffer, pagesize=A4)
                    width, height = A4
                    y_pos = {"y": height - 30}

                    # Header
                    c.setFont("Helvetica-Bold", 24)
                    c.drawString(50, y_pos["y"], name)
                    y_pos["y"] -= 30

                    contact_info = " | ".join(filter(None, [phone, email_contact, github, linkedin, website, social]))
                    c.setFont("Helvetica", 10)
                    c.drawString(50, y_pos["y"], contact_info)
                    y_pos["y"] -= 20

                    c.setStrokeColor(colors.grey)
                    c.setLineWidth(0.5)
                    c.line(50, y_pos["y"], width - 50, y_pos["y"])
                    y_pos["y"] -= 15

                    # Helper functions
                    def draw_section(title):
                        c.setFont("Helvetica-Bold", 14)
                        c.setFillColor(colors.darkblue)
                        c.drawString(50, y_pos["y"], title)
                        y_pos["y"] -= 15
                        c.setFillColor(colors.black)
                        c.setFont("Helvetica", 12)

                    def draw_text_block(text, line_height=14):
                        for line in text.split("\n"):
                            c.drawString(50, y_pos["y"], line)
                            y_pos["y"] -= line_height

                    # About Me
                    if about_me:
                        draw_section("About Me")
                        draw_text_block(about_me)
                        y_pos["y"] -= 10

                    # Education
                    if st.session_state.education_list:
                        draw_section("Education")
                        for edu in st.session_state.education_list:
                            edu_text = f"{edu['degree']} at {edu['school']} ({edu['start']} - {edu['end']})"
                            draw_text_block(edu_text)
                            if edu['description']:
                                draw_text_block(edu['description'])
                        y_pos["y"] -= 10

                    # Experience
                    if st.session_state.experience_list:
                        draw_section("Experience")
                        for exp in st.session_state.experience_list:
                            exp_text = f"{exp['position']} at {exp['company']} ({exp['start']} - {exp['end']})"
                            draw_text_block(exp_text)
                            if exp['description']:
                                draw_text_block(exp['description'])
                        y_pos["y"] -= 10

                    # Projects
                    if st.session_state.project_list:
                        draw_section("Projects")
                        for proj in st.session_state.project_list:
                            draw_text_block(proj['name'])
                            if proj['description']:
                                draw_text_block(proj['description'])
                            if proj['start'] or proj['end']:
                                draw_text_block(f"{proj['start']} - {proj['end']}")
                            if proj['link']:
                                draw_text_block(f"Link: {proj['link']}")
                        y_pos["y"] -= 10

                    # Skills & Languages (two-column)
                    x_left = 50
                    x_right = 300
                    max_y = y_pos["y"]

                    if skills:
                        draw_section("Skills")
                        skill_list = [s.strip() for s in skills.split(",") if s.strip()]
                        y_skill = y_pos["y"]
                        for skill in skill_list:
                            c.drawString(x_left, y_skill, f"- {skill}")
                            y_skill -= 12
                        max_y = min(max_y, y_skill)

                    if languages:
                        draw_section("Languages")
                        lang_list = [l.strip() for l in languages.split(",") if l.strip()]
                        y_lang = y_pos["y"]
                        for lang in lang_list:
                            c.drawString(x_right, y_lang, f"- {lang}")
                            y_lang -= 12
                        max_y = min(max_y, y_lang)

                    y_pos["y"] = max_y - 10

                    # Achievements
                    if achievements:
                        draw_section("Achievements / Awards")
                        draw_text_block(achievements)

                    c.save()
                    buffer.seek(0)

                    st.download_button(
                        label="Download Professional PDF Resume",
                        data=buffer,
                        file_name="resume_professional.pdf",
                        mime="application/pdf"
                    )
            else:
                st.error("Incorrect password")
        else:
            st.error("User not found")
