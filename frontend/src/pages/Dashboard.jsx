import React, { useEffect, useState } from "react";
import axios from "axios";
import AdminLayout from "../components/AdminLayout";
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

import "../styles/Dashboard.css";

const COLORS = ["#7b2cbf", "#9d4edd", "#c77dff", "#6a0dad"];

function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [charts, setCharts] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  const [memberPie, setMemberPie] = useState([]);

  const [studentDepartments, setStudentDepartments] = useState([]);
  const [studentYears, setStudentYears] = useState([]);
  const [studentDivisions, setStudentDivisions] = useState([]);
  const [teacherDepartments, setTeacherDepartments] = useState([]);
  const [deptBarData, setDeptBarData] = useState([]);
  const [attendanceLineData, setAttendanceLineData] = useState([]);

  const [memberFilters, setMemberFilters] = useState({
    memberType: "",
    department: "",
    year: "",
    division: "",
  });

  const [lineFilters, setLineFilters] = useState({
    date: new Date().toISOString().split("T")[0], // today
    startHour: 8,
    endHour: 18,
  });


  // ------------------ LOAD PIE ------------------
  const loadMemberChart = async (filters = {}) => {
    try {
      const res = await axios.get(
        "http://127.0.0.1:8000/admin/charts/members",
        { params: filters }
      );
      setMemberPie(res.data?.length ? res.data : [{ name: "No Data", value: 0 }]);
    } catch {
      setMemberPie([{ name: "No Data", value: 0 }]);
    }
  };

  const loadDepartmentBarChart = async (filters = {}) => {
  try {
    const res = await axios.get(
      "http://127.0.0.1:8000/admin/charts/department-wise",
      { params: filters }
    );
    setDeptBarData(res.data);
  } catch (err) {
    console.error("Failed to load bar chart", err);
    setDeptBarData([]);
  }
};

