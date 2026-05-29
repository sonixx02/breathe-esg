export function formatNumber(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return value;
  return new Intl.NumberFormat("en", { maximumFractionDigits: 1 }).format(number);
}
