from sqlalchemy import create_engine
from models import Base

# Connect to the same database your app uses
engine = create_engine('sqlite:///attendance.db', connect_args={'check_same_thread': False})

# Create all tables defined in models.py
Base.metadata.create_all(engine)

print("Tables created successfully!")
