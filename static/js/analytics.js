document.addEventListener("DOMContentLoaded", async () => {
  if (!window.Chart) return;
  const response = await fetch("/analytics/data");
  const data = await response.json();
  const blue = "#0b5ed7";
  const green = "#198754";
  const yellow = "#f59f00";
  const red = "#dc3545";

  const buildChart = (id, config) => {
    const canvas = document.querySelector(id);
    if (canvas) new Chart(canvas, config);
  };

  buildChart("#gradeDistributionChart", {
    type: "doughnut",
    data: {
      labels: ["A", "B", "C", "D", "F"],
      datasets: [{ data: data.gradeDistribution || [], backgroundColor: [blue, "#42a5ff", green, yellow, red] }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });

  buildChart("#subjectPerformanceChart", {
    type: "bar",
    data: {
      labels: data.subjectLabels || [],
      datasets: [{ label: "Average grade", data: data.subjectScores || [], backgroundColor: blue }],
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100 } } },
  });

  buildChart("#assignmentCompletionChart", {
    type: "line",
    data: {
      labels: data.assignmentLabels || [],
      datasets: [{ label: "Completion %", data: data.assignmentCompletion || [], borderColor: green, backgroundColor: "rgba(25,135,84,.12)", fill: true }],
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, max: 100 } } },
  });

  buildChart("#teacherActivityChart", {
    type: "bar",
    data: {
      labels: data.teacherLabels || [],
      datasets: [{ label: "Assignments created", data: data.teacherActivity || [], backgroundColor: "#42a5ff" }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });

  buildChart("#monthlyStatsChart", {
    type: "line",
    data: {
      labels: data.monthlyLabels || [],
      datasets: [{ label: "Assignments created", data: data.monthlyStats || [], borderColor: blue, backgroundColor: "rgba(11,94,215,.12)", fill: true }],
    },
    options: { responsive: true, maintainAspectRatio: false },
  });
});
