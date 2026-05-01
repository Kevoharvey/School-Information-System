/* =============================================================
   EduNova — app.js
   Pure fetch() ↔ Flask JSON API. No Jinja2. No page reloads.
   ============================================================= */

var currentUser = null;   // { id, name, role }
var selectedRole = 'student';
var signupRole   = 'student';

/* ─────────────────────────────────────────
   HELPERS
───────────────────────────────────────── */
function showToast(message) {
  var toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.display = 'block';
  setTimeout(function () { toast.style.display = 'none'; }, 3000);
}

async function api(method, url, body) {
  const opts = {
    method: method,
    headers: { 'Content-Type': 'application/json' }
  };
  if (body) opts.body = JSON.stringify(body);
  const res  = await fetch(url, opts);
  const data = await res.json();
  return data;
}

/* ─────────────────────────────────────────
   PAGE / NAVIGATION
───────────────────────────────────────── */
function showPage(pageId) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  var target = document.getElementById('page-' + pageId);
  if (target) target.classList.add('active');

  document.querySelectorAll('#nav-guest a').forEach(a => a.classList.remove('active'));
  var activeLink = document.getElementById('nl-' + pageId);
  if (activeLink) activeLink.classList.add('active');

  window.scrollTo(0, 0);

  // Load dynamic data for public pages
  if (pageId === 'teachers')   loadPublicTeachers();
  if (pageId === 'subjects')   loadPublicSubjects();
  if (pageId === 'classrooms') loadPublicClassrooms();
}

function showStudentPage(subId) {
  showDashboard('student');
  document.querySelectorAll('#page-student .sub-page').forEach(s => s.classList.remove('active'));
  var target = document.getElementById(subId);
  if (target) target.classList.add('active');

  document.querySelectorAll('#page-student .sidebar-link').forEach(l => {
    l.classList.remove('active');
    if ((l.getAttribute('onclick') || '').indexOf(subId) !== -1) l.classList.add('active');
  });

  window.scrollTo(0, 0);

  // Load data for each sub-page
  if (subId === 'stu-dashboard' && currentUser) loadStudentDashboard();
  if (subId === 'stu-grades'    && currentUser) loadStudentGrades();
}

function showTeacherPage(subId) {
  showDashboard('teacher');
  document.querySelectorAll('#page-teacher .sub-page').forEach(s => s.classList.remove('active'));
  var target = document.getElementById(subId);
  if (target) target.classList.add('active');

  document.querySelectorAll('#page-teacher .sidebar-link').forEach(l => {
    l.classList.remove('active');
    if ((l.getAttribute('onclick') || '').indexOf(subId) !== -1) l.classList.add('active');
  });

  window.scrollTo(0, 0);

  if (subId === 'tch-dashboard' && currentUser) loadTeacherDashboard();
  if (subId === 'tch-students'  && currentUser) loadTeacherStudents();
  if (subId === 'tch-classrooms') loadTeacherClassrooms();
}

function showDashboard(role) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  var pg = document.getElementById('page-' + role);
  if (pg) pg.classList.add('active');
}

/* ─────────────────────────────────────────
   ROLE PICKERS
───────────────────────────────────────── */
function selectRole(role) {
  selectedRole = role;
  document.getElementById('role-student').classList.toggle('selected', role === 'student');
  document.getElementById('role-teacher').classList.toggle('selected', role === 'teacher');
}

function selectSignupRole(role) {
  signupRole = role;
  document.getElementById('signup-role-student').classList.toggle('selected', role === 'student');
  document.getElementById('signup-role-teacher').classList.toggle('selected', role === 'teacher');
  var label = document.getElementById('signup-id-label');
  var input = document.getElementById('signup-id');
  if (role === 'teacher') {
    label.textContent = 'Staff ID (numeric)';
    input.placeholder = 'e.g. 1001';
  } else {
    label.textContent = 'Student ID (numeric)';
    input.placeholder = 'e.g. 2001';
  }
}

