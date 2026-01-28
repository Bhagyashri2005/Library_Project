import { useEffect, useRef, useState } from "react";
import axios from "axios";
import "../styles/scan.css";

const API_URL = "http://127.0.0.1:8000/scan";

export default function ScanPage() {
  const inputRef = useRef(null);

  const [scanValue, setScanValue] = useState("");
  const [message, setMessage] = useState("");
  const [status, setStatus] = useState(""); // success | error

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = async (e) => {
    if (e.key === "Enter") {
      if (!scanValue.trim()) return;

      try {
        const res = await axios.post(API_URL, {
          user_id: scanValue,
        });

        setMessage(res.data.message);
        setStatus("success");
      } catch (err) {
        setMessage(err.response?.data?.detail || "Scan failed");
        setStatus("error");
      }

      setScanValue("");
      inputRef.current?.focus();
    }
  };

  return (
    <div className="scan-page">
      <h1 className="scan-title">Library Entry Scan</h1>

      <input
        ref={inputRef}
        className="scan-input"
        type="text"
        placeholder="Scan ID Card"
        value={scanValue}
        onChange={(e) => setScanValue(e.target.value)}
        onKeyDown={handleKeyDown}
        autoFocus
      />

      {message && (
        <div className={`scan-message ${status}`}>
          {message}
        </div>
      )}
    </div>
  );
}
