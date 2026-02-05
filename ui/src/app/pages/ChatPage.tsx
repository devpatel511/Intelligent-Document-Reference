import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatContext } from '@/app/contexts/ChatContext';
import { FileNavigator } from '@/app/components/FileNavigator';
import { ChatHistory } from '@/app/components/ChatHistory';
import { ChatMessages } from '@/app/components/ChatMessages';
import { ChatInput } from '@/app/components/ChatInput';
import { Button } from '@/app/components/ui/button';
import { Settings, PanelLeftClose, PanelLeft, History, PanelRightClose } from 'lucide-react';
import { cn } from '@/app/components/ui/utils';

export function ChatPage() {
  const [showFileNav, setShowFileNav] = useState(true);
  const [showHistory, setShowHistory] = useState(true);
  const navigate = useNavigate();

  return (
    <div className="flex h-screen bg-background">
      {/* Chat History Sidebar */}
      <div
        className={cn(
          'border-r bg-card transition-all duration-300',
          showHistory ? 'w-64' : 'w-0 overflow-hidden'
        )}
      >
        {showHistory && <ChatHistory onClose={() => setShowHistory(false)} />}
      </div>

      {/* File Navigator */}
      <div
        className={cn(
          'border-r bg-card transition-all duration-300',
          showFileNav ? 'w-64' : 'w-0 overflow-hidden'
        )}
      >
        {showFileNav && (
          <div className="h-full flex flex-col">
            <div className="p-4 border-b">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-semibold">Context Files</h2>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => setShowFileNav(false)}
                >
                  <PanelLeftClose className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Select files to include in context
              </p>
            </div>
            <div className="flex-1 overflow-y-auto">
              <FileNavigator type="context" />
            </div>
          </div>
        )}
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-16 border-b flex items-center justify-between px-4 bg-card">
          <div className="flex items-center gap-2">
            {!showHistory && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowHistory(true)}
              >
                <History className="h-4 w-4" />
              </Button>
            )}
            {!showFileNav && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowFileNav(true)}
              >
                <PanelLeft className="h-4 w-4" />
              </Button>
            )}
            <h1 className="text-lg font-semibold">RAG Chatbot</h1>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate('/settings')}
          >
            <Settings className="h-4 w-4 mr-2" />
            Settings
          </Button>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-hidden">
          <ChatMessages />
        </div>

        {/* Input Area */}
        <div className="border-t bg-card p-4">
          <ChatInput />
        </div>
      </div>
    </div>
  );
}