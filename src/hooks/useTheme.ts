'use client'

import { useEffect } from 'react'
import { useUIStore } from '@/stores/useUIStore'

export function useTheme() {
  const { theme, setTheme } = useUIStore()

  useEffect(() => {
    const root = document.documentElement

    if (theme === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      const applySystem = () => {
        root.classList.toggle('dark', mq.matches)
      }
      applySystem()
      mq.addEventListener('change', applySystem)
      return () => mq.removeEventListener('change', applySystem)
    }

    root.classList.toggle('dark', theme === 'dark')
  }, [theme])

  return { theme, setTheme }
}
