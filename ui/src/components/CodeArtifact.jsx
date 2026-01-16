import React, { useState } from 'react';
import {
  FileCode,
  Copy,
  Download,
  Check,
  ChevronDown,
  ChevronRight,
  Sparkles,
  GitBranch,
  Eye,
  EyeOff,
  Info,
  ExternalLink,
  Zap,
  BookOpen
} from 'lucide-react';

/**
 * CodeArtifact Component
 * 
 * Enhanced code display with:
 * - Syntax highlighting with line numbers
 * - Confidence badges and AI indicators
 * - Reasoning trace panel
 * - RAG source attribution
 * - Copy/download actions
 * - Diff view toggle
 */

// Confidence badge component
const ConfidenceBadge = ({ value }) => {
  const percentage = Math.round(value * 100);
  const color = percentage >= 90 ? 'emerald' :
                percentage >= 75 ? 'orange' :
                percentage >= 50 ? 'yellow' : 'red';
  
  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold bg-${color}-950 text-${color}-400 border border-${color}-800`}>
      <Zap size={10} />
      <span>{percentage}%</span>
    </div>
  );
};

// File type icon based on extension
const getFileIcon = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const iconMap = {
    'cls': '🔷', // Apex class
    'trigger': '⚡', // Apex trigger
    'js': '🟨', // JavaScript
    'jsx': '⚛️', // React
    'ts': '🔷', // TypeScript
    'tsx': '⚛️', // React TypeScript
    'py': '🐍', // Python
    'java': '☕', // Java
    'html': '🌐', // HTML
    'css': '🎨', // CSS
    'json': '📋', // JSON
    'xml': '📄', // XML
    'md': '📝', // Markdown
  };
  return iconMap[ext] || '📄';
};

// Language detection based on filename
const getLanguage = (filename) => {
  const ext = filename.split('.').pop()?.toLowerCase();
  const langMap = {
    'cls': 'apex',
    'trigger': 'apex',
    'js': 'javascript',
    'jsx': 'javascript',
    'ts': 'typescript',
    'tsx': 'typescript',
    'py': 'python',
    'java': 'java',
    'html': 'html',
    'css': 'css',
    'json': 'json',
    'xml': 'xml',
    'md': 'markdown',
  };
  return langMap[ext] || 'text';
};

// Reasoning trace panel
const ReasoningTrace = ({ trace, expanded, onToggle }) => {
  if (!trace || trace.length === 0) return null;

  return (
    <div className="border-t border-zinc-800">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Sparkles size={14} className="text-orange-500" />
          <span className="text-xs font-medium text-zinc-400">AI Reasoning</span>
          <span className="text-xs text-zinc-600">({trace.length} steps)</span>
        </div>
        {expanded ? <ChevronDown size={14} className="text-zinc-500" /> : <ChevronRight size={14} className="text-zinc-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {trace.map((step, index) => (
            <div key={index} className="flex items-start gap-3 text-xs">
              <span className="w-5 h-5 rounded-full bg-orange-600/20 text-orange-400 flex items-center justify-center shrink-0 font-mono">
                {index + 1}
              </span>
              <span className="text-zinc-400 leading-relaxed">{step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// RAG sources panel
const RAGSources = ({ sources, expanded, onToggle }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="border-t border-zinc-800">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <BookOpen size={14} className="text-blue-500" />
          <span className="text-xs font-medium text-zinc-400">Source References</span>
          <span className="text-xs text-zinc-600">({sources.length} files)</span>
        </div>
        {expanded ? <ChevronDown size={14} className="text-zinc-500" /> : <ChevronRight size={14} className="text-zinc-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {sources.map((source, index) => (
            <div key={index} className="flex items-center justify-between p-2 bg-zinc-950 rounded-lg">
              <div className="flex items-center gap-2 min-w-0">
                <FileCode size={12} className="text-zinc-500 shrink-0" />
                <span className="text-xs text-zinc-400 truncate">{source.file_path}</span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`text-xs font-mono ${
                  source.similarity_score >= 0.8 ? 'text-emerald-400' :
                  source.similarity_score >= 0.6 ? 'text-orange-400' :
                  'text-zinc-500'
                }`}>
                  {Math.round(source.similarity_score * 100)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Code line component with diff highlighting
const CodeLine = ({ lineNumber, content, type = 'context' }) => {
  const isAdded = type === 'add' || (content.startsWith('+') && !content.startsWith('+++'));
  const isRemoved = type === 'remove' || (content.startsWith('-') && !content.startsWith('---'));
  
  return (
    <div className={`flex ${
      isAdded ? 'bg-emerald-950/30' : 
      isRemoved ? 'bg-red-950/30' : 
      ''
    }`}>
      <span className="w-12 shrink-0 text-zinc-700 text-right pr-4 select-none text-xs py-0.5">
        {lineNumber}
      </span>
      <code className={`flex-1 text-xs py-0.5 ${
        isAdded ? 'text-emerald-400' : 
        isRemoved ? 'text-red-400' : 
        'text-zinc-400'
      }`}>
        {content || ' '}
      </code>
    </div>
  );
};

// Main CodeArtifact component
export default function CodeArtifact({
  filename,
  content,
  language,
  description,
  confidenceScore = 0,
  patternsUsed = [],
  reasoningTrace = [],
  ragSources = [],
  hasTests = false,
  testCoverageEstimate = null,
  complexityScore = null,
  showDiff = false,
  previousContent = null,
  className = ''
}) {
  const [copied, setCopied] = useState(false);
  const [showLineNumbers, setShowLineNumbers] = useState(true);
  const [reasoningExpanded, setReasoningExpanded] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [diffMode, setDiffMode] = useState(showDiff);

  const detectedLanguage = language || getLanguage(filename);
  const fileIcon = getFileIcon(filename);
  const lines = content?.split('\n') || [];

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className={`bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-xl ${className}`}>
      {/* Header */}
      <div className="bg-zinc-900/80 px-4 py-3 border-b border-zinc-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <span className="text-lg">{fileIcon}</span>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-zinc-200 text-sm font-medium truncate">{filename}</span>
                <span className="text-xs text-zinc-600 px-1.5 py-0.5 bg-zinc-800 rounded">
                  {detectedLanguage}
                </span>
              </div>
              {description && (
                <p className="text-xs text-zinc-500 mt-0.5 truncate">{description}</p>
              )}
            </div>
          </div>
          
          <div className="flex items-center gap-2 shrink-0">
            {/* Badges */}
            <div className="hidden sm:flex items-center gap-2">
              {confidenceScore > 0 && <ConfidenceBadge value={confidenceScore} />}
              
              <div className="flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-blue-950 text-blue-400 border border-blue-800">
                <Sparkles size={10} />
                <span>AI Generated</span>
              </div>
              
              {hasTests && (
                <div className="flex items-center gap-1 px-2 py-1 rounded-full text-xs bg-emerald-950 text-emerald-400 border border-emerald-800">
                  <Check size={10} />
                  <span>Tested</span>
                </div>
              )}
            </div>
            
            {/* Actions */}
            <div className="flex items-center gap-1 ml-2">
              <button
                onClick={() => setShowLineNumbers(!showLineNumbers)}
                className="p-2 rounded-lg hover:bg-zinc-800 transition-colors text-zinc-500 hover:text-zinc-300"
                title={showLineNumbers ? 'Hide line numbers' : 'Show line numbers'}
              >
                {showLineNumbers ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
              
              {previousContent && (
                <button
                  onClick={() => setDiffMode(!diffMode)}
                  className={`p-2 rounded-lg transition-colors ${
                    diffMode ? 'bg-orange-600/20 text-orange-400' : 'hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300'
                  }`}
                  title="Toggle diff view"
                >
                  <GitBranch size={14} />
                </button>
              )}
              
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors text-xs text-zinc-400 hover:text-zinc-200"
              >
                {copied ? <Check size={12} /> : <Copy size={12} />}
                {copied ? 'Copied!' : 'Copy'}
              </button>
              
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 transition-colors text-xs text-zinc-400 hover:text-zinc-200"
              >
                <Download size={12} />
                Download
              </button>
            </div>
          </div>
        </div>
        
        {/* Patterns and metrics row */}
        {(patternsUsed.length > 0 || testCoverageEstimate || complexityScore) && (
          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-zinc-800">
            {patternsUsed.length > 0 && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-600">Patterns:</span>
                <div className="flex gap-1">
                  {patternsUsed.map((pattern, i) => (
                    <span key={i} className="text-xs px-2 py-0.5 bg-zinc-800 text-zinc-400 rounded">
                      {pattern}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            {testCoverageEstimate && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-600">Coverage:</span>
                <span className="text-xs text-emerald-400 font-mono">{testCoverageEstimate}%</span>
              </div>
            )}
            
            {complexityScore && (
              <div className="flex items-center gap-2">
                <span className="text-xs text-zinc-600">Complexity:</span>
                <span className={`text-xs font-medium ${
                  complexityScore === 'low' ? 'text-emerald-400' :
                  complexityScore === 'medium' ? 'text-orange-400' :
                  'text-red-400'
                }`}>
                  {complexityScore}
                </span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Code content */}
      <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
        <pre className="text-xs leading-relaxed font-mono p-4">
          {lines.map((line, i) => (
            <CodeLine
              key={i}
              lineNumber={showLineNumbers ? i + 1 : null}
              content={line}
            />
          ))}
        </pre>
      </div>

      {/* Reasoning trace */}
      <ReasoningTrace
        trace={reasoningTrace}
        expanded={reasoningExpanded}
        onToggle={() => setReasoningExpanded(!reasoningExpanded)}
      />

      {/* RAG sources */}
      <RAGSources
        sources={ragSources}
        expanded={sourcesExpanded}
        onToggle={() => setSourcesExpanded(!sourcesExpanded)}
      />

      {/* Footer with stats */}
      <div className="px-4 py-2 bg-zinc-900/50 border-t border-zinc-800 flex items-center justify-between text-xs text-zinc-600">
        <span>{lines.length} lines</span>
        <span>{content?.length || 0} characters</span>
      </div>
    </div>
  );
}
