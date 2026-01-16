import React, { useState, useMemo } from 'react';
import {
  FileCode,
  GitBranch,
  Plus,
  Minus,
  ChevronDown,
  ChevronRight,
  Copy,
  Download,
  Eye,
  EyeOff,
  AlertTriangle,
  CheckCircle2,
  Lightbulb,
  Database,
  Zap,
  FileText
} from 'lucide-react';

/**
 * DiffViewer Component
 * 
 * Git-style unified diff viewer with:
 * - Syntax-highlighted diff rendering
 * - File grouping
 * - "Why this change" reasoning panel
 * - RAG source attribution
 * - Impact analysis sidebar
 */

// Parse unified diff into structured hunks
const parseDiff = (diffText) => {
  if (!diffText) return [];
  
  const files = [];
  const lines = diffText.split('\n');
  let currentFile = null;
  let currentHunk = null;
  
  for (const line of lines) {
    if (line.startsWith('diff --git')) {
      if (currentFile) files.push(currentFile);
      const match = line.match(/diff --git a\/(.+) b\/(.+)/);
      currentFile = {
        oldPath: match ? match[1] : 'unknown',
        newPath: match ? match[2] : 'unknown',
        hunks: [],
        additions: 0,
        deletions: 0
      };
      currentHunk = null;
    } else if (line.startsWith('@@')) {
      const match = line.match(/@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@(.*)?/);
      if (match && currentFile) {
        currentHunk = {
          oldStart: parseInt(match[1]),
          oldCount: parseInt(match[2]) || 1,
          newStart: parseInt(match[3]),
          newCount: parseInt(match[4]) || 1,
          header: match[5] || '',
          lines: []
        };
        currentFile.hunks.push(currentHunk);
      }
    } else if (currentHunk) {
      const type = line.startsWith('+') ? 'add' : line.startsWith('-') ? 'del' : 'context';
      currentHunk.lines.push({ content: line.slice(1) || '', type });
      if (type === 'add') currentFile.additions++;
      if (type === 'del') currentFile.deletions++;
    }
  }
  
  if (currentFile) files.push(currentFile);
  return files;
};

// Line component
const DiffLine = ({ line, lineNumber, type }) => {
  const bgColor = {
    add: 'bg-emerald-950/50',
    del: 'bg-red-950/50',
    context: 'bg-transparent'
  }[type];
  
  const textColor = {
    add: 'text-emerald-400',
    del: 'text-red-400',
    context: 'text-zinc-400'
  }[type];
  
  const prefix = {
    add: '+',
    del: '-',
    context: ' '
  }[type];
  
  return (
    <div className={`flex ${bgColor} hover:bg-zinc-800/50 transition-colors`}>
      <div className="w-12 shrink-0 text-right pr-2 text-xs text-zinc-600 select-none border-r border-zinc-800">
        {lineNumber}
      </div>
      <div className={`w-6 shrink-0 text-center text-xs ${textColor} select-none`}>
        {prefix}
      </div>
      <pre className={`flex-1 text-xs ${textColor} overflow-x-auto px-2`}>
        {line.content || ' '}
      </pre>
    </div>
  );
};

