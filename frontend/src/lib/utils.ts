import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"
import type { User } from "@/lib/types"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Role hierarchy - higher values have more permissions
const ROLE_HIERARCHY = {
  'user': 1,
  'admin': 2,
  'super_admin': 3
}

export function hasPermission(user: User | null, requiredRole: string): boolean {
  if (!user || !user.roles) return false

  const requiredLevel = ROLE_HIERARCHY[requiredRole as keyof typeof ROLE_HIERARCHY] || 0
  const userMaxLevel = Math.max(...user.roles.map((role: string) =>
    ROLE_HIERARCHY[role as keyof typeof ROLE_HIERARCHY] || 0
  ))

  return userMaxLevel >= requiredLevel
}

export function getRequiredRole(pathname: string): string | null {
  // Define route-based role requirements
  if (pathname.startsWith('/admin')) {
    return 'admin'
  }
  if (pathname.startsWith('/dashboard')) {
    return 'user'
  }
  return null
}
