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
