# 📊 All SQL Queries in the App — Explained

-----

## 🔐 Auth & Session

**Login**

```sql
SELECT * FROM Users WHERE LOWER(Email)=%s
```

Fetches a user by email (case-insensitive) to verify their password on login.

**Forgot Password**

```sql
SELECT User_ID FROM Users WHERE LOWER(Email)=%s
UPDATE Users SET Password_Hash=%s WHERE User_ID=%s
```

Finds the account by email, then overwrites the password hash with the new one.

**Password Upgrade (bcrypt migration)**

```sql
UPDATE Users SET Password_Hash=%s WHERE User_ID=%s
```

Silently upgrades a legacy hash to bcrypt the moment a user logs in successfully — zero downtime migration.

-----

## 🧭 Navbar / Context Processor

```sql
SELECT Student_Photo FROM Student WHERE User_ID=%s
```

Grabs the logged-in student’s photo to display in the nav bar.

-----

## 📋 Dashboard

**Student view**

```sql
SELECT COUNT(*) AS c FROM Studies WHERE Student_ID=%s
SELECT COUNT(DISTINCT a.Assignment_ID) AS c FROM Assignment a
SELECT COUNT(*) AS c FROM Assignment
SELECT COUNT(*) AS c FROM Submission WHERE Student_ID=%s AND Score IS NOT NULL
SELECT Student_ID, CONCAT(Fname,' ',Lname) AS name, Level, Status, Enrolled_At
FROM Student WHERE Student_ID=%s
```

Shows the student’s own enrollment and submission stats.

**Admin/Teacher view**

```sql
SELECT COUNT(*) AS c FROM Student
SELECT COUNT(*) AS c FROM Instructor
SELECT COUNT(*) AS c FROM Assignment
SELECT COUNT(DISTINCT Student_ID) AS c FROM Studies WHERE Grade >= 90
SELECT Student_ID, ... FROM Student ORDER BY Enrolled_At DESC LIMIT 6
```

Counts everything school-wide and surfaces the 6 most recently enrolled students.

**Upcoming Assignments (all roles)**

```sql
SELECT a.Assignment_ID, a.Title, s.Subject_Name, a.Due_Date, a.Status
FROM Assignment a
JOIN Subject s ON a.Subject_ID=s.Subject_ID
ORDER BY a.Due_Date ASC LIMIT 5
```

Shows the 5 soonest-due assignments across all subjects.

-----

## 👩‍🎓 Students Page

**List with filters**

```sql
SELECT Student_ID, Fname, Lname, Level, Batch_Year, Student_Email, ...
FROM Student
WHERE (%s='' OR Level LIKE %s)
  AND (%s='' OR Status=%s)
  AND (%s='' OR CONCAT(Fname,' ',Lname) LIKE %s OR ...)
ORDER BY Level, Enrolled_At DESC
```

Dynamically filters by grade level, status, and a search term across name/email/ID. Empty strings act as “no filter” — avoids building dynamic SQL.

**Add Student — duplicate check**

```sql
SELECT User_ID FROM Users WHERE LOWER(Email)=%s
```

Prevents two accounts sharing the same email.

**Add Student — insert**

```sql
INSERT INTO Users (Full_Name, Email, Password_Hash, Role) VALUES (...)
INSERT INTO Student (User_ID, Fname, Lname, Level, ...) VALUES (...)
```

Creates the login account first, then the student profile linked by `User_ID`.

**Edit Student**

```sql
UPDATE Student SET Fname=%s, Lname=%s, Level=%s, ... WHERE Student_ID=%s
UPDATE Users SET Full_Name=%s, Email=%s WHERE User_ID=%s
```

Keeps both `Student` and `Users` tables in sync on every edit.

**Delete Student**

```sql
SELECT st.User_ID, st.Fname, ..., u.Email AS User_Email
FROM Student st LEFT JOIN Users u ON st.User_ID=u.User_ID
WHERE st.Student_ID=%s

DELETE FROM Users WHERE User_ID=%s
DELETE FROM Student_Registration WHERE Full_Name=%s OR Email=%s OR Parent_Email=%s
```

Deletes the `Users` row (which cascades to `Student` via FK), then cleans up the original registration record too. Also fires an expulsion email.

-----

## 👤 Student Profile

```sql
SELECT st.*, u.Email FROM Student st
LEFT JOIN Users u ON st.User_ID=u.User_ID
WHERE st.Student_ID=%s
```

