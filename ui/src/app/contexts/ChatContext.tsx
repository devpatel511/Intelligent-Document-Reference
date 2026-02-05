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
  indexedDirectories: string[];
  excludedFiles: string[];
  excludedDirectories: string[];
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
  addIndexedDirectory: (path: string) => void;
  removeIndexedDirectory: (path: string) => void;
  addExcludedDirectory: (path: string) => void;
  removeExcludedDirectory: (path: string) => void;
  addExclusionPattern: (pattern: string) => void;
  removeExclusionPattern: (pattern: string) => void;
  setSystemPrompt: (prompt: string) => void;
  setDarkMode: (enabled: boolean) => void;
  setUserInfo: (info: string) => void;
  importFolder: (files: FileList, type: 'inclusion' | 'exclusion') => Promise<void>;
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
  const [indexedDirectories, setIndexedDirectories] = useState<string[]>([]);
  const [excludedFiles, setExcludedFiles] = useState<string[]>([]);
  const [excludedDirectories, setExcludedDirectories] = useState<string[]>([]);
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
        if (data.inclusion.files) {
          setIndexedFiles(data.inclusion.files);
        }
        if (data.inclusion.directories) {
          setIndexedDirectories(data.inclusion.directories);
        }
      }
      if (data.exclusion) {
        if (data.exclusion.files) {
          setExcludedFiles(data.exclusion.files);
        }
        if (data.exclusion.directories) {
          setExcludedDirectories(data.exclusion.directories);
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

  const importFolder = async (files: FileList, type: 'inclusion' | 'exclusion') => {
    try {
      if (files.length === 0) return;
      
      // Extract folder path from first file's webkitRelativePath
      const firstFile = files[0] as File & { webkitRelativePath?: string };
      if (!firstFile.webkitRelativePath) {
        throw new Error('Folder selection not supported in this browser');
      }
      
      const folderPath = firstFile.webkitRelativePath.split('/')[0];
      const allFilePaths: string[] = [];
      
      // Extract all file paths from the folder
      Array.from(files).forEach((file) => {
        const fileWithPath = file as File & { webkitRelativePath?: string };
        if (fileWithPath.webkitRelativePath) {
          // Convert to relative path format
          const relativePath = fileWithPath.webkitRelativePath;
          allFilePaths.push(relativePath);
        }
      });
      
      if (type === 'inclusion') {
        // Add folder to directories list
        if (!indexedDirectories.includes(folderPath)) {
          setIndexedDirectories((prev) => [...prev, folderPath]);
        }
        // Add all files to indexed files
        setIndexedFiles((prev) => {
          const newFiles = [...prev];
          allFilePaths.forEach((path) => {
            if (!newFiles.includes(path)) {
              newFiles.push(path);
            }
          });
          return newFiles;
        });
      } else {
        // Add folder to excluded directories list
        if (!excludedDirectories.includes(folderPath)) {
          setExcludedDirectories((prev) => [...prev, folderPath]);
        }
        // Add all files to excluded files
        setExcludedFiles((prev) => {
          const newFiles = [...prev];
          allFilePaths.forEach((path) => {
            if (!newFiles.includes(path)) {
              newFiles.push(path);
            }
          });
          return newFiles;
        });
      }
    } catch (error) {
      console.error('Failed to import folder:', error);
      throw error;
    }
  };

  const addIndexedDirectory = (path: string) => {
    if (!indexedDirectories.includes(path)) {
      setIndexedDirectories((prev) => [...prev, path]);
    }
  };

  const removeIndexedDirectory = (path: string) => {
    setIndexedDirectories((prev) => prev.filter((p) => p !== path));
    // Also remove all files from that directory
    setIndexedFiles((prev) => prev.filter((p) => !p.startsWith(path)));
  };

  const addExcludedDirectory = (path: string) => {
    if (!excludedDirectories.includes(path)) {
      setExcludedDirectories((prev) => [...prev, path]);
    }
  };

  const removeExcludedDirectory = (path: string) => {
    setExcludedDirectories((prev) => prev.filter((p) => p !== path));
    // Also remove all files from that directory
    setExcludedFiles((prev) => prev.filter((p) => !p.startsWith(path)));
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
        indexedDirectories,
        excludedFiles,
        excludedDirectories,
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
        addIndexedDirectory,
        removeIndexedDirectory,
        addExcludedDirectory,
        removeExcludedDirectory,
        addExclusionPattern,
        removeExclusionPattern,
        setSystemPrompt,
        setDarkMode,
        setUserInfo,
        importFolder,
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