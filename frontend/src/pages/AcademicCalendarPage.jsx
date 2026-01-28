import { useEffect, useState } from "react";
import axios from "axios";
import AdminLayout from "../components/AdminLayout";
import "../styles/academicCalendar.css";

const API_URL = "http://localhost:8000/academic-calendar";
const PAGE_SIZE = 10;

export default function AcademicCalendarPage() {
  const [events, setEvents] = useState([]);
  const [filteredEvents, setFilteredEvents] = useState([]);
  const [csvFile, setCsvFile] = useState(null);

  // single add form
  const [form, setForm] = useState({
    date: "",
    event_type: "Holiday",
    description: "",
  });

  // edit modal (LIKE TIMETABLE)
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState({
    event_id: null,
    date: "",
    event_type: "",
    description: "",
  });

  // filters
  const [filterDate, setFilterDate] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterDescription, setFilterDescription] = useState("");

  // pagination
  const [currentPage, setCurrentPage] = useState(1);

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    const res = await axios.get(API_URL);
    setEvents(res.data);
    setFilteredEvents(res.data);
    setCurrentPage(1);
  };

  /* ================= ADD SINGLE EVENT ================= */
  const handleAdd = async () => {
    if (!form.date || !form.event_type || !form.description) {
      alert("All fields are required");
      return;
    }

    try {
      await axios.post(API_URL, form);
      setForm({ date: "", event_type: "Holiday", description: "" });
      fetchEvents();
    } catch {
      alert("Failed to add event");
    }
  };

  /* ================= EDIT (LIKE TIMETABLE) ================= */
  const openEdit = (row) => {
    setEditData({ ...row });
    setShowEdit(true);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();

    try {
      await axios.put(`${API_URL}/${editData.event_id}`, {
        date: editData.date,
        event_type: editData.event_type,
        description: editData.description,
      });
      alert("Event updated successfully");
      setShowEdit(false);
      fetchEvents();
    } catch {
      alert("Update failed");
    }
  };

  /* ================= DELETE ================= */
  const handleDelete = async (id) => {
    if (!window.confirm("Delete this event?")) return;
    await axios.delete(`${API_URL}/${id}`);
    fetchEvents();
  };

  /* ================= FILTER ================= */
  const applyFilters = () => {
    let data = [...events];

    if (filterDate) data = data.filter(e => e.date === filterDate);
    if (filterType) data = data.filter(e => e.event_type === filterType);
    if (filterDescription)
      data = data.filter(e =>
        e.description.toLowerCase().includes(filterDescription.toLowerCase())
      );

    setFilteredEvents(data);
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilterDate("");
    setFilterType("");
    setFilterDescription("");
    setFilteredEvents(events);
    setCurrentPage(1);
  };

  /* ================= CSV UPLOAD ================= */
  const handleUpload = async () => {
    if (!csvFile) return alert("Please select a CSV file");

    const text = await csvFile.text();
    const rows = text.split("\n").slice(1);

    const eventsToUpload = rows
      .map((row) => {
        const [date, event_type, description] = row.split(",");
        if (!date || !event_type || !description) return null;
        return {
          date: date.trim(),
          event_type: event_type.trim(),
          description: description.trim(),
        };
      })
      .filter(Boolean);

    if (eventsToUpload.length === 0)
      return alert("No valid rows found");

    await axios.post(`${API_URL}/bulk`, eventsToUpload);
    alert("CSV uploaded successfully");
    fetchEvents();
  };

  /* ================= PAGINATION ================= */
  const totalPages = Math.ceil(filteredEvents.length / PAGE_SIZE);
  const startIndex = (currentPage - 1) * PAGE_SIZE;
  const paginatedEvents = filteredEvents.slice(
    startIndex,
    startIndex + PAGE_SIZE
  );

  return (
    <AdminLayout>
      <div className="calendar-root">
        <h2 className="page-title">Academic Calendar Management</h2>

        {/* FILTER + TABLE */}
        <div className="calendar-card">
          <h3 className="section-title">Academic Events</h3>

          <div className="calendar-filter-bar">
            <input type="date" value={filterDate} onChange={(e)=>setFilterDate(e.target.value)} />

            <select value={filterType} onChange={(e)=>setFilterType(e.target.value)}>
              <option value="">All Types</option>
              <option value="Holiday">Holiday</option>
              <option value="Event">Event</option>
              <option value="Exam">Exam</option>
            </select>

            <input
              type="text"
              placeholder="Search description"
              value={filterDescription}
              onChange={(e)=>setFilterDescription(e.target.value)}
            />

            <button className="primary-btn" onClick={applyFilters}>Apply</button>
            <button className="clear-btn" onClick={clearFilters}>Clear</button>
          </div>

          <table className="calendar-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {paginatedEvents.length === 0 ? (
                <tr><td colSpan="4" className="empty-text">No records found</td></tr>
              ) : (
                paginatedEvents.map((e) => (
                  <tr key={e.event_id}>
                    <td>{e.date}</td>
                    <td>{e.event_type}</td>
                    <td>{e.description}</td>
                    <td>
                      <button className="edit-btn" onClick={()=>openEdit(e)}>Edit</button>
                      <button className="delete-btn" onClick={()=>handleDelete(e.event_id)}>Delete</button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div className="pagination">
              <button disabled={currentPage===1} onClick={()=>setCurrentPage(p=>p-1)}>Previous</button>
              <span>Page {currentPage} of {totalPages}</span>
              <button disabled={currentPage===totalPages} onClick={()=>setCurrentPage(p=>p+1)}>Next</button>
            </div>
          )}
        </div>
      </div>

      {/* SINGLE ADD */}
      <div className="calendar-upload-bar">
        <input type="date" value={form.date} onChange={(e)=>setForm({...form,date:e.target.value})} />
        <select value={form.event_type} onChange={(e)=>setForm({...form,event_type:e.target.value})}>
          <option value="Holiday">Holiday</option>
          <option value="Event">Event</option>
          <option value="Exam">Exam</option>
        </select>
        <input value={form.description} placeholder="Event description" onChange={(e)=>setForm({...form,description:e.target.value})} />
        <button className="primary-btn" onClick={handleAdd}>Add</button>
      </div>

      {/* CSV UPLOAD */}
      <div className="calendar-upload-bar">
        <input type="file" accept=".csv" onChange={(e)=>setCsvFile(e.target.files[0])} />
        <button className="primary-btn" onClick={handleUpload}>Upload CSV</button>
      </div>

      {/* EDIT MODAL */}
      {showEdit && (
        <div className="modal">
          <div className="modal-box">
            <h3>Edit Academic Event</h3>
            <form onSubmit={handleUpdate}>
              <input type="date" value={editData.date} onChange={(e)=>setEditData({...editData,date:e.target.value})} />
              <select value={editData.event_type} onChange={(e)=>setEditData({...editData,event_type:e.target.value})}>
                <option value="Holiday">Holiday</option>
                <option value="Event">Event</option>
                <option value="Exam">Exam</option>
              </select>
              <input value={editData.description} onChange={(e)=>setEditData({...editData,description:e.target.value})} />
              <div className="modal-actions">
                <button type="submit" className="btn primary">Update</button>
                <button type="button" className="btn" onClick={()=>setShowEdit(false)}>Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
