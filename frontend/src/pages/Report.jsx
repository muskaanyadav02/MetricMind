import {
  Download,
  FileText,
  Filter,
  Search,
} from "lucide-react";

import { useState } from "react";

import DataTable from "../components/DataTable";

import { reportData } from "../utils/analytics";

import "./Report.css";

function Reports() {
  const [search, setSearch] = useState("");

  const filteredData = reportData.filter((row) =>
    Object.values(row)
      .join(" ")
      .toLowerCase()
      .includes(search.toLowerCase())
  );

  const downloadCSV = () => {
    const header = [
      "Order Date",
      "Category",
      "Region",
      "Sales",
      "Profit",
    ];

    const rows = reportData.map((row) => [
      row.date,
      row.category,
      row.region,
      row.sales,
      row.profit,
    ]);

    const csv = [
      header,
      ...rows,
    ]
      .map((row) => row.join(","))
      .join("\n");

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "metricmind-sales-report.csv";
    link.click();

    URL.revokeObjectURL(url);
  };

  return (
    <div className="reports-page">

      <div className="page-heading">
        <div>
          <span className="eyebrow">REPORTS</span>
          <h1>Business Reports</h1>
          <p>
            View, filter and export your business data.
          </p>
        </div>

        <button
          className="primary-button"
          onClick={downloadCSV}
        >
          <Download size={15} />
          Download CSV
        </button>
      </div>

      <div className="report-summary">
        <div>
          <span>REPORT TYPE</span>
          <strong>Sales Report</strong>
        </div>

        <div>
          <span>RECORDS</span>
          <strong>1,999</strong>
        </div>

        <div>
          <span>TOTAL SALES</span>
          <strong>₹56,591</strong>
        </div>

        <div>
          <span>TOTAL PROFIT</span>
          <strong>₹24,813</strong>
        </div>
      </div>

      <div className="report-card">

        <div className="report-toolbar">
          <div className="report-title">
            <div className="report-icon">
              <FileText size={17} />
            </div>

            <div>
              <strong>Sales Report</strong>
              <span>Dataset records</span>
            </div>
          </div>

          <div className="report-tools">

            <div className="table-search">
              <Search size={14} />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search records..."
              />
            </div>

            <button className="filter-button">
              <Filter size={14} />
              Filter
            </button>
          </div>
        </div>

        <DataTable data={filteredData} />

        <div className="table-footer">
          <span>
            Showing {filteredData.length} of 1,999 records
          </span>

          <div>
            <button>Previous</button>
            <button className="current">1</button>
            <button>2</button>
            <button>3</button>
            <button>Next</button>
          </div>
        </div>

      </div>
    </div>
  );
}

export default Reports;