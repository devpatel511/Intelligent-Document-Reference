import { useState } from 'react';
import { useChatContext, FileNode } from '@/app/contexts/ChatContext';
import { Checkbox } from '@/app/components/ui/checkbox';
import { ChevronRight, ChevronDown, File, Folder } from 'lucide-react';
import { cn } from '@/app/components/ui/utils';

interface FileNavigatorProps {
  type: 'context' | 'indexing' | 'exclusion';
}

export function FileNavigator({ type }: FileNavigatorProps) {
  const { fileTree, selectedFiles, toggleFileSelection, indexedFiles, toggleIndexedFile, excludedFiles, toggleExcludedFile } =
    useChatContext();

  const isChecked = (path: string) => {
    if (type === 'context') {
      return selectedFiles.includes(path);
    } else if (type === 'exclusion') {
      return excludedFiles.includes(path);
    }
    return indexedFiles.includes(path);
  };

  const handleToggle = (path: string) => {
    if (type === 'context') {
      toggleFileSelection(path);
    } else if (type === 'exclusion') {
      toggleExcludedFile(path);
    } else {
      toggleIndexedFile(path);
    }
  };

  return (
    <div className="p-2">
      {fileTree.map((node) => (
        <FileTreeNode
          key={node.id}
          node={node}
          isChecked={isChecked}
          onToggle={handleToggle}
          level={0}
          type={type}
        />
      ))}
    </div>
  );
}

interface FileTreeNodeProps {
  node: FileNode;
  isChecked: (path: string) => boolean;
  onToggle: (path: string) => void;
  level: number;
}

function FileTreeNode({ node, isChecked, onToggle, level, type }: FileTreeNodeProps & { type: 'context' | 'indexing' | 'exclusion' }) {
  const [isExpanded, setIsExpanded] = useState(level === 0);

  const handleCheckboxChange = (checked: boolean) => {
    if (type === 'context') {
      // For context, only allow files (leaf nodes), not directories
      if (node.type === 'file') {
        onToggle(node.path);
      } else if (node.type === 'folder' && node.children) {
        // For folders in context mode, recursively select/deselect all file children only
        const selectAllFiles = (n: FileNode) => {
          if (n.type === 'file') {
            if (checked !== isChecked(n.path)) {
              onToggle(n.path);
            }
          } else if (n.children) {
            n.children.forEach(selectAllFiles);
          }
        };
        node.children.forEach(selectAllFiles);
      }
    } else {
      // For indexing/exclusion, allow both files and folders
      onToggle(node.path);
      if (node.type === 'folder' && node.children) {
        node.children.forEach((child) => {
          if (checked !== isChecked(child.path)) {
            onToggle(child.path);
          }
          if (child.type === 'folder' && child.children) {
            child.children.forEach((grandchild) => {
              if (checked !== isChecked(grandchild.path)) {
                onToggle(grandchild.path);
              }
            });
          }
        });
      }
    }
  };

  return (
    <div>
      <div
        className={cn(
          'flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-accent cursor-pointer',
          'group'
        )}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {node.type === 'folder' && (
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-0.5 hover:bg-accent-foreground/10 rounded"
          >
            {isExpanded ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
        )}

        <Checkbox
          id={node.id}
          checked={isChecked(node.path)}
          onCheckedChange={handleCheckboxChange}
          className="h-4 w-4"
        />

        <label
          htmlFor={node.id}
          className="flex items-center gap-2 flex-1 cursor-pointer select-none"
        >
          {node.type === 'folder' ? (
            <Folder className="h-4 w-4 text-blue-500" />
          ) : (
            <File className="h-4 w-4 text-muted-foreground" />
          )}
          <span className="text-sm">{node.name}</span>
        </label>
      </div>

      {node.type === 'folder' && isExpanded && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode
              key={child.id}
              node={child}
              isChecked={isChecked}
              onToggle={onToggle}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}