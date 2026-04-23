from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    Time,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import date

Base = declarative_base()

# =======================
# Users (Login Accounts)
# =======================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)

    # later we can add roles: secretary, teacher, accountant


# =======================
# Choir Members
# =======================
class Member(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    category = Column(String(20), nullable=False)  # Soprano, Alto, Tenor, Bass

    signins = relationship(
        "SignIn",
        back_populates="member",
        cascade="all, delete"
    )


# =======================
# Attendance Sign-ins
# =======================
class SignIn(Base):
    __tablename__ = "sign_ins"

    id = Column(Integer, primary_key=True)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    sign_date = Column(Date, nullable=False)
    sign_time = Column(Time)

    member = relationship("Member", back_populates="signins")


# =======================
# Announcements (NEW)
# =======================
class Announcement(Base):
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(Date, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    author = relationship("User")

#=======================
# Contribution Types 
#=======================
class ContributionType(Base):
    __tablename__ = "contribution_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)

    default_amount = Column(Integer)  # example: 5000 for Ada

    contributions = relationship("Contribution", back_populates="type")


#============================
# Contributions ---
#============================
class Contribution(Base):
    __tablename__ = "contributions"

    id = Column(Integer, primary_key=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    type_id = Column(Integer, ForeignKey("contribution_types.id"), nullable=False)

    event_id = Column(Integer, ForeignKey("rambirambi_events.id"))

    amount = Column(Integer, nullable=False)

    month = Column(Integer)
    year = Column(Integer)

    date = Column(Date, default=date.today)

    member = relationship("Member")
    type = relationship("ContributionType", back_populates="contributions")

    event = relationship("RambirambiEvent", back_populates="contributions")


#====================
# Rambirambi Events 
#====================
# --- Rambirambi Events ---
class RambirambiEvent(Base):
    __tablename__ = "rambirambi_events"

    id = Column(Integer, primary_key=True)

    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)

    description = Column(String(200))

    date_created = Column(Date, default=date.today)

    member = relationship("Member")

    contributions = relationship("Contribution", back_populates="event")