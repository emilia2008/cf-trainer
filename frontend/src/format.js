// Codeforces ranks, lowest first. `color` names a CSS variable defined in styles.css.
export const RANKS = [
  { min: 0, title: "Newbie", color: "newbie" },
  { min: 1200, title: "Pupil", color: "pupil" },
  { min: 1400, title: "Specialist", color: "specialist" },
  { min: 1600, title: "Expert", color: "expert" },
  { min: 1900, title: "Candidate Master", color: "cm" },
  { min: 2100, title: "Master", color: "master" },
  { min: 2300, title: "International Master", color: "master" },
  { min: 2400, title: "Grandmaster", color: "red" },
  { min: 2600, title: "International Grandmaster", color: "red" },
  { min: 3000, title: "Legendary Grandmaster", color: "red" },
];

export function rankFor(rating) {
  const value = rating ?? 0;
  return RANKS.reduce((current, rank) => (value >= rank.min ? rank : current), RANKS[0]);
}

export function rankColor(title) {
  const rank = RANKS.find((r) => r.title === title) ?? RANKS[0];
  return `var(--rank-${rank.color})`;
}

const compact = new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat("en");
const date = new Intl.DateTimeFormat("en", { year: "numeric", month: "short", day: "numeric" });
const monthYear = new Intl.DateTimeFormat("en", { year: "numeric", month: "short" });

export const formatNumber = (n) => (n == null ? "—" : whole.format(n));
export const formatCompact = (n) => (n == null ? "—" : compact.format(n));
export const formatPercent = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
export const formatDate = (unixSeconds) => date.format(new Date(unixSeconds * 1000));
export const formatMonthYear = (ms) => monthYear.format(new Date(ms));
export const formatSigned = (n) => (n == null ? "—" : n > 0 ? `+${whole.format(n)}` : whole.format(n));

export function formatDateTime(iso) {
  if (!iso) return "never";
  return new Date(iso).toLocaleString("en", { dateStyle: "medium", timeStyle: "short" });
}

export const problemCode = (p) => `${p.contest_id ?? ""}${p.index}`;
