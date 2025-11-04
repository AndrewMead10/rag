export function formatNumber(value: number) {
  return new Intl.NumberFormat().format(value)
}

export function formatVectorLimit(current: number, limit: number | null) {
  if (!limit || limit < 0) {
    return `${formatNumber(current)} / Unlimited`
  }
  return `${formatNumber(current)} / ${formatNumber(limit)}`
}
