/* =============================================================
   EduNova — student.js
   Standalone JS for the /student page (student.html).
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

  if (id === 'stu-dashboard' && currentUser) loadStudentDashboard();
  if (id === 'stu-grades'    && currentUser) loadStudentGrades();
}

/* ─── Dashboard stats ─── */
async function loadStudentDashboard() {
  var data = await api('GET', '/api/stats');
  if (!data.ok) return;
  document.querySelectorAll('.stat-students').forEach(function (e) { e.textContent = data.stats.students; });
  document.querySelectorAll('.stat-instructors').forEach(function (e) { e.textContent = data.stats.instructors; });
  document.querySelectorAll('.stat-classrooms').forEach(function (e) { e.textContent = data.stats.classrooms; });
  document.querySelectorAll('.stat-subjects').forEach(function (e) { e.textContent = data.stats.subjects; });
}

/* ─── Grades (live from DB) ─── */
async function loadStudentGrades() {
  if (!currentUser) return;
  var data = await api('GET', '/api/students/' + currentUser.id + '/grades');
  if (!data.ok) return;

  var tbody = document.getElementById('grades-tbody');
  if (!tbody) return;

  if (!data.grades.length) {
    tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;color:var(--muted);padding:30px">No grades recorded yet.</td></tr>';
    return;
  }

  tbody.innerHTML = data.grades.map(function (g) {
    var score = parseFloat(g.Grades);
    var pill = score >= 90 ? 'grade-a' : score >= 75 ? 'grade-b' : score >= 60 ? 'grade-c' : 'grade-d';
    var letter = score >= 95 ? 'A+' : score >= 90 ? 'A' : score >= 85 ? 'A-' : score >= 80 ? 'B+' : score >= 75 ? 'B' : score >= 70 ? 'B-' : score >= 65 ? 'C+' : score >= 60 ? 'C' : 'F';
    return '<tr><td>' + g.Subject_Name + '</td><td>' + score.toFixed(1) + ' / 100</td><td><span class="grade-pill ' + pill + '">' + letter + '</span></td></tr>';
  }).join('');
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
    if (data.ok && data.user && data.user.role === 'student') {
      currentUser = data.user;
      var badge = document.getElementById('user-avatar-badge');
      var initials = data.user.name.split(' ').map(function (w) { return w[0]; }).slice(0, 2).join('').toUpperCase();
      if (badge) { badge.textContent = initials; }
      var nameBadge = document.getElementById('user-name-badge');
      if (nameBadge) nameBadge.textContent = data.user.name.split(' ')[0];
      var firstName = document.getElementById('stu-first-name');
      if (firstName) firstName.textContent = data.user.name.split(' ')[0];
      loadStudentDashboard();
    } else {
      window.location.href = '/';
    }
  } catch (e) {
    window.location.href = '/';
  }
});