/* ─────────────────────────────────────────
   SIGN IN
───────────────────────────────────────── */
async function doSignIn() {
  var email    = document.getElementById('signin-email').value.trim();
  var password = document.getElementById('signin-password').value.trim();

  if (!email)             { showToast('⚠️ Please enter your ID.'); return; }
  if (password.length < 4) { showToast('⚠️ Password must be at least 4 characters.'); return; }

  // Use the numeric part of the email field as ID (or the whole value if no @)
  var idVal = email.indexOf('@') !== -1 ? email.split('@')[0] : email;

  const data = await api('POST', '/api/signin', { role: selectedRole, id: idVal, password: password });
  if (!data.ok) {
    showToast('❌ ' + data.error);
    return;
  }
  loginUser(data.user);
}

/* ─────────────────────────────────────────
   SIGN UP
───────────────────────────────────────── */
async function doSignUp() {
  var name     = document.getElementById('signup-name').value.trim();
  var email    = document.getElementById('signup-email').value.trim();
  var id       = document.getElementById('signup-id').value.trim();
  var password = document.getElementById('signup-password').value.trim();

  if (!name)                          { showToast('⚠️ Please enter your full name.'); return; }
  if (!email || email.indexOf('@') === -1) { showToast('⚠️ Please enter a valid email.'); return; }
  if (!id)                            { showToast('⚠️ Please enter your ID.'); return; }
  if (password.length < 6)           { showToast('⚠️ Password must be at least 6 characters.'); return; }

  const data = await api('POST', '/api/signup', { role: signupRole, name, email, id, password });
  if (!data.ok) {
    showToast('❌ ' + data.error);
    return;
  }
  loginUser(data.user);
  showToast('🎉 Account created! Welcome, ' + name.split(' ')[0] + '!');
}

/* ─────────────────────────────────────────
   LOGIN USER
───────────────────────────────────────── */
function loginUser(user) {
  currentUser = user;

  document.getElementById('nav-actions-guest').style.display = 'none';
  document.getElementById('nav-actions-user').style.display  = 'block';

  var initials = user.name.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase();
  var badge = document.getElementById('user-avatar-badge');
  badge.textContent = initials;
  badge.className   = 'user-avatar ' + (user.role === 'teacher' ? 'avatar-teacher' : 'avatar-student');
  document.getElementById('user-name-badge').textContent = user.name.split(' ')[0];

  document.getElementById('nav-guest').style.display   = 'none';
  document.getElementById('nav-student').style.display = 'none';
  document.getElementById('nav-teacher').style.display = 'none';

  if (user.role === 'student') {
    document.getElementById('nav-student').style.display = 'flex';
    var el = document.getElementById('stu-first-name');
    if (el) el.textContent = user.name.split(' ')[0];
    showStudentPage('stu-dashboard');
  } else {
    document.getElementById('nav-teacher').style.display = 'flex';
    var el2 = document.getElementById('tch-first-name');
    if (el2) el2.textContent = user.name.split(' ')[0];
    showTeacherPage('tch-dashboard');
  }
}

/* ─────────────────────────────────────────
   LOGOUT
───────────────────────────────────────── */
async function logout() {
  await api('POST', '/api/signout');
  currentUser = null;

  document.getElementById('nav-actions-guest').style.display = 'flex';
  document.getElementById('nav-actions-user').style.display  = 'none';
  document.getElementById('nav-guest').style.display         = 'flex';
  document.getElementById('nav-student').style.display       = 'none';
  document.getElementById('nav-teacher').style.display       = 'none';

  document.getElementById('signin-email').value    = '';
  document.getElementById('signin-password').value = '';
  selectedRole = 'student';
  selectRole('student');

  showPage('home');
  showToast('👋 You have been signed out.');
}

