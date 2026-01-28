import React, { useEffect, useState } from "react";
import axios from "axios";
import AdminLayout from "../components/AdminLayout";
import "../styles/timetable.css";

const DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
const ROWS_PER_PAGE = 10;

export default function TimetablePage() {
  const [day, setDay] = useState("Monday");
  const [timetable, setTimetable] = useState([]);
  const [currentPage, setCurrentPage] = useState(1);

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

  // inline add
  const [newEntry, setNewEntry] = useState({
    department: "",
    year: "",
    division: "",
    batch: "",
    subject: "",
    teacher_id: "",
    start_time: "",
    end_time: "",
    type: "Lecture"
  });

  // edit
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState(null);

  // csv
  const [file, setFile] = useState(null);

  // =====================================================
  // LOAD TIMETABLE
  // =====================================================
  const loadTimetable = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/admin/timetable", {
        params: {
          day_of_week: day,
          ...filters
        }
      });
      setTimetable(res.data || []);
      setCurrentPage(1);
    } catch {
      alert("Failed to load timetable");
    }
  };

  // =====================================================
  // LOAD FILTER OPTIONS
  // =====================================================
  const loadFilters = async () => {
    try {
      const res = await axios.get(
        "http://127.0.0.1:8000/admin/timetable/filters",
        { params: filters }
      );
      setFilterOptions(res.data);
    } catch {
      alert("Failed to load filters");
    }
  };

  useEffect(() => {
    loadTimetable();
  }, [day]);

  useEffect(() => {
    loadFilters();
  }, [filters.department, filters.year, filters.division]);

  // =====================================================
  // PAGINATION
  // =====================================================
  const totalPages = Math.ceil(timetable.length / ROWS_PER_PAGE);
  const paginatedData = timetable.slice(
    (currentPage - 1) * ROWS_PER_PAGE,
    currentPage * ROWS_PER_PAGE
  );

  // =====================================================
  // ADD SINGLE ENTRY (FormData ❗)
  // =====================================================
  const handleAddSingle = async (e) => {
    e.preventDefault();

    const fd = new FormData();
    fd.append("department", newEntry.department);
    fd.append("year", newEntry.year);
    fd.append("division", newEntry.division);
    fd.append("subject", newEntry.subject);
    fd.append("teacher_id", newEntry.teacher_id);
    fd.append("day_of_week", day);
    fd.append("start_time", newEntry.start_time);
    fd.append("end_time", newEntry.end_time);
    fd.append("type", newEntry.type);
    if (newEntry.batch) fd.append("batch", newEntry.batch);

    try {
      await axios.post("http://127.0.0.1:8000/admin/timetable/add", fd);
      alert("Timetable entry added");
      loadTimetable();
    } catch (err) {
      alert(err.response?.data?.detail || "Add failed");
    }
  };

  // =====================================================
  // UPDATE ENTRY (FormData ❗)
  // =====================================================
  const handleUpdate = async (e) => {
    e.preventDefault();

    const fd = new FormData();
    Object.entries(editData).forEach(([k, v]) => {
      if (v !== null) fd.append(k, v);
    });

    try {
      await axios.put(
        `http://127.0.0.1:8000/admin/timetable/update/${editData.timetable_id}`,
        fd
      );
      alert("Updated successfully");
      setShowEdit(false);
      loadTimetable();
    } catch (err) {
      alert(err.response?.data?.detail || "Update failed");
    }
  };
  
  // Delete
  const handleDelete = async (id) => {
  if (!window.confirm("Are you sure you want to delete this entry?")) return;

  try {
    await axios.delete(
      `http://127.0.0.1:8000/admin/timetable/delete/${id}`
    );
    alert("Timetable entry deleted");
    loadTimetable();
  } catch (err) {
    alert(err.response?.data?.detail || "Delete failed");
  }
};

