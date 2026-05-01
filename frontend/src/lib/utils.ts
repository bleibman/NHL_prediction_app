export function formatSeason(s: number): string {
  const start = Math.floor(s / 10000);
  const end = (start + 1).toString().slice(-2);
  return `${start}\u201325` === `${start}\u2013${end}`
    ? `${start}\u2013${end}`
    : `${start}\u2013${end}`;
}

export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
