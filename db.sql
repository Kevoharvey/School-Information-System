DROP DATABASE IF EXISTS school_db;
CREATE DATABASE school_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE school_db;

CREATE TABLE Users (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Full_Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) NOT NULL UNIQUE,
    Password_Hash VARCHAR(255) NOT NULL,
    Role ENUM('student','teacher','admin') NOT NULL,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO Users (Full_Name, Email, Password_Hash, Role) VALUES ('Mostafa El Shafey','Mostafa.ElShafey@gmail.com', 'scrypt:32768:8:1$joabjGxNE3UlNpg3$21a920099d5aa7d6a2558f109e6ead2f5d35a9d6d1f0af6b077360381eada853880866b463d738a2ea0372db3c628f8ef46c4cb40f8131f505d96c2592ea3ad8', 'admin');

CREATE TABLE Department (
    Dept_ID INT AUTO_INCREMENT PRIMARY KEY,
    Dept_Name VARCHAR(100) NOT NULL UNIQUE,
    Dept_Head VARCHAR(100)
);

CREATE TABLE Employee (
    Emp_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT UNIQUE,
    Emp_FName VARCHAR(50) NOT NULL,
    Emp_Lname VARCHAR(50) NOT NULL,
    Emp_Email VARCHAR(150),
    Emp_Pnum VARCHAR(20),
    Employment_Date DATE,
    Emp_Status ENUM('Active','On Leave','Probation') DEFAULT 'Active',
    Supervisor_ID INT,
    Dept_ID INT NOT NULL,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE CASCADE,
    FOREIGN KEY (Supervisor_ID) REFERENCES Employee(Emp_ID) ON DELETE SET NULL,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID)
);

CREATE TABLE Instructor (
    Emp_ID INT PRIMARY KEY,
    Qualification VARCHAR(200),
    Specialization VARCHAR(100),
    FOREIGN KEY (Emp_ID) REFERENCES Employee(Emp_ID) ON DELETE CASCADE
);

CREATE TABLE Classroom (
    Classroom_ID INT AUTO_INCREMENT PRIMARY KEY,
    Classroom_Name VARCHAR(50),
    Classroom_Level VARCHAR(50),
    Classroom_Capacity INT,
    Classroom_Building VARCHAR(100),
    Classroom_Floor VARCHAR(20)
);

CREATE TABLE Subject (
    Subject_ID INT AUTO_INCREMENT PRIMARY KEY,
    Subject_Name VARCHAR(100) NOT NULL,
    Subject_Level VARCHAR(50),
    Subject_Slots INT,
    Credits INT DEFAULT 3,
    Dept_ID INT,
    Classroom_ID INT,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID) ON DELETE SET NULL,
    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID) ON DELETE SET NULL
);

CREATE TABLE Student (
    Student_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT UNIQUE,
    Fname VARCHAR(50) NOT NULL,
    Lname VARCHAR(50) NOT NULL,
    Level VARCHAR(50),
    Batch_Year INT,
    Birth_Date DATE,
    Gender VARCHAR(20),
    Nationality VARCHAR(80),
    Student_Email VARCHAR(150),
    Student_Pnum VARCHAR(20),
    Parent_Name VARCHAR(100),
    Parent_Pnum VARCHAR(20),
    Parent_Email VARCHAR(150),
    Student_Address VARCHAR(250),
    Previous_School VARCHAR(150),
    Student_Photo VARCHAR(255),
    Birth_Certificate VARCHAR(255),
    Previous_Transcript VARCHAR(255),
    Notes TEXT,
    Status ENUM('Active','Enrolled','Pending') DEFAULT 'Pending',
    Enrolled_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE CASCADE
);

CREATE TABLE Studies (
    Student_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    Grade DECIMAL(5,2),
    Semester VARCHAR(20) DEFAULT 'CURRENT',
    PRIMARY KEY (Student_ID, Subject_ID, Semester),
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);

CREATE TABLE Teaches (
    Emp_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    PRIMARY KEY (Emp_ID, Subject_ID),
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);

CREATE TABLE Attendance (
    Att_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID INT NOT NULL,
    Subject_ID INT NOT NULL,
    Att_Date DATE NOT NULL,
    Present BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) ON DELETE CASCADE,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE
);

CREATE TABLE Assignment (
    Assignment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(200) NOT NULL,
    Description TEXT,
    Subject_ID INT NOT NULL,
    Emp_ID INT,
    Due_Date DATE,
    Max_Score DECIMAL(5,2) DEFAULT 100,
    File_Path VARCHAR(255),
    Status ENUM('Active','Grading','Published','Closed') DEFAULT 'Active',
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE,
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID) ON DELETE SET NULL
);

