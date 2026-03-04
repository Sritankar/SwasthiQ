import { NavLink, Route, Routes } from "react-router-dom";

import DashboardPage from "./pages/DashboardPage";
import InventoryPage from "./pages/InventoryPage";
import MedicineDetailPage from "./pages/MedicineDetailPage";
import PatientSalesPage from "./pages/PatientSalesPage";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/inventory", label: "Inventory" },
  { to: "/patient-sales", label: "Patient Sales" }
];

function App() {
  return (
    <div className="app-shell">
      <aside className="side-panel">
        <div className="brand-block">
          <p className="brand-kicker">SwasthiQ EMR</p>
          <h1>Pharmacy Module</h1>
        </div>
        <nav className="menu">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "menu-item active" : "menu-item")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="content">
        <header className="page-head">
          <h2>Pharmacy Operations</h2>
          <p>Real-time sales and inventory controls</p>
        </header>

        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/inventory" element={<InventoryPage />} />
          <Route path="/inventory/:medicineId" element={<MedicineDetailPage />} />
          <Route path="/patient-sales" element={<PatientSalesPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
