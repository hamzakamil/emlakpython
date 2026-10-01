export const THEMES = {
  KLASIK: 'klasik',
  MODERNKOYU: 'modern-koyu',
  YUMUSAK: 'yumusak',
} as const

let currentTheme = localStorage.getItem('tema') || 'KLASIK'

function applyTheme(themeKey: keyof typeof THEMES): void {
  document.documentElement.classList.remove(
    ...Object.values(THEMES).map((theme) => `theme-${theme}`),
  )
  document.documentElement.classList.add(`theme-${THEMES[themeKey]}`)
}

window.addEventListener('DOMContentLoaded', () => {
  const themeKey = currentTheme in THEMES ? currentTheme as keyof typeof THEMES : 'KLASIK'
  applyTheme(themeKey)
})

export function setTheme(themeKey: keyof typeof THEMES): void {
  currentTheme = themeKey
  localStorage.setItem('tema', themeKey)
  applyTheme(themeKey)
  window.dispatchEvent(new Event('theme-change'))
}
