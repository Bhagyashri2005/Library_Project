import { BrowserRouter, Routes, Route } from "react-router-dom";
import AdminLogin from "./pages/AdminLogin";
import Dashboard from "./pages/Dashboard";
import MembersPage from "./pages/MembersPage";
import TimetablePage from "./pages/TimetablePage";
import LogsPage from "./pages/LogsPage";
import Logout from "./pages/Logout";
import SettingsPage from "./pages/SettingsPage";
import AcademicCalendarPage from "./pages/AcademicCalendarPage";
import ScanPage from "./pages/ScanPage";



function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Default page -> Login */}
        <Route path="/" element={<AdminLogin />} />

        {/* Admin login */}
        <Route path="/admin/login" element={<AdminLogin />} />

        {/* Admin Dashboard */}
        <Route path="/admin/dashboard" element={<Dashboard />} />
         <Route path="/admin/members" element={<MembersPage />} />
         <Route path="/admin/timetable" element={<TimetablePage />} />

         <Route path="/admin/academic-calendar" element={ <AcademicCalendarPage />}/>

        <Route path="/admin/logs" element={<LogsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="/logout" element={<Logout />} />
        <Route path="/scan" element={<ScanPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
