export type Appearance = 'dark' | 'light';
export function applyAppearance(theme: Appearance): boolean {
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', theme === 'light' ? '#f8f9fb' : '#101114');
  try { localStorage.setItem('rapidready-appearance', theme); return true; }
  catch { return false; }
}
