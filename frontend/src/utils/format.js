export function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(Number(value) || 0)
}

export function formatNumber(value) {
  return new Intl.NumberFormat('en-IN', {
    maximumFractionDigits: 0,
  }).format(Number(value) || 0)
}

export function formatPercent(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

export function shortCurrency(value) {
  const number = Number(value) || 0

  if (Math.abs(number) >= 1000000) {
    return `₹${(number / 1000000).toFixed(1)}M`
  }

  if (Math.abs(number) >= 1000) {
    return `₹${(number / 1000).toFixed(1)}K`
  }

  return `₹${number.toFixed(0)}`
}