import { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "../styles/login.css";

function AdminLogin() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleLogin = async () => {
  setError("");

  try {
    const response = await axios.post("http://127.0.0.1:8000/admin/login", {
      username,
      password,
    });

    if (response.data.status === "success") {
      localStorage.setItem("admin", JSON.stringify(response.data));
      navigate("/admin/dashboard");
    } else {
      setError("Invalid username or password");
    }
  } catch (err) {
    setError("Server Error ❌");
  }
};


  return (
    <div className="login-page">
    <div className="login-container">
      <h2>Admin Login</h2>

      <input
        type="text"
        placeholder="Enter Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />

      <input
        type="password"
        placeholder="Enter Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />

      <button onClick={handleLogin}>Login</button>

      {error && <p className="error">{error}</p>}
    </div>
    </div>
  );
}

export default AdminLogin;
