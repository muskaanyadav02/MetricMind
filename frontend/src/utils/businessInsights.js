
const CSV_PATH = "/data/global_superstore.csv";

function parseCSV(text) {
  const rows = [];
  let row = [];
  let value = "";
  let quoted = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (char === '"') {
      if (quoted && text[i + 1] === '"') {
        value += '"';
        i++;
      } else {
        quoted = !quoted;
      }
    } else if (char === "," && !quoted) {
      row.push(value);
      value = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && text[i + 1] === "\n") {
        i++;
      }

      row.push(value);

      if (row.some((item) => item.trim() !== "")) {
        rows.push(row);
      }

      row = [];
      value = "";
    } else {
      value += char;
    }
  }

  if (value.length > 0 || row.length > 0) {
    row.push(value);
    if (row.some((item) => item.trim() !== "")) {
      rows.push(row);
    }
  }

  if (quoted) {
    throw new Error("The CSV contains an unclosed quoted field.");
  }

  if (rows.length < 2) {
    throw new Error("The CSV file contains no usable data.");
  }

  const headers = rows[0].map((header) =>
    header.replace(/^\uFEFF/, "").trim()
  );

  if (headers.some((header) => !header)) {
    throw new Error("The CSV contains an empty column name.");
  }

  if (new Set(headers).size !== headers.length) {
    throw new Error("The CSV contains duplicate column names.");
  }

  return rows.slice(1).map((values) =>
    Object.fromEntries(
      headers.map((header, index) => [
        header,
        (values[index] ?? "").trim(),
      ])
    )
  );
}

function number(value) {
  if (value === null || value === undefined || value === "") {
    return null;
  }

  const result = Number(value);
  return Number.isFinite(result) ? result : null;
}

function groupBy(rows, key, metric) {
  const groups = new Map();

  for (const row of rows) {
    const name = row[key]?.trim();

    if (!name) continue;

    const current = groups.get(name) ?? {
      name,
      sales: 0,
      profit: 0,
      quantity: 0,
      count: 0,
    };

    current.sales += number(row.Sales) ?? 0;
    current.profit += number(row.Profit) ?? 0;
    current.quantity += number(row.Quantity) ?? 0;
    current.count++;

    groups.set(name, current);
  }

  return [...groups.values()].sort((a, b) => {
    if (b[metric] !== a[metric]) {
      return b[metric] - a[metric];
    }

    return a.name.localeCompare(b.name);
  });
}

export async function loadBusinessInsights() {
  const response = await fetch(CSV_PATH);

  if (!response.ok) {
    throw new Error(
      `Could not load the business dataset (${response.status}).`
    );
  }

  const text = await response.text();
  const rows = parseCSV(text);

  const required = [
    "Category",
    "Region",
    "Product.Name",
    "Sales",
    "Profit",
    "Order.Date",
  ];

  const missing = required.filter(
    (column) => !(column in rows[0])
  );

  if (missing.length) {
    throw new Error(
      `The dataset is missing required columns: ${missing.join(", ")}`
    );
  }

  const validRows = rows.filter((row) => {
    return (
      Boolean(row.Category) &&
      Boolean(row.Region) &&
      Boolean(row["Product.Name"]) &&
      number(row.Sales) !== null &&
      number(row.Profit) !== null
    );
  });

  if (validRows.length === 0) {
    throw new Error("No valid business records were found.");
  }

  const totalSales = validRows.reduce(
    (sum, row) => sum + number(row.Sales),
    0
  );

  const totalProfit = validRows.reduce(
    (sum, row) => sum + number(row.Profit),
    0
  );

  const categories = groupBy(validRows, "Category", "profit");
  const regions = groupBy(validRows, "Region", "sales");
  const products = groupBy(validRows, "Product.Name", "profit");

  const lossProducts = products
    .filter((product) => product.profit < 0)
    .sort((a, b) => a.profit - b.profit)
    .slice(0, 5);

  // Keep dates as YYYY-MM-DD strings to avoid timezone shifts.
  const datedRows = validRows
    .map((row) => ({
      ...row,
      dateKey: String(row["Order.Date"] ?? "").slice(0, 10),
    }))
    .filter((row) => {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(row.dateKey)) {
        return false;
      }

      const parsed = new Date(`${row.dateKey}T00:00:00Z`);

      return (
        !Number.isNaN(parsed.getTime()) &&
        parsed.toISOString().slice(0, 10) === row.dateKey
      );
    });

  const dates = datedRows
    .map((row) => row.dateKey)
    .sort();

  const monthlyGroups = new Map();

  for (const row of datedRows) {
    const month = row.dateKey.slice(0, 7);

    monthlyGroups.set(
      month,
      (monthlyGroups.get(month) ?? 0) + number(row.Sales)
    );
  }

  const monthlySales = [...monthlyGroups.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, sales]) => ({ month, sales }));

  let monthlyChange = null;

  if (monthlySales.length >= 2) {
    const previous = monthlySales[monthlySales.length - 2].sales;
    const latest = monthlySales[monthlySales.length - 1].sales;

    monthlyChange =
      previous === 0
        ? null
        : ((latest - previous) / Math.abs(previous)) * 100;
  }

  return {
    recordCount: validRows.length,
    totalSales,
    totalProfit,
    profitMargin: totalSales
      ? (totalProfit / totalSales) * 100
      : 0,
    dateRange: {
      start: dates[0] ?? null,
      end: dates[dates.length - 1] ?? null,
    },
    categories,
    regions,
    topCategory: categories[0] ?? null,
    topRegion: regions[0] ?? null,
    lossProducts,
    monthlySales,
    monthlyChange,
  };
}