/* =============================================================
   STUDENT DASHBOARD
============================================================= */
async function loadStudentDashboard() {
  const data = await api('GET', '/api/stats');
  if (!data.ok) return;

  // Update live stats bar on home page too
  var statsMap = {
    '.stat-students': data.stats.students,
    '.stat-instructors': data.stats.instructors,
    '.stat-classrooms': data.stats.classrooms,
    '.stat-subjects': data.stats.subjects
  };
  for (var sel in statsMap) {
    var els = document.querySelectorAll(sel);
    els.forEach(el => { el.textContent = statsMap[sel]; });
  }
}

/* =============================================================
   STUDENT GRADES
============================================================= */
async function loadStudentGrades() {
  if (!currentUser) return;
  const data = await api('GET', '/api/students/' + currentUser.id + '/grades');
  if (!data.ok) return;

  var tbody = document.getElementById('grades-tbody');
  if (!tbody) return;

  if (!data.grades.length) {
    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:30px">No grades recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = data.grades.map(function(g) {
    var score = parseFloat(g.Grades);
    var pill  = gradeClass(score);
    var letter = gradeLabel(score);
    return '<tr><td>' + g.Subject_Name + '</td><td>' + (g.Grades !== null ? score.toFixed(1) : '—') + ' / 100</td><td><span class="grade-pill ' + pill + '">' + letter + '</span></td></tr>';
  }).join('');
}

function gradeClass(score) {
  if (score >= 90) return 'grade-a';
  if (score >= 75) return 'grade-b';
  if (score >= 60) return 'grade-c';
  return 'grade-d';
}

function gradeLabel(score) {
  if (score >= 95) return 'A+';
  if (score >= 90) return 'A';
  if (score >= 85) return 'A-';
  if (score >= 80) return 'B+';
  if (score >= 75) return 'B';
  if (score >= 70) return 'B-';
  if (score >= 65) return 'C+';
  if (score >= 60) return 'C';
  return 'F';
}

/* =============================================================
   TEACHER DASHBOARD
============================================================= */
async function loadTeacherDashboard() {
  if (!currentUser) return;
  const data = await api('GET', '/api/teacher/' + currentUser.id + '/subjects');
  if (!data.ok) return;

  var list = document.getElementById('tch-subjects-list');
  if (!list) return;

  if (!data.subjects.length) {
    list.innerHTML = '<p style="color:var(--muted);padding:20px 0">No subjects assigned yet.</p>';
    return;
  }

  list.innerHTML = data.subjects.map(function(s) {
    return '<div class="schedule-item"><div class="sched-dot" style="background:var(--blue)"></div><div><div class="sched-name">' + s.Subject_Name + '</div><div class="sched-room">Level ' + (s.Subject_Level || '—') + ' · ' + (s.Subject_Slots || '—') + ' slots</div></div></div>';
  }).join('');
}

async function loadTeacherStudents() {
  if (!currentUser) return;
  const data = await api('GET', '/api/teacher/' + currentUser.id + '/students');
  if (!data.ok) return;

  var tbody = document.getElementById('tch-students-tbody');
  if (!tbody) return;

  if (!data.students.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:30px">No students enrolled in your subjects yet.</td></tr>';
    return;
  }

  tbody.innerHTML = data.students.map(function(s) {
    return '<tr><td>' + s.Fname + ' ' + s.Lname + '</td><td>' + s.Student_ID + '</td><td>' + (s.Level || '—') + '</td><td>' + (s.Student_Email || '—') + '</td></tr>';
  }).join('');
}

