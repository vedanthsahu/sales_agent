import React from 'react';
import { FileMeta } from '../../types';
import { Icons } from '../../constants';

interface FileMenuProps {
  isOpen: boolean;
  files: FileMeta[];
  selectedFileIds: string[];
  onToggle: (fileId: string) => void;
  onClose: () => void;
}

export const FileMenu: React.FC<FileMenuProps> = ({
  isOpen,
  files,
  selectedFileIds,
  onToggle,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="absolute bottom-full left-0 mb-4 w-80 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden z-20 animate-fade-in origin-bottom-left">
      <div className="bg-gray-50 px-4 py-3 border-b border-gray-100 flex justify-between items-center">
        <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">Select Files</h3>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          <Icons.X className="w-4 h-4" />
        </button>
      </div>
      <div className="p-2 max-h-80 overflow-y-auto">
        {files.length === 0 && (
          <div className="text-xs text-gray-500 px-3 py-2">No files available for this domain.</div>
        )}
        {files.map((file) => {
          const isSelected = selectedFileIds.includes(file.file_id);
          const isReady = file.processing_status === 'completed';
          const canToggle = isReady || isSelected;
          return (
            <button
              key={file.file_id}
              onClick={() => canToggle && onToggle(file.file_id)}
              className={`w-full text-left p-3 rounded-lg transition-colors duration-200 group ${
                canToggle ? 'hover:bg-primary-50' : 'opacity-50 cursor-not-allowed'
              }`}
            >
              <div className="flex items-start gap-3">
                <div className={`mt-0.5 w-4 h-4 rounded border ${
                  isSelected ? 'bg-primary-600 border-primary-600' : 'border-gray-300'
                }`} />
                <div>
                  <div className="font-semibold text-gray-800 text-sm">{file.filename}</div>
                  <div className="text-xs text-gray-500 mt-0.5">
                    Status: {file.processing_status || 'uploaded'}
                  </div>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};
