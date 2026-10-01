
import { Download, FileText, Filter, Search } from "lucide-react";
import { useMemo, useState } from "react";
import DataTable from "../components/DataTable";
import { reportData } from "../utils/analytics";
import "./Report.css";

const PAGE_SIZE = 5;
const MAX_VISIBLE_PAGES = 3;

// Parse formatted amounts such as "₹2,480", "2,480", or "-₹350".
const parseAmount = (value) => {
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : 0;
  }

  const cleanedValue = String(value ?? "").replace(/[^\d.-]/g, "");
  const amount = Number(cleanedValue);

  return Number.isFinite(amount) ? amount : 0;
};

// Escape values so commas, quotes, and line breaks remain valid in CSV.
const escapeCSV = (value) => {
  const text = String(value ?? "");
  return `"${text.replace(/"/g, '""')}"`;
};

function Reports() {
  const [search, setSearch] = useState("");
  const [currentPage, setCurrentPage] = useState(1);

  // Calculate totals using the complete dataset.
  const { totalSales, totalProfit } = useMemo(() => {
    return reportData.reduce(
      (totals, row) => ({
        totalSales: totals.totalSales + parseAmount(row.sales),
        totalProfit: totals.totalProfit + parseAmount(row.profit),
      }),
      { totalSales: 0, totalProfit: 0 }
    );
  }, []);

  // Search across every field in each report record.
  const filteredData = useMemo(() => {
    const searchTerm = search.trim().toLowerCase();

    if (!searchTerm) {
      return reportData;
    }

    return reportData.filter((row) =>
      Object.values(row)
        .join(" ")
        .toLowerCase()
        .includes(searchTerm)
    );
  }, [search]);

  // Calculate pagination from the filtered records.
  const totalRecords = filteredData.length;
  const totalPages = Math.ceil(totalRecords / PAGE_SIZE);

  const safePage = Math.min(
    Math.max(currentPage, 1),
    Math.max(totalPages, 1)
  );

  const startIndex =
    totalRecords === 0 ? 0 : (safePage - 1) * PAGE_SIZE;

  const endIndex = Math.min(startIndex + PAGE_SIZE, totalRecords);

  const paginatedData = filteredData.slice(startIndex, endIndex);

  // Display up to three page buttons around the current page.
  const visiblePages = useMemo(() => {
    if (totalPages === 0) {
      return [];
    }

    const firstPage = Math.max(
      1,
      Math.min(
        safePage - Math.floor(MAX_VISIBLE_PAGES / 2),
        totalPages - MAX_VISIBLE_PAGES + 1
      )
    );

    const lastPage = Math.min(
      totalPages,
      firstPage + MAX_VISIBLE_PAGES - 1
    );

    return Array.from(
      { length: lastPage - firstPage + 1 },
      (_, index) => firstPage + index
    );
  }, [safePage, totalPages]);

  const handleSearch = (event) => {
    setSearch(event.target.value);
    setCurrentPage(1);
  };

  const clearSearch = () => {
    setSearch("");
    setCurrentPage(1);
  };

  // Export all matching records, not just the current page.
  const downloadCSV = () => {
    const header = [
      "Order Date",
      "Category",
      "Region",
      "Sales",
      "Profit",
    ];

    const rows = filteredData.map((row) => [
      row.date,
      row.category,
      row.region,
      row.sales,
      row.profit,
    ]);

    const csvContent = [header, ...rows]
      .map((row) => row.map(escapeCSV).join(","))
      .join("\r\n");

    // BOM improves Unicode and currency-symbol compatibility in spreadsheet apps.
    const blob = new Blob(["\uFEFF", csvContent], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "metricmind-sales-report.csv";

    document.body.appendChild(link);
    link.click();
    link.remove();

    // Delay revocation to allow the browser to begin the download.
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="reports-page">
      {/* Page heading */}
      <div className="page-heading">
        <div>
          <span className="eyebrow">REPORTS</span>
          <h1>Business Reports</h1>
          <p>View, filter and export your business data.</p>
        </div>

        <button
          className="primary-button"
          onClick={downloadCSV}
          type="button"
          disabled={totalRecords === 0}
        >
          <Download size={15} aria-hidden="true" />
          Download CSV
        </button>
      </div>

      {/* Summary cards */}
      <div className="report-summary">
        <div>
          <span>REPORT TYPE</span>
          <strong>Sales Report</strong>
        </div>

        <div>
          <span>RECORDS</span>
          <strong>{reportData.length.toLocaleString("en-IN")}</strong>
        </div>

        <div>
          <span>TOTAL SALES</span>
          <strong>
            ₹{totalSales.toLocaleString("en-IN", {
              maximumFractionDigits: 2,
            })}
          </strong>
        </div>

        <div>
          <span>TOTAL PROFIT</span>
          <strong>
            ₹{totalProfit.toLocaleString("en-IN", {
              maximumFractionDigits: 2,
            })}
          </strong>
        </div>
      </div>

      {/* Report table */}
      <div className="report-card">
        <div className="report-toolbar">
          <div className="report-title">
            <div className="report-icon">
              <FileText size={17} aria-hidden="true" />
            </div>

            <div>
              <strong>Sales Report</strong>
              <span>
                {totalRecords.toLocaleString("en-IN")} matching records
              </span>
            </div>
          </div>

          <div className="report-tools">
            <div className="table-search">
              <Search size={14} aria-hidden="true" />

              <input
                type="search"
                value={search}
                onChange={handleSearch}
                placeholder="Search records..."
                aria-label="Search report records"
              />
            </div>

            <button
              className="filter-button"
              onClick={clearSearch}
              type="button"
              disabled={!search}
              title="Clear search"
            >
              <Filter size={14} aria-hidden="true" />
              Clear
            </button>
          </div>
        </div>

        <DataTable data={paginatedData} />

        {/* Pagination footer */}
        <div className="table-footer">
          <span>
            Showing {startIndex + (totalRecords > 0 ? 1 : 0)}–
            {endIndex} of {totalRecords.toLocaleString("en-IN")} records
          </span>

          <div className="pagination" aria-label="Report pagination">
            <button
              type="button"
              onClick={() =>
                setCurrentPage((page) => Math.max(1, page - 1))
              }
              disabled={safePage <= 1 || totalPages === 0}
              aria-label="Previous page"
            >
              Previous
            </button>

            {visiblePages.map((page) => (
              <button
                key={page}
                type="button"
                className={safePage === page ? "current" : ""}
                onClick={() => setCurrentPage(page)}
                aria-label={`Page ${page}`}
                aria-current={safePage === page ? "page" : undefined}
              >
                {page}
              </button>
            ))}

            <button
              type="button"
              onClick={() =>
                setCurrentPage((page) =>
                  Math.min(Math.max(totalPages, 1), page + 1)
                )
              }
              disabled={totalPages === 0 || safePage >= totalPages}
              aria-label="Next page"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Reports;
