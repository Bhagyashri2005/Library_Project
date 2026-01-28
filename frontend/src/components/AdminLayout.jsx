import { useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import "../styles/Dashboard.css";

export default function AdminLayout({ children }) {
  const navigate = useNavigate();
  const location = useLocation();  // <-- Detect current route

  useEffect(() => {
    const admin = localStorage.getItem("admin");
    if (!admin) {
      navigate("/admin/login", { replace: true });
    }
  }, [navigate]);

  return (
    <div className="dashboard-root">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="logo">LibPro</div>
          <div className="brand-title">Admin</div>
        </div>

        <nav>
          <ul>
            <li
              onClick={() => navigate("/admin/dashboard")}
              className={location.pathname === "/admin/dashboard" ? "active" : ""}
            >
              Dashboard
            </li>

             <li
              onClick={() => navigate("/admin/logs")}
              className={location.pathname === "/admin/logs" ? "active" : ""}
            >
              Logs
            </li>

            <li
              onClick={() => navigate("/admin/members")}
              className={location.pathname === "/admin/members" ? "active" : ""}
            >
              Members
            </li>
           

            <li
              onClick={() => navigate("/admin/timetable")}
              className={location.pathname === "/admin/timetable" ? "active" : ""}
            >
              Timetable
            </li>

            <li
              onClick={() => navigate("/admin/academic-calendar")}
              className={
                location.pathname === "/admin/academic-calendar" ? "active" : ""
              }
            >
              Academic Calendar
            </li>

            {/* <li
              onClick={() => navigate("/admin/settings")}
              className={location.pathname === "/admin/settings" ? "active" : ""}
            >
              Settings
            </li> */}
            <li onClick={() => navigate("/settings")}>Settings</li>


             <li onClick={() => navigate("/logout")}>
              Logout
            </li>
            
          </ul>
        </nav>
      </aside>

      {/* Main content */}
      <main className="main-area">{children}</main>
    </div>
  );
}
