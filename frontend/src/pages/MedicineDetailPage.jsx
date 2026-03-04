import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { inventoryApi } from "../api/client";
import ErrorState from "../components/ErrorState";
import Loader from "../components/Loader";
import StatusBadge from "../components/StatusBadge";
import { formatCurrency, formatDate, formatDateTime } from "../utils/format";

function MedicineDetailPage() {
  const { medicineId } = useParams();
  const [medicine, setMedicine] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const loadMedicine = useCallback(async () => {
    if (!medicineId) return;
    setLoading(true);
    setError("");
    try {
      const response = await inventoryApi.getMedicine(medicineId);
      setMedicine(response);
    } catch (err) {
      setError(err.message ?? "Unable to load medicine details");
    } finally {
      setLoading(false);
    }
  }, [medicineId]);

  useEffect(() => {
    loadMedicine();
  }, [loadMedicine]);

  async function runStatusAction(status) {
    if (!medicineId) return;
    setBusy(true);
    setError("");
    try {
      const updated = await inventoryApi.markStatus(medicineId, status);
      setMedicine(updated);
    } catch (err) {
      setError(err.message ?? "Unable to update status");
    } finally {
      setBusy(false);
    }
  }

  if (loading) return <Loader label="Loading medicine details..." />;
  if (error && !medicine) return <ErrorState message={error} onRetry={loadMedicine} />;

  return (
    <section className="detail-page">
      <article className="panel">
        <div className="panel-head detail-head">
          <h3>Medicine Details</h3>
          <Link className="tiny link" to="/inventory">
            Back to Inventory
          </Link>
        </div>
        {error ? <ErrorState message={error} /> : null}
        {medicine ? (
          <div className="detail-grid">
            <div>
              <p className="detail-label">Name</p>
              <h4>{medicine.name}</h4>
            </div>
            <div>
              <p className="detail-label">Generic Name</p>
              <h4>{medicine.generic_name || "Not provided"}</h4>
            </div>
            <div>
              <p className="detail-label">Category</p>
              <h4>{medicine.category}</h4>
            </div>
            <div>
              <p className="detail-label">Manufacturer</p>
              <h4>{medicine.manufacturer || "Not provided"}</h4>
            </div>
            <div>
              <p className="detail-label">Batch Number</p>
              <h4>{medicine.batch_number}</h4>
            </div>
            <div>
              <p className="detail-label">Unit Price</p>
              <h4>{formatCurrency(medicine.unit_price)}</h4>
            </div>
            <div>
              <p className="detail-label">Stock</p>
              <h4>{medicine.stock_quantity}</h4>
            </div>
            <div>
              <p className="detail-label">Reorder Level</p>
              <h4>{medicine.reorder_level}</h4>
            </div>
            <div>
              <p className="detail-label">Expiry Date</p>
              <h4>{formatDate(medicine.expiry_date)}</h4>
            </div>
            <div>
              <p className="detail-label">Status</p>
              <h4>
                <StatusBadge status={medicine.status} />
              </h4>
            </div>
            <div>
              <p className="detail-label">Created At</p>
              <h4>{formatDateTime(medicine.created_at)}</h4>
            </div>
            <div>
              <p className="detail-label">Updated At</p>
              <h4>{formatDateTime(medicine.updated_at)}</h4>
            </div>
          </div>
        ) : null}

        <div className="detail-actions">
          <button type="button" disabled={busy} onClick={() => runStatusAction("active")}>
            Mark Active
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => runStatusAction("low_stock")}>
            Mark Low Stock
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => runStatusAction("expired")}>
            Mark Expired
          </button>
          <button type="button" className="ghost" disabled={busy} onClick={() => runStatusAction("out_of_stock")}>
            Mark Out Of Stock
          </button>
        </div>
      </article>
    </section>
  );
}

export default MedicineDetailPage;

