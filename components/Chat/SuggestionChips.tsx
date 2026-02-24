import React from 'react';

interface SuggestionChipsProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  disabled: boolean;
  onRequireDomain?: () => void;
}

export const SuggestionChips: React.FC<SuggestionChipsProps> = ({
  suggestions,
  onSelect,
  disabled,
  onRequireDomain
}) => {
  if (!suggestions || suggestions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 mt-4 animate-fade-in">
      {suggestions.map((suggestion, index) => (
        <button
          key={index}
          onClick={() => {
            if (disabled) {
              onRequireDomain?.();
              return;
            }
            onSelect(suggestion);
          }}
          aria-disabled={disabled}
          className={`text-sm px-4 py-2 bg-white border border-primary-100 text-primary-700 rounded-full shadow-sm transition-all duration-200 active:scale-95 text-left ${
            disabled
              ? 'opacity-50 cursor-not-allowed'
              : 'hover:bg-primary-50 hover:border-primary-200 hover:shadow-md'
          }`}
        >
          {suggestion}
        </button>
      ))}
    </div>
  );
};
