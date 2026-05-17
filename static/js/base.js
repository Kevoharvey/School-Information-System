document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.querySelector("[data-theme-toggle]");
  const getStoredTheme = () => {
    try {
      return localStorage.getItem("gis-theme");
    } catch {
      return null;
    }
  };
  const setStoredTheme = (theme) => {
    try {
      localStorage.setItem("gis-theme", theme);
    } catch {
      // The visual theme can still change even when storage is unavailable.
    }
  };
  const applyTheme = (theme) => {
    const isDark = theme === "dark";

    document.documentElement.dataset.theme = theme;
    document.documentElement.dataset.bsTheme = theme;

    if (themeToggle) {
      themeToggle.setAttribute("aria-pressed", String(isDark));
      themeToggle.setAttribute("aria-label", isDark ? "Switch to light mode" : "Switch to dark mode");
      themeToggle.setAttribute("title", isDark ? "Switch to light mode" : "Switch to dark mode");
      themeToggle.innerHTML = `<i class="bi ${isDark ? "bi-sun" : "bi-moon-stars"}" aria-hidden="true"></i>`;
    }
  };

  const savedTheme = getStoredTheme();
  const initialTheme = savedTheme || document.documentElement.dataset.theme || "light";
  applyTheme(initialTheme);

  themeToggle?.addEventListener("click", () => {
    const nextTheme = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    setStoredTheme(nextTheme);
    applyTheme(nextTheme);
  });

  document.querySelectorAll("[data-confirm]").forEach((button) => {
    button.addEventListener("click", (event) => {
      if (!window.confirm(button.dataset.confirm)) {
        event.preventDefault();
      }
    });
  });

  // Global date restrictions
  const today = new Date().toISOString().split('T')[0];
  
  // No future dates allowed for Birth Date and Attendance Date
  document.querySelectorAll('input[type="date"][name="birth_date"], input[type="date"][name="att_date"]').forEach(el => {
    el.setAttribute('max', today);
  });

  // No past dates allowed for Employment Date and Assignment Deadline
  document.querySelectorAll('input[type="date"][name="employment_date"], input[type="date"][name="due_date"]').forEach(el => {
    el.setAttribute('min', today);
  });

  // Global Phone Number constraints
  document.querySelectorAll('input[type="tel"], input[name*="phone"], input[name*="Phone"]').forEach(el => {
    el.setAttribute('pattern', '[0-9+\\\\s\\\\-()]+');
    el.setAttribute('title', 'Please enter a valid phone number');
  });

  // Global Password constraints
  document.querySelectorAll('input[type="password"]').forEach(el => {
    if(!el.hasAttribute('minlength')) {
      el.setAttribute('minlength', '8');
    }
  });

  // Global Numeric constraints (Scores, Capacity)
  document.querySelectorAll('input[name="max_score"], input[name="score"]').forEach(el => {
    if(!el.hasAttribute('min')) el.setAttribute('min', '0');
    if(!el.hasAttribute('max')) el.setAttribute('max', '100');
  });

  document.querySelectorAll('input[name="capacity"]').forEach(el => {
    if(!el.hasAttribute('min')) el.setAttribute('min', '1');
  });
});