CREATE TABLE Submission (
    Sub_ID INT AUTO_INCREMENT PRIMARY KEY,
    Assignment_ID INT NOT NULL,
    Student_ID INT NOT NULL,
    Submitted_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    File_Path VARCHAR(255),
    Notes TEXT,
    Score DECIMAL(5,2),
    Feedback TEXT,
    FOREIGN KEY (Assignment_ID) REFERENCES Assignment(Assignment_ID) ON DELETE CASCADE,
    FOREIGN KEY (Student_ID) REFERENCES Student(Student_ID) ON DELETE CASCADE
);

CREATE TABLE Schedule_Entry (
    Entry_ID INT AUTO_INCREMENT PRIMARY KEY,
    Subject_ID INT NOT NULL,
    Classroom_ID INT,
    Emp_ID INT,
    Day_Of_Week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'),
    Start_Time TIME,
    End_Time TIME,
    FOREIGN KEY (Subject_ID) REFERENCES Subject(Subject_ID) ON DELETE CASCADE,
    FOREIGN KEY (Classroom_ID) REFERENCES Classroom(Classroom_ID) ON DELETE SET NULL,
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID) ON DELETE SET NULL
);

CREATE TABLE Notification (
    Notif_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT,
    Title VARCHAR(200) NOT NULL,
    Message TEXT,
    Type ENUM('assignment','grade','announcement','system','attendance') DEFAULT 'announcement',
    Is_Read BOOLEAN DEFAULT FALSE,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE CASCADE
);
CREATE TABLE Student_Registration (
    Student_Reg_ID INT AUTO_INCREMENT PRIMARY KEY,
    
    -- Personal Information
    Full_Name VARCHAR(100) NOT NULL,
    Birth_Date DATE,
    Gender VARCHAR(20),
    Nationality VARCHAR(80),

    -- Contact Information
    Email VARCHAR(150),
    Phone VARCHAR(20),

    -- Enrollment Information
    Grade_Applied VARCHAR(50),
    
    -- Guardian Information
    Parent_Name VARCHAR(100),
    Parent_Phone VARCHAR(20),
    Parent_Email VARCHAR(150),

    -- Address Information
    Address VARCHAR(250),
    Previous_School VARCHAR(150),
    Birth_Certificate VARCHAR(255),
    Student_Photo VARCHAR(255),
    Previous_Transcript VARCHAR(255),
    Notes TEXT,
    Status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',
    Submitted_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Teacher_Registration (
    Teacher_Reg_ID INT AUTO_INCREMENT PRIMARY KEY,

    -- Contact Information
    Full_Name VARCHAR(100) NOT NULL,
    Contact_Email VARCHAR(150) NOT NULL,
    Phone_Number VARCHAR(20) NOT NULL,

    -- Teacher Information
    Department VARCHAR(100) NOT NULL,
    Specialization VARCHAR(150),
    Qualification VARCHAR(200) NOT NULL,
    Available_Start_Date DATE,
    Address TEXT,

    -- Additional Information
    Notes TEXT,

    -- Application Status
    Status ENUM('Pending','Approved','Rejected') DEFAULT 'Pending',

    -- Submission Timestamp
    Submitted_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Is_An (
    Emp_ID INT NOT NULL,
    Dept_ID INT NOT NULL,
    PRIMARY KEY (Emp_ID, Dept_ID),
    FOREIGN KEY (Emp_ID) REFERENCES Instructor(Emp_ID) ON DELETE CASCADE,
    FOREIGN KEY (Dept_ID) REFERENCES Department(Dept_ID) ON DELETE CASCADE
);

-- No placeholder student, teacher, grade, assignment, schedule, notification, or registration data is inserted.
-- Start the app and sign in with an existing admin account.

CREATE TABLE Graduated_Student (
    Grad_ID INT AUTO_INCREMENT PRIMARY KEY,
    Student_ID INT,
    Full_Name VARCHAR(100),
    Email VARCHAR(150),
    Graduation_Date DATE,
    Batch_Year INT,
    Level_At_Graduation VARCHAR(50),
    Notes TEXT
);

CREATE TABLE Activity_Logs (
    Log_ID INT AUTO_INCREMENT PRIMARY KEY,
    User_ID INT,
    Action VARCHAR(100) NOT NULL,
    Table_Name VARCHAR(100),
    Action_Time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (User_ID) REFERENCES Users(User_ID) ON DELETE SET NULL
);
