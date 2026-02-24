import { Domain, FileMeta } from '../types';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

export const uploadFile = async (
  file: File,
  domain: Domain
): Promise<{ file_id: string; processing_status: string; domain: string }> => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('domain', domain);

  const response = await fetch(`${BACKEND_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Upload failed');
  }

  return response.json();
};

export const listFiles = async (domain?: Domain): Promise<FileMeta[]> => {
  const url = new URL(`${BACKEND_URL}/files`);
  if (domain) {
    url.searchParams.set('domain', domain);
  }

  const response = await fetch(url.toString(), {
    method: 'GET',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to fetch files');
  }

  return response.json();
};

export const startSession = async (userId: string): Promise<{ session_id: string; user_id: string }> => {
  const response = await fetch(`${BACKEND_URL}/session/start`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to start session');
  }

  return response.json();
};

export const endSession = async (sessionId: string): Promise<{ status: string }> => {
  const response = await fetch(`${BACKEND_URL}/session/end`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to end session');
  }

  return response.json();
};

export const getChatHistory = async (
  sessionId: string,
  domain: Domain
): Promise<{ session_id: string; domain: Domain; messages: { role: string; content: string; timestamp?: number }[] }> => {
  const url = new URL(`${BACKEND_URL}/history`);
  url.searchParams.set('session_id', sessionId);
  url.searchParams.set('domain', domain);

  const response = await fetch(url.toString(), {
    method: 'GET',
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Failed to fetch history');
  }

  return response.json();
};
