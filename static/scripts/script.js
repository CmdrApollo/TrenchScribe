// script.js
document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme');
  
    // Apply saved theme on load
    if (currentTheme === 'dark') {
      document.body.classList.add('dark-mode');
    }
  
    // Toggle theme on button click
    toggleButton.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
  
      // Save the current theme to localStorage
      const theme = document.body.classList.contains('dark-mode') ? 'dark' : 'light';
      localStorage.setItem('theme', theme);
    });
  });
  