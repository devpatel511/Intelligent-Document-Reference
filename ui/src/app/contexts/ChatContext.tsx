import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type MessageRole = 'user' | 'assistant';

export interface Message {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
}

// Chat history removed - not focusing on that right now

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
  messages: Message[];
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
  isLoading: boolean;
  // General settings
  systemPrompt: string;
  darkMode: boolean;
  userInfo: string;
  sendMessage: (content: string) => Promise<void>;
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
  setSystemPrompt: (prompt: string) => void;
  setDarkMode: (enabled: boolean) => void;
  setUserInfo: (info: string) => void;
  uploadFolder: (folderPath: string, type: 'inclusion' | 'exclusion') => Promise<void>;
  saveFileIndexingConfig: (config: {
    inclusion?: { files?: string[]; directories?: string[] };
    exclusion?: { files?: string[]; directories?: string[]; patterns?: string[] };
    context?: { files?: string[] };
  }) => Promise<boolean>;
  loadFiles: () => Promise<void>;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function ChatProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inferenceMode, setInferenceMode] = useState<InferenceMode>('retrieval');
  const [selectedModel, setSelectedModel] = useState<ModelType>('gpt-4');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [modelProvider, setModelProvider] = useState<ModelProvider>('online');
  const [localEndpoint, setLocalEndpoint] = useState<string>('http://localhost:8000');
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({
    'gpt-4': '',
    'gemini-2.5': '',
    'claude-3': '',
  });
  const [temperature, setTemperature] = useState<number>(0.7);
  const [contextSize, setContextSize] = useState<number>(4096);
  const [indexedFiles, setIndexedFiles] = useState<string[]>([]);
  const [excludedFiles, setExcludedFiles] = useState<string[]>([]);
  const [exclusionPatterns, setExclusionPatterns] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  // General settings
  const [systemPrompt, setSystemPrompt] = useState<string>('You are a helpful AI assistant that provides accurate and detailed answers based on the provided context.');
  const [darkMode, setDarkMode] = useState<boolean>(false);
  const [userInfo, setUserInfo] = useState<string>('');

  // Load files and context from backend on mount
  useEffect(() => {
    loadFiles();
    loadContextFiles();
    loadFileIndexingConfig();
  }, []);

  const loadContextFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files/context`);
      const data = await response.json();
      if (data.files && Array.isArray(data.files)) {
        // Only set files, filter out directories
        const filesOnly = data.files.filter((path: string) => !path.endsWith('/'));
        setSelectedFiles(filesOnly);
      }
    } catch (error) {
      console.error('Failed to load context files:', error);
    }
  };

  const loadFileIndexingConfig = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files/indexing`);
      const data = await response.json();
      if (data.inclusion) {
        // Combine files and files from directories
        const allIncluded: string[] = [];
        if (data.inclusion.files) {
          allIncluded.push(...data.inclusion.files);
        }
        // TODO: Expand directories to individual files if needed
        setIndexedFiles(allIncluded);
      }
      if (data.exclusion) {
        if (data.exclusion.files) {
          setExcludedFiles(data.exclusion.files);
        }
        if (data.exclusion.patterns) {
          setExclusionPatterns(data.exclusion.patterns);
        }
      }
    } catch (error) {
      console.error('Failed to load file indexing config:', error);
    }
  };

  const saveFileIndexingConfig = async (config: {
    inclusion?: { files?: string[]; directories?: string[] };
    exclusion?: { files?: string[]; directories?: string[]; patterns?: string[] };
    context?: { files?: string[] };
  }) => {
    try {
      const response = await fetch(`${API_BASE_URL}/files/indexing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });
      const data = await response.json();
      if (data.status === 'ok') {
        // Reload context files after save
        await loadContextFiles();
        await loadFileIndexingConfig();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to save file indexing config:', error);
      return false;
    }
  };

  const loadFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/files/`);
      const data = await response.json();
      if (data.files && Array.isArray(data.files)) {
        setFileTree(data.files);
      }
    } catch (error) {
      console.error('Failed to load files:', error);
      // Keep empty file tree on error
      setFileTree([]);
    }
  };

  const sendMessage = async (content: string) => {
    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
          model: selectedModel,
          mode: inferenceMode,
          selected_files: selectedFiles,
          temperature,
          context_size: contextSize,
        }),
      });

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: data.answer || 'No response received',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: Message = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: 'Error: Failed to get response from server. Please check your connection and try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
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

  const uploadFolder = async (folderPath: string, type: 'inclusion' | 'exclusion') => {
    try {
      // TODO: Implement actual folder upload API call
      // For now, just add to the appropriate list
      if (type === 'inclusion') {
        setIndexedFiles((prev) => [...prev, folderPath]);
      } else {
        setExcludedFiles((prev) => [...prev, folderPath]);
      }
    } catch (error) {
      console.error('Failed to upload folder:', error);
      throw error;
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
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
        isLoading,
        systemPrompt,
        darkMode,
        userInfo,
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
        setSystemPrompt,
        setDarkMode,
        setUserInfo,
        uploadFolder,
        saveFileIndexingConfig,
        loadFiles,
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