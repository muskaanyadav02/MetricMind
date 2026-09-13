export function formatCurrency(value) {
  return `₹${Number(value).toLocaleString("en-IN")}`;
}

export function formatCompact(value) {
  if (value >= 100000) {
    return `₹${(value / 100000).toFixed(1)}L`;
  }

  if (value >= 1000) {
    return `₹${(value / 1000).toFixed(1)}K`;
  }

  return `₹${value}`;
}