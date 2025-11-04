import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { initTheme, setTheme, type ThemeMode } from '@/lib/theme'

export function ThemeToggle() {
  const [mode, setMode] = useState<ThemeMode>('light')

  useEffect(() => {
    const initial = initTheme()
    setMode(initial)
  }, [])

  const handleToggle = () => {
    const nextMode: ThemeMode = mode === 'light' ? 'dark' : 'light'
    setMode(nextMode)
    setTheme(nextMode)
  }

  return (
    <Button variant="ghost" size="icon" onClick={handleToggle} aria-label="Toggle theme">
      {mode === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  )
}
