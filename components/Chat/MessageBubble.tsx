import React from 'react';
import { Message } from '../../types';
import { Icons } from '../../constants';
import { motion } from "framer-motion";

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';

  // Basic formatting for markdown-like bolding if needed, though simple text is fine for MVP
  const formatText = (text: string) => {
    return text.split('\n').map((line, i) => (
      <React.Fragment key={i}>
        {line}
        <br />
      </React.Fragment>
    ));
  };

  return (
    <motion.div
  layout
  initial={{ opacity: 0, y: 25, scale: 0.98 }}
  animate={{ opacity: 1, y: 0, scale: 1 }}
  transition={{
    type: "spring",
    stiffness: 280,
    damping: 22,
    mass: 0.8
  }}
  className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-6 group`}
>

      <div className={`flex max-w-[85%] md:max-w-[75%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-3`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser ? 'bg-neutral-800 text-white' : 'bg-primary-600 text-white'
          } shadow-sm`}>
          {isUser ? <Icons.User className="w-5 h-5" /> : <Icons.Bot className="w-5 h-5" />}
        </div>

        {/* Bubble */}
        <div className={`relative px-5 py-3.5 rounded-2xl shadow-sm text-sm md:text-base leading-relaxed ${
          isUser 
            ? 'bg-neutral-800 text-white rounded-tr-sm' 
            : 'bg-white border border-gray-100 text-gray-800 rounded-tl-sm'
        }`}>
          {message.isTyping ? (
             <motion.div
  className="flex space-x-1.5 h-5 items-center"
  initial="hidden"
  animate="visible"
>
  {[0,1,2].map(i => (
    <motion.div
      key={i}
      className="w-2 h-2 bg-current rounded-full"
      variants={{
        hidden: { opacity: 0.3, scale: 0.8 },
        visible: {
          opacity: [0.3, 1, 0.3],
          scale: [0.8, 1.2, 0.8],
          transition: {
            duration: 1.2,
            repeat: Infinity,
            delay: i * 0.2
          }
        }
      }}
    />
  ))}

               <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-75" style={{ animationDelay: '0ms' }}></div>
               <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-75" style={{ animationDelay: '150ms' }}></div>
               <div className="w-2 h-2 bg-current rounded-full animate-bounce opacity-75" style={{ animationDelay: '300ms' }}></div>
</motion.div>
          ) : (
            <div>{formatText(message.text)}</div>
          )}
        </div>
      </div>
</motion.div>
  );
};