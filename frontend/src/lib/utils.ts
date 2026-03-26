import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { format } from "date-fns";
import { ko } from "date-fns/locale";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return format(new Date(dateStr), "yyyy-MM-dd", { locale: ko });
}

export function formatDateTime(dateStr: string): string {
  return format(new Date(dateStr), "yyyy-MM-dd HH:mm", { locale: ko });
}

export function formatCurrency(amount: number): string {
  if (amount == null) return "-";
  if (amount >= 100_000_000) {
    return `${(amount / 100_000_000).toFixed(1)}억원`;
  }
  if (amount >= 10_000) {
    return `${Math.round(amount / 10_000).toLocaleString()}만원`;
  }
  return `${amount.toLocaleString()}원`;
}

export function formatCurrencyManWon(amountInManWon: number): string {
  if (amountInManWon == null) return "-";
  if (amountInManWon >= 10_000) {
    return `${(amountInManWon / 10_000).toFixed(1)}억원`;
  }
  return `${Math.round(amountInManWon).toLocaleString()}만원`;
}
