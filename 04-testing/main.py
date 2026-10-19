
# Import the database setup function from sql_tools.py
from sql_tools import setup_database


# Download and load the taxi dataset into DuckDB.
# The function returns the number of rows loaded.
count = setup_database()

# Display the number of records.
print(f"Total trips: {count}")
