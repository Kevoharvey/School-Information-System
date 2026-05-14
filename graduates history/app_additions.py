# ============================================================
#  PASTE THESE THREE ROUTES INTO app.py
#  Place them right after the existing api_student_grades() route
#  (i.e. after the "/api/students/<int:student_id>/grades" block)
# ============================================================


# ── UPDATE STUDENT STATUS ────────────────────────────────────
@app.route("/api/students/<int:student_id>/status", methods=["PUT"])
def api_student_status_update(student_id):
    """Change a student's enrollment status and optionally record graduation date / notes."""
    d = request.get_json(silent=True) or {}
    status = d.get("status", "").strip().lower()

    valid_statuses = ("ongoing", "gap_year", "expelled", "graduated")
    if status not in valid_statuses:
        return jsonify({
            "ok": False,
            "error": f"Status must be one of: {', '.join(valid_statuses)}"
        }), 400

    graduation_date = d.get("graduation_date") or None
    status_notes    = (d.get("status_notes") or "").strip() or None

    # Auto-fill today's date when graduating without an explicit date
    if status == "graduated" and not graduation_date:
        from datetime import date as _date
        graduation_date = _date.today().isoformat()

    # Clear graduation date when moving away from graduated status
    if status != "graduated":
        graduation_date = None

    db_query(
        """UPDATE Student
           SET Status=%s, Graduation_Date=%s, Status_Notes=%s
           WHERE Student_ID=%s""",
        (status, graduation_date, status_notes, student_id),
        commit=True
    )
    return jsonify({"ok": True, "message": f"Student status updated to '{status}'."})


# ── GRADUATE HISTORY — all students with status breakdown ────
@app.route("/api/graduates", methods=["GET"])
def api_graduates_list():
    """Return all students ordered by status, plus per-status counts."""
    rows = db_query("""
        SELECT Student_ID, Fname, Lname, Level, Status,
               Graduation_Date, Status_Notes, Student_Email,
               TIMESTAMPDIFF(YEAR, Birth_Date, CURDATE()) AS Age
        FROM Student
        ORDER BY
            CASE Status
                WHEN 'graduated' THEN 1
                WHEN 'ongoing'   THEN 2
                WHEN 'gap_year'  THEN 3
                WHEN 'expelled'  THEN 4
            END,
            CASE WHEN Graduation_Date IS NOT NULL
                 THEN Graduation_Date END DESC,
            Student_ID
    """)
    for r in (rows or []):
        if r.get("Graduation_Date"):
            r["Graduation_Date"] = str(r["Graduation_Date"])

    # Per-status counts for the summary cards
    count_rows = db_query("""
        SELECT Status, COUNT(*) AS count
        FROM Student
        GROUP BY Status
    """)
    count_map = {row["Status"]: row["count"] for row in (count_rows or [])}

    return jsonify({"ok": True, "students": rows or [], "counts": count_map})


# ── FILTER STUDENTS BY STATUS ────────────────────────────────
@app.route("/api/students/status/<string:status>", methods=["GET"])
def api_students_by_status(status):
    """Return only students that match the given status."""
    valid_statuses = ("ongoing", "gap_year", "expelled", "graduated")
    if status not in valid_statuses:
        return jsonify({"ok": False, "error": "Invalid status"}), 400

    rows = db_query("""
        SELECT Student_ID, Fname, Lname, Level, Status,
               Graduation_Date, Status_Notes, Student_Email
        FROM Student
        WHERE Status = %s
        ORDER BY Student_ID
    """, (status,))
    for r in (rows or []):
        if r.get("Graduation_Date"):
            r["Graduation_Date"] = str(r["Graduation_Date"])
    return jsonify({"ok": True, "students": rows or []})
