import React, { createContext, useContext, useState, ReactNode } from 'react';

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: Date;
  updatedAt: Date;
}

export type InferenceMode = 'retrieval' | 'q&a' | 'deep-research';
export type ModelType = 'gpt-4' | 'gemini-2.5' | 'claude-3' | 'llama-3';
export type ModelProvider = 'local' | 'online';

export interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  path: string;
  selected?: boolean;
  children?: FileNode[];
}

interface ChatContextType {
  chats: Chat[];
  currentChatId: string | null;
  currentChat: Chat | null;
  inferenceMode: InferenceMode;
  selectedModel: ModelType;
  selectedFiles: string[];
  fileTree: FileNode[];
  modelProvider: ModelProvider;
  localEndpoint: string;
  apiKeys: Record<string, string>;
  temperature: number;
  contextSize: number;
  indexedFiles: string[];
  excludedFiles: string[];
  exclusionPatterns: string[];
  createNewChat: () => void;
  selectChat: (chatId: string) => void;
  sendMessage: (content: string) => void;
  setInferenceMode: (mode: InferenceMode) => void;
  setSelectedModel: (model: ModelType) => void;
  toggleFileSelection: (path: string) => void;
  setModelProvider: (provider: ModelProvider) => void;
  setLocalEndpoint: (endpoint: string) => void;
  setApiKey: (model: string, key: string) => void;
  setTemperature: (temp: number) => void;
  setContextSize: (size: number) => void;
  toggleIndexedFile: (path: string) => void;
  toggleExcludedFile: (path: string) => void;
  addExclusionPattern: (pattern: string) => void;
  removeExclusionPattern: (pattern: string) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const mockFileTree: FileNode[] = [
  {
    id: '1',
    name: 'documents',
    type: 'folder',
    path: '/documents',
    children: [
      { id: '1-1', name: 'research_paper.pdf', type: 'file', path: '/documents/research_paper.pdf' },
      { id: '1-2', name: 'notes.txt', type: 'file', path: '/documents/notes.txt' },
      {
        id: '1-3',
        name: 'reports',
        type: 'folder',
        path: '/documents/reports',
        children: [
          { id: '1-3-1', name: 'Q1_report.docx', type: 'file', path: '/documents/reports/Q1_report.docx' },
          { id: '1-3-2', name: 'Q2_report.docx', type: 'file', path: '/documents/reports/Q2_report.docx' },
        ],
      },
    ],
  },
  {
    id: '2',
    name: 'projects',
    type: 'folder',
    path: '/projects',
    children: [
      { id: '2-1', name: 'project_proposal.md', type: 'file', path: '/projects/project_proposal.md' },
      { id: '2-2', name: 'architecture.drawio', type: 'file', path: '/projects/architecture.drawio' },
    ],
  },
  {
    id: '3',
    name: 'references',
    type: 'folder',
    path: '/references',
    children: [
      { id: '3-1', name: 'api_documentation.pdf', type: 'file', path: '/references/api_documentation.pdf' },
      { id: '3-2', name: 'user_guide.pdf', type: 'file', path: '/references/user_guide.pdf' },
    ],
  },
];

const initialChats: Chat[] = [
  {
    id: '1',
    title: 'Research on Machine Learning',
    messages: [
      {
        id: 'm1',
        role: 'user',
        content: 'Can you explain the key concepts in machine learning?',
        timestamp: new Date('2025-01-28T10:00:00'),
      },
      {
        id: 'm2',
        role: 'assistant',
        content: 'Machine learning is a subset of artificial intelligence that focuses on building systems that learn from data. Key concepts include supervised learning, unsupervised learning, neural networks, and deep learning...',
        timestamp: new Date('2025-01-28T10:00:15'),
      },
    ],
    createdAt: new Date('2025-01-28T10:00:00'),
    updatedAt: new Date('2025-01-28T10:00:15'),
  },
  {
    id: '2',
    title: 'Project Architecture Discussion',
    messages: [
      {
        id: 'm3',
        role: 'user',
        content: 'Help me design a scalable microservices architecture',
        timestamp: new Date('2025-01-27T15:30:00'),
      },
      {
        id: 'm4',
        role: 'assistant',
        content: 'For a scalable microservices architecture, consider these key components: API Gateway, Service Discovery, Load Balancing, and Container Orchestration...',
        timestamp: new Date('2025-01-27T15:30:20'),
      },
    ],
    createdAt: new Date('2025-01-27T15:30:00'),
    updatedAt: new Date('2025-01-27T15:30:20'),
  },
];

export function ChatProvider({ children }: { children: ReactNode }) {
  const [chats, setChats] = useState<Chat[]>(initialChats);
  const [currentChatId, setCurrentChatId] = useState<string | null>(initialChats[0].id);
  const [inferenceMode, setInferenceMode] = useState<InferenceMode>('retrieval');
  const [selectedModel, setSelectedModel] = useState<ModelType>('gpt-4');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [fileTree] = useState<FileNode[]>(mockFileTree);
  const [modelProvider, setModelProvider] = useState<ModelProvider>('online');
  const [localEndpoint, setLocalEndpoint] = useState<string>('http://localhost:8000');
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    'gpt-4': '',
    'gemini-2.5': '',
    'claude-3': '',
  });
  const [temperature, setTemperature] = useState<number>(0.7);
  const [contextSize, setContextSize] = useState<number>(4096);
  const [indexedFiles, setIndexedFiles] = useState<string[]>([
    '/documents/research_paper.pdf',
    '/documents/notes.txt',
  ]);
  const [excludedFiles, setExcludedFiles] = useState<string[]>([]);
  const [exclusionPatterns, setExclusionPatterns] = useState<string[]>([]);

  const currentChat = chats.find((chat) => chat.id === currentChatId) || null;

  const createNewChat = () => {
    const newChat: Chat = {
      id: Date.now().toString(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    setChats([newChat, ...chats]);
    setCurrentChatId(newChat.id);
  };

  const selectChat = (chatId: string) => {
    setCurrentChatId(chatId);
  };

  const sendMessage = (content: string) => {
    if (!currentChatId) {
      createNewChat();
    }

    const chatId = currentChatId || Date.now().toString();

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Mock assistant response
    const assistantMessage: Message = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: `This is a mock response to: "${content}". In a real application, this would be generated by the selected model (${selectedModel}) in ${inferenceMode} mode.`,
      timestamp: new Date(),
    };

    setChats((prevChats) =>
      prevChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              messages: [...chat.messages, userMessage, assistantMessage],
              updatedAt: new Date(),
              title: chat.messages.length === 0 ? content.slice(0, 50) : chat.title,
            }
          : chat
      )
    );
  };

  const toggleFileSelection = (path: string) => {
    setSelectedFiles((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path]
    );
  };

  const setApiKey = (model: string, key: string) => {
    setApiKeys((prev) => ({ ...prev, [model]: key }));
  };

  const toggleIndexedFile = (path: string) => {
    setIndexedFiles((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path]
    );
  };

  const toggleExcludedFile = (path: string) => {
    setExcludedFiles((prev) =>
      prev.includes(path) ? prev.filter((p) => p !== path) : [...prev, path]
    );
  };

  const addExclusionPattern = (pattern: string) => {
    setExclusionPatterns((prev) => [...prev, pattern]);
  };

  const removeExclusionPattern = (pattern: string) => {
    setExclusionPatterns((prev) => prev.filter((p) => p !== pattern));
  };

  return (
    <ChatContext.Provider
      value={{
        chats,
        currentChatId,
        currentChat,
        inferenceMode,
        selectedModel,
        selectedFiles,
        fileTree,
        modelProvider,
        localEndpoint,
        apiKeys,
        temperature,
        contextSize,
        indexedFiles,
        excludedFiles,
        exclusionPatterns,
        createNewChat,
        selectChat,
        sendMessage,
        setInferenceMode,
        setSelectedModel,
        toggleFileSelection,
        setModelProvider,
        setLocalEndpoint,
        setApiKey,
        setTemperature,
        setContextSize,
        toggleIndexedFile,
        toggleExcludedFile,
        addExclusionPattern,
        removeExclusionPattern,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
}