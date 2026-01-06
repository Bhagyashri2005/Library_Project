import { useEffect, useState } from "react";
import axios from "axios";
import "../styles/settings.css";
import AdminLayout from "../components/AdminLayout";

function SettingsPage() {
  const [username, setUsername] = useState("");
  const [role, setRole] = useState("");
  const [oldPassword, setOldPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    axios
      .get("http://127.0.0.1:8000/admin/profile")
      .then((res) => {
        setUsername(res.data.username);
        setRole(res.data.role);
      })
      .catch(() => {
        setError("Failed to load admin profile");
      });
  }, []);

  const handleUpdate = async () => {
    setMessage("");
    setError("");

    if (!username || !oldPassword || !newPassword) {
      setError("All fields are required");
      return;
    }

    try {
      const res = await axios.put(
        "http://127.0.0.1:8000/admin/update-profile",
        {
          username: username,
          old_password: oldPassword,
          new_password: newPassword,
        }
      );

      setMessage(res.data.message);
      setOldPassword("");
      setNewPassword("");
    } catch (err) {
      setError(err.response?.data?.detail || "Update failed");
    }
  };

  return (
    <AdminLayout>
    <div className="settings-container">
      <h2 className="settings-title">⚙️ Settings</h2>

      <div className="settings-card">
        <div className="settings-profile">
          <div className="settings-avatar">👤</div>
          <p className="settings-role">{role}</p>
        </div>

        <label>Username</label>
        <input
          type="text"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />

        <label>Old Password</label>
        <input
          type="password"
          value={oldPassword}
          onChange={(e) => setOldPassword(e.target.value)}
        />

        <label>New Password</label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />

        <button className="settings-btn" onClick={handleUpdate}>
          Save Changes
        </button>

        {message && <p className="settings-success">{message}</p>}
        {error && <p className="settings-error">{error}</p>}
      </div>
    </div>
    </AdminLayout>
  );
}

export default SettingsPage;
