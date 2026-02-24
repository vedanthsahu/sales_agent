import React, { useState } from 'react';
import { ChatInterface } from './components/Chat/ChatInterface';
import { LoginPage } from './components/Auth/LoginPage';
import { endSession, startSession } from './services/backendService';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleLogin = async (email: string) => {
    try {
      const session = await startSession(email);
      setSessionId(session.session_id);
      setIsAuthenticated(true);
    } catch (error) {
      console.error("Failed to start session", error);
    }
  };

  const handleLogout = async () => {
    try {
      if (sessionId) {
        await endSession(sessionId);
      }
    } catch (error) {
      console.error("Failed to end session", error);
    } finally {
      setIsAuthenticated(false);
      setSessionId(null);
    }
  };

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center bg-gray-50 text-gray-900 font-sans overflow-hidden">
      {isAuthenticated ? (
        sessionId ? (
          <ChatInterface onLogout={handleLogout} sessionId={sessionId} />
        ) : null
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </div>
  );
};

export default App;
