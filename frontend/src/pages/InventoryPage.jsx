import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { inventoryApi } from "../api/client";
import ErrorState from "../components/ErrorState";
import Loader from "../components/Loader";
import MedicineModal from "../components/MedicineModal";
import StatCard from "../components/StatCard";
import StatusBadge from "../components/StatusBadge";
import { formatCurrency, formatDate } from "../utils/format";

function InventoryPage() {
  const [summary, setSummary] = useState(null);
  const [medicines, setMedicines] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [savingRow, setSavingRow] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);

  const [filterInputs, setFilterInputs] = useState({ q: "", category: "", status: "" });
  const [activeFilters, setActiveFilters] = useState({ q: "", category: "", status: "" });

  const [modalOpen, setModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState("create");
  const [selectedMedicine, setSelectedMedicine] = useState(null);

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [pageSize, total]);

  const loadInventory = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [summaryRes, listRes] = await Promise.all([
        inventoryApi.getSummary(),
        inventoryApi.listMedicines({
          ...activeFilters,
          page,
          page_size: pageSize
        })
      ]);
      setSummary(summaryRes);
      setMedicines(listRes.items ?? []);
      setTotal(listRes.total ?? 0);
    } catch (err) {
      setError(err.message ?? "Unable to load inventory");
    } finally {
      setLoading(false);
    }
  }, [activeFilters, page, pageSize]);

  const loadCategories = useCallback(async () => {
    try {
      const categoryData = await inventoryApi.getCategories();
      setCategories(categoryData ?? []);
    } catch {
      setCategories([]);
    }
  }, []);

  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    loadInventory();
  }, [loadInventory]);

  function openCreateModal() {
    setModalMode("create");
    setSelectedMedicine(null);
    setModalOpen(true);
  }

  function openEditModal(medicine) {
    setModalMode("edit");
    setSelectedMedicine(medicine);
    setModalOpen(true);
  }

  async function handleSaveMedicine(payload) {
    if (modalMode === "edit" && selectedMedicine) {
      await inventoryApi.updateMedicine(selectedMedicine.id, payload);
    } else {
      await inventoryApi.addMedicine(payload);
    }
    await loadInventory();
    await loadCategories();
  }

  async function handleStatusChange(medicineId, status) {
    setSavingRow(medicineId);
    try {
      await inventoryApi.markStatus(medicineId, status);
      await loadInventory();
    } catch (err) {
      setError(err.message ?? "Unable to update status");
    } finally {
      setSavingRow(0);
    }
  }

  function submitFilters(event) {
    event.preventDefault();
    setPage(1);
    setActiveFilters(filterInputs);
  }

  function clearFilters() {
    const empty = { q: "", category: "", status: "" };
    setFilterInputs(empty);
    setActiveFilters(empty);
    setPage(1);
  }

  if (loading) return <Loader label="Loading inventory..." />;

  return (
    <section className="inventory-page">
      {error ? <ErrorState message={error} onRetry={loadInventory} /> : null}

      <div className="card-grid">
        <StatCard title="Total Medicines" value={summary?.total_medicines ?? 0} accent="accent-sky" />
        <StatCard title="Active" value={summary?.active_count ?? 0} accent="accent-emerald" />
        <StatCard title="Low Stock" value={summary?.low_stock_count ?? 0} accent="accent-amber" />
        <StatCard title="Expired" value={summary?.expired_count ?? 0} accent="accent-coral" />
      </div>

      <article className="panel">
        <div className="panel-head inventory-head">
          <h3>Inventory Table</h3>
          <button type="button" onClick={openCreateModal}>
            Add Medicine
          </button>
        </div>

        <form className="filter-row" onSubmit={submitFilters}>
          <input
            type="search"
            placeholder="Search medicine, category, manufacturer, batch..."
            value={filterInputs.q}
            onChange={(event) => setFilterInputs((prev) => ({ ...prev, q: event.target.value }))}
          />
          <select
            value={filterInputs.category}
            onChange={(event) => setFilterInputs((prev) => ({ ...prev, category: event.target.value }))}
          >
            <option value="">All Categories</option>
            {categories.map((category) => (
              <option key={category} value={category}>
                {category}
              </option>
            ))}
          </select>
          <select
            value={filterInputs.status}
            onChange={(event) => setFilterInputs((prev) => ({ ...prev, status: event.target.value }))}
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="low_stock">Low Stock</option>
            <option value="expired">Expired</option>
            <option value="out_of_stock">Out Of Stock</option>
          </select>
          <button type="submit">Apply</button>
          <button type="button" className="ghost" onClick={clearFilters}>
            Reset
          </button>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Medicine</th>
                <th>Category</th>
                <th>Batch</th>
                <th>Unit Price</th>
                <th>Stock</th>
                <th>Expiry</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {medicines.length ? (
                medicines.map((medicine) => (
                  <tr key={medicine.id}>
                    <td>
                      <strong>{medicine.name}</strong>
                      <small>{medicine.generic_name || "Generic not set"}</small>
                    </td>
                    <td>{medicine.category}</td>
                    <td>{medicine.batch_number}</td>
                    <td>{formatCurrency(medicine.unit_price)}</td>
                    <td>
                      {medicine.stock_quantity} / <span className="muted-inline">RL {medicine.reorder_level}</span>
                    </td>
                    <td>{formatDate(medicine.expiry_date)}</td>
                    <td>
                      <StatusBadge status={medicine.status} />
                    </td>
                    <td className="action-cell">
                      <button type="button" className="tiny" onClick={() => openEditModal(medicine)}>
                        Edit
                      </button>
                      <button
                        type="button"
                        className="tiny ghost"
                        disabled={savingRow === medicine.id}
                        onClick={() => handleStatusChange(medicine.id, "out_of_stock")}
                      >
                        Mark OOS
                      </button>
                      <button
                        type="button"
                        className="tiny ghost"
                        disabled={savingRow === medicine.id}
                        onClick={() => handleStatusChange(medicine.id, "expired")}
                      >
                        Mark Expired
                      </button>
                      <Link className="tiny link" to={`/inventory/${medicine.id}`}>
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="muted">
                    No medicines found for selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div className="pager">
          <button type="button" onClick={() => setPage((prev) => Math.max(1, prev - 1))} disabled={page <= 1}>
            Previous
          </button>
          <span>
            Page {page} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
            disabled={page >= totalPages}
          >
            Next
          </button>
        </div>
      </article>

      <MedicineModal
        open={modalOpen}
        mode={modalMode}
        medicine={selectedMedicine}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveMedicine}
      />
    </section>
  );
}

export default InventoryPage;

