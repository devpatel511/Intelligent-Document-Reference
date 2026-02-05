import { useEffect, useRef } from 'react';
import { useChatContext } from '@/app/contexts/ChatContext';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { User, Bot } from 'lucide-react';
import { cn } from '@/app/components/ui/utils';
import { format } from 'date-fns';

export function ChatMessages() {
  const { currentChat } = useChatContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [currentChat?.messages]);

  if (!currentChat || currentChat.messages.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4 max-w-md px-4">
          <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto">
            <Bot className="h-8 w-8 text-primary" />
          </div>
          <div>
            <h2 className="text-xl font-semibold mb-2">Start a Conversation</h2>
            <p className="text-muted-foreground">
              Ask me anything! Select files from the left sidebar to include them in your
              conversation context.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <ScrollArea className="h-full" ref={scrollRef}>
      <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
        {currentChat.messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-4',
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}

            <div
              className={cn(
                'flex-1 space-y-2 max-w-[80%]',
                message.role === 'user' && 'flex flex-col items-end'
              )}
            >
              <div
                className={cn(
                  'rounded-lg px-4 py-3',
                  message.role === 'user'
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-muted'
                )}
              >
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
              </div>
              <div className="text-xs text-muted-foreground px-2">
                {format(message.timestamp, 'HH:mm')}
              </div>
            </div>

            {message.role === 'user' && (
              <Avatar className="h-8 w-8 mt-1">
                <AvatarFallback className="bg-secondary">
                  <User className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
            )}
          </div>
        ))}
      </div>
    </ScrollArea>
  );
}
