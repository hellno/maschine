import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function hashEmail(email: string): string {
  const normalized = email.toLowerCase().trim();
  return btoa(normalized).replace(/=+$/, '');
}
