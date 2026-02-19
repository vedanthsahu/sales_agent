export interface Message {
  id: string;
  role: 'user' | 'model';
  text: string;
  isTyping?: boolean;
}

export interface ChatState {
  messages: Message[];
  isLoading: boolean;
  followUpSuggestions: string[];
}

export type Domain = 'rpa' | 'it' | 'hr' | 'security';

export interface Topic {
  id: Domain;
  label: string;
  description: string;
  prompt: string;
  icon: 'cpu' | 'users' | 'code' | 'shield'; // Mapping to icon names
}

export interface FileMeta {
  file_id: string;
  filename: string;
  created_at?: string;
  processing_status?: string;
  domain?: Domain;
}

export interface Source {
  file_id?: string | null;
  chunk_id?: string | null;
  chunk_index?: number | null;
  domain?: Domain | string | null;
  score?: number;
  text_preview?: string;
}

export interface ChatResponse {
  answer: string;
  follow_up_questions: string[];
  sources: Source[];
  confidence_score: number;
  latency_ms: number;
}

export enum LoadingState {
  IDLE = 'IDLE',
  STREAMING_RESPONSE = 'STREAMING_RESPONSE',
  GENERATING_SUGGESTIONS = 'GENERATING_SUGGESTIONS',
}
