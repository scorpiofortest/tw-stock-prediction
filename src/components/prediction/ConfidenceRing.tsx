'use client'

import { motion } from 'framer-motion'
import { DIRECTION_COLORS } from '@/lib/constants'
import type { Direction } from '@/types/prediction'

interface ConfidenceRingProps {
  value: number
  direction: Direction
  size?: number
}

export function ConfidenceRing({ value, direction, size = 120 }: ConfidenceRingProps) {
  const strokeWidth = 10
  const radius = (size - strokeWidth) / 2
  const circumference = 2 * Math.PI * radius
  const center = size / 2
  const fillColor = DIRECTION_COLORS[direction].fill

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox={`0 0 ${size} ${size}`} className="rotate-[-90deg]">
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={strokeWidth}
          className="stroke-gray-200 dark:stroke-gray-700"
          fill="none"
        />
        {/* Progress circle */}
        <motion.circle
          cx={center}
          cy={center}
          r={radius}
          strokeWidth={strokeWidth}
          fill="none"
          stroke={fillColor}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - value / 100) }}
          transition={{ type: 'spring', stiffness: 100, damping: 20, duration: 1.5 }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <motion.span
          key={value}
          initial={{ opacity: 0, scale: 0.5 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-2xl font-bold md:text-3xl"
        >
          {value}%
        </motion.span>
        <span className="text-xs text-muted-foreground">信心值</span>
      </div>
    </div>
  )
}
