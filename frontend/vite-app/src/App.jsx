import { Routes, Route, Navigate } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import ChatPage from "./pages/ChatPage";
import UploadPage from "./pages/UploadPage";
import SearchPage from "./pages/SearchPage";

export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<ChatPage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
