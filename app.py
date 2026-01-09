from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import bcrypt
import requests
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- DATABASE CONFIG ----------
# SQLite for now, change to PostgreSQL later
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///placement.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ================= MODELS =================

class Student(db.Model):
    email = db.Column(db.String, primary_key=True)
    name = db.Column(db.String)
    password = db.Column(db.LargeBinary)

class Admin(db.Model):
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.LargeBinary)
    role = db.Column(db.String)

class Education(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    department = db.Column(db.String)
    cgpa = db.Column(db.Float)
    backlogs = db.Column(db.Integer)

class Resume(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    github = db.Column(db.String)
    linkedin = db.Column(db.String)

class ResumeCheck(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    score = db.Column(db.Integer)
    status = db.Column(db.String)

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    department = db.Column(db.String)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    company = db.Column(db.String)
    applied_on = db.Column(db.String)
    status = db.Column(db.String)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String)
    message = db.Column(db.String)
    created_on = db.Column(db.String)
    seen = db.Column(db.Integer, default=0)

class AdminLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    admin = db.Column(db.String)
    student_email = db.Column(db.String)
    company = db.Column(db.String)
    old_status = db.Column(db.String)
    new_status = db.Column(db.String)
    action_time = db.Column(db.String)

# ---------- INIT ----------
with app.app_context():
    db.create_all()

    if not Admin.query.filter_by(username="admin").first():
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        db.session.add(Admin(username="admin", password=hashed, role="super_admin"))
        db.session.commit()

# ================= STUDENT =================

@app.route("/", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        s = Student.query.filter_by(email=request.form["email"]).first()
        if s and bcrypt.checkpw(request.form["password"].encode(), s.password):
            session.clear()
            session["student"] = s.email
            return redirect("/dashboard")
        return "Invalid login"
    return render_template("login.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        hashed = bcrypt.hashpw(request.form["password"].encode(), bcrypt.gensalt())
        db.session.add(Student(
            email=request.form["email"],
            name=request.form["name"],
            password=hashed
        ))
        db.session.commit()
        return redirect("/")
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "student" not in session:
        return redirect("/")
    notes = Notification.query.filter_by(email=session["student"]).order_by(Notification.id.desc()).all()
    for n in notes:
        n.seen = 1
    db.session.commit()
    return render_template("dashboard.html", notifications=notes)

@app.route("/education", methods=["GET", "POST"])
def education():
    if "student" not in session:
        return redirect("/")
    if request.method == "POST":
        db.session.add(Education(
            email=session["student"],
            department=request.form["department"],
            cgpa=float(request.form["cgpa"]),
            backlogs=int(request.form["backlogs"])
        ))
        db.session.commit()
        return redirect("/dashboard")
    return render_template("education.html")

@app.route("/resume", methods=["GET", "POST"])
def resume():
    if "student" not in session:
        return redirect("/")
    if request.method == "POST":
        db.session.add(Resume(
            email=session["student"],
            github=request.form["github"],
            linkedin=request.form["linkedin"]
        ))
        db.session.commit()
        return redirect("/verify")
    return render_template("resume.html")

@app.route("/verify")
def verify():
    if "student" not in session:
        return redirect("/")
    email = session["student"]
    r = Resume.query.filter_by(email=email).first()
    e = Education.query.filter_by(email=email).first()

    score = 0
    try:
        if r and r.github and r.github.startswith("https://github.com/") and requests.get(r.github, timeout=5).status_code == 200:
            score += 25
    except: pass
    try:
        if r and r.linkedin and r.linkedin.startswith("https://www.linkedin.com/") and requests.get(r.linkedin, timeout=5).status_code == 200:
            score += 25
    except: pass

    if e:
        rules = {"CSE":6, "ECE":6.5, "EEE":6, "MECH":6.5, "CIVIL":6}
        if e.cgpa >= rules.get(e.department.upper(), 6):
            score += 50

    status = "GENUINE" if score >= 60 else "FAKE"
    ResumeCheck.query.filter_by(email=email).delete()
    db.session.add(ResumeCheck(email=email, score=score, status=status))
    db.session.add(Notification(
        email=email,
        message=f"Resume verification completed: {status}",
        created_on=str(datetime.now())
    ))
    db.session.commit()
    return render_template("verify.html", score=score, status=status)

@app.route("/companies")
def companies():
    if "student" not in session:
        return redirect("/")
    v = ResumeCheck.query.filter_by(email=session["student"]).first()
    if not v or v.status != "GENUINE":
        return "Resume not verified"
    dept = Education.query.filter_by(email=session["student"]).first().department
    comps = Company.query.filter_by(department=dept).all()
    return render_template("companies.html", companies=[c.name for c in comps])

@app.route("/apply/<company>")
def apply(company):
    if "student" not in session:
        return redirect("/")
    db.session.add(Application(
        email=session["student"],
        company=company,
        applied_on=str(datetime.now()),
        status="Applied"
    ))
    db.session.add(Notification(
        email=session["student"],
        message=f"Applied to {company}",
        created_on=str(datetime.now())
    ))
    db.session.commit()
    return redirect("/dashboard")

# ================= ADMIN =================

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        a = Admin.query.filter_by(username=request.form["username"]).first()
        if a and bcrypt.checkpw(request.form["password"].encode(), a.password):
            session["admin"] = a.username
            session["role"] = a.role
            return redirect("/admin/dashboard")
        return "Invalid admin"
    return render_template("admin_login.html")

@app.route("/admin/dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin")
    if request.method == "POST" and session["role"] == "super_admin":
        db.session.add(Company(
            name=request.form["name"],
            department=request.form["department"]
        ))
        db.session.commit()
    apps = Application.query.all()
    comps = Company.query.all()
    return render_template("admin_dashboard.html", data=apps, companies=comps, role=session["role"])

@app.route("/admin/update/<email>/<company>/<status>")
def admin_update(email, company, status):
    if "admin" not in session:
        return redirect("/admin")
    app_row = Application.query.filter_by(email=email, company=company).first()
    old = app_row.status
    app_row.status = status
    db.session.add(AdminLog(
        admin=session["admin"],
        student_email=email,
        company=company,
        old_status=old,
        new_status=status,
        action_time=str(datetime.now())
    ))
    db.session.add(Notification(
        email=email,
        message=f"Application status updated to {status} for {company}",
        created_on=str(datetime.now())
    ))
    db.session.commit()
    return redirect("/admin/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
