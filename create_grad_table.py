from db_config import execute

sql = """
CREATE TABLE IF NOT EXISTS Graduated_Student (
    Grad_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID INT,
    Full_Name VARCHAR(100),
    Email VARCHAR(150),
    Graduation_Date DATE,
    Batch_Year INT,
    Level_At_Graduation VARCHAR(50),
    Notes TEXT
);
"""

try:
    execute(sql)
    print("Graduated_Student table created successfully.")
except Exception as e:
    print(f"Error creating table: {e}")
