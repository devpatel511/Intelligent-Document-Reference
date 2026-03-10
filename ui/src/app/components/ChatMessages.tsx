import { useEffect, useRef } from 'react';
import { useChatContext, Citation } from '@/app/contexts/ChatContext';
import { ScrollArea } from '@/app/components/ui/scroll-area';
import { Avatar, AvatarFallback } from '@/app/components/ui/avatar';
import { User, Bot, FileText } from 'lucide-react';
import { cn } from '@/app/components/ui/utils';
import { format } from 'date-fns';

/** Extract just the file name from a full path */
function fileName(path: string): string {
  return path.split(/[\\/]/).pop() || path;
}

function CitationsList({ citations }: { citations: Citation[] }) {
  if (!citations || citations.length === 0) return null;
  return (
    <div className="mt-2 border-t pt-2">
      <p className="text-xs font-medium text-muted-foreground mb-1">Sources</p>
      <div className="flex flex-wrap gap-1.5">
        {citations.map((c, i) => (
          <span
            key={i}
            className="inline-flex items-center gap-1 text-xs bg-background border rounded-md px-2 py-0.5"
            title={c.file_path}
          >
            <FileText className="h-3 w-3 text-muted-foreground" />
            <span className="truncate max-w-[180px]">{fileName(c.file_path)}</span>
            <span className="text-muted-foreground">
              {Math.round(c.relevance * 100)}%
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

export function ChatMessages() {
  const { messages, isLoading } = useChatContext();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  if (messages.length === 0) {
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
        {messages.map((message) => (
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
                {message.role === 'assistant' && message.citations && (
                  <CitationsList citations={message.citations} />
                )}
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
        {isLoading && (
          <div className="flex gap-4 justify-start">
            <Avatar className="h-8 w-8 mt-1">
              <AvatarFallback className="bg-primary text-primary-foreground">
                <Bot className="h-4 w-4" />
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-2 max-w-[80%]">
              <div className="rounded-lg px-4 py-3 bg-muted">
                <p className="text-sm text-muted-foreground">Thinking...</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