// =====================================================
// OPEN EDIT MODAL
// =====================================================
const openEdit = (row) => {
  setEditData({
    ...row
  });
  setShowEdit(true);
};


  // =====================================================
  // CSV UPLOAD
  // =====================================================
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
    } catch {
      alert("CSV upload failed");
    }
  };

  // =====================================================
  // UI
  // =====================================================
  return (
    <AdminLayout>
      <h2>Timetable Management</h2>

      {/* DAYS */}
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

      {/* TABLE */}
      <div className="tt-card">
      <table className="tt-table" >
        <thead>
          <tr>
            <th>Dept</th>
            <th>Year</th>
            <th>Div</th>
            <th>Time</th>
            <th>Subject</th>
            <th>Teacher</th>
            <th>Edit</th>
            <th>Delete</th>
          </tr>
        </thead>
        <tbody>
          {paginatedData.map((t) => (
            <tr key={t.timetable_id}>
              <td>{t.department}</td>
              <td>{t.year}</td>
              <td>{t.division}</td>
              <td>{t.start_time} - {t.end_time}</td>
              <td>{t.subject}</td>
              <td>{t.teacher_id}</td>
              <td>
                <button className="btn " onClick={() => openEdit(t)}>
                  Edit
                </button>
              </td>

              <td>
                <button
                  className="btn danger"
                  onClick={() => handleDelete(t.timetable_id)}
                >
                  Delete
                </button>
              </td>

            </tr>
          ))}
        </tbody>
      </table>

      {/* PAGINATION */}
      {totalPages > 1 && (
        <div className="pagination">
          <button disabled={currentPage === 1}
            onClick={() => setCurrentPage(p => p - 1)}>Prev</button>
          <span>{currentPage} / {totalPages}</span>
          <button disabled={currentPage === totalPages}
            onClick={() => setCurrentPage(p => p + 1)}>Next</button>
        </div>
      )}
      </div>

      {/* INLINE ADD */}
      <div className="add-form">
      <h3>Add Entry</h3>
      <form onSubmit={handleAddSingle}>
        <input placeholder="Dept" onChange={e=>setNewEntry({...newEntry,department:e.target.value})}/>
        <input placeholder="Year" onChange={e=>setNewEntry({...newEntry,year:e.target.value})}/>
        <input placeholder="Division" onChange={e=>setNewEntry({...newEntry,division:e.target.value})}/>
        <input placeholder="Batch (optional)" onChange={e=>setNewEntry({...newEntry,batch:e.target.value})}/>
        <input placeholder="Subject" onChange={e=>setNewEntry({...newEntry,subject:e.target.value})}/>
        <input placeholder="Teacher ID" onChange={e=>setNewEntry({...newEntry,teacher_id:e.target.value})}/>
        <input type="time" onChange={e=>setNewEntry({...newEntry,start_time:e.target.value})}/>
        <input type="time" onChange={e=>setNewEntry({...newEntry,end_time:e.target.value})}/>
        <select onChange={e=>setNewEntry({...newEntry,type:e.target.value})}>
          <option>Lecture</option>
          <option>Practical</option>
        </select>
        <button className="btn">Add</button>
      </form>
      

      {/* CSV */}
      <h3>Upload CSV</h3>
      <form onSubmit={handleUpload}>
        <input type="file" accept=".csv" onChange={e=>setFile(e.target.files[0])}/>
        <button className="btn">Upload</button>
      </form>
      </div>

      {/* EDIT MODAL */}
      {showEdit && (
        <div className="modal">
          <form onSubmit={handleUpdate}>
            <input value={editData.subject} onChange={e=>setEditData({...editData,subject:e.target.value})}/>
            <input value={editData.teacher_id} onChange={e=>setEditData({...editData,teacher_id:e.target.value})}/>
            <input type="time" value={editData.start_time} onChange={e=>setEditData({...editData,start_time:e.target.value})}/>
            <input type="time" value={editData.end_time} onChange={e=>setEditData({...editData,end_time:e.target.value})}/>
            <button>Update</button>
            <button type="button" onClick={()=>setShowEdit(false)}>Cancel</button>
          </form>
        </div>
      )}
    </AdminLayout>
  );
}
