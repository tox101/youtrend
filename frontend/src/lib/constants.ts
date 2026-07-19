export const COUNTRIES = [
  { code: "KR", name: "대한민국", flag: "🇰🇷" },
  { code: "US", name: "미국", flag: "🇺🇸" },
  { code: "JP", name: "일본", flag: "🇯🇵" },
  { code: "IN", name: "인도", flag: "🇮🇳" },
  { code: "GB", name: "영국", flag: "🇬🇧" },
  { code: "CA", name: "캐나다", flag: "🇨🇦" },
  { code: "AU", name: "호주", flag: "🇦🇺" },
  { code: "GLOBAL", name: "전체", flag: "🌍" },
] as const;

export type CountryCode = (typeof COUNTRIES)[number]["code"];

export const PERIODS = [
  { value: "daily", label: "오늘" },
  { value: "weekly", label: "주간" },
  { value: "monthly", label: "월간" },
] as const;

export const TREND_HOURS = [1, 3, 6, 12, 24] as const;

export function formatViews(n: number): string {
  if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toString();
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function getScoreColor(score: number): string {
  if (score >= 90) return "text-rose-400";
  if (score >= 70) return "text-amber-400";
  if (score >= 50) return "text-emerald-400";
  return "text-slate-400";
}

export function getScoreBg(score: number): string {
  if (score >= 90) return "bg-rose-500/20 border-rose-500/40";
  if (score >= 70) return "bg-amber-500/20 border-amber-500/40";
  if (score >= 50) return "bg-emerald-500/20 border-emerald-500/40";
  return "bg-slate-500/20 border-slate-500/40";
}
