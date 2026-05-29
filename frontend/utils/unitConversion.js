export const AREA_SQFT_FACTORS = {
  sqft: 1,
  sqm: 10.7639,
  sqyrd: 9,
};

export function convertArea(value, fromUnit = "sqft", toUnit = "sqft") {
  const numeric = Number(value);
  const fromFactor = AREA_SQFT_FACTORS[fromUnit] || 1;
  const toFactor = AREA_SQFT_FACTORS[toUnit] || fromFactor;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return (numeric * fromFactor) / toFactor;
}

export function normalizeToSqft(value, unit = "sqft") {
  const numeric = Number(value);
  const factor = AREA_SQFT_FACTORS[unit] || 1;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return numeric * factor;
}

export function convertRate(value, fromUnit = "sqft", toUnit = "sqft") {
  const numeric = Number(value);
  const fromFactor = AREA_SQFT_FACTORS[fromUnit] || 1;
  const toFactor = AREA_SQFT_FACTORS[toUnit] || fromFactor;
  if (!Number.isFinite(numeric) || numeric <= 0) return null;
  return (numeric / fromFactor) * toFactor;
}

export function calculateTotalArea(carpetArea, loadingFactor = 1) {
  const area = Number(carpetArea);
  const factor = Number(loadingFactor);
  if (!Number.isFinite(area) || area <= 0) return null;
  return area * (Number.isFinite(factor) && factor > 0 ? factor : 1);
}
