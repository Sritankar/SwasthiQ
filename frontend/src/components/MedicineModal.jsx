import { useEffect, useState } from "react";

function toFormState(medicine) {
  if (!medicine) {
    return {
      name: "",
      generic_name: "",
      category: "",
      manufacturer: "",
      batch_number: "",
      unit_price: "",
      stock_quantity: "",
      reorder_level: "",
      expiry_date: "",
      is_active: true
    };
  }

  return {
    name: medicine.name ?? "",
    generic_name: medicine.generic_name ?? "",
    category: medicine.category ?? "",
    manufacturer: medicine.manufacturer ?? "",
    batch_number: medicine.batch_number ?? "",
    unit_price: medicine.unit_price ?? "",
    stock_quantity: medicine.stock_quantity ?? "",
    reorder_level: medicine.reorder_level ?? "",
    expiry_date: medicine.expiry_date ?? "",
    is_active: medicine.is_active ?? true
  };
}

function MedicineModal({ open, mode, medicine, onClose, onSave }) {
  const [form, setForm] = useState(toFormState(medicine));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (open) {
      setForm(toFormState(medicine));
      setError("");
      setSaving(false);
    }
  }, [medicine, open]);

  if (!open) return null;

  function setField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");

    const payload = {
      name: form.name.trim(),
      generic_name: form.generic_name.trim() || null,
      category: form.category.trim(),
      manufacturer: form.manufacturer.trim() || null,
      batch_number: form.batch_number.trim(),
      unit_price: Number(form.unit_price),
      stock_quantity: Number(form.stock_quantity),
      reorder_level: Number(form.reorder_level),
      expiry_date: form.expiry_date,
      is_active: form.is_active
    };

    try {
      await onSave(payload);
      onClose();
    } catch (submitError) {
      setError(submitError.message ?? "Unable to save medicine");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose} role="presentation">
      <div className="modal-shell" onClick={(event) => event.stopPropagation()} role="dialog" aria-modal="true">
        <div className="modal-head">
          <h3>{mode === "edit" ? "Update Medicine" : "Add Medicine"}</h3>
          <button type="button" onClick={onClose} aria-label="Close modal">
            X
          </button>
        </div>

        <form className="modal-form" onSubmit={handleSubmit}>
          <label>
            Name
            <input required value={form.name} onChange={(event) => setField("name", event.target.value)} />
          </label>
          <label>
            Generic Name
            <input value={form.generic_name} onChange={(event) => setField("generic_name", event.target.value)} />
          </label>
          <label>
            Category
            <input required value={form.category} onChange={(event) => setField("category", event.target.value)} />
          </label>
          <label>
            Manufacturer
            <input value={form.manufacturer} onChange={(event) => setField("manufacturer", event.target.value)} />
          </label>
          <label>
            Batch Number
            <input required value={form.batch_number} onChange={(event) => setField("batch_number", event.target.value)} />
          </label>
          <label>
            Unit Price
            <input
              required
              min="0.01"
              step="0.01"
              type="number"
              value={form.unit_price}
              onChange={(event) => setField("unit_price", event.target.value)}
            />
          </label>
          <label>
            Stock Quantity
            <input
              required
              min="0"
              type="number"
              value={form.stock_quantity}
              onChange={(event) => setField("stock_quantity", event.target.value)}
            />
          </label>
          <label>
            Reorder Level
            <input
              required
              min="0"
              type="number"
              value={form.reorder_level}
              onChange={(event) => setField("reorder_level", event.target.value)}
            />
          </label>
          <label>
            Expiry Date
            <input
              required
              type="date"
              value={form.expiry_date}
              onChange={(event) => setField("expiry_date", event.target.value)}
            />
          </label>
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(event) => setField("is_active", event.target.checked)}
            />
            Visible in inventory
          </label>

          {error ? <p className="field-error">{error}</p> : null}

          <div className="modal-actions">
            <button type="button" className="ghost" onClick={onClose} disabled={saving}>
              Cancel
            </button>
            <button type="submit" disabled={saving}>
              {saving ? "Saving..." : mode === "edit" ? "Update" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default MedicineModal;