// File diff component
const FileDiff = ({ file, expanded, onToggle }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async (e) => {
    e.stopPropagation();
    const content = file.hunks.map(h => 
      h.lines.map(l => (l.type === 'add' ? '+' : l.type === 'del' ? '-' : ' ') + l.content).join('\n')
    ).join('\n');
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  return (
    <div className="border border-zinc-800 rounded-lg overflow-hidden">
      {/* File header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 bg-zinc-900/80 flex items-center gap-3 hover:bg-zinc-800/50 transition-colors"
      >
        <div className="shrink-0">
          {expanded ? 
            <ChevronDown size={16} className="text-zinc-500" /> : 
            <ChevronRight size={16} className="text-zinc-500" />
          }
        </div>
        
        <FileCode size={16} className="text-orange-500 shrink-0" />
        
        <span className="text-sm font-mono text-zinc-200 truncate flex-1 text-left">
          {file.newPath}
        </span>
        
        <div className="flex items-center gap-3 shrink-0">
          {file.additions > 0 && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <Plus size={12} />
              {file.additions}
            </span>
          )}
          {file.deletions > 0 && (
            <span className="text-xs text-red-400 flex items-center gap-1">
              <Minus size={12} />
              {file.deletions}
            </span>
          )}
          <button
            onClick={handleCopy}
            className="p-1 rounded hover:bg-zinc-700 transition-colors"
          >
            {copied ? <CheckCircle2 size={14} className="text-emerald-400" /> : <Copy size={14} className="text-zinc-500" />}
          </button>
        </div>
      </button>
      
      {/* Diff content */}
      {expanded && (
        <div className="bg-zinc-950 font-mono text-sm overflow-x-auto">
          {file.hunks.map((hunk, hunkIdx) => (
            <div key={hunkIdx}>
              {/* Hunk header */}
              <div className="px-4 py-1 bg-blue-950/30 text-blue-400 text-xs border-y border-zinc-800">
                @@ -{hunk.oldStart},{hunk.oldCount} +{hunk.newStart},{hunk.newCount} @@
                {hunk.header && <span className="text-zinc-500 ml-2">{hunk.header}</span>}
              </div>
              
              {/* Lines */}
              {hunk.lines.map((line, lineIdx) => {
                const lineNum = line.type === 'del' 
                  ? hunk.oldStart + hunk.lines.slice(0, lineIdx).filter(l => l.type !== 'add').length
                  : hunk.newStart + hunk.lines.slice(0, lineIdx).filter(l => l.type !== 'del').length;
                
                return (
                  <DiffLine
                    key={lineIdx}
                    line={line}
                    lineNumber={lineNum}
                    type={line.type}
                  />
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Reasoning trace panel
const ReasoningPanel = ({ reasoningTrace, ragSources, patternsApplied }) => {
  const [expanded, setExpanded] = useState(true);
  
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-zinc-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Lightbulb size={16} className="text-yellow-500" />
          <span className="text-sm font-medium text-zinc-200">Why This Change</span>
        </div>
        {expanded ? <ChevronDown size={16} className="text-zinc-500" /> : <ChevronRight size={16} className="text-zinc-500" />}
      </button>
      
      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* Reasoning steps */}
          {reasoningTrace && reasoningTrace.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-zinc-500 uppercase mb-2">Reasoning Steps</h4>
              <ol className="space-y-2">
                {reasoningTrace.map((step, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                    <span className="shrink-0 w-5 h-5 rounded-full bg-zinc-800 text-zinc-500 text-xs flex items-center justify-center">
                      {i + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          )}
          
          {/* RAG sources */}
          {ragSources && ragSources.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-zinc-500 uppercase mb-2 flex items-center gap-1">
                <Database size={12} />
                RAG Sources Used
              </h4>
              <div className="flex flex-wrap gap-2">
                {ragSources.map((source, i) => (
                  <span key={i} className="px-2 py-1 bg-purple-950/50 text-purple-400 text-xs rounded border border-purple-800">
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Patterns applied */}
          {patternsApplied && patternsApplied.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold text-zinc-500 uppercase mb-2 flex items-center gap-1">
                <GitBranch size={12} />
                Patterns Applied
              </h4>
              <div className="flex flex-wrap gap-2">
                {patternsApplied.map((pattern, i) => (
                  <span key={i} className="px-2 py-1 bg-blue-950/50 text-blue-400 text-xs rounded border border-blue-800">
                    {pattern}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Impact analysis panel
const ImpactPanel = ({ impactAnalysis }) => {
  const [expanded, setExpanded] = useState(true);
  
  if (!impactAnalysis) return null;
  
  const riskColors = {
    low: 'text-emerald-400 bg-emerald-950/50 border-emerald-800',
    medium: 'text-yellow-400 bg-yellow-950/50 border-yellow-800',
    high: 'text-red-400 bg-red-950/50 border-red-800'
  };
  
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-zinc-800/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle size={16} className="text-orange-500" />
          <span className="text-sm font-medium text-zinc-200">Impact Analysis</span>
        </div>
        {expanded ? <ChevronDown size={16} className="text-zinc-500" /> : <ChevronRight size={16} className="text-zinc-500" />}
      </button>
      
      {expanded && (
        <div className="px-4 pb-4 space-y-4">
          {/* Breaking change risk */}
          <div className="flex items-center justify-between">
            <span className="text-xs text-zinc-500">Breaking Change Risk</span>
            <span className={`px-2 py-0.5 text-xs font-semibold rounded border ${riskColors[impactAnalysis.breaking_change_risk || 'low']}`}>
              {(impactAnalysis.breaking_change_risk || 'low').toUpperCase()}
            </span>
          </div>
          
          {/* Affected classes */}
          {impactAnalysis.affected_classes?.length > 0 && (
            <div>
              <h4 className="text-xs text-zinc-500 mb-1">Affected Classes</h4>
              <div className="flex flex-wrap gap-1">
                {impactAnalysis.affected_classes.map((cls, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-xs font-mono rounded">
                    {cls}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Affected methods */}
          {impactAnalysis.affected_methods?.length > 0 && (
            <div>
              <h4 className="text-xs text-zinc-500 mb-1">Affected Methods</h4>
              <div className="flex flex-wrap gap-1">
                {impactAnalysis.affected_methods.map((method, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-xs font-mono rounded">
                    {method}()
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Affected tests */}
          {impactAnalysis.affected_tests?.length > 0 && (
            <div>
              <h4 className="text-xs text-zinc-500 mb-1">Tests to Update</h4>
              <div className="flex flex-wrap gap-1">
                {impactAnalysis.affected_tests.map((test, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-orange-950/50 text-orange-400 text-xs font-mono rounded border border-orange-800">
                    {test}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Migration notes */}
          {impactAnalysis.migration_notes?.length > 0 && (
            <div>
              <h4 className="text-xs text-zinc-500 mb-1">Migration Notes</h4>
              <ul className="space-y-1">
                {impactAnalysis.migration_notes.map((note, i) => (
                  <li key={i} className="text-xs text-zinc-400 flex items-start gap-1">
                    <span className="text-zinc-600">•</span>
                    {note}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Main DiffViewer component
export default function DiffViewer({
  diffContent = '',
  filesModified = [],
  hunks = [],
  reasoningTrace = [],
  ragSourcesUsed = [],
  patternsApplied = [],
  impactAnalysis = null,
  confidence = 0,
  className = ''
}) {
  const [expandedFiles, setExpandedFiles] = useState(new Set([0])); // First file expanded by default
  const [showReasoning, setShowReasoning] = useState(true);
  
  // Parse diff content
  const parsedFiles = useMemo(() => {
    if (diffContent) {
      return parseDiff(diffContent);
    }
    // If no diff content, create from hunks
    if (hunks.length > 0) {
      const fileMap = {};
      for (const hunk of hunks) {
        if (!fileMap[hunk.file]) {
          fileMap[hunk.file] = {
            oldPath: hunk.file,
            newPath: hunk.file,
            hunks: [],
            additions: 0,
            deletions: 0
          };
        }
        // Parse hunk content
        const lines = (hunk.content || '').split('\n').map(line => ({
          content: line.startsWith('+') || line.startsWith('-') ? line.slice(1) : line,
          type: line.startsWith('+') ? 'add' : line.startsWith('-') ? 'del' : 'context'
        }));
        fileMap[hunk.file].hunks.push({
          oldStart: hunk.old_start || 1,
          oldCount: hunk.old_count || 0,
          newStart: hunk.new_start || 1,
          newCount: hunk.new_count || 0,
          header: hunk.description || '',
          lines
        });
        fileMap[hunk.file].additions += lines.filter(l => l.type === 'add').length;
        fileMap[hunk.file].deletions += lines.filter(l => l.type === 'del').length;
      }
      return Object.values(fileMap);
    }
    return [];
  }, [diffContent, hunks]);
  
  // Toggle file expansion
  const toggleFile = (index) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedFiles(newExpanded);
  };
  
  // Calculate totals
  const totalAdditions = parsedFiles.reduce((sum, f) => sum + f.additions, 0);
  const totalDeletions = parsedFiles.reduce((sum, f) => sum + f.deletions, 0);
  
  // Download as patch
  const handleDownload = () => {
    const content = diffContent || parsedFiles.map(f => 
      `diff --git a/${f.oldPath} b/${f.newPath}\n` +
      f.hunks.map(h => 
        `@@ -${h.oldStart},${h.oldCount} +${h.newStart},${h.newCount} @@${h.header ? ' ' + h.header : ''}\n` +
        h.lines.map(l => (l.type === 'add' ? '+' : l.type === 'del' ? '-' : ' ') + l.content).join('\n')
      ).join('\n')
    ).join('\n');
    
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'changes.patch';
    a.click();
    URL.revokeObjectURL(url);
  };
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h3 className="text-lg font-semibold text-zinc-200 flex items-center gap-2">
            <GitBranch size={20} className="text-orange-500" />
            Code Changes
          </h3>
          
          <div className="flex items-center gap-3 text-sm">
            <span className="text-zinc-500">{parsedFiles.length} files</span>
            <span className="text-emerald-400 flex items-center gap-1">
              <Plus size={14} />
              {totalAdditions}
            </span>
            <span className="text-red-400 flex items-center gap-1">
              <Minus size={14} />
              {totalDeletions}
            </span>
          </div>
          
          {confidence > 0 && (
            <div className="flex items-center gap-1 px-2 py-1 bg-orange-950/50 border border-orange-800 rounded-full">
              <Zap size={12} className="text-orange-400" />
              <span className="text-xs font-semibold text-orange-400">
                {Math.round(confidence * 100)}% Confidence
              </span>
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowReasoning(!showReasoning)}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              showReasoning 
                ? 'bg-yellow-950/50 text-yellow-400 border border-yellow-800' 
                : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
            }`}
          >
            {showReasoning ? <Eye size={14} /> : <EyeOff size={14} />}
            Why This Change
          </button>
          
          <button
            onClick={handleDownload}
            className="flex items-center gap-1 px-3 py-1.5 bg-zinc-800 text-zinc-300 rounded-lg text-xs font-medium hover:bg-zinc-700 transition-colors border border-zinc-700"
          >
            <Download size={14} />
            Download Patch
          </button>
        </div>
      </div>
      
      {/* Main content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Diff viewer */}
        <div className={`space-y-3 ${showReasoning ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          {parsedFiles.length > 0 ? (
            parsedFiles.map((file, index) => (
              <FileDiff
                key={index}
                file={file}
                expanded={expandedFiles.has(index)}
                onToggle={() => toggleFile(index)}
              />
            ))
          ) : (
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 text-center">
              <FileText size={32} className="mx-auto mb-3 text-zinc-600" />
              <p className="text-zinc-500">No diff content available</p>
            </div>
          )}
        </div>
        
        {/* Reasoning sidebar */}
        {showReasoning && (
          <div className="space-y-4">
            <ReasoningPanel
              reasoningTrace={reasoningTrace}
              ragSources={ragSourcesUsed}
              patternsApplied={patternsApplied}
            />
            <ImpactPanel impactAnalysis={impactAnalysis} />
          </div>
        )}
      </div>
    </div>
  );
}
