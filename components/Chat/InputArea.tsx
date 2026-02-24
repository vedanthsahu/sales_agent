import React, { useState, useRef, useEffect } from 'react';
import { Icons } from '../../constants';
import { TopicMenu } from './TopicMenu';
import { FileMenu } from './FileMenu';
import { Domain, Topic, FileMeta } from '../../types';
import { motion, AnimatePresence } from "framer-motion";

interface InputAreaProps {
  onSendMessage: (text: string, file: File | null) => void;
  isLoading: boolean;
  selectedDomain: Domain | null;
  onSelectDomain: (domain: Domain) => void;
  onRequestDomainSelection: () => void;
  availableFiles: FileMeta[];
  selectedFileIds: string[];
  onToggleFileSelection: (fileId: string) => void;
}

export const InputArea: React.FC<InputAreaProps> = ({
  onSendMessage,
  isLoading,
  selectedDomain,
  onSelectDomain,
  onRequestDomainSelection,
  availableFiles,
  selectedFileIds,
  onToggleFileSelection
}) => {
  const [inputText, setInputText] = useState('');
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isFileMenuOpen, setIsFileMenuOpen] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const isDomainMissing = selectedDomain === null;
  const isGeneralDomain = selectedDomain === 'general';
  const isChatDisabled = isDomainMissing;
  const areFileActionsDisabled = isGeneralDomain || isLoading;
  
  // Speech Recognition Setup
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (SpeechRecognition) {
        recognitionRef.current = new SpeechRecognition();
        recognitionRef.current.continuous = false;
        recognitionRef.current.interimResults = false;
        recognitionRef.current.lang = 'en-US';

        recognitionRef.current.onresult = (event: any) => {
          const transcript = event.results[0][0].transcript;
          setInputText((prev) => (prev ? prev + ' ' + transcript : transcript));
          setIsListening(false);
        };

        recognitionRef.current.onerror = (event: any) => {
          console.error('Speech recognition error', event.error);
          setIsListening(false);
        };

        recognitionRef.current.onend = () => {
          setIsListening(false);
        };
      }
    }
  }, []);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [inputText]);

  useEffect(() => {
    if (selectedDomain === 'general' && selectedFile) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  }, [selectedDomain, selectedFile]);

  useEffect(() => {
    if (isDomainMissing || isGeneralDomain) {
      setIsFileMenuOpen(false);
    }
  }, [isDomainMissing, isGeneralDomain]);

  const requireDomain = () => {
    if (isDomainMissing) {
      onRequestDomainSelection();
      return true;
    }
    return false;
  };

  const handleSend = () => {
    if (requireDomain()) return;
    if ((!inputText.trim() && !selectedFile) || isLoading) return;
    onSendMessage(inputText, selectedFile);
    setInputText('');
    setSelectedFile(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTopicSelect = (topic: Topic) => {
    setIsMenuOpen(false);
    onSelectDomain(topic.id);
    if (!inputText.trim()) {
      setInputText(topic.prompt);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
    } else {
      setIsListening(true);
      recognitionRef.current?.start();
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUploadClick = () => {
    if (requireDomain()) return;
    if (areFileActionsDisabled) return;
    fileInputRef.current?.click();
  };

  const handleFileMenuToggle = () => {
    if (requireDomain()) return;
    if (areFileActionsDisabled) return;
    setIsFileMenuOpen(!isFileMenuOpen);
  };

  const inputPlaceholder = isChatDisabled
    ? "Select a domain to start chatting"
    : isLoading
      ? "Processing..."
      : "Type or speak...";

  const selectedFiles = isGeneralDomain
    ? []
    : availableFiles.filter(f => selectedFileIds.includes(f.file_id));

  return (
    <div className="relative w-full max-w-4xl mx-auto p-4 bg-white/80 backdrop-blur-md border-t border-gray-100">
      
      {/* Selected File Chip */}
      {selectedFile && (
        <div className="absolute -top-10 left-4 bg-primary-50 border border-primary-100 text-primary-700 px-3 py-1 rounded-lg text-sm flex items-center gap-2 animate-fade-in shadow-sm">
          <Icons.Paperclip className="w-3.5 h-3.5" />
          <span className="truncate max-w-[200px]">{selectedFile.name}</span>
          <button 
            onClick={() => {
              setSelectedFile(null);
              if (fileInputRef.current) fileInputRef.current.value = '';
            }}
            className="hover:text-primary-900"
          >
            <Icons.X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Selected Files For RAG */}
      {selectedFiles.length > 0 && (
        <div className="absolute -top-10 right-4 flex flex-wrap gap-2">
          {selectedFiles.map((file) => (
            <div key={file.file_id} className="bg-gray-50 border border-gray-200 text-gray-700 px-3 py-1 rounded-lg text-xs flex items-center gap-2 animate-fade-in shadow-sm">
              <Icons.Paperclip className="w-3.5 h-3.5" />
              <span className="truncate max-w-[160px]">{file.filename}</span>
              <button
                onClick={() => onToggleFileSelection(file.file_id)}
                className="hover:text-gray-900"
              >
                <Icons.X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Container for input and controls */}
      <div className="relative flex items-end gap-2 bg-white border border-gray-200 rounded-2xl shadow-sm p-2 focus-within:ring-2 focus-within:ring-primary-500/20 focus-within:border-primary-500 transition-all duration-200">
        
        {/* Left Actions: File Upload & Menu */}
        <div className="flex items-center gap-1 pb-1 pl-1">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileChange} 
            disabled={areFileActionsDisabled}
            className="hidden" 
          />
          <button
            onClick={handleUploadClick}
            className={`p-2 rounded-xl transition-colors duration-200 ${
              isDomainMissing || areFileActionsDisabled
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-400 hover:text-primary-600 hover:bg-primary-50'
            }`}
            title={isGeneralDomain ? "Uploads require a specific domain" : "Upload File"}
            type="button"
          >
            <Icons.Plus className="w-5 h-5" />
          </button>

          <div className="relative">
            <button
              onClick={handleFileMenuToggle}
              aria-disabled={isDomainMissing || areFileActionsDisabled}
              className={`p-2 rounded-xl transition-colors duration-200 ${
                isFileMenuOpen
                  ? 'bg-primary-100 text-primary-600'
                  : isDomainMissing || areFileActionsDisabled
                    ? 'text-gray-300 cursor-not-allowed'
                    : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
              title={isGeneralDomain ? "General uses all documents" : "Select Files"}
              type="button"
              disabled={false}
            >
              <Icons.Paperclip className="w-5 h-5" />
            </button>
            <FileMenu
              isOpen={isFileMenuOpen}
              files={availableFiles}
              selectedFileIds={selectedFileIds}
              onToggle={onToggleFileSelection}
              onClose={() => setIsFileMenuOpen(false)}
            />
          </div>

          <div className="relative">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className={`p-2 rounded-xl transition-colors duration-200 ${
                isMenuOpen ? 'bg-primary-100 text-primary-600' : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
              }`}
              title="Select Domain"
              type="button"
            >
              <Icons.Menu className="w-5 h-5" />
            </button>
            <TopicMenu 
              isOpen={isMenuOpen} 
              onSelect={handleTopicSelect} 
              onClose={() => setIsMenuOpen(false)} 
            />
          </div>
        </div>

        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (requireDomain()) {
              textareaRef.current?.blur();
            }
          }}
          onClick={() => {
            if (requireDomain()) {
              textareaRef.current?.blur();
            }
          }}
          placeholder={inputPlaceholder}
          disabled={isLoading}
          readOnly={isDomainMissing}
          rows={1}
          className="flex-1 max-h-32 min-h-[44px] py-3 px-1 bg-transparent border-none outline-none text-gray-800 placeholder-gray-400 resize-none overflow-y-auto"
        />

        {/* Right Action Buttons */}
        <div className="flex items-center gap-1 pb-1 pr-1">
          
          {/* Voice Input */}
          <motion.button
  onClick={() => {
    if (requireDomain()) return;
    toggleListening();
  }}
  animate={isListening ? {
    boxShadow: [
      "0 0 0px rgba(239,68,68,0.4)",
      "0 0 20px rgba(239,68,68,0.6)",
      "0 0 0px rgba(239,68,68,0.4)"
    ]
  } : {}}
  transition={{ duration: 1.5, repeat: Infinity }}
  className={`p-2 rounded-xl transition-all duration-200 ${
    isListening
      ? 'bg-red-50 text-red-500'
      : isDomainMissing
        ? 'text-gray-300 cursor-not-allowed'
        : 'text-gray-400 hover:text-gray-600 hover:bg-gray-100'
  }`}
>
  <Icons.Mic className="w-5 h-5" />
</motion.button>


          {/* Send Button */}
          <motion.button
  onClick={handleSend}
  disabled={(!inputText.trim() && !selectedFile) || isLoading}
  whileTap={{ scale: 0.9 }}
  whileHover={{ scale: 1.05 }}
  animate={{
    backgroundColor:
      (inputText.trim() || selectedFile) && !isLoading && !isDomainMissing
        ? "#171717"
        : "#f3f4f6"
  }}
  className={`p-2 rounded-xl transition-all duration-200 flex items-center justify-center shadow-md`}
>
  <AnimatePresence mode="wait">
    {isLoading ? (
      <motion.div
        key="loading"
        initial={{ opacity: 0, rotate: -90 }}
        animate={{ opacity: 1, rotate: 360 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.6, repeat: Infinity, ease: "linear" }}
      >
        <Icons.Cpu className="w-5 h-5 text-white" />
      </motion.div>
    ) : (
      <motion.div
        key="send"
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0 }}
      >
        <Icons.Send className="w-5 h-5 text-white" />
      </motion.div>
    )}
  </AnimatePresence>
</motion.button>

        </div>
      </div>
      
      <div className="text-center text-xs text-gray-400 mt-2">
        Files will be processed by the RAG RPA . AI responses may vary.
      </div>
    </div>
  );
};
