import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function Logout() {
  const navigate = useNavigate();

  useEffect(() => {
    localStorage.removeItem("admin");
    navigate("/admin/login", { replace: true });
  }, [navigate]);

  return <p>Logging out...</p>;
}
