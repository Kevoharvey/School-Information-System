document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".alert[data-auto-dismiss]").forEach((alertEl) => {
    setTimeout(() => {
      const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
      alert.close();
    }, 5000);
  });

  // Global date restrictions
  const today = new Date().toISOString().split('T')[0];
  
  // No future dates allowed for Birth Date
  document.querySelectorAll('input[type="date"][name="birth_date"]').forEach(el => {
    el.setAttribute('max', today);
  });

  // No past dates allowed for Available Start Date (Employment Date)
  document.querySelectorAll('input[type="date"][name="employment_date"]').forEach(el => {
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
});
