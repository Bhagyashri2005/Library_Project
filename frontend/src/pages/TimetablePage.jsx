import React, { useEffect, useState } from "react";
import axios from "axios";
import AdminLayout from "../components/AdminLayout";
import "../styles/timetable.css";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];

export default function TimetablePage() {
  const [day, setDay] = useState("Monday");
  const [timetable, setTimetable] = useState([]);

  // filters
  const [filters, setFilters] = useState({
    department: "",
    year: "",
    division: "",
    batch: ""
  });

  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    years: [],
    divisions: [],
    batches: []
  });

  // edit modal
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState(null);

  // csv
  const [file, setFile] = useState(null);

  // ================= LOAD TIMETABLE =================
  const loadTimetable = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/timetable", {
        params: {
          day_of_week: day,
          ...filters
        }
      });
      setTimetable(res.data || []);
    } catch {
      alert("Failed to load timetable");
    }
  };

  // ================= LOAD FILTER OPTIONS =================
  const loadFilterOptions = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/timetable/filters", {
        params: {
          department: filters.department,
          year: filters.year,
          division: filters.division
        }
      });
      setFilterOptions(res.data);
    } catch {
      alert("Failed to load filter options");
    }
  };

  useEffect(() => {
    loadTimetable();
  }, [day]);

  useEffect(() => {
    loadFilterOptions();
  }, [filters.department, filters.year, filters.division]);

  // ================= EDIT =================
  const openEdit = (row) => {
    setEditData({ ...row });
    setShowEdit(true);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();

    try {
      await axios.put(
        `http://127.0.0.1:8000/admin/timetable/update/${editData.id}`,
        editData
      );
      alert("Timetable updated successfully");
      setShowEdit(false);
      loadTimetable();
    } catch (err) {
      alert(err.response?.data?.detail || "Update failed");
    }
  };

  // ================= CSV UPLOAD =================
  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return alert("Select CSV file");

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/admin/timetable/upload",
        fd
      );
      alert(`Added: ${res.data.added}, Skipped: ${res.data.skipped}`);
      loadTimetable();
      setFile(null);
    } catch {
      alert("Upload failed");
    }
  };

  return (
    <AdminLayout>
      <div className="tt-page">
        <h2>Timetable Management</h2>

        {/* DAY SELECTOR */}
        <div className="tt-days">
          {DAYS.map((d) => (
            <button
              key={d}
              className={day === d ? "active" : ""}
              onClick={() => setDay(d)}
            >
              {d}
            </button>
          ))}
        </div>

        {/* FILTERS */}
        <div className="tt-filters">
          <select
            value={filters.department}
            onChange={(e) =>
              setFilters({ department: e.target.value, year: "", division: "", batch: "" })
            }
          >
            <option value="">All Departments</option>
            {filterOptions.departments.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>

          <select
            value={filters.year}
            onChange={(e) =>
              setFilters({ ...filters, year: e.target.value, division: "", batch: "" })
            }
          >
            <option value="">All Years</option>
            {filterOptions.years.map((y) => (
              <option key={y}>{y}</option>
            ))}
          </select>

          <select
            value={filters.division}
            onChange={(e) =>
              setFilters({ ...filters, division: e.target.value, batch: "" })
            }
          >
            <option value="">All Divisions</option>
            {filterOptions.divisions.map((d) => (
              <option key={d}>{d}</option>
            ))}
          </select>

          <select
            value={filters.batch}
            onChange={(e) =>
              setFilters({ ...filters, batch: e.target.value })
            }
          >
            <option value="">All Batches</option>
            {filterOptions.batches.map((b) => (
              <option key={b}>{b}</option>
            ))}
          </select>

          <button className="btn" onClick={loadTimetable}>
            Apply
          </button>
        </div>

        {/* TABLE */}
        <div className="tt-table">
          <h3>Timetable Entries</h3>
          <table>
            <thead>
              <tr>
                <th>Dept</th>
                <th>Year</th>
                <th>Div</th>
                <th>Day</th>
                <th>Start</th>
                <th>End</th>
                <th>Subject</th>
                <th>Teacher ID</th>
                <th>Edit</th>
              </tr>
            </thead>

            <tbody>
              {timetable.length === 0 ? (
                <tr>
                  <td colSpan="9" className="center">No records found</td>
                </tr>
              ) : (
                timetable.map((t) => (
                  <tr key={t.id}>
                    <td>{t.department}</td>
                    <td>{t.year}</td>
                    <td>{t.division}</td>
                    <td>{t.day_of_week}</td>
                    <td>{t.start_time}</td>
                    <td>{t.end_time}</td>
                    <td>{t.subject}</td>
                    <td>{t.teacher_id}</td>
                    <td>
                      <button className="btn small" onClick={() => openEdit(t)}>
                        Edit
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* CSV UPLOAD */}
        <div className="upload-section">
          <h3>Upload Timetable CSV</h3>
          <form onSubmit={handleUpload}>
            <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} />
            <button className="btn">Upload</button>
          </form>
        </div>

        {/* EDIT MODAL */}
        {showEdit && (
          <div className="modal">
            <div className="modal-box">
              <h3>Edit Timetable</h3>

              <form onSubmit={handleUpdate}>
                <input value={editData.subject} onChange={(e)=>setEditData({...editData,subject:e.target.value})} />
                <input value={editData.teacher_id} onChange={(e)=>setEditData({...editData,teacher_id:e.target.value})} />
                <input value={editData.start_time} onChange={(e)=>setEditData({...editData,start_time:e.target.value})} />
                <input value={editData.end_time} onChange={(e)=>setEditData({...editData,end_time:e.target.value})} />

                <div className="modal-actions">
                  <button type="submit" className="btn primary">Update</button>
                  <button type="button" className="btn" onClick={()=>setShowEdit(false)}>Cancel</button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </AdminLayout>
  );
}


// import React, { useState, useEffect } from "react";
// import axios from "axios";
// import AdminLayout from "../components/AdminLayout";
// import "../styles/timetable.css";

// export default function TimetablePage() {
//   const [role, setRole] = useState("");
//   const [filters, setFilters] = useState({ department: "", year: "", division: "", teacher_id: "" });
//   const [timetable, setTimetable] = useState([]);
//   const [form, setForm] = useState({
//     department: "",
//     year: "",
//     division: "",
//     day_of_week: "",
//     start_time: "",
//     end_time: "",
//     subject: "",
//     teacher_id: "",
//   });
//   const [file, setFile] = useState(null);

//   const loadTimetable = async () => {
//     const res = await axios.get("http://127.0.0.1:8000/admin/timetable", {
//       params: { role, ...filters },
//     });
//     setTimetable(res.data);
//   };

//   useEffect(() => {
//     if (role) loadTimetable();
//   }, [role, filters]);

//   const handleAdd = async (e) => {
//     e.preventDefault();
//     const fd = new FormData();
//     Object.entries(form).forEach(([k, v]) => fd.append(k, v));
//     fd.append("role", role);
//     await axios.post("http://127.0.0.1:8000/admin/timetable/add", fd);
//     alert("Lecture added!");
//     loadTimetable();
//   };

//   const handleUpload = async (e) => {
//     e.preventDefault();
//     const fd = new FormData();
//     fd.append("file", file);
//     const res = await axios.post("http://127.0.0.1:8000/admin/timetable/upload", fd);
//     alert(`Uploaded ${res.data.added} entries`);
//     loadTimetable();
//   };

//   return (
//     <AdminLayout>
//       <div className="timetable-page">
//         <h2>Timetable Management</h2>

//         {/* Select Role */}
//         <div className="role-selector">
//           <label>Select Role:</label>
//           <select value={role} onChange={(e) => setRole(e.target.value)}>
//             <option value="">-- Select --</option>
//             <option value="student">Student</option>
//             <option value="teacher">Teacher</option>
//           </select>
//         </div>

//         {/* Filters for Student */}
//         {role === "student" && (
//           <div className="filter-group">
//             <select onChange={(e) => setFilters({ ...filters, department: e.target.value })}>
//               <option value="">Department</option>
//               <option value="Computer">Computer</option>
//               <option value="IT">IT</option>
//             </select>
//             <select onChange={(e) => setFilters({ ...filters, year: e.target.value })}>
//               <option value="">Year</option>
//               <option value="FE">FE</option>
//               <option value="SE">SE</option>
//               <option value="TE">TE</option>
//               <option value="BE">BE</option>
//             </select>
//             <select onChange={(e) => setFilters({ ...filters, division: e.target.value })}>
//               <option value="">Division</option>
//               <option value="A">A</option>
//               <option value="B">B</option>
//             </select>
//           </div>
//         )}

//         {/* Filters for Teacher */}
//         {role === "teacher" && (
//           <div className="filter-group">
//             <input
//               placeholder="Enter Teacher ID (e.g., T001)"
//               onChange={(e) => setFilters({ ...filters, teacher_id: e.target.value })}
//             />
//           </div>
//         )}

//         {/* Add Lecture Form */}
//         {role && (
//           <form className="timetable-form" onSubmit={handleAdd}>
//             {role === "student" && (
//               <>
//                 <input placeholder="Department" onChange={(e) => setForm({ ...form, department: e.target.value })} required />
//                 <input placeholder="Year" onChange={(e) => setForm({ ...form, year: e.target.value })} required />
//                 <input placeholder="Division" onChange={(e) => setForm({ ...form, division: e.target.value })} required />
//               </>
//             )}
//             <select onChange={(e) => setForm({ ...form, day_of_week: e.target.value })} required>
//               <option value="">Day</option>
//               <option>Monday</option><option>Tuesday</option><option>Wednesday</option>
//               <option>Thursday</option><option>Friday</option><option>Saturday</option>
//             </select>
//             <input type="time" onChange={(e) => setForm({ ...form, start_time: e.target.value })} required />
//             <input type="time" onChange={(e) => setForm({ ...form, end_time: e.target.value })} required />
//             <input placeholder="Subject" onChange={(e) => setForm({ ...form, subject: e.target.value })} required />
//             <input placeholder="Teacher ID" onChange={(e) => setForm({ ...form, teacher_id: e.target.value })} required />
//             <button className="btn primary" type="submit">Add Lecture</button>
//           </form>
//         )}

//         {/* Upload CSV */}
//         <form className="upload-form" onSubmit={handleUpload}>
//           <label>Upload CSV:</label>
//           <input type="file" accept=".csv" onChange={(e) => setFile(e.target.files[0])} required />
//           <button className="btn">Upload</button>
//         </form>

//         {/* Display Timetable */}
//         <div className="timetable-list">
//           <h3>Timetable Entries</h3>
//           <table>
//             <thead>
//               <tr>
//                 <th>Dept</th><th>Year</th><th>Div</th><th>Day</th>
//                 <th>Start</th><th>End</th><th>Subject</th><th>Teacher ID</th>
//               </tr>
//             </thead>
//             <tbody>
//               {timetable.length === 0 ? (
//                 <tr><td colSpan="8" className="center">No records found</td></tr>
//               ) : (
//                 timetable.map((t, i) => (
//                   <tr key={i}>
//                     <td>{t.department}</td>
//                     <td>{t.year}</td>
//                     <td>{t.division}</td>
//                     <td>{t.day_of_week}</td>
//                     <td>{t.start_time}</td>
//                     <td>{t.end_time}</td>
//                     <td>{t.subject}</td>
//                     <td>{t.teacher_id}</td>
//                   </tr>
//                 ))
//               )}
//             </tbody>
//           </table>
//         </div>
//       </div>
//     </AdminLayout>
//   );
// }
