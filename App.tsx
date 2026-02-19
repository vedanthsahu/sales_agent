import React, { useState } from 'react';
import { ChatInterface } from './components/Chat/ChatInterface';
import { LoginPage } from './components/Auth/LoginPage';

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
  };

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center bg-gray-50 text-gray-900 font-sans overflow-hidden">
      {isAuthenticated ? (
        <ChatInterface onLogout={handleLogout} />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
    </div>
  );
};

export default App;