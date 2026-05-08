document.addEventListener("DOMContentLoaded", () => {
  const sidebarToggle = document.querySelector("[data-sidebar-toggle]");
  const getStoredSidebarState = () => {
    try {
      return localStorage.getItem("gis-sidebar");
    } catch {
      return null;
    }
  };
  const setStoredSidebarState = (state) => {
    try {
      localStorage.setItem("gis-sidebar", state);
    } catch {
      // The sidebar can still resize even when storage is unavailable.
    }
  };
  const applySidebarState = (state) => {
    const isCollapsed = state === "collapsed";

    document.documentElement.dataset.sidebar = isCollapsed ? "collapsed" : "expanded";

    if (sidebarToggle) {
      sidebarToggle.setAttribute("aria-pressed", String(isCollapsed));
      sidebarToggle.setAttribute("aria-label", isCollapsed ? "Expand sidebar" : "Collapse sidebar");
      sidebarToggle.setAttribute("title", isCollapsed ? "Expand sidebar" : "Collapse sidebar");
      sidebarToggle.innerHTML = `<i class="bi ${isCollapsed ? "bi-layout-sidebar" : "bi-layout-sidebar-inset"}" aria-hidden="true"></i><span class="sidebar-label">${isCollapsed ? "Expand" : "Collapse"}</span>`;
    }
  };

  const initialState = getStoredSidebarState() || document.documentElement.dataset.sidebar || "expanded";
  applySidebarState(initialState);

  sidebarToggle?.addEventListener("click", () => {
    const nextState = document.documentElement.dataset.sidebar === "collapsed" ? "expanded" : "collapsed";
    setStoredSidebarState(nextState);
    applySidebarState(nextState);
  });
});
