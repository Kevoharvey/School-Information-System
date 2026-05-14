@app.route('/follow_up_parents')
def follow_up_parents():

    # Get students who are absent
    cursor.execute("""
        SELECT 
            s.Student_ID,
            s.Fname,
            s.Lname,
            s.Parent_Email,
            a.Att_Date
        FROM attendance a
        JOIN student s
        ON a.Student_ID = s.Student_ID
        WHERE a.Present = 0
    """)

    absent_students = cursor.fetchall()

    # Follow up with parents
    for student in absent_students:

        parent_email = student['Parent_Email']
        student_name = student['Fname'] + " " + student['Lname']

        # Example notification
        message = f"Your child {student_name} was absent on {student['Att_Date']}."

        # Print instead of real email sending
        print("Sending email to:", parent_email)
        print("Message:", message)

    return "Parent follow-up completed successfully"