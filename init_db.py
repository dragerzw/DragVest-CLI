from app.db import engine, Base
from app.models import User, Portfolio, Investment, Security, Transaction

# Create all tables in the database
Base.metadata.create_all(engine)

print("Database tables created successfully.")