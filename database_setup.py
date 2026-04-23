from sqlalchemy import create_engine
from models import Base

engine = create_engine('sqlite:///attendance.db', echo=True)

# Create all tables defined in models.py
Base.metadata.create_all(engine)
print("Database and tables created successfully.")
