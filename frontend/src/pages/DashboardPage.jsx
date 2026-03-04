import { useCallback, useEffect, useMemo, useState } from "react";

import { dashboardApi } from "../api/client";
import ErrorState from "../components/ErrorState";
import Loader from "../components/Loader";
import StatCard from "../components/StatCard";
import { formatCurrency, formatDateTime } from "../utils/format";

function todayIsoDate() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [salesSummary, setSalesSummary] = useState(null);
  const [itemsSold, setItemsSold] = useState(null);
  const [lowStock, setLowStock] = useState(null);
  const [purchaseOrders, setPurchaseOrders] = useState(null);
  const [recentSales, setRecentSales] = useState([]);

  const selectedDate = useMemo(todayIsoDate, []);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [salesSummaryRes, itemsSoldRes, lowStockRes, poRes, recentSalesRes] = await Promise.all([
        dashboardApi.getSalesSummary(selectedDate),
        dashboardApi.getItemsSold(selectedDate),
        dashboardApi.getLowStock(5),
        dashboardApi.getPurchaseOrders(),
        dashboardApi.getRecentSales(8)
      ]);
      setSalesSummary(salesSummaryRes);
      setItemsSold(itemsSoldRes);
      setLowStock(lowStockRes);
      setPurchaseOrders(poRes);
      setRecentSales(recentSalesRes?.sales ?? []);
    } catch (err) {
      setError(err.message ?? "Unable to load dashboard");
    } finally {
      setLoading(false);
    }
  }, [selectedDate]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) return <Loader label="Loading dashboard..." />;
  if (error) return <ErrorState message={error} onRetry={loadDashboard} />;

  return (
    <section className="dashboard">
      <div className="card-grid">
        <StatCard
          title="Today's Sales"
          value={formatCurrency(salesSummary?.total_revenue)}
          hint={`${salesSummary?.transaction_count ?? 0} transactions`}
          accent="accent-emerald"
        />
        <StatCard
          title="Items Sold"
          value={itemsSold?.total_items_sold ?? 0}
          hint={`${selectedDate}`}
          accent="accent-sky"
        />
        <StatCard
          title="Low Stock"
          value={lowStock?.low_stock_count ?? 0}
          hint="Needs replenishment"
          accent="accent-amber"
        />
        <StatCard
          title="Purchase Orders"
          value={purchaseOrders?.total_orders ?? 0}
          hint={`${purchaseOrders?.pending_orders ?? 0} pending`}
          accent="accent-coral"
        />
      </div>

      <div className="split-grid">
        <article className="panel">
          <div className="panel-head">
            <h3>Purchase Order Summary</h3>
          </div>
          <ul className="stats-list">
            <li>
              <span>Pending</span>
              <strong>{purchaseOrders?.pending_orders ?? 0}</strong>
            </li>
            <li>
              <span>Completed</span>
              <strong>{purchaseOrders?.completed_orders ?? 0}</strong>
            </li>
            <li>
              <span>Cancelled</span>
              <strong>{purchaseOrders?.cancelled_orders ?? 0}</strong>
            </li>
            <li>
              <span>Total Value</span>
              <strong>{formatCurrency(purchaseOrders?.total_order_value)}</strong>
            </li>
          </ul>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h3>Low Stock Alerts</h3>
          </div>
          {lowStock?.items?.length ? (
            <ul className="alert-list">
              {lowStock.items.map((item) => (
                <li key={item.id}>
                  <div>
                    <strong>{item.name}</strong>
                    <small>Expiry: {item.expiry_date}</small>
                  </div>
                  <span>{item.stock_quantity} left</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">No low stock medicines right now.</p>
          )}
        </article>
      </div>

      <article className="panel">
        <div className="panel-head">
          <h3>Recent Sales</h3>
        </div>
        {recentSales.length ? (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Medicine</th>
                  <th>Quantity</th>
                  <th>Amount</th>
                  <th>Sold At</th>
                </tr>
              </thead>
              <tbody>
                {recentSales.map((sale) => (
                  <tr key={sale.id}>
                    <td>{sale.medicine_name}</td>
                    <td>{sale.quantity}</td>
                    <td>{formatCurrency(sale.total_amount)}</td>
                    <td>{formatDateTime(sale.sold_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted">No recent sales available.</p>
        )}
      </article>
    </section>
  );
}

export default DashboardPage;
