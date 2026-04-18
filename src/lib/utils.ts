import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { Direction } from '@/types/prediction'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function parseDirection(directionStr: string): Direction {
  if (directionStr.includes('看漲') || directionStr.includes('上漲')) {
    return 'bullish'
  } else if (directionStr.includes('看跌') || directionStr.includes('下跌')) {
    return 'bearish'
  } else {
    return 'neutral'
  }
}