Full student record merged with their login email.

```sql
SELECT sub.Subject_Name, st.Grade, st.Semester
FROM Studies st
JOIN Subject sub ON st.Subject_ID=sub.Subject_ID
WHERE st.Student_ID=%s
ORDER BY st.Semester DESC, sub.Subject_Name
```

All grades, newest semester first.

```sql
SELECT su.Sub_ID, su.Submitted_At, su.Score, su.Feedback, su.File_Path, a.Title, a.Max_Score
FROM Submission su
JOIN Assignment a ON su.Assignment_ID=a.Assignment_ID
WHERE su.Student_ID=%s
ORDER BY su.Submitted_At DESC
```

Assignment submission history with scores and feedback.

```sql
SELECT ROUND(AVG(Grade),2) AS avg_grade, COUNT(*) AS grade_count
FROM Studies WHERE Student_ID=%s
```

Calculates GPA-style average across all graded subjects.

```sql
SELECT COUNT(*) AS total, SUM(CASE WHEN Present THEN 1 ELSE 0 END) AS present
FROM Attendance WHERE Student_ID=%s
```

Attendance rate: present sessions ÷ total sessions × 100.

-----

## 👨‍🏫 Teachers / Academic Page

**List teachers**

```sql
SELECT e.Emp_ID, ..., COUNT(DISTINCT t.Subject_ID) AS subject_count
FROM Employee e
JOIN Instructor i ON e.Emp_ID=i.Emp_ID
JOIN Department d ON e.Dept_ID=d.Dept_ID
LEFT JOIN Teaches t ON i.Emp_ID=t.Emp_ID
WHERE (%s='' OR d.Dept_Name=%s) AND (%s='' OR e.Emp_Status=%s)
GROUP BY e.Emp_ID
```

Lists all instructors with their department, qualifications, and how many subjects they teach.

**Department & Classroom helpers (upsert)**

```sql
SELECT Dept_ID FROM Department WHERE Dept_Name=%s
INSERT INTO Department (Dept_Name) VALUES (%s)

SELECT Classroom_ID FROM Classroom WHERE Classroom_Name=%s
INSERT INTO Classroom (Classroom_Name) VALUES (%s)
```

`ensure_department()` and `ensure_classroom()` create the row only if it doesn’t exist yet.

-----

## 📝 Assignments

**Student view**

```sql
SELECT a.*, s.Subject_Name, CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name,
       su.Sub_ID, su.Score, su.Feedback, su.Submitted_At, su.File_Path AS solution_file
FROM Assignment a
JOIN Subject s ON a.Subject_ID=s.Subject_ID
LEFT JOIN Employee e ON a.Emp_ID=e.Emp_ID
LEFT JOIN Submission su ON a.Assignment_ID=su.Assignment_ID AND su.Student_ID=%s
ORDER BY a.Due_Date IS NULL, a.Due_Date ASC
```

`ORDER BY a.Due_Date IS NULL` pushes undated assignments to the bottom without needing a CASE. The `LEFT JOIN Submission` attaches the student’s own submission in one shot.

**Teacher/Admin view**

```sql
SELECT ..., COUNT(DISTINCT sub.Sub_ID) AS submitted,
       (SELECT COUNT(*) FROM Student) AS total_students
FROM Assignment a ... LEFT JOIN Submission sub ...
GROUP BY a.Assignment_ID
```

Shows submission count vs. total students — real-time completion rate.

**Submit Assignment**

```sql
INSERT INTO Submission (Assignment_ID, Student_ID, File_Path, Notes) VALUES (...)
```

**Grade Submission**

```sql
UPDATE Submission SET Score=%s, Feedback=%s WHERE Sub_ID=%s

UPDATE Assignment SET Status='Grading'
WHERE Assignment_ID = (SELECT Assignment_ID FROM Submission WHERE Sub_ID=%s)
AND Status = 'Active'
```

Flips the assignment status to “Grading” only once — only if it was still “Active”.

**Sync grade into Studies (upsert)**

```sql
SELECT Student_ID, Subject_ID FROM Submission su
JOIN Assignment a ON su.Assignment_ID=a.Assignment_ID
WHERE su.Sub_ID=%s

-- Then either:
UPDATE Studies SET Grade=%s WHERE Student_ID=%s AND Subject_ID=%s AND Semester='CURRENT'
-- or:
INSERT INTO Studies (Student_ID, Subject_ID, Grade, Semester) VALUES (...)
```

