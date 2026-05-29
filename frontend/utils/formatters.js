export function formatInr(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: numeric % 1 === 0 ? 0 : 2,
    maximumFractionDigits: 2,
  }).format(numeric);
}

export function formatNumber(value, options = {}) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
    ...options,
  }).format(numeric);
}

export function formatRate(value) {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "N/A";
  return `₹${formatNumber(numeric, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function formatArea(value, unit = "sqft") {
  const numeric = Number(value);
  if (!Number.isFinite(numeric) || numeric <= 0) return "N/A";
  return `${formatNumber(numeric)} ${unit || "sqft"}`;
}

export function rateLabel(unit = "sqft") {
  return `Rate per ${unit || "sqft"}`;
}
