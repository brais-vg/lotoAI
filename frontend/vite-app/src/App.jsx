import { Routes, Route } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import ChatPage from "./pages/ChatPage";
import UploadPage from "./pages/UploadPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<ChatPage />} />
        <Route path="upload" element={<UploadPage />} />
      </Route>
    </Routes>
  );
}
