const labelMap = {
  active: "Active",
  low_stock: "Low Stock",
  expired: "Expired",
  out_of_stock: "Out of Stock"
};

function StatusBadge({ status }) {
  const label = labelMap[status] ?? status;
  return <span className={`status-badge ${status}`}>{label}</span>;
}

export default StatusBadge;

