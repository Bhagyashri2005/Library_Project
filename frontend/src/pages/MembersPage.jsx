import React, { useEffect, useState } from "react";
import axios from "axios";
import AdminLayout from "../components/AdminLayout";
import "../styles/members.css";

export default function MembersPage() {
  const [role, setRole] = useState("");
  const [members, setMembers] = useState([]);
  const [file, setFile] = useState(null);

  // pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // filters (selected values)
  const [filters, setFilters] = useState({
    department: "",
    year: "",
    division: "",
    batch: ""
  });

  // filter dropdown options (from DB)
  const [filterOptions, setFilterOptions] = useState({
    departments: [],
    years: [],
    divisions: [],
    batches: []
  });

  // add form
  const [form, setForm] = useState({
    member_id: "",
    name: "",
    department: "",
    year: "",
    division: "",
    batch: "",
    email: "",
    contact_no: "",
    designation: ""
  });

  // edit
  const [showEdit, setShowEdit] = useState(false);
  const [editForm, setEditForm] = useState(null);

  // ================= LOAD MEMBERS =================
  const loadMembers = async (r, p = 1) => {
    if (!r) return;

    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/admin/members/${r}`,
        {
          params: {
            page: p,
            page_size: 10,
            ...filters
          }
        }
      );

      setMembers(res.data.data || []);
      setTotalPages(res.data.total_pages || 1);
      setPage(p);
    } catch {
      alert("Failed to load members");
    }
  };

  // ================= LOAD FILTER OPTIONS =================
  const loadFilterOptions = async (r) => {
    if (!r) return;

    try {
      const res = await axios.get(
        `http://127.0.0.1:8000/admin/members/filters/${r}`
      );
      setFilterOptions(res.data);
    } catch {
      alert("Failed to load filter options");
    }
  };

  // ================= ADD MEMBER =================
  const handleAdd = async (e) => {
    e.preventDefault();


    if (!role) {
      alert("Please select role");
      return;
    }

    // ---- Frontend Validation ----
    if (!form.member_id.trim()) {
      alert("ID is required");
      return;
    }

    if (!form.name.trim()) {
      alert("Name is required");
      return;
    }

    if (!form.department.trim()) {
      alert("Department is required");
      return;
    }

    if (!/^\S+@\S+\.\S+$/.test(form.email)) {
      alert("Invalid email format");
      return;
    }

    if (!/^\d{10}$/.test(form.contact_no)) {
      alert("Contact number must be 10 digits");
      return;
    }

    if (role === "student") {
      if (!form.year || !form.division || !form.batch) {
        alert("Year, Division and Batch are required for students");
        return;
      }
    }

    if (role === "teacher" && !form.designation) {
      alert("Designation is required for teachers");
      return;
    }


    const fd = new FormData();
    Object.entries(form).forEach(([k, v]) => fd.append(k, v));
    fd.append("role", role);

    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/members/add",
        fd
      );

      alert(`${role === "student" ? "Student" : "Teacher"} added successfully`);
      loadMembers(role, 1);

      setForm({
        member_id: "",
        name: "",
        department: "",
        year: "",
        division: "",
        batch: "",
        email: "",
        contact_no: "",
        designation: ""
      });


    } catch (err) {
      alert(err.response?.data?.detail || "Add failed");
    }
  };

  // ================= EDIT =================
  const openEdit = (m) => {
    setEditForm({
      member_id: m.student_id || m.teacher_id,
      name: m.name,
      department: m.department,
      year: m.year || "",
      division: m.division || "",
      batch: m.batch || "",
      email: m.email,
      contact_no: m.contact_no,
      designation: m.designation || ""
    });
    setShowEdit(true);
  };

  const handleUpdate = async () => {
    const fd = new FormData();
    Object.entries(editForm).forEach(([k, v]) => fd.append(k, v));
    fd.append("role", role);

    try {
      await axios.put(
        "http://127.0.0.1:8000/admin/members/update",
        fd
      );
      alert("Updated successfully");
      setShowEdit(false);
      loadMembers(role, page);
    } catch (err) {
      alert(err.response?.data?.detail || "Update failed");
    }
  };

  // ================= CSV UPLOAD =================
  const handleUpload = async (e) => {
    e.preventDefault();

    if (!role) {
      alert("Please select role");
      return;
    }

    if (!file) {
      alert("Please select CSV file");
      return;
    }

    const fd = new FormData();
    fd.append("role", role);
    fd.append("file", file);

    try {
      const res = await axios.post(
        "http://127.0.0.1:8000/admin/members/upload",
        fd
      );

      alert(
        `Upload completed\n\nAdded: ${res.data.added}\nSkipped: ${res.data.skipped}`
      );

      loadMembers(role, 1);
      setFile(null);

    } catch (err) {
      alert(err.response?.data?.detail || "Upload failed");
    }
  };

  return (
    <AdminLayout>
      <div className="members-page">
        <h2>Members Management</h2>

        {/* ROLE SELECTOR */}
        <div className="role-selector">
          <label>Select Role:</label>
          <select
            value={role}
            onChange={(e) => {
              const r = e.target.value;
              setRole(r);
              setPage(1);
              setFilters({ department: "", year: "", division: "", batch: "" });
              loadFilterOptions(r);
              loadMembers(r, 1);
            }}
          >
            <option value="">-- Select --</option>
            <option value="student">Student</option>
            <option value="teacher">Teacher</option>
          </select>
        </div>

        {role && (
          <>
            {/* FILTER BAR */}
            <div className="members-filters">
              <select
                value={filters.department}
                onChange={(e) =>
                  setFilters({ ...filters, department: e.target.value })
                }
              >
                <option value="">All Departments</option>
                {filterOptions.departments?.map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>

              {role === "student" && (
                <>
                  <select
                    value={filters.year}
                    onChange={(e) =>
                      setFilters({ ...filters, year: e.target.value })
                    }
                  >
                    <option value="">All Years</option>
                    {filterOptions.years?.map((y) => (
                      <option key={y} value={y}>{y}</option>
                    ))}
                  </select>

                  <select
                    value={filters.division}
                    onChange={(e) =>
                      setFilters({ ...filters, division: e.target.value })
                    }
                  >
                    <option value="">All Divisions</option>
                    {filterOptions.divisions?.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>

                  <select
                    value={filters.batch}
                    onChange={(e) =>
                      setFilters({ ...filters, batch: e.target.value })
                    }
                  >
                    <option value="">All Batches</option>
                    {filterOptions.batches?.map((b) => (
                      <option key={b} value={b}>{b}</option>
                    ))}
                  </select>
                </>
              )}

              <button
                className="btn"
                onClick={() => loadMembers(role, 1)}
              >
                Apply
              </button>
            </div>

            {/* MEMBERS TABLE */}
            <div className="members-list">
              <h3>All {role === "student" ? "Students" : "Teachers"}</h3>

              <table>
                <thead>
                  {role === "student" ? (
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Department</th>
                      <th>Year</th>
                      <th>Division</th>
                      <th>Batch</th>
                      <th>Email</th>
                      <th>Contact</th>
                      <th>Action</th>
                    </tr>
                  ) : (
                    <tr>
                      <th>ID</th>
                      <th>Name</th>
                      <th>Department</th>
                      <th>Email</th>
                      <th>Contact</th>
                      <th>Designation</th>
                      <th>Action</th>
                    </tr>
                  )}
                </thead>

                <tbody>
                  {members.length === 0 ? (
                    <tr>
                      <td colSpan="8" className="center">
                        No records found
                      </td>
                    </tr>
                  ) : (
                    members.map((m, i) => (
                      <tr key={i}>
                        <td>{m.student_id || m.teacher_id}</td>
                        <td>{m.name}</td>
                        <td>{m.department}</td>
                        {role === "student" ? (
                          <>
                            <td>{m.year}</td>
                            <td>{m.division}</td>
                            <td>{m.batch}</td>
                            <td>{m.email}</td>
                            <td>{m.contact_no}</td>
                          </>
                        ) : (
                          <>
                            <td>{m.email}</td>
                            <td>{m.contact_no}</td>
                            <td>{m.designation}</td>
                          </>
                        )}
                        <td><button className="btn outline" onClick={() => openEdit(m)}>Edit</button></td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>

              {/* PAGINATION */}
              <div className="pagination">
                <button
                  disabled={page === 1}
                  onClick={() => loadMembers(role, page - 1)}
                >
                  Prev
                </button>

                <span>Page {page} of {totalPages}</span>

                <button
                  disabled={page === totalPages}
                  onClick={() => loadMembers(role, page + 1)}
                >
                  Next
                </button>
              </div>
            </div>

        {/* EDIT MODAL */}
        {showEdit && (
          <div className="modal-backdrop">
            <div className="modal-box">
              <h3>Edit {role}</h3>

              <input value={editForm.member_id} disabled />
              <input value={editForm.name}
                onChange={(e)=>setEditForm({...editForm,name:e.target.value})} />
              <input value={editForm.department}
                onChange={(e)=>setEditForm({...editForm,department:e.target.value})} />
              <input value={editForm.email}
                onChange={(e)=>setEditForm({...editForm,email:e.target.value})} />
              <input value={editForm.contact_no}
                onChange={(e)=>setEditForm({...editForm,contact_no:e.target.value})} />
                <input value={editForm.year}
                onChange={(e)=>setEditForm({...editForm,year:e.target.value})} />
                <input value={editForm.division}
                onChange={(e)=>setEditForm({...editForm,division:e.target.value})} />
                <input value={editForm.batch}
                onChange={(e)=>setEditForm({...editForm,batch:e.target.value})} />

              {role==="teacher" && (
                <input value={editForm.designation}
                  onChange={(e)=>setEditForm({...editForm,designation:e.target.value})}/>
              )}

              <div className="modal-actions">
                <button className="btn outline" onClick={()=>setShowEdit(false)}>
                  Cancel
                </button>
                <button className="btn primary" onClick={handleUpdate}>
                  Update
                </button>
              </div>
            </div>
          </div>
        )}

            {/* ADD MEMBER */}
            <div className="member-form">
              <h3>Add New {role === "student" ? "Student" : "Teacher"}</h3>

              <form onSubmit={handleAdd}>
                <input
                  placeholder={role === "student" ? "Student ID" : "Teacher ID"}
                  value={form.member_id}
                  onChange={(e) =>
                    setForm({ ...form, member_id: e.target.value })
                  }
                  required
                />

                <input
                  placeholder="Name"
                  value={form.name}
                  onChange={(e) =>
                    setForm({ ...form, name: e.target.value })
                  }
                  required
                />

                <input
                  placeholder="Department"
                  value={form.department}
                  onChange={(e) =>
                    setForm({ ...form, department: e.target.value })
                  }
                  required
                />

                {role === "student" && (
                  <>
                    <input
                      placeholder="Year"
                      value={form.year}
                      onChange={(e) =>
                        setForm({ ...form, year: e.target.value })
                      }
                      required
                    />
                    <input
                      placeholder="Division"
                      value={form.division}
                      onChange={(e) =>
                        setForm({ ...form, division: e.target.value })
                      }
                      required
                    />
                    <input
                      placeholder="Batch"
                      value={form.batch}
                      onChange={(e) =>
                        setForm({ ...form, batch: e.target.value })
                      }
                      required
                    />
                  </>
                )}

                <input
                  placeholder="Email"
                  value={form.email}
                  onChange={(e) =>
                    setForm({ ...form, email: e.target.value })
                  }
                  required
                />

                <input
                  placeholder="Contact No"
                  value={form.contact_no}
                  onChange={(e) =>
                    setForm({ ...form, contact_no: e.target.value })
                  }
                  required
                />

                {role === "teacher" && (
                  <input
                    placeholder="Designation"
                    value={form.designation}
                    onChange={(e) =>
                      setForm({ ...form, designation: e.target.value })
                    }
                    required
                  />
                )}

                <button type="submit" className="btn primary">
                  Add
                </button>
              </form>
            </div>

            {/* CSV UPLOAD */}
            <div className="upload-section">
              <h3>Upload CSV File</h3>
              <form onSubmit={handleUpload}>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setFile(e.target.files[0])}
                  required
                />
                <button type="submit" className="btn">
                  Upload
                </button>
              </form>
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
}
