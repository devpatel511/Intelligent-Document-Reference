import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChatProvider } from '@/app/contexts/ChatContext';
import { ChatPage } from '@/app/pages/ChatPage';
import { SettingsPage } from '@/app/pages/SettingsPage';

export default function App() {
  return (
    <Router>
      <ChatProvider>
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </ChatProvider>
    </Router>
  );
}
