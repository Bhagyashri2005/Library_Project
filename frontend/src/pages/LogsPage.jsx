import React, { useEffect, useState } from "react";
import axios from "axios";
import ManualEntryModal from "../components/ManualEntryModal";
import "../styles/logs.css";
import AdminLayout from "../components/AdminLayout";


function LogsPage() {

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    q: "",
    role: "",
    action: "",
    department: "",
    dateFrom: "",
    dateTo: "",
  });
const [departments, setDepartments] = useState([]);
const [years, setYears] = useState([]);
const [divisions, setDivisions] = useState([]);
const [batches, setBatches] = useState([]);

  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [totalPages, setTotalPages] = useState(1);

  const [showModal, setShowModal] = useState(false);

  const fetchLogs = async (p = 1) => {
  setLoading(true);
  try {
    const res = await axios.get("http://127.0.0.1:8000/admin/logs", {
      params: {
        page: p,
        page_size: pageSize,
        user_id: filters.q,
        role: filters.role,
        department: filters.department,
        year: filters.year,
        division: filters.division,
        batch: filters.batch,
        action: filters.action,
        dateFrom: filters.dateFrom,
        dateTo: filters.dateTo,
      },
    });

    // 🔁 map backend response → UI expected structure
    const mappedLogs = (res.data.data || []).map((log) => ({
      log_id: log.log_id,
      user_id: log.user_id,
      name: log.name,
      role: log.role,
      department: log.department,
      action: log.action,
      timestamp: new Date(log.scan_time).toLocaleString(),

      // derive remarks for UI
      status:
        log.status === "SKIP"
          ? `${log.matched_subject || "Class"} Skipped`
          : "Normal",
    }));

    setLogs(mappedLogs);
    setTotalPages(res.data.total_pages || 1);
    setPage(p);
  } catch (err) {
    console.error("Error fetching logs:", err);
  }
  setLoading(false);
};


  useEffect(() => {
    fetchLogs(1);
  }, []);

  const handleFilterChange = (e) => {
    setFilters({ ...filters, [e.target.name]: e.target.value });
  };

  const clearFilters = () => {
    setFilters({
      q: "",
      role: "",
      action: "",
      department: "",
      dateFrom: "",
      dateTo: "",
    });
    fetchLogs(1);
  };

  const fetchDepartments = async () => {
  try {
    const res = await axios.get("http://127.0.0.1:8000/admin/logs/departments");
    setDepartments(res.data || []);
  } catch (err) {
    console.error("Failed to load departments");
  }
};
useEffect(() => {
  fetchLogs(1);
  fetchDepartments();
}, []);

useEffect(() => {
  const fetchDepartments = async () => {
    const res = await axios.get(
      "http://127.0.0.1:8000/admin/logs/departments/by-role",
      { params: { role: filters.role } }
    );
    setDepartments(res.data || []);
  };

  fetchDepartments();
}, [filters.role]);

useEffect(() => {
  axios
    .get("http://127.0.0.1:8000/admin/logs/students/meta")
    .then((res) => {
      setYears(res.data.years || []);
      setDivisions(res.data.divisions || []);
      setBatches(res.data.batches || []);
    });
}, []);


const exportLogs = async () => {
  try {
    const res = await axios.get(
      "http://127.0.0.1:8000/admin/logs/export",
      {
        params: {
          user_id: filters.q,
          department: filters.department,
          action: filters.action,
          dateFrom: filters.dateFrom,
          dateTo: filters.dateTo,
        },
        responseType: "blob",
      }
    );

    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "logs_report.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (err) {
    console.error("Export failed", err);
  }
};



  return (
    <AdminLayout>
    <div className="logs-root">

      <div className="logs-header">
        <h2>Logs</h2>
        <button className="btn primary" onClick={() => setShowModal(true)}>
          + Manual Entry/Exit
        </button>
      </div>

      {/* Filter Bar */}
      <div className="logs-filters">
        <input
          name="q"
          placeholder="Search user ID, name, remarks..."
          value={filters.q}
          onChange={handleFilterChange}
        />

        <select name="role" value={filters.role} onChange={handleFilterChange}>
          <option value="">Role</option>
          <option value="student">Student</option>
          <option value="teacher">Teacher</option>
        </select>

        <select name="action" value={filters.action} onChange={handleFilterChange}>
          <option value="">Action</option>
          <option value="entry">Entry</option>
          <option value="exit">Exit</option>
        </select>

        <select
          name="department"
          value={filters.department}
          onChange={handleFilterChange}
        >
          <option value="">Department</option>
          {departments.map((d) => (
            <option key={d} value={d}>{d}</option>
          ))}
        </select>
        
        {filters.role === "student" && (
          <>
            <select name="year" onChange={handleFilterChange}>
              <option value="">Year</option>
              {years.map(y => <option key={y} value={y}>{y}</option>)}
            </select>

            <select name="division" onChange={handleFilterChange}>
              <option value="">Division</option>
              {divisions.map(d => <option key={d} value={d}>{d}</option>)}
            </select>

            <select name="batch" onChange={handleFilterChange}>
              <option value="">Batch</option>
              {batches.map(b => <option key={b} value={b}>{b}</option>)}
            </select>
          </>
        )}


        <input
          name="dateFrom"
          type="date"
          value={filters.dateFrom}
          onChange={handleFilterChange}
        />

        <input
          name="dateTo"
          type="date"
          value={filters.dateTo}
          onChange={handleFilterChange}
        />

        <button className="btn" onClick={() => fetchLogs(1)}>Apply</button>
        <button className="btn outline" onClick={clearFilters}>Clear</button>
        <button className="btn outline" onClick={exportLogs}>Export</button>

      </div>

      {/* Logs Table */}
      <div className="logs-card">
        {loading ? (
          <p className="center">Loading logs...</p>
        ) : (
          <>
            <table className="logs-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>User ID</th>
                  <th>Name</th>
                  <th>Role</th>
                  <th>Dept</th>
                  <th>Action</th>
                  <th>Status</th>
                  <th>Time</th>
                </tr>
              </thead>

              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="center">No logs found</td>
                  </tr>
                ) : (
                  logs.map((log, i) => (
                    <tr key={log.log_id}>
                      <td>{(page - 1) * pageSize + (i + 1)}</td>
                      <td>{log.user_id}</td>
                      <td>{log.name || "-"}</td>
                      <td>{log.role}</td>
                      <td>{log.department || "-"}</td>
                      <td>{log.action}</td>
                      <td>{log.status}</td>
                      <td>{log.timestamp}</td>
                      
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination */}
            <div className="logs-pagination">
              <button disabled={page === 1} onClick={() => fetchLogs(1)}>First</button>
              <button disabled={page === 1} onClick={() => fetchLogs(page - 1)}>Prev</button>

              <span>Page {page} of {totalPages}</span>

              <button disabled={page === totalPages} onClick={() => fetchLogs(page + 1)}>Next</button>
              <button disabled={page === totalPages} onClick={() => fetchLogs(totalPages)}>Last</button>
            </div>
          </>
        )}
      </div>

      {showModal && (
        <ManualEntryModal
          onClose={() => setShowModal(false)}
          onSaved={() => fetchLogs(page)}
        />
      )}
    </div>
    </AdminLayout>
  );
}

export default LogsPage;
