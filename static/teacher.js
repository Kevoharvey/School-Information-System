/* =============================================================
   EduNova — teacher.js
   Standalone JS for the /teacher page (teacher.html).
   Handles sub-page navigation, API calls, session restore.
   ============================================================= */

var currentUser = null;

/* ─── Helpers ─── */
function showToast(msg) {
  var t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(function () { t.style.display = 'none'; }, 3000);
}

async function api(method, url, body) {
  var opts = { method: method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  var res = await fetch(url, opts);
  return res.json();
}

/* ─── Sub-page switching ─── */
function showSubPage(id) {
  document.querySelectorAll('.sub-page').forEach(function (s) { s.classList.remove('active'); });
  var el = document.getElementById(id);
  if (el) el.classList.add('active');

  document.querySelectorAll('.sidebar-link').forEach(function (l) {
    l.classList.remove('active');
    if ((l.getAttribute('onclick') || '').indexOf(id) !== -1) l.classList.add('active');
  });

  document.querySelectorAll('.nav-links a').forEach(function (a) {
    a.classList.remove('active');
    if ((a.getAttribute('onclick') || '').indexOf(id) !== -1) a.classList.add('active');
  });

  window.scrollTo(0, 0);

  if (id === 'tch-dashboard'  && currentUser) loadTeacherDashboard();
  if (id === 'tch-students'   && currentUser) loadTeacherStudents();
  if (id === 'tch-classrooms')                loadTeacherClassrooms();
}

/* ─── Dashboard: My Subjects ─── */
async function loadTeacherDashboard() {
  if (!currentUser) return;
  var data = await api('GET', '/api/teacher/' + currentUser.id + '/subjects');
  if (!data.ok) return;

  var list = document.getElementById('tch-subjects-list');
  if (!list) return;

  if (!data.subjects.length) {
    list.innerHTML = '<p style="color:var(--muted);padding:20px 0">No subjects assigned yet.</p>';
    return;
  }

  list.innerHTML = data.subjects.map(function (s) {
    return '<div class="schedule-item"><div class="sched-dot" style="background:var(--blue)"></div><div><div class="sched-name">' + s.Subject_Name + '</div><div class="sched-room">Level ' + (s.Subject_Level || '—') + ' · ' + (s.Subject_Slots || '—') + ' slots</div></div></div>';
  }).join('');
}

/* ─── My Students (live) ─── */
async function loadTeacherStudents() {
  if (!currentUser) return;
  var data = await api('GET', '/api/teacher/' + currentUser.id + '/students');
  if (!data.ok) return;

  var tbody = document.getElementById('tch-students-tbody');
  if (!tbody) return;

  if (!data.students.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:30px">No students enrolled in your subjects yet.</td></tr>';
    return;
  }

  tbody.innerHTML = data.students.map(function (s) {
    return '<tr><td>' + s.Fname + ' ' + s.Lname + '</td><td>' + s.Student_ID + '</td><td>' + (s.Level || '—') + '</td><td>' + (s.Student_Email || '—') + '</td></tr>';
  }).join('');
}

/* ─── Classrooms (live) ─── */
async function loadTeacherClassrooms() {
  var data = await api('GET', '/api/classrooms');
  if (!data.ok) return;

  var grid = document.getElementById('tch-classroom-grid');
  if (!grid) return;

  if (!data.classrooms.length) {
    grid.innerHTML = '<p style="color:var(--muted)">No classrooms available.</p>';
    return;
  }

  grid.innerHTML = data.classrooms.map(function (c) {
    return '<div class="classroom-card available"><div class="classroom-name">Room ' + c.Classroom_ID + '</div><div class="classroom-capacity">Capacity: ' + (c.Classroom_Capacity || '—') + ' students</div><div class="classroom-capacity">' + (c.Classroom_Building || '') + (c.Classroom_Floor ? ' · Floor ' + c.Classroom_Floor : '') + '</div><div class="classroom-status">Available</div><button class="btn btn-blue" onclick="bookClassroom(' + c.Classroom_ID + ')">Book Now</button></div>';
  }).join('');
}

function bookClassroom(roomId) {
  showToast('✅ Room ' + roomId + ' has been booked successfully!');
}

function cancelBooking(roomId) {
  showToast('❌ Booking for Room ' + roomId + ' has been cancelled.');
}

/* ─── Save Grade ─── */
async function saveGrade() {
  var studentId = document.getElementById('grade-student-id').value.trim();
  var subjectId = document.getElementById('grade-subject-id').value.trim();
  var gradeVal  = document.getElementById('grade-value').value.trim();

  if (!studentId || !subjectId || !gradeVal) {
    showToast('⚠️ Please fill in all fields.');
    return;
  }

  var g = parseFloat(gradeVal);
  if (isNaN(g) || g < 0 || g > 100) {
    showToast('⚠️ Grade must be between 0 and 100.');
    return;
  }

  var data = await api('POST', '/api/grades', {
    student_id: parseInt(studentId),
    subject_id: parseInt(subjectId),
    grade: g
  });

  if (!data.ok) {
    showToast('❌ ' + data.error);
    return;
  }

  showToast('✅ ' + data.message);
  document.getElementById('grade-student-id').value = '';
  document.getElementById('grade-subject-id').value = '';
  document.getElementById('grade-value').value = '';
}

/* ─── Logout ─── */
async function logout() {
  await api('POST', '/api/signout');
  window.location.href = '/';
}

/* ─── Init: restore session ─── */
document.addEventListener('DOMContentLoaded', async function () {
  try {
    var data = await api('GET', '/api/me');
    if (data.ok && data.user && data.user.role === 'teacher') {
      currentUser = data.user;
      var badge = document.getElementById('user-avatar-badge');
      var initials = data.user.name.split(' ').map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase();
      if (badge) { badge.textContent = initials; }
      var nameBadge = document.getElementById('user-name-badge');
      if (nameBadge) nameBadge.textContent = data.user.name.split(' ')[0];
      var firstName = document.getElementById('tch-first-name');
      if (firstName) firstName.textContent = data.user.name.split(' ')[0];
      loadTeacherDashboard();
    } else {
      window.location.href = '/';
    }
  } catch (e) {
    window.location.href = '/';
  }
});
