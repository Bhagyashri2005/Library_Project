import React, { useState } from "react";
import axios from "axios";
import "../styles/logs.css";

function ManualEntryModal({ onClose, onSaved }) {
  const [form, setForm] = useState({
    user_id: "",
    action: "entry",
  });

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const submitForm = async () => {
    if (!form.user_id) {
      alert("Please enter User ID");
      return;
    }

    try {
      await axios.post(
        "http://127.0.0.1:8000/admin/logs/manual",
        null,
        {
          params: {
            user_id: form.user_id,
            action: form.action,
          },
        }
      );

      onSaved();
      onClose();
    } catch (err) {
      // ✅ THIS IS THE CORRECT PLACE
      alert(err.response?.data?.detail || "Action not allowed");
    }
  };

  return (
    <div className="modal-backdrop">
      <div className="modal-box">
        <h3>Manual Entry / Exit</h3>

        <label>User ID</label>
        <input
          name="user_id"
          value={form.user_id}
          onChange={handleChange}
          placeholder="Enter Student / Teacher ID"
        />

        <label>Action</label>
        <select
          name="action"
          value={form.action}
          onChange={handleChange}
        >
          <option value="entry">Entry</option>
          <option value="exit">Exit</option>
        </select>

        <div className="modal-actions">
          <button className="btn outline" onClick={onClose}>
            Cancel
          </button>
          <button className="btn primary" onClick={submitForm}>
            Submit
          </button>
        </div>
      </div>
    </div>
  );
}

export default ManualEntryModal;



// import React, { useState } from "react";
// import axios from "axios";
// import "../styles/logs.css";

// function ManualEntryModal({ onClose, onSaved }) {
//   const [form, setForm] = useState({
//     user_id: "",
//     role: "student",
//     action: "entry",
//     remarks: "",
//   });

//   const handleChange = (e) => {
//     setForm({ ...form, [e.target.name]: e.target.value });
//   };

//   const submitForm = async () => {
//   try {
//     await axios.post("http://127.0.0.1:8000/admin/logs/manual", null, {
//       params: {
//         user_id: form.user_id,
//         role: form.role,
//         action: form.action,
//         remarks: form.remarks
//       }
//     });

//     onSaved();
//     onClose();
//   } catch (err) {
//     alert("Error adding manual entry");
//   }
// };


//   return (
//     <div className="modal-backdrop">
//       <div className="modal-box">
//         <h3>Manual Entry / Exit</h3>

//         <label>User ID</label>
//         <input
//           name="user_id"
//           value={form.user_id}
//           onChange={handleChange}
//           placeholder="Enter Student/Teacher ID"
//         />

//         <label>Role</label>
//         <select name="role" value={form.role} onChange={handleChange}>
//           <option value="student">Student</option>
//           <option value="teacher">Teacher</option>
//         </select>

//         <label>Action</label>
//         <select name="action" value={form.action} onChange={handleChange}>
//           <option value="entry">Entry</option>
//           <option value="exit">Exit</option>
//         </select>

//         <label>Remarks</label>
//         <input
//           name="remarks"
//           value={form.remarks}
//           onChange={handleChange}
//           placeholder="Optional"
//         />

//         <div className="modal-actions">
//           <button className="btn outline" onClick={onClose}>Cancel</button>
//           <button className="btn primary" onClick={submitForm}>Submit</button>
//         </div>
//       </div>
//     </div>
//   );
// }

// export default ManualEntryModal;
