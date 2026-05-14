from db_config import execute

sql = """
CREATE TABLE IF NOT EXISTS Activity_Logs (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT,
    Action VARCHAR(100) NOT NULL,
    Table_Name VARCHAR(100),
    Action_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE SET NULL
);
"""

try:
    execute(sql)
    print("Activity_Logs table created successfully.")
except Exception as e:
    print(f"Error creating table: {e}")
