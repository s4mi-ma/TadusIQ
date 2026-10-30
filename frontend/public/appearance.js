// Parser-blocking, same-origin bootstrap: apply the preference before the app or its CSS renders.
(() => {
  let theme = 'dark';
  try { if (localStorage.getItem('rapidready-appearance') === 'light') theme = 'light'; } catch {}
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'light' ? '#f8f9fb' : '#101114');
})();
