import { useNavigate } from 'react-router-dom';
import { useChatContext } from '@/app/contexts/ChatContext';
import { FileNavigator } from '@/app/components/FileNavigator';
import { ExclusionConfigDialog } from '@/app/components/ExclusionConfigDialog';
import { Button } from '@/app/components/ui/button';
import { Input } from '@/app/components/ui/input';
import { Label } from '@/app/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/app/components/ui/tabs';
import { RadioGroup, RadioGroupItem } from '@/app/components/ui/radio-group';
import { Slider } from '@/app/components/ui/slider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/app/components/ui/card';
import { ArrowLeft } from 'lucide-react';

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
  } = useChatContext();

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
        <Tabs defaultValue="models" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="models">Model Configuration</TabsTrigger>
            <TabsTrigger value="indexing">File Indexing</TabsTrigger>
            <TabsTrigger value="advanced">Advanced Settings</TabsTrigger>
          </TabsList>

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
                    <span className="text-xs text-muted-foreground">Files to be indexed</span>
                  </div>
                  <div className="border border-black rounded-lg h-[300px] overflow-y-auto">
                    <FileNavigator type="indexing" />
                  </div>
                </div>

                {/* Exclusion List */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">Exclusion List</h3>
                    <div className="flex items-center gap-3">
                      <ExclusionConfigDialog />
                      <span className="text-xs text-muted-foreground">Files to be excluded</span>
                    </div>
                  </div>
                  <div className="border border-black rounded-lg h-[300px] overflow-y-auto">
                    <FileNavigator type="exclusion" />
                  </div>
                </div>

                <p className="text-sm text-muted-foreground">
                  Included files will be used for retrieval-augmented generation, while excluded files will be ignored. Changes are saved automatically.
                </p>
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