Keeps the grade book (`Studies`) in sync with assignment scores automatically.

-----

## 📊 Analytics

**Overview**

```sql
SELECT ROUND(AVG(Grade),1) AS avg_grade,
       (SELECT COUNT(*) FROM Student) AS total_students, ...
FROM Studies
```

School-wide averages using scalar subqueries for the counts.

**Subject performance**

```sql
SELECT sub.Subject_Name, ROUND(AVG(st.Grade),1) AS avg_grade, COUNT(st.Student_ID) AS student_count
FROM Studies st
JOIN Subject sub ON st.Subject_ID=sub.Subject_ID
GROUP BY sub.Subject_ID ORDER BY avg_grade DESC
```

Ranks subjects by performance — great for spotting which class is struggling.

**Grade Distribution**

```sql
SELECT
  SUM(CASE WHEN Grade>=90 THEN 1 ELSE 0 END) AS A_count,
  SUM(CASE WHEN Grade>=80 AND Grade<90 THEN 1 ELSE 0 END) AS B_count,
  SUM(CASE WHEN Grade>=70 AND Grade<80 THEN 1 ELSE 0 END) AS C_count,
  SUM(CASE WHEN Grade>=60 AND Grade<70 THEN 1 ELSE 0 END) AS D_count,
  SUM(CASE WHEN Grade<60 THEN 1 ELSE 0 END) AS F_count
FROM Studies
```

Classic conditional aggregation — computes A/B/C/D/F counts in a single pass.

**Assignment Completion Rate**

```sql
SELECT a.Title, COUNT(su.Sub_ID) AS submitted,
       (SELECT COUNT(*) FROM Student) AS total_students
FROM Assignment a
LEFT JOIN Submission su ON a.Assignment_ID=su.Assignment_ID
GROUP BY a.Assignment_ID
ORDER BY a.Created_At DESC LIMIT 8
```

Each assignment’s submission count divided by total students = completion %.

**Teacher Activity**

```sql
SELECT CONCAT(e.Emp_FName,' ',e.Emp_Lname) AS teacher_name,
       COUNT(a.Assignment_ID) AS assignments_created
FROM Employee e
JOIN Instructor i ON e.Emp_ID=i.Emp_ID
LEFT JOIN Assignment a ON i.Emp_ID=a.Emp_ID
GROUP BY e.Emp_ID ORDER BY assignments_created DESC LIMIT 8
```

Shows which teachers are most active in creating assignments.

**Monthly Stats**

```sql
SELECT DATE_FORMAT(Created_At, '%Y-%m') AS month_label, COUNT(*) AS total
FROM Assignment
GROUP BY DATE_FORMAT(Created_At, '%Y-%m')
ORDER BY month_label ASC LIMIT 12
```

Monthly assignment creation trend over the past year.

-----

## 🗓️ Schedule

**List entries**

```sql
SELECT se.Entry_ID, se.Day_Of_Week, TIME_FORMAT(se.Start_Time,'%H:%i') AS start_t, ...
FROM Schedule_Entry se
JOIN Subject sub ON se.Subject_ID=sub.Subject_ID
LEFT JOIN Classroom c ON se.Classroom_ID=c.Classroom_ID
LEFT JOIN Employee e ON se.Emp_ID=e.Emp_ID
ORDER BY FIELD(se.Day_Of_Week,'Monday','Tuesday','Wednesday','Thursday','Friday'), se.Start_Time
```

`FIELD()` sorts weekdays in Mon→Fri order instead of alphabetically.

**Add Schedule Entry**

```sql
INSERT INTO Schedule_Entry (Subject_ID, Emp_ID, Classroom_ID, Day_Of_Week, Start_Time, End_Time)
VALUES (...)
INSERT IGNORE INTO Teaches (Emp_ID, Subject_ID) VALUES (%s, %s)
```

`INSERT IGNORE` ensures no duplicate in the `Teaches` junction table — silent and safe.

-----

## 🔔 Notifications

**Fetch notifications**

```sql
SELECT * FROM Notification
WHERE User_ID=%s OR User_ID IS NULL
ORDER BY Created_At DESC
```

Gets personal notifications AND broadcast ones (`User_ID IS NULL` = sent to everyone).

