import pyodbc

# Replace with your connection string details
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=event-horizon.database.windows.net,1433;'
    'DATABASE=eventhorizon-db;'
    'UID=frhnahnr;'
    'PWD=F@rhanah13;'
    'Encrypt=yes;'
    'TrustServerCertificate=no;'
    'Connection Timeout=30;'
)

cursor = conn.cursor()

# Create Users table
cursor.execute("""
CREATE TABLE Users (
    UserID INT PRIMARY KEY IDENTITY,
    Email NVARCHAR(100),
    Password NVARCHAR(100),
    Role NVARCHAR(50)
)
""")

# Create Events table
cursor.execute("""
CREATE TABLE Events (
    EventID INT PRIMARY KEY IDENTITY,
    Name NVARCHAR(100),
    Description NVARCHAR(MAX),
    Date DATE,
    Location NVARCHAR(100),
    Capacity INT,
    OrganizerID INT
)
""")

# Create Attendees table
cursor.execute("""
CREATE TABLE Attendees (
    AttendeeID INT PRIMARY KEY IDENTITY,
    FullName NVARCHAR(100),
    Email NVARCHAR(100),
    EventID INT
)
""")

conn.commit()
print("✅ Tables created successfully!")

cursor.close()
conn.close()
