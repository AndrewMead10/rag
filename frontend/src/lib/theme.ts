export type ThemeMode = 'light' | 'dark'

const THEME_STORAGE_KEY = 'vectorlab-theme'

export function getStoredTheme(): ThemeMode | null {
  if (typeof window === 'undefined') return null
  const value = window.localStorage.getItem(THEME_STORAGE_KEY)
  if (value === 'light' || value === 'dark') {
    return value
  }
  return null
}

export function detectPreferredTheme(): ThemeMode {
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

export function applyTheme(theme: ThemeMode) {
  if (typeof document === 'undefined') return
  document.documentElement.classList.toggle('dark', theme === 'dark')
  document.body.classList.toggle('dark', theme === 'dark')
}

export function setTheme(theme: ThemeMode) {
  if (typeof window === 'undefined') return
  applyTheme(theme)
  window.localStorage.setItem(THEME_STORAGE_KEY, theme)
}

export function initTheme() {
  const stored = getStoredTheme()
  const theme = stored ?? detectPreferredTheme()
  applyTheme(theme)
  if (!stored) {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, theme)
    } catch {
      // ignore storage write failures
    }
  }
  return theme
}
