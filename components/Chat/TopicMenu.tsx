import React from 'react';
import { PREDEFINED_TOPICS, Icons } from '../../constants';
import { Topic } from '../../types';

interface TopicMenuProps {
  isOpen: boolean;
  onSelect: (topic: Topic) => void;
  onClose: () => void;
}

export const TopicMenu: React.FC<TopicMenuProps> = ({ isOpen, onSelect, onClose }) => {
  if (!isOpen) return null;

  const renderIcon = (iconName: string) => {
    switch (iconName) {
      case 'cpu': return <Icons.Cpu className="w-5 h-5" />;
      case 'code': return <Icons.Code className="w-5 h-5" />;
      case 'users': return <Icons.Users className="w-5 h-5" />;
      case 'shield': return <Icons.Shield className="w-5 h-5" />;
      default: return <Icons.Sparkles className="w-5 h-5" />;
    }
  };

  return (
    <div className="absolute bottom-full right-0 mb-4 w-72 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-20 animate-fade-in origin-bottom-right">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-100 flex justify-between items-center">
        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Select Domain</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <Icons.X className="w-4 h-4" />
        </button>
      </div>
      <div className="p-2 max-h-80 overflow-y-auto">
        {PREDEFINED_TOPICS.map((topic) => (
          <button
            key={topic.id}
            onClick={() => onSelect(topic)}
            className="w-full text-left p-3 hover:bg-primary-50 rounded-lg transition-colors duration-200 group"
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
    </div>
  );
};
