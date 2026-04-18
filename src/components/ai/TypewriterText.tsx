'use client'

import { useState, useEffect } from 'react'

interface TypewriterTextProps {
  text: string
  speed?: number
  onComplete?: () => void
  className?: string
}

export function TypewriterText({ text, speed = 30, onComplete, className }: TypewriterTextProps) {
  const [displayed, setDisplayed] = useState('')
  const [index, setIndex] = useState(0)

  useEffect(() => {
    setDisplayed('')
    setIndex(0)
  }, [text])

  useEffect(() => {
    if (index < text.length) {
      const timer = setTimeout(() => {
        setDisplayed((prev) => prev + text[index])
        setIndex((prev) => prev + 1)
      }, speed)
      return () => clearTimeout(timer)
    } else if (index === text.length && text.length > 0) {
      onComplete?.()
    }
  }, [index, text, speed, onComplete])

  return (
    <span className={className}>
      {displayed}
      {index < text.length && (
        <span className="inline-block h-4 w-0.5 animate-pulse bg-current" />
      )}
    </span>
  )
}