const loadAttendanceTimeline = async (filters = lineFilters) => {
  try {
    const res = await axios.get(
      "http://127.0.0.1:8000/admin/charts/attendance-timeline",
      {
        params: {
          date: filters.date,
          start_hour: filters.startHour,
          end_hour: filters.endHour,
        },
      }
    );
    setAttendanceLineData(res.data);
  } catch (err) {
    console.error("Failed to load attendance timeline", err);
    setAttendanceLineData([]);
  }
};

  // ------------------ APPLY ------------------
  const handleApplyFilters = () => {
    const params = {};

    if (memberFilters.memberType)
      params.member_type = memberFilters.memberType;

    if (memberFilters.department)
      params.department = memberFilters.department;

    if (memberFilters.memberType === "student") {
      if (memberFilters.year) params.year = memberFilters.year;
      if (memberFilters.division) params.division = memberFilters.division;
    }

    loadMemberChart(params);
    loadDepartmentBarChart(params);
  };

  // ------------------ RESET ------------------
  const handleResetFilters = () => {
    setMemberFilters({
      memberType: "",
      department: "",
      year: "",
      division: "",
    });

    setStudentDepartments([]);
    setStudentYears([]);
    setStudentDivisions([]);
    setTeacherDepartments([]);

    loadMemberChart();
    loadDepartmentBarChart();
  };

  

  // ------------------ DASHBOARD DATA ------------------
  useEffect(() => {
    async function fetchData() {
      try {
        const [sRes, cRes] = await Promise.all([
          axios.get("http://127.0.0.1:8000/admin/summary"),
          axios.get("http://127.0.0.1:8000/admin/stats/charts"),
        ]);
        setSummary(sRes.data);
        setCharts(cRes.data);
      } catch {
        setErr("Failed to load dashboard");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  // ------------------ DEFAULT PIE ------------------
  useEffect(() => {
    loadMemberChart();
  }, []);

  useEffect(() => {
  loadDepartmentBarChart();
}, []);

  // ------------------ STUDENT DEPARTMENTS ------------------
  useEffect(() => {
    if (memberFilters.memberType === "student") {
      axios
        .get("http://127.0.0.1:8000/admin/filters/student/departments")
        .then(res => setStudentDepartments(res.data));
    }
  }, [memberFilters.memberType]);

  // ------------------ STUDENT YEARS (ALL LOGIC FIXED) ------------------
  useEffect(() => {
    if (memberFilters.memberType === "student") {
      const params = {};
      if (memberFilters.department)
        params.department = memberFilters.department;

      axios
        .get("http://127.0.0.1:8000/admin/filters/student/years", { params })
        .then(res => setStudentYears(res.data));
    } else {
      setStudentYears([]);
    }
  }, [memberFilters.department, memberFilters.memberType]);

  // ------------------ STUDENT DIVISIONS (ALL LOGIC FIXED) ------------------
  useEffect(() => {
    if (memberFilters.memberType === "student") {
      const params = {};
      if (memberFilters.department)
        params.department = memberFilters.department;
      if (memberFilters.year)
        params.year = memberFilters.year;

      axios
        .get("http://127.0.0.1:8000/admin/filters/student/divisions", { params })
        .then(res => setStudentDivisions(res.data));
    } else {
      setStudentDivisions([]);
    }
  }, [memberFilters.department, memberFilters.year, memberFilters.memberType]);

  // ------------------ TEACHER DEPARTMENTS ------------------
  useEffect(() => {
    if (memberFilters.memberType === "teacher") {
      axios
        .get("http://127.0.0.1:8000/admin/filters/teacher/departments")
        .then(res => setTeacherDepartments(res.data));
    }
  }, [memberFilters.memberType]);

useEffect(() => {
  loadAttendanceTimeline(lineFilters);
}, [lineFilters]);



  if (loading) return <div className="dash-loading">Loading...</div>;
  if (err) return <div className="dash-error">{err}</div>;

  return (
    <AdminLayout>
      <header className="topbar">
        <h1>Admin Dashboard</h1>
      </header>
      {/* <header className="topbar">
        <h1>Admin Dashboard</h1>
        <div className="top-actions">Welcome, Admin</div>
      </header> */}

         <section className="stats-strip">
             <div className="stat-box blue">
               <div className="stat-icon">🎓</div>
               <div className="stat-info">
                 <h2>{summary?.total_students ?? 0}</h2>
                 <p>Total Students</p>
               </div>
             </div>

             <div className="stat-box orange">
               <div className="stat-icon">👩‍🏫</div>
               <div className="stat-info">
                 <h2>{summary?.total_teachers ?? 0}</h2>
                 <p>Total Teachers</p>
               </div>
             </div>

             <div className="stat-box green">
               <div className="stat-icon">👍</div>
               <div className="stat-info">
                 <h2>{summary?.today_entries ?? 0}</h2>
                 <p>Check-in Today</p>
               </div>
             </div>

             <div className="stat-box red">
               <div className="stat-icon">👎</div>
               <div className="stat-info">
                 <h2>{summary?.today_exits ?? 0}</h2>
                 <p>Check-out Today</p>
               </div>
             </div>

             <div className="stat-box purple">
               <div className="stat-icon">⚠️</div>
               <div className="stat-info">
                 <h2>{summary?.skipping_alerts ?? 0}</h2>
                 <p>Skipping Class Alerts</p>
               </div>
             </div>
           </section>



      {/* ------------------ PIE ------------------ */}
      <section className="charts-grid">
        <div className="panel chart-with-filters">
          <h3>Members Distribution</h3>

          <div className="chart-layout">
            <div className="chart-area">
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie
                    data={memberPie}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={90}
                    label
                  >
                    {memberPie.map((_, idx) => (
                      <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-filters">
              <h4>Filter</h4>

              <label>Member Type</label>
              <select
                value={memberFilters.memberType}
                onChange={(e) =>
                  setMemberFilters({
                    memberType: e.target.value,
                    department: "",
                    year: "",
                    division: "",
                  })
                }
              >
                <option value="">All</option>
                <option value="student">Student</option>
                <option value="teacher">Teacher</option>
              </select>

              {memberFilters.memberType && (
                <>
                  <label>Department</label>
                  <select
                    value={memberFilters.department}
                    onChange={(e) =>
                      setMemberFilters({ ...memberFilters, department: e.target.value })
                    }
                  >
                    <option value="">All</option>
                    {memberFilters.memberType === "student" &&
                      studentDepartments.map(dep => (
                        <option key={dep} value={dep}>{dep}</option>
                      ))}
                    {memberFilters.memberType === "teacher" &&
                      teacherDepartments.map(dep => (
                        <option key={dep} value={dep}>{dep}</option>
                      ))}
                  </select>
                </>
              )}

              {memberFilters.memberType === "student" && (
                <>
                  <label>Year</label>
                  <select
                    value={memberFilters.year}
                    onChange={(e) =>
                      setMemberFilters({ ...memberFilters, year: e.target.value })
                    }
                  >
                    <option value="">All</option>
                    {studentYears.map(yr => (
                      <option key={yr} value={yr}>{yr}</option>
                    ))}
                  </select>

                  <label>Division</label>
                  <select
                    value={memberFilters.division}
                    onChange={(e) =>
                      setMemberFilters({ ...memberFilters, division: e.target.value })
                    }
                  >
                    <option value="">All</option>
                    {studentDivisions.map(div => (
                      <option key={div} value={div}>{div}</option>
                    ))}
                  </select>
                </>
              )}

              <div className="filter-actions">
                <button className="apply-filter-btn" onClick={handleApplyFilters}>Apply</button>
                <button className="reset-filter-btn" onClick={handleResetFilters}>Reset</button>
              </div>
            </div>
          </div>
        </div>

        <div className="panel">
             <h3>Entry vs Exit (Today)</h3>
             <ResponsiveContainer width="100%" height={240}>
               
               <BarChart data={deptBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="department" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="students" fill="#7b2cbf" />
                  <Bar dataKey="teachers" fill="#9d4edd" />
                </BarChart>
             </ResponsiveContainer>
           </div>
      </section>

      {/* ================= Attendance Trend (Full Width) ================= */}
      <div className="attendance-trend-container">
        <h3 className="attendance-title">
          Attendance Trend (Today: 8 AM – 6 PM)
        </h3>

        <div className="attendance-filters">
          <div>
            <label>Date</label>
            <input
              type="date"
              value={lineFilters.date}
              onChange={(e) =>
                setLineFilters({ ...lineFilters, date: e.target.value })
              }
            />
          </div>

          <div>
            <label>From</label>
            <select
              value={lineFilters.startHour}
              onChange={(e) =>
                setLineFilters({ ...lineFilters, startHour: Number(e.target.value) })
              }
            >
              {[...Array(24)].map((_, h) => (
                <option key={h} value={h}>
                  {h <= 12 ? `${h} AM` : `${h - 12} PM`}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label>To</label>
            <select
              value={lineFilters.endHour}
              onChange={(e) =>
                setLineFilters({ ...lineFilters, endHour: Number(e.target.value) })
              }
            >
              {[...Array(24)].map((_, h) => (
                <option key={h} value={h}>
                  {h <= 12 ? `${h} AM` : `${h - 12} PM`}
                </option>
              ))}
            </select>
          </div>
        </div>


        <ResponsiveContainer width="100%" height={360}>
          <LineChart data={attendanceLineData}>
            <CartesianGrid strokeDasharray="3 3" />

            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Legend />

            {/* ENTRY */}
            <Line
              type="monotone"
              dataKey="entry"
              stroke="#2ecc71"
              strokeWidth={3}
              dot={{ r: 4 }}
              name="Check-in"
            />

            {/* EXIT */}
            <Line
              type="monotone"
              dataKey="exit"
              stroke="#f1c40f"
              strokeWidth={3}
              dot={{ r: 4 }}
              name="Check-out"
            />

            {/* SKIPPING */}
            <Line
              type="monotone"
              dataKey="skip"
              stroke="#e74c3c"
              strokeWidth={3}
              dot={{ r: 4 }}
              name="Skipping"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>



    </AdminLayout>
  );
}

export default Dashboard;