**Mark all as read**

```sql
UPDATE Notification SET Is_Read=TRUE
WHERE User_ID=%s OR User_ID IS NULL
```

Marks all visible notifications as read in one shot.

**Auto-notify on new assignment**

```sql
SELECT User_ID FROM Student WHERE User_ID IS NOT NULL
INSERT INTO Notification (User_ID, Title, Message, Type) VALUES (...)
```

Loops through all students and inserts one notification per student. Works well, though a broadcast column would be more efficient at scale.

-----

## ✅ Attendance

**Load form data**

```sql
SELECT Subject_ID, Subject_Name FROM Subject ORDER BY Subject_Name

SELECT st.Student_ID, st.Fname, st.Lname, st.Student_Email
FROM Student ORDER BY st.Fname, st.Lname

SELECT Student_ID, Present FROM Attendance
WHERE Subject_ID=%s AND Att_Date=%s
```

Loads the subject list, all students, and any existing records for the chosen date.

**Save Attendance (upsert per student)**

```sql
SELECT Att_ID FROM Attendance
WHERE Student_ID=%s AND Subject_ID=%s AND Att_Date=%s

UPDATE Attendance SET Present=%s WHERE Att_ID=%s
-- or --
INSERT INTO Attendance (Student_ID, Subject_ID, Att_Date, Present) VALUES (...)
```

For each student: update if a record exists, insert if not. Idempotent — safe to re-submit the same session.

**Attendance Summary**

```sql
SELECT s.Subject_ID, s.Subject_Name,
       COUNT(DISTINCT a.Att_Date) AS sessions,
       COUNT(a.Att_ID) AS total_records,
       SUM(CASE WHEN a.Present THEN 1 ELSE 0 END) AS present_count
FROM Subject s
LEFT JOIN Attendance a ON s.Subject_ID=a.Subject_ID
GROUP BY s.Subject_ID ORDER BY s.Subject_Name
```

Overview table showing sessions held, total records, and attendance counts per subject.

-----

## 🏛️ Admin Dashboard & Registration Review

**REGISTRATION_UNION_QUERY**

```sql
SELECT ... FROM Student_Registration
UNION ALL
SELECT ... FROM Teacher_Registration
```

Normalizes two structurally different registration tables into one consistent shape for unified filtering, sorting, and pagination.

**Approve/Reject registration**

```sql
UPDATE Student_Registration SET Status=%s WHERE Student_Reg_ID=%s
UPDATE Teacher_Registration SET Status=%s WHERE Teacher_Reg_ID=%s
```

Stamps the registration as Approved or Rejected after processing. On approval, the `create_student_from_registration()` or `create_teacher_from_registration()` helpers run the full Users + Student/Employee + Instructor insert chains.

-----

## 🤖 AI Assistant (Gemini / Fallback)

**Example fallback query**

```sql
SELECT st.Student_ID, CONCAT(st.Fname,' ',st.Lname) AS student_name,
       ROUND(AVG(s.Grade),2) AS average_grade
FROM Student st
JOIN Studies s ON st.Student_ID=s.Student_ID
GROUP BY st.Student_ID
ORDER BY average_grade DESC LIMIT 10
```

The AI takes a natural-language question, generates a `SELECT` query, validates it (no INSERT/DROP/etc.), and executes it. The fallback patterns cover common questions like “top students” or “who failed math” when the Gemini API is unavailable.

-----

## 🗝️ Key Patterns Used Throughout

|Pattern                             |Where Used                                   |
|------------------------------------|---------------------------------------------|
|`LOWER(Email)` on both sides        |All email lookups — case-insensitive matching|
|Empty string as “no filter” trick   |Students, Teachers, Registrations list pages |
|Scalar subqueries in SELECT         |Dashboard counts, analytics totals           |
|`CASE WHEN` aggregation             |Grade distribution, attendance rates         |
|`LEFT JOIN` + NULL check for upserts|Attendance save, Studies grade sync          |
|`UNION ALL` to merge tables         |Registration review                          |
|`FIELD()` for custom sort order     |Schedule weekday ordering                    |
|`INSERT IGNORE`                     |Teaches junction table                       |
|`DATE_FORMAT` for grouping          |Monthly assignment trend chart               |
|`ORDER BY col IS NULL`              |Push null dates to bottom without CASE       |