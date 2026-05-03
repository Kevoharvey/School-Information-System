// ── Dark Mode Toggle ──────────────────────────────────────────
// Persists user preference in localStorage & respects system preference.

(function () {
    const STORAGE_KEY = "nrc-theme";

    function getPreferredTheme() {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored) return stored;
        return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }

    function applyTheme(theme) {
        document.documentElement.setAttribute("data-theme", theme);
        // Update toggle icon
        const btn = document.getElementById("theme-toggle-btn");
        if (btn) btn.textContent = theme === "dark" ? "☀️" : "🌙";
    }

    // Apply immediately (before paint) to avoid flash
    applyTheme(getPreferredTheme());

    // Once DOM is ready, inject the toggle button if not already present
    document.addEventListener("DOMContentLoaded", () => {
        // Create toggle button
        let btn = document.getElementById("theme-toggle-btn");
        if (!btn) {
            btn = document.createElement("button");
            btn.id = "theme-toggle-btn";
            btn.className = "theme-toggle";
            btn.setAttribute("aria-label", "Toggle dark mode");
            btn.setAttribute("title", "Toggle dark mode");
            document.body.appendChild(btn);
        }

        // Set correct icon
        const current = getPreferredTheme();
        applyTheme(current);

        // Toggle on click
        btn.addEventListener("click", () => {
            const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem(STORAGE_KEY, next);
            applyTheme(next);
        });

        // Listen for system theme changes
        window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", (e) => {
            if (!localStorage.getItem(STORAGE_KEY)) {
                applyTheme(e.matches ? "dark" : "light");
            }
        });
    });
})();