/* =============================================================
   PUBLIC PAGES — Teachers, Subjects, Classrooms
============================================================= */
async function loadPublicTeachers() {
  const data = await api('GET', '/api/instructors');
  if (!data.ok) return;

  var grid = document.getElementById('public-teachers-grid');
  if (!grid) return;

  var colors = ['#dbeafe','#dcfce7','#fef3c7','#ede9fe','#fee2e2','#cffafe'];
  var emojis = ['👨‍🏫','👩‍🏫','👨‍🔬','👩‍💻','👨‍🎨','👩‍⚕️'];

  if (!data.instructors.length) {
    grid.innerHTML = '<p style="color:var(--muted)">No instructors found.</p>';
    return;
  }

  grid.innerHTML = data.instructors.map(function(t, i) {
    var bg  = colors[i % colors.length];
    var em  = emojis[i % emojis.length];
    return '<div class="teacher-card"><div class="teacher-avatar" style="background:' + bg + '">' + em + '</div><div class="teacher-name">' + t.Emp_FName + ' ' + t.Emp_Lname + '</div><div class="teacher-subject">' + (t.Qualification || t.Dept_Name) + '</div><div class="teacher-room">' + t.Dept_Name + ' · ' + (t.Employment_Date || 'N/A') + '</div></div>';
  }).join('');
}

async function loadPublicSubjects() {
  const data = await api('GET', '/api/subjects');
  if (!data.ok) return;

  var tbody = document.getElementById('public-subjects-tbody');
  if (!tbody) return;

  if (!data.subjects.length) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center;color:var(--muted);padding:30px">No subjects found.</td></tr>';
    return;
  }

  tbody.innerHTML = data.subjects.map(function(s) {
    var room = s.Classroom_Building ? s.Classroom_Building + (s.Classroom_Floor ? ' · Floor ' + s.Classroom_Floor : '') : '—';
    return '<tr><td>' + s.Subject_Name + '</td><td>' + (s.Subject_Level || '—') + '</td><td>' + (s.Subject_Slots || '—') + ' slots</td><td>' + room + '</td></tr>';
  }).join('');
}

async function loadPublicClassrooms() {
  const data = await api('GET', '/api/classrooms');
  if (!data.ok) return;

  var list = document.getElementById('public-classrooms-list');
  if (!list) return;

  if (!data.classrooms.length) {
    list.innerHTML = '<p style="color:var(--muted)">No classrooms found.</p>';
    return;
  }

  list.innerHTML = data.classrooms.map(function(c) {
    return '<div class="room-card"><div class="room-num">' + c.Classroom_ID + '</div><div class="room-name">' + (c.Classroom_Building || 'Building') + (c.Classroom_Floor ? ' · Floor ' + c.Classroom_Floor : '') + '</div><div class="room-cap">Capacity: ' + (c.Classroom_Capacity || '—') + ' students</div></div>';
  }).join('');
}

/* =============================================================
   TEACHER CLASSROOM BOOKING (live data)
============================================================= */
async function loadTeacherClassrooms() {
  const data = await api('GET', '/api/classrooms');
  if (!data.ok) return;

  var grid = document.getElementById('tch-classroom-grid');
  if (!grid) return;

  if (!data.classrooms.length) {
    grid.innerHTML = '<p style="color:var(--muted)">No classrooms available.</p>';
    return;
  }

  grid.innerHTML = data.classrooms.map(function(c) {
    return '<div class="classroom-card available"><div class="classroom-name">Room ' + c.Classroom_ID + '</div><div class="classroom-capacity">Capacity: ' + (c.Classroom_Capacity || '—') + ' students</div><div class="classroom-capacity">' + (c.Classroom_Building || '') + (c.Classroom_Floor ? ' · Floor ' + c.Classroom_Floor : '') + '</div><div class="classroom-status">Available</div><button class="btn btn-blue" onclick="bookClassroom(' + c.Classroom_ID + ')">Book Now</button></div>';
  }).join('');
}

function bookClassroom(roomId) {
  showToast('✅ Room ' + roomId + ' has been booked successfully!');
}

function cancelBooking(roomId) {
  showToast('❌ Booking for Room ' + roomId + ' has been cancelled.');
}

/* =============================================================
   INIT — restore session on page load
============================================================= */
document.addEventListener('DOMContentLoaded', async function () {
  // Check if user has an active Flask session
  const data = await api('GET', '/api/me');
  if (data.ok && data.user) {
    loginUser(data.user);
  } else {
    showPage('home');
  }
});
