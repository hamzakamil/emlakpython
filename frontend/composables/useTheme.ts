import { onMounted, ref } from 'vue'
import { THEMES } from '../src/themes/index'

export function useTheme() {
  const theme = ref<keyof typeof THEMES>(
    (localStorage.getItem('tema') as keyof typeof THEMES) || 'KLASIK',
  )

  const applyTheme = (themeKey: keyof typeof THEMES): void => {
    document.documentElement.classList.remove(
      ...Object.values(THEMES).map((value) => `theme-${value}`),
    )
    document.documentElement.classList.add(`theme-${THEMES[themeKey]}`)
  }

  const toggleTheme = (newTheme: keyof typeof THEMES): void => {
    localStorage.setItem('tema', newTheme)
    theme.value = newTheme
    applyTheme(newTheme)
    window.dispatchEvent(new Event('theme-change'))
  }

  onMounted(() => applyTheme(theme.value))
  return { theme, toggleTheme }
}
