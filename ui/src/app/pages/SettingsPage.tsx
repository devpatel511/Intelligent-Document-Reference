import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useChatContext } from '@/app/contexts/ChatContext';
import { FileNavigator } from '@/app/components/FileNavigator';
import { ExclusionConfigDialog } from '@/app/components/ExclusionConfigDialog';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { Textarea } from '@/app/components/ui/textarea';
import { Switch } from '@/app/components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/app/components/ui/radio-group';
import { Slider } from '@/app/components/ui/slider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card';
import { ArrowLeft, Upload, Moon, Sun, Save, Check } from 'lucide-react';

export function SettingsPage() {
  const navigate = useNavigate();
  const {
    modelProvider,
    setModelProvider,
    localEndpoint,
    setLocalEndpoint,
    apiKeys,
    setApiKey,
    temperature,
    setTemperature,
    contextSize,
    setContextSize,
    systemPrompt,
    setSystemPrompt,
    darkMode,
    setDarkMode,
    userInfo,
    setUserInfo,
    uploadFolder,
    indexedFiles,
    excludedFiles,
    exclusionPatterns,
    toggleIndexedFile,
    toggleExcludedFile,
    saveFileIndexingConfig,
  } = useChatContext();
  
  const [isSaving, setIsSaving] = useState(false);

  const handleFolderUpload = async (type: 'inclusion' | 'exclusion') => {
    // Create a file input element
    const input = document.createElement('input');
    input.type = 'file';
    input.webkitdirectory = true;
    input.multiple = true;
    
    input.onchange = async (e) => {
      const target = e.target as HTMLInputElement;
      if (target.files && target.files.length > 0) {
        const folderPath = target.files[0].webkitRelativePath.split('/')[0];
        try {
          await uploadFolder(folderPath, type);
          // Don't save yet - user will click Save button
        } catch (error) {
          alert(`Failed to upload folder: ${error}`);
        }
      }
    };
    
    input.click();
  };

  const handleSaveFileIndexing = async () => {
    setIsSaving(true);
    try {
      // Collect all selected files (only files, not directories)
      const inclusionFiles = indexedFiles.filter(f => !f.endsWith('/'));
      const exclusionFiles = excludedFiles.filter(f => !f.endsWith('/'));
      
      // Get context files from indexed files that are selected
      // For now, we'll use indexedFiles as context files (user selects in inclusion)
      const contextFiles = inclusionFiles;
      
      const success = await saveFileIndexingConfig({
        inclusion: {
          files: inclusionFiles,
          directories: [], // TODO: Track directories separately
        },
        exclusion: {
          files: exclusionFiles,
          directories: [],
          patterns: exclusionPatterns,
        },
        context: {
          files: contextFiles,
        },
      });
      
      if (success) {
        alert('File indexing configuration saved successfully!');
      } else {
        alert('Failed to save file indexing configuration.');
      }
    } catch (error) {
      alert(`Error saving configuration: ${error}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="px-4 py-4 flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/chat')}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-semibold">Settings</h1>
        </div>
      </div>

      {/* Settings Content */}
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Tabs defaultValue="general" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="general">General Settings</TabsTrigger>
            <TabsTrigger value="models">Model Configuration</TabsTrigger>
            <TabsTrigger value="indexing">File Indexing</TabsTrigger>
            <TabsTrigger value="advanced">Advanced Settings</TabsTrigger>
          </TabsList>

          {/* General Settings */}
          <TabsContent value="general" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Appearance</CardTitle>
                <CardDescription>Customize the look and feel of the application</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label htmlFor="dark-mode">Dark Mode</Label>
                    <p className="text-sm text-muted-foreground">
                      Switch between light and dark theme
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {darkMode ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4" />}
                    <Switch
                      id="dark-mode"
                      checked={darkMode}
                      onCheckedChange={setDarkMode}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>System Prompt</CardTitle>
                <CardDescription>
                  Customize the system prompt that guides the AI's behavior
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="system-prompt">System Prompt</Label>
                  <Textarea
                    id="system-prompt"
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                    placeholder="You are a helpful AI assistant..."
                    className="min-h-[120px]"
                  />
                  <p className="text-sm text-muted-foreground">
                    This prompt will be used to set the AI's behavior and personality
                  </p>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Information</CardTitle>
                <CardDescription>
                  Provide context about yourself to personalize responses
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="user-info">User Information</Label>
                  <Textarea
                    id="user-info"
                    value={userInfo}
                    onChange={(e) => setUserInfo(e.target.value)}
                    placeholder="Enter information about yourself, your role, preferences, etc."
                    className="min-h-[100px]"
                  />
                  <p className="text-sm text-muted-foreground">
                    This information will help the AI provide more personalized responses
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Model Configuration */}
          <TabsContent value="models" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Model Provider</CardTitle>
                <CardDescription>
                  Choose between local models or online API services
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <RadioGroup
                  value={modelProvider}
                  onValueChange={(value) => setModelProvider(value as 'local' | 'online')}
                  className="gap-4"
                >
                  <div className="flex items-center space-x-2 border border-input rounded-lg p-4 cursor-pointer hover:bg-accent">
                    <RadioGroupItem value="online" id="online" className="border-black" />
                    <Label htmlFor="online" className="cursor-pointer flex-1">Online Models</Label>
                  </div>
                  <div className="flex items-center space-x-2 border border-input rounded-lg p-4 cursor-pointer hover:bg-accent">
                    <RadioGroupItem value="local" id="local" className="border-black" />
                    <Label htmlFor="local" className="cursor-pointer flex-1">Local Models</Label>
                  </div>
                </RadioGroup>

                {modelProvider === 'local' ? (
                  <div className="space-y-2">
                    <Label htmlFor="endpoint">Local Inference Endpoint</Label>
                    <Input
                      id="endpoint"
                      type="url"
                      placeholder="http://localhost:8000"
                      value={localEndpoint}
                      onChange={(e) => setLocalEndpoint(e.target.value)}
                    />
                    <p className="text-sm text-muted-foreground">
                      Enter the URL of your local inference server (e.g., Ollama, LM Studio)
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="gpt4-key">OpenAI API Key (GPT-4)</Label>
                      <Input
                        id="gpt4-key"
                        type="password"
                        placeholder="sk-..."
                        value={apiKeys['gpt-4'] || ''}
                        onChange={(e) => setApiKey('gpt-4', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="gemini-key">Google API Key (Gemini 2.5)</Label>
                      <Input
                        id="gemini-key"
                        type="password"
                        placeholder="AI..."
                        value={apiKeys['gemini-2.5'] || ''}
                        onChange={(e) => setApiKey('gemini-2.5', e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="claude-key">Anthropic API Key (Claude 3)</Label>
                      <Input
                        id="claude-key"
                        type="password"
                        placeholder="sk-ant-..."
                        value={apiKeys['claude-3'] || ''}
                        onChange={(e) => setApiKey('claude-3', e.target.value)}
                      />
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* File Indexing */}
          <TabsContent value="indexing">
            <Card>
              <CardHeader>
                <CardTitle>Document Indexing</CardTitle>
                <CardDescription>
                  Select files and folders to include or exclude from RAG retrieval
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Inclusion List */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Inclusion List</h3>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleFolderUpload('inclusion')}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Folder
                      </Button>
                      <span className="text-xs text-muted-foreground">Files to be indexed</span>
                    </div>
                  </div>
                  <div className="border border-black rounded-lg h-[300px] overflow-y-auto">
                    <FileNavigator type="indexing" />
                  </div>
                </div>

                {/* Exclusion List */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Exclusion List</h3>
                    <div className="flex items-center gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={() => handleFolderUpload('exclusion')}
                      >
                        <Upload className="h-4 w-4 mr-2" />
                        Upload Folder
                      </Button>
                      <ExclusionConfigDialog />
                      <span className="text-xs text-muted-foreground">Files to be excluded</span>
                    </div>
                  </div>
                  <div className="border border-black rounded-lg h-[300px] overflow-y-auto">
                    <FileNavigator type="exclusion" />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4 border-t">
                  <p className="text-sm text-muted-foreground">
                    Included files will be used for retrieval-augmented generation, while excluded files will be ignored. You can upload entire folders or select individual files.
                  </p>
                  <Button
                    onClick={handleSaveFileIndexing}
                    disabled={isSaving}
                    className="ml-4"
                  >
                    {isSaving ? (
                      <>
                        <span className="animate-spin mr-2">⏳</span>
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4 mr-2" />
                        Save Configuration
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Advanced Settings */}
          <TabsContent value="advanced" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Generation Parameters</CardTitle>
                <CardDescription>
                  Fine-tune model behavior and performance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="temperature">Temperature</Label>
                      <span className="text-sm text-muted-foreground">{temperature}</span>
                    </div>
                    <Slider
                      id="temperature"
                      min={0}
                      max={2}
                      step={0.1}
                      value={[temperature]}
                      onValueChange={(value) => setTemperature(value[0])}
                    />
                    <p className="text-sm text-muted-foreground">
                      Controls randomness. Lower values make output more focused and
                      deterministic.
                    </p>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label htmlFor="context">Context Size</Label>
                      <span className="text-sm text-muted-foreground">{contextSize}</span>
                    </div>
                    <Slider
                      id="context"
                      min={1024}
                      max={32768}
                      step={1024}
                      value={[contextSize]}
                      onValueChange={(value) => setContextSize(value[0])}
                    />
                    <p className="text-sm text-muted-foreground">
                      Maximum number of tokens to use for context window.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Retrieval Settings</CardTitle>
                <CardDescription>Configure RAG retrieval behavior</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="top-k">Top-K Results</Label>
                  <Input id="top-k" type="number" defaultValue="5" min="1" max="20" />
                  <p className="text-sm text-muted-foreground">
                    Number of relevant documents to retrieve
                  </p>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="chunk-size">Chunk Size</Label>
                  <Input id="chunk-size" type="number" defaultValue="512" min="128" max="2048" />
                  <p className="text-sm text-muted-foreground">
                    Size of text chunks for document processing
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}