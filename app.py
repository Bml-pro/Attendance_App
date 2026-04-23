from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from datetime import date, datetime, timedelta
from io import BytesIO

from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

import plotly.graph_objs as go
import plotly.io as pio

from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

from models import Base, Member, SignIn, User, Announcement, Contribution, ContributionType, RambirambiEvent


# -------------------------
# Flask App
# -------------------------
app = Flask(__name__)
app.secret_key = "attendance_secret_key"


# -------------------------
# Database
# -------------------------
engine = create_engine("sqlite:///attendance.db", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)

DBSession = sessionmaker(bind=engine)
db_session = DBSession()   # ✅ FIXED NAME


# -------------------------
# Default Contribution Types
# -------------------------
default_types = [
    {"name": "Ada", "amount": 5000},
    {"name": "Rambirambi", "amount": 2000}
]

for t in default_types:
    exists = db_session.query(ContributionType).filter_by(name=t["name"]).first()
    if not exists:
        db_session.add(ContributionType(name=t["name"], default_amount=t["amount"]))

db_session.commit()


# -------------------------
# Flask Login Setup
# -------------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# -------------------------
# User Wrapper
# -------------------------
class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.username = user.username
        self.is_admin = user.is_admin


@login_manager.user_loader
def load_user(user_id):
    user = db_session.get(User, int(user_id))   # ✅ FIXED
    return UserLogin(user) if user else None


# -------------------------
# Admin Protection
# -------------------------
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(*args, **kwargs):
        if not current_user.is_admin:
            flash("No permission", "danger")
            return redirect(url_for("member_sign"))
        return f(*args, **kwargs)
    return decorated


# -------------------------
# ✅ Landing Page (FIRST PAGE)
# -------------------------
@app.route("/")
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("welcome.html")


# -------------------------
# Home (After Login)
# -------------------------
@app.route("/home")
@login_required
def index():
    announcements = db_session.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return render_template("index.html", announcements=announcements)


# -------------------------
# Login
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db_session.query(User).filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(UserLogin(user))
            flash("Logged in!", "success")

            return redirect(url_for("admin_dashboard" if user.is_admin else "member_sign"))

        flash("Invalid credentials", "danger")

    return render_template("login.html")


# -------------------------
# Logout
# -------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out", "success")
    return redirect(url_for("welcome"))   # ✅ redirect to landing


# -------------------------
# Register
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirm")
        is_admin = True if request.form.get("is_admin") == "on" else False

        if password != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))

        if db_session.query(User).filter_by(username=username).first():
            flash("Username exists", "warning")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            is_admin=is_admin
        )

        db_session.add(new_user)
        db_session.commit()

        flash("Account created", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# -------------------------
# Member Sign
# -------------------------
@app.route("/sign", methods=["GET", "POST"])
@login_required
def member_sign():

    if current_user.is_admin:
        return redirect(url_for("admin_dashboard"))

    allowed_days = ["Tuesday", "Wednesday", "Saturday"]
    if datetime.now().strftime("%A") not in allowed_days:
        flash("Signing only Tue, Wed, Sat", "danger")
        return redirect(url_for("index"))

    categories = ["Soprano", "Alto", "Tenor", "Bass"]

    members_by_category = {
        cat: db_session.query(Member).filter_by(category=cat).all()
        for cat in categories
    }

    if request.method == "POST":
        member_id = request.form.get("member_id")

        exists = db_session.query(SignIn).filter_by(
            member_id=member_id,
            sign_date=date.today()
        ).first()

        if not exists:
            db_session.add(SignIn(
                member_id=member_id,
                sign_date=date.today(),
                sign_time=datetime.now().time()
            ))
            db_session.commit()
            flash("Signed successfully", "success")
        else:
            flash("Already signed", "info")

    return render_template("sign.html", members_by_category=members_by_category, categories=categories)


#========================
#today
#========================
@app.route("/today")
@admin_required
def today():
    today_signins = db_session.query(SignIn)\
        .filter(SignIn.sign_date == date.today()).all()

    return render_template("today.html", signins=today_signins)


# -------------------------
# Members
# -------------------------
@app.route("/members", methods=["GET", "POST"])
@admin_required
def members():

    categories = ["Soprano", "Alto", "Tenor", "Bass"]

    if request.method == "POST":
        db_session.add(Member(
            name=request.form.get("name"),
            category=request.form.get("category")
        ))
        db_session.commit()
        return redirect(url_for("members"))

    members_by_category = {
        cat: db_session.query(Member).filter_by(category=cat).all()
        for cat in categories
    }

    return render_template("members.html", members_by_category=members_by_category, categories=categories)


# -------------------------
# Admin Dashboard
# -------------------------
@app.route("/admin_dashboard")
@admin_required
def admin_dashboard():

    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    total_members = db_session.query(func.count(Member.id)).scalar()
    total_signins = db_session.query(func.count(SignIn.id)).scalar()

    today_signins = db_session.query(func.count(SignIn.id))\
        .filter(SignIn.sign_date == today).scalar()

    weekly_signins = db_session.query(func.count(SignIn.id))\
        .filter(SignIn.sign_date.between(week_start, week_end)).scalar()

    # Chart data
    members = db_session.query(Member).all()

    names = []
    counts = []

    for m in members:
        count = db_session.query(func.count(SignIn.id))\
            .filter(SignIn.member_id == m.id).scalar()

        names.append(m.name)
        counts.append(count)

    import plotly.graph_objs as go
    import plotly.io as pio

    fig = go.Figure([go.Bar(x=names, y=counts)])
    fig.update_layout(title="Attendance per Member")

    chart_html = pio.to_html(fig, full_html=False)

    # Today's records
    today_records = db_session.query(SignIn)\
        .filter(SignIn.sign_date == today).all()

    return render_template(
        "admin_dashboard.html",
        total_members=total_members,
        total_signins=total_signins,
        today_signins=today_signins,
        weekly_signins=weekly_signins,
        chart_html=chart_html,
        today_records=today_records
    )


# -------------------------
# Contributions
# -------------------------
@app.route("/contributions")
@admin_required
def contributions():

    members = db_session.query(Member).all()
    events = db_session.query(RambirambiEvent).all()

    return render_template("contributions.html", members=members, events=events)

#==========================
#annoucements
#==========================
@app.route("/announcements", methods=["GET", "POST"])
@admin_required
def announcements():

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")

        if not title or not content:
            flash("Title and content required", "warning")
            return redirect(url_for("announcements"))

        new_announcement = Announcement(
            title=title,
            content=content,
            created_at=date.today(),
            created_by=current_user.id
        )

        db_session.add(new_announcement)
        db_session.commit()

        flash("Announcement added", "success")
        return redirect(url_for("announcements"))

    announcements = db_session.query(Announcement)\
        .order_by(Announcement.created_at.desc()).all()

    return render_template("announcements.html", announcements=announcements)


# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)