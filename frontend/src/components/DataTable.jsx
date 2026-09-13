function DataTable({ data }) {
  return (
    <div className="data-table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            <th>Order Date</th>
            <th>Category</th>
            <th>Region</th>
            <th>Sales</th>
            <th>Profit</th>
          </tr>
        </thead>

        <tbody>
          {data.map((row, index) => (
            <tr key={index}>
              <td>{row.date}</td>
              <td>{row.category}</td>
              <td>{row.region}</td>
              <td>{row.sales}</td>
              <td className="profit">{row.profit}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;