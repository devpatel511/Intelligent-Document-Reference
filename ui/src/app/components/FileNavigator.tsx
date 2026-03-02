import { useState } from 'react';
import { useChatContext, FileNode } from '@/app/contexts/ChatContext';
import { Checkbox } from '@/app/components/ui/checkbox';
import { ChevronRight, ChevronDown, File, Folder } from 'lucide-react';
import { cn } from '@/app/components/ui/utils';

interface FileNavigatorProps {
  type: 'context' | 'indexing' | 'exclusion';
}

/** Recursively collect all leaf file paths under a node. */
function getAllLeafFiles(node: FileNode): string[] {
  if (node.type === 'file') return [node.path];
  if (!node.children) return [];
  return node.children.flatMap(getAllLeafFiles);
}

/** Recursively collect all paths (files + folders) under a node, including itself. */
function getAllPaths(node: FileNode): string[] {
  const paths = [node.path];
  if (node.children) {
    for (const child of node.children) {
      paths.push(...getAllPaths(child));
    }
  }
  return paths;
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
  type: 'context' | 'indexing' | 'exclusion';
}

function FileTreeNode({ node, isChecked, onToggle, level, type }: FileTreeNodeProps) {
  const [isExpanded, setIsExpanded] = useState(level === 0);

  // Compute checked/indeterminate state for folders
  const getFolderCheckState = (): boolean | 'indeterminate' => {
    if (node.type !== 'folder') return isChecked(node.path);

    if (type === 'context') {
      // In context mode, folder state is derived from leaf files
      const leaves = getAllLeafFiles(node);
      if (leaves.length === 0) return false;
      const checkedCount = leaves.filter((p) => isChecked(p)).length;
      if (checkedCount === 0) return false;
      if (checkedCount === leaves.length) return true;
      return 'indeterminate';
    } else {
      // In indexing/exclusion mode, folder state is derived from all descendants
      const allPaths = getAllPaths(node);
      // Exclude the node itself from the check to determine child state
      const childPaths = allPaths.slice(1);
      if (childPaths.length === 0) return isChecked(node.path);
      const selfChecked = isChecked(node.path);
      const checkedCount = childPaths.filter((p) => isChecked(p)).length;
      if (selfChecked && checkedCount === childPaths.length) return true;
      if (!selfChecked && checkedCount === 0) return false;
      return 'indeterminate';
    }
  };

  const handleCheckboxChange = (checked: boolean | 'indeterminate') => {
    // Determine target state: if indeterminate or unchecked, we want to check all; otherwise uncheck all
    const targetChecked = checked === true;

    if (type === 'context') {
      if (node.type === 'file') {
        onToggle(node.path);
      } else if (node.type === 'folder' && node.children) {
        // Recursively select/deselect all leaf files
        const leaves = getAllLeafFiles(node);
        for (const path of leaves) {
          if (targetChecked !== isChecked(path)) {
            onToggle(path);
          }
        }
      }
    } else {
      // For indexing/exclusion, toggle all paths recursively
      const allPaths = getAllPaths(node);
      for (const path of allPaths) {
        if (targetChecked !== isChecked(path)) {
          onToggle(path);
        }
      }
    }
  };

  const checkState = node.type === 'folder' ? getFolderCheckState() : isChecked(node.path);

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
            className="p-0.5 hover:bg-accent-foreground/10 rounded cursor-pointer"
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
          checked={checkState}
          onCheckedChange={handleCheckboxChange}
          className="h-4 w-4 cursor-pointer"
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
              type={type}
            />
          ))}
        </div>
      )}
    </div>
  );
}
