const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? (import.meta.env.DEV ? "http://localhost:8000/api" : "/api");

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {})
    },
    ...options
  });

  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const message = payload?.detail ?? payload?.message ?? "Request failed";
    throw new Error(message);
  }

  return payload?.data;
}

function withQuery(basePath, params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") return;
    query.set(key, value);
  });
  const queryString = query.toString();
  return queryString ? `${basePath}?${queryString}` : basePath;
}

export const dashboardApi = {
  getSalesSummary(date) {
    return request(withQuery("/dashboard/sales-summary", { target_date: date }));
  },
  getItemsSold(date) {
    return request(withQuery("/dashboard/items-sold", { target_date: date }));
  },
  getLowStock(limit = 10) {
    return request(withQuery("/dashboard/low-stock", { limit }));
  },
  getPurchaseOrders() {
    return request("/dashboard/purchase-orders");
  },
  getRecentSales(limit = 10) {
    return request(withQuery("/dashboard/recent-sales", { limit }));
  }
};

export const inventoryApi = {
  getSummary() {
    return request("/inventory/summary");
  },
  listMedicines(params) {
    return request(withQuery("/inventory/medicines", params));
  },
  getCategories() {
    return request("/inventory/categories");
  },
  getMedicine(medicineId) {
    return request(`/inventory/medicines/${medicineId}`);
  },
  addMedicine(payload) {
    return request("/inventory/medicines", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  updateMedicine(medicineId, payload) {
    return request(`/inventory/medicines/${medicineId}`, {
      method: "PUT",
      body: JSON.stringify(payload)
    });
  },
  markStatus(medicineId, status) {
    return request(`/inventory/medicines/${medicineId}/status`, {
      method: "PATCH",
      body: JSON.stringify({ status })
    });
  }
};

export const patientSalesApi = {
  createSale(payload) {
    return request("/patient-sales", {
      method: "POST",
      body: JSON.stringify(payload)
    });
  },
  listRecords(params) {
    return request(withQuery("/patient-sales", params));
  },
  listPatientRecords(patientId, limit = 25) {
    return request(withQuery(`/patient-sales/patients/${patientId}/records`, { limit }));
  }
};
