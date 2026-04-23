from datetime import date, timedelta
from sqlalchemy import func
from models import Member, SignIn

def weekly_summary(session):
    """Return days signed in the past 7 days for each member."""
    start = date.today() - timedelta(days=7)
    return (
        session.query(
            Member.name,
            func.count(func.distinct(SignIn.sign_date)).label("days_signed_week")
        )
        .outerjoin(SignIn)
        .filter((SignIn.sign_date >= start) | (SignIn.sign_date.is_(None)))
        .group_by(Member.id)
        .order_by(Member.name)
        .all()
    )

def monthly_summary(session):
    """Return days signed in the past 30 days for each member."""
    start = date.today() - timedelta(days=30)
    return (
        session.query(
            Member.name,
            func.count(func.distinct(SignIn.sign_date)).label("days_signed_month")
        )
        .outerjoin(SignIn)
        .filter((SignIn.sign_date >= start) | (SignIn.sign_date.is_(None)))
        .group_by(Member.id)
        .order_by(Member.name)
        .all()
    )

def avg_signin_time(session):
    """Average sign-in time (as string HH:MM) per member."""
    return (
        session.query(
            Member.name,
            func.strftime('%H:%M', func.avg(func.strftime('%s', SignIn.sign_time))).label("avg_time")
        )
        .join(SignIn)
        .group_by(Member.id)
        .all()
    )
