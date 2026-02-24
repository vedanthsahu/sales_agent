import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PREDEFINED_TOPICS, Icons } from '../../constants';
import { Topic } from '../../types';

interface DomainModalProps {
  isOpen: boolean;
  onSelect: (topic: Topic) => void;
  onClose: () => void;
}

export const DomainModal: React.FC<DomainModalProps> = ({ isOpen, onSelect, onClose }) => {
  if (!isOpen) return null;

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case 'cpu': return <Icons.Cpu className="w-5 h-5" />;
      case 'code': return <Icons.Code className="w-5 h-5" />;
      case 'users': return <Icons.Users className="w-5 h-5" />;
      case 'shield': return <Icons.Shield className="w-5 h-5" />;
      case 'sparkles': return <Icons.Sparkles className="w-5 h-5" />;
      default: return <Icons.Sparkles className="w-5 h-5" />;
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <motion.div
          className="w-full max-w-md mx-4 bg-white rounded-2xl shadow-2xl border border-gray-100 overflow-hidden"
          initial={{ y: 20, opacity: 0, scale: 0.98 }}
          animate={{ y: 0, opacity: 1, scale: 1 }}
          exit={{ y: 10, opacity: 0, scale: 0.98 }}
          transition={{ type: 'spring', stiffness: 260, damping: 22 }}
        >
          <div className="bg-gray-50 px-5 py-4 border-b border-gray-100 flex justify-between items-center">
            <div>
              <h3 className="text-sm font-bold text-gray-800">Select a Domain</h3>
              <p className="text-xs text-gray-500 mt-1">Choose the right context before you continue.</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <Icons.X className="w-4 h-4" />
            </button>
          </div>
          <div className="p-3 max-h-[60vh] overflow-y-auto">
            {PREDEFINED_TOPICS.map((topic) => (
              <button
                key={topic.id}
                onClick={() => onSelect(topic)}
                className="w-full text-left p-3 hover:bg-primary-50 rounded-xl transition-colors duration-200 group"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 text-primary-500 group-hover:text-primary-600">
                    {renderIcon(topic.icon)}
                  </div>
                  <div>
                    <div className="font-semibold text-gray-800 text-sm">{topic.label}</div>
                    <div className="text-xs text-gray-500 mt-0.5">{topic.description}</div>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
