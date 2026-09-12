function number(value) {
  if (value === null || value === undefined || value === '') {
    return 0
  }

  const cleaned = String(value).replace(/[^0-9.-]/g, '')
  return Number(cleaned) || 0
}

export function normalizeRow(row) {
  const normalized = {}

  Object.entries(row).forEach(([key, value]) => {
    const cleanKey = key
      .trim()
      .toLowerCase()
      .replace(/[_-]+/g, ' ')
      .replace(/\s+/g, ' ')

    normalized[cleanKey] = value
  })

  return {
    orderDate:
      normalized['order date'] ||
      normalized['order_date'] ||
      normalized['date'],

    category:
      normalized['category'] ||
      'Unknown',

    subCategory:
      normalized['sub category'] ||
      normalized['subcategory'] ||
      'Unknown',

    region:
      normalized['region'] ||
      'Unknown',

    country:
      normalized['country'] ||
      'Unknown',

    sales: number(
      normalized['sales'] ||
      normalized['revenue']
    ),

    profit: number(
      normalized['profit']
    ),

    quantity: number(
      normalized['quantity']
    ),

    discount: number(
      normalized['discount']
    ),
  }
}

export function prepareData(rows) {
  return rows
    .map(normalizeRow)
    .filter((row) => row.category !== 'Unknown' || row.sales !== 0)
}

export function totalSales(data) {
  return data.reduce((sum, row) => sum + row.sales, 0)
}

export function totalProfit(data) {
  return data.reduce((sum, row) => sum + row.profit, 0)
}

export function totalQuantity(data) {
  return data.reduce((sum, row) => sum + row.quantity, 0)
}

export function totalOrders(data) {
  const orders = new Set()

  data.forEach((row) => {
    if (row.orderDate) {
      orders.add(`${row.orderDate}-${row.country}-${row.category}-${row.sales}`)
    }
  })

  return orders.size || data.length
}

export function averageOrderValue(data) {
  const orders = totalOrders(data)

  if (!orders) return 0

  return totalSales(data) / orders
}

export function groupByCategory(data) {
  const groups = {}

  data.forEach((row) => {
    if (!groups[row.category]) {
      groups[row.category] = {
        name: row.category,
        sales: 0,
        profit: 0,
        quantity: 0,
      }
    }

    groups[row.category].sales += row.sales
    groups[row.category].profit += row.profit
    groups[row.category].quantity += row.quantity
  })

  return Object.values(groups)
}

export function groupByRegion(data) {
  const groups = {}

  data.forEach((row) => {
    if (!groups[row.region]) {
      groups[row.region] = {
        name: row.region,
        sales: 0,
        profit: 0,
        quantity: 0,
      }
    }

    groups[row.region].sales += row.sales
    groups[row.region].profit += row.profit
    groups[row.region].quantity += row.quantity
  })

  return Object.values(groups)
}

export function groupByMonth(data) {
  const groups = {}

  data.forEach((row) => {
    if (!row.orderDate) return

    const date = new Date(row.orderDate)

    if (Number.isNaN(date.getTime())) return

    const key = `${date.getFullYear()}-${String(
      date.getMonth() + 1
    ).padStart(2, '0')}`

    if (!groups[key]) {
      groups[key] = {
        month: key,
        sales: 0,
        profit: 0,
        quantity: 0,
      }
    }

    groups[key].sales += row.sales
    groups[key].profit += row.profit
    groups[key].quantity += row.quantity
  })

  return Object.values(groups).sort((a, b) =>
    a.month.localeCompare(b.month)
  )
}

export function topCategoryByProfit(data) {
  const categories = groupByCategory(data)

  return categories.sort((a, b) => b.profit - a.profit)[0] || null
}

export function topRegionBySales(data) {
  const regions = groupByRegion(data)

  return regions.sort((a, b) => b.sales - a.sales)[0] || null
}

export function categoryMargins(data) {
  return groupByCategory(data).map((item) => ({
    ...item,
    margin: item.sales
      ? (item.profit / item.sales) * 100
      : 0,
  }))
}

export function getDashboardMetrics(data) {
  const sales = totalSales(data)
  const profit = totalProfit(data)
  const orders = totalOrders(data)

  return {
    sales,
    profit,
    orders,
    avgOrderValue: orders ? sales / orders : 0,
    quantity: totalQuantity(data),
    margin: sales ? (profit / sales) * 100 : 0,
    categories: groupByCategory(data),
    regions: groupByRegion(data),
    monthly: groupByMonth(data),
    categoryMargins: categoryMargins(data),
    topCategory: topCategoryByProfit(data),
    topRegion: topRegionBySales(data),
  }
}