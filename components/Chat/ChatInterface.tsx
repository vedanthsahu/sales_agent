import React, { useState, useRef, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { Domain, Message, LoadingState, FileMeta } from '../../types';
import { handleChatResponse } from '../../services/geminiService';
import { listFiles, uploadFile } from '../../services/backendService';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';
import { SuggestionChips } from './SuggestionChips';
import { Icons, PREDEFINED_TOPICS } from '../../constants';
import { motion, AnimatePresence } from "framer-motion";

interface ChatInterfaceProps {
  onLogout: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({ onLogout }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'model',
      text: "Hello! I'm your Sales Assistant. I can help you with RPA, IT Infrastructure, HR Solutions, and more. How can I assist you today?"
    }
  ]);
  const [loadingState, setLoadingState] = useState<LoadingState>(LoadingState.IDLE);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [selectedDomain, setSelectedDomain] = useState<Domain | null>(null);
  const [availableFiles, setAvailableFiles] = useState<FileMeta[]>([]);
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logic
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, suggestions]);

  const selectedDomainLabel = selectedDomain
    ? PREDEFINED_TOPICS.find((topic) => topic.id === selectedDomain)?.label ?? selectedDomain.toUpperCase()
    : null;

  const handleDomainSelect = (domain: Domain) => {
    setSelectedDomain(domain);
    setSuggestions([]);
    setSelectedFileIds([]);
    refreshFiles(domain);
  };

  const refreshFiles = async (domain: Domain) => {
    try {
      const files = await listFiles(domain);
      setAvailableFiles(files);
    } catch (error) {
      console.error("Failed to load files", error);
    }
  };

  const toggleFileSelection = (fileId: string) => {
    setSelectedFileIds((prev) => {
      if (prev.includes(fileId)) {
        return prev.filter((id) => id !== fileId);
      }
      if (prev.length >= 10) {
        console.warn("Maximum of 10 files can be selected for RAG.");
        return prev;
      }
      return [...prev, fileId];
    });
  };

  const handleSendMessage = async (text: string, file: File | null = null) => {
    if (!selectedDomain) return;
    const messageId = uuidv4();
    let displayMessage = text;
    if (file) {
        displayMessage = text ? `${text} \n[Attached: ${file.name}]` : `[Attached: ${file.name}]`;
    }

    // 1. Add User Message
    const userMsg: Message = { id: messageId, role: 'user', text: displayMessage };
    setMessages(prev => [...prev, userMsg]);
    setSuggestions([]); // Clear previous suggestions
    setLoadingState(LoadingState.STREAMING_RESPONSE);

    // 2. Prepare History for API
    const history = messages.map(m => ({
      role: m.role,
      parts: [{ text: m.text }]
    }));

    // 3. Add Placeholder for Model Response
    const modelMsgId = uuidv4();
    const modelMsgPlaceholder: Message = { id: modelMsgId, role: 'model', text: '', isTyping: true };
    setMessages(prev => [...prev, modelMsgPlaceholder]);

    let effectiveFileIds = [...selectedFileIds];

    try {
      // Upload file if attached
      if (file) {
        const uploadResult = await uploadFile(file, selectedDomain);
        if (uploadResult?.file_id) {
          if (!effectiveFileIds.includes(uploadResult.file_id)) {
            if (effectiveFileIds.length >= 10) {
              console.warn("Maximum of 10 files can be used for RAG. New upload not added.");
            } else {
              effectiveFileIds = [...effectiveFileIds, uploadResult.file_id];
            }
          }
          setSelectedFileIds(effectiveFileIds);
          await refreshFiles(selectedDomain);
        }
      }

      // 4. Backend Response (single source of truth)
      const result = await handleChatResponse(
        selectedDomain,
        history,
        text || (file ? `Analyze file: ${file.name}` : ''),
        effectiveFileIds
      );

      setMessages(prev => prev.map(msg => 
        msg.id === modelMsgId ? { ...msg, text: result.answer, isTyping: false } : msg
      ));

      setSuggestions(result.follow_up_questions || []);

    } catch (error) {
      console.error("Chat Error", error);
      setMessages(prev => prev.map(msg => 
        msg.id === modelMsgId ? { ...msg, text: "I'm sorry, I encountered an error connecting to the service. Please try again.", isTyping: false } : msg
      ));
    } finally {
      setLoadingState(LoadingState.IDLE);
    }
  };

  return (
    <div className="flex flex-col h-full w-full bg-white shadow-2xl overflow-hidden md:h-screen">
      
      {/* Header */}
      <div className="bg-white border-b border-gray-100 p-4 flex items-center justify-between z-10 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-tr from-primary-600 to-primary-400 rounded-xl flex items-center justify-center text-white shadow-lg shadow-primary-500/30">
            <Icons.Sparkles className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-lg text-gray-900 tracking-tight">Sales Assist AI</h1>
              {selectedDomainLabel && (
                <span className="text-[10px] uppercase tracking-wide bg-primary-50 text-primary-700 border border-primary-100 px-2 py-0.5 rounded-full font-semibold">
                  Domain: {selectedDomainLabel}
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500 font-medium">Powered by Vedanth RAG</p>
          </div>
        </div>
        
        {/* Logout Button */}
        <button 
            onClick={onLogout}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
        >
            <span className="hidden sm:inline">Logout</span>
            <Icons.LogOut className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Area */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 md:p-6 bg-[#f8fafc] scroll-smooth"
      >
        {/* Adjusted container to use min-h-full instead of h-full to fix scrolling issues */}
        <div className="w-full min-h-full flex flex-col justify-end px-4 md:px-8 lg:px-12">

             
            <AnimatePresence initial={false}>
  {messages.map((msg) => (
    <motion.div key={msg.id} layout>
      <MessageBubble message={msg} />
    </motion.div>
  ))}
</AnimatePresence>

            
            {/* Suggestion Chips */}
            {suggestions.length > 0 && loadingState === LoadingState.IDLE && (
            <div className="ml-11 md:ml-14 mb-6">
                <p className="text-xs text-gray-400 mb-2 font-medium uppercase tracking-wide">Suggested Actions</p>
                <SuggestionChips 
                suggestions={suggestions} 
                onSelect={(txt) => handleSendMessage(txt, null)} 
                disabled={loadingState !== LoadingState.IDLE || !selectedDomain}
                />
            </div>
            )}
            
            <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="z-10 bg-white">
        <InputArea 
          onSendMessage={handleSendMessage} 
          isLoading={loadingState !== LoadingState.IDLE} 
          selectedDomain={selectedDomain}
          onSelectDomain={handleDomainSelect}
          availableFiles={availableFiles}
          selectedFileIds={selectedFileIds}
          onToggleFileSelection={toggleFileSelection}
        />
      </div>
    </div>
  );
};
