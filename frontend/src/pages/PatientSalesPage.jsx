import { useCallback, useEffect, useMemo, useState } from "react";

import { inventoryApi, patientSalesApi } from "../api/client";
import ErrorState from "../components/ErrorState";
import Loader from "../components/Loader";
import { formatCurrency, formatDateTime } from "../utils/format";

function PatientSalesPage() {
  const [medicines, setMedicines] = useState([]);
  const [records, setRecords] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");

  const [form, setForm] = useState({
    patient_id: "",
    patient_name: "",
    medicine_id: "",
    quantity: 1,
    dosage_instructions: "",
    notes: ""
  });

  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total, pageSize]);

  const loadMedicines = useCallback(async () => {
    const listResponse = await inventoryApi.listMedicines({ page: 1, page_size: 100 });
    setMedicines(listResponse?.items ?? []);
  }, []);

  const loadRecords = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const response = await patientSalesApi.listRecords({
        q: query,
        page,
        page_size: pageSize
      });
      setRecords(response?.items ?? []);
      setTotal(response?.total ?? 0);
    } catch (err) {
      setError(err.message ?? "Unable to load patient sale records");
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, query]);

  useEffect(() => {
    async function initialize() {
      try {
        await loadMedicines();
      } catch (err) {
        setError(err.message ?? "Unable to load patient sales page");
        setLoading(false);
      }
    }
    initialize();
  }, [loadMedicines]);

  useEffect(() => {
    loadRecords();
  }, [loadRecords]);

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    try {
      await patientSalesApi.createSale({
        patient_id: form.patient_id.trim(),
        patient_name: form.patient_name.trim() || null,
        medicine_id: Number(form.medicine_id),
        quantity: Number(form.quantity),
        dosage_instructions: form.dosage_instructions.trim() || null,
        notes: form.notes.trim() || null
      });

      setForm((prev) => ({
        ...prev,
        quantity: 1,
        dosage_instructions: "",
        notes: ""
      }));
      setPage(1);
      await loadRecords();
      await loadMedicines();
    } catch (err) {
      setError(err.message ?? "Unable to record sale");
    } finally {
      setSaving(false);
    }
  }

  function handleSearch(event) {
    event.preventDefault();
    setPage(1);
    setQuery(searchInput.trim());
  }

  if (loading) return <Loader label="Loading patient sales..." />;

  return (
    <section className="patient-sales-page">
      {error ? <ErrorState message={error} onRetry={loadRecords} /> : null}

      <article className="panel">
        <div className="panel-head">
          <h3>Sell Medicine to Patient</h3>
        </div>
        <form className="sale-form" onSubmit={handleSubmit}>
          <label>
            Patient ID
            <input
              required
              value={form.patient_id}
              onChange={(event) => setField("patient_id", event.target.value)}
              placeholder="e.g. PAT-1024"
            />
          </label>
          <label>
            Patient Name
            <input
              value={form.patient_name}
              onChange={(event) => setField("patient_name", event.target.value)}
              placeholder="Optional"
            />
          </label>
          <label>
            Medicine
            <select
              required
              value={form.medicine_id}
              onChange={(event) => setField("medicine_id", event.target.value)}
            >
              <option value="">Select Medicine</option>
              {medicines
                .filter((medicine) => medicine.stock_quantity > 0)
                .map((medicine) => (
                  <option key={medicine.id} value={medicine.id}>
                    {medicine.name} (Stock: {medicine.stock_quantity})
                  </option>
                ))}
            </select>
          </label>
          <label>
            Quantity
            <input
              required
              min="1"
              type="number"
              value={form.quantity}
              onChange={(event) => setField("quantity", event.target.value)}
            />
          </label>
          <label>
            Dosage Instructions
            <input
              value={form.dosage_instructions}
              onChange={(event) => setField("dosage_instructions", event.target.value)}
              placeholder="e.g. 1 tablet after food"
            />
          </label>
          <label>
            Notes
            <input value={form.notes} onChange={(event) => setField("notes", event.target.value)} />
          </label>
          <div className="sale-form-actions">
            <button type="submit" disabled={saving}>
              {saving ? "Recording..." : "Record Sale"}
            </button>
          </div>
        </form>
      </article>

      <article className="panel">
        <div className="panel-head">
          <h3>Patient Medicine Records</h3>
        </div>

        <form className="record-search" onSubmit={handleSearch}>
          <input
            type="search"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            placeholder="Search by patient ID, patient name, or medicine"
          />
          <button type="submit">Search</button>
        </form>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Patient ID</th>
                <th>Patient Name</th>
                <th>Medicine</th>
                <th>Qty</th>
                <th>Total</th>
                <th>Dosage</th>
                <th>Sold At</th>
              </tr>
            </thead>
            <tbody>
              {records.length ? (
                records.map((record) => (
                  <tr key={record.id}>
                    <td>{record.patient_id}</td>
                    <td>{record.patient_name || "-"}</td>
                    <td>{record.medicine_name}</td>
                    <td>{record.quantity}</td>
                    <td>{formatCurrency(record.total_amount)}</td>
                    <td>{record.dosage_instructions || "-"}</td>
                    <td>{formatDateTime(record.sold_at)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="muted">
                    No patient medicine records found.
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
    </section>
  );
}

export default PatientSalesPage;
