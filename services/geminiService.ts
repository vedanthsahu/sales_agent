import { Domain, ChatResponse } from "../types";

/**
 * Handles the chat interaction via backend only.
 */
export const handleChatResponse = async (
  domain: Domain,
  sessionId: string,
  history: { role: string; parts: { text: string }[] }[],
  currentMessage: string,
  fileIds: string[]
): Promise<ChatResponse> => {
  const BACKEND_URL = (import.meta as any)?.env?.VITE_BACKEND_URL
    ? `${(import.meta as any).env.VITE_BACKEND_URL}/chat`
    : 'http://localhost:8000/chat';
  const payload = {
    domain,
    session_id: sessionId,
    message: currentMessage,
    file_ids: fileIds || [], // keep explicit
    history: history,
  };

  console.group("CHAT REQUEST (frontend)");
  console.log("URL:", BACKEND_URL);
  console.log("Payload:", payload);
  console.log("Payload JSON:", JSON.stringify(payload, null, 2));
  console.groupEnd();

  const response = await fetch(BACKEND_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || 'Backend unavailable or returned error');
  }

  const data = await response.json();

  if (!data?.answer) {
    throw new Error('Backend response missing answer');
  }

  return data as ChatResponse;
};
