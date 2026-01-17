import React, { useState, useCallback } from 'react';
import api from './api';
import { DiffViewer, OutputBundle, WorkflowVisualizer, CodeArtifact, TestSuiteMatrix, TraceabilityMatrix } from './components';
import {
  Layers,
  Copy,
  Download,
  CheckSquare,
  Square,
  FileSearch,
  Code2,
  TestTube2,
  CheckCircle2,
  Zap,
  Activity,
  AlertTriangle,
  Hash,
  ShieldCheck,
  Clock,
  ChevronDown,
  ChevronRight,
  ArrowLeft,
  RefreshCw,
  Github,
  FileCode,
  Terminal,
  Loader2,
  X,
  Check,
  ExternalLink,
  Play,
  Settings,
  Eye,
  Sparkles
} from 'lucide-react';

// Toast notification component
const Toast = ({ message, type, onClose }) => (
  <div className={`fixed top-4 right-4 z-[100] animate-in slide-in-from-top-2 duration-300 flex items-center gap-3 px-4 py-3 rounded-lg shadow-2xl border ${
    type === 'success' ? 'bg-emerald-950 border-emerald-800 text-emerald-300' :
    type === 'error' ? 'bg-red-950 border-red-800 text-red-300' :
    'bg-zinc-900 border-zinc-700 text-zinc-300'
  }`}>
    {type === 'success' && <Check size={16} />}
    {type === 'error' && <X size={16} />}
    <span className="text-sm font-medium">{message}</span>
    <button onClick={onClose} className="ml-2 hover:opacity-70"><X size={14} /></button>
  </div>
);

// Loading spinner
const Spinner = ({ size = 20, className = '' }) => (
  <Loader2 size={size} className={`animate-spin ${className}`} />
);

// Header component with back button
const Header = ({ showBack, onBack, status }) => (
  <header className="border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-xl sticky top-0 z-50 px-6 py-3 flex items-center justify-between">
    <div className="flex items-center gap-4">
      {showBack && (
        <button 
          onClick={onBack}
          className="p-2 hover:bg-zinc-800 rounded-lg transition-colors mr-2"
        >
          <ArrowLeft size={18} className="text-zinc-400" />
        </button>
      )}
      <div className="bg-gradient-to-br from-orange-500 to-orange-700 rounded-lg p-2 shadow-lg shadow-orange-900/30">
        <Layers className="text-white w-5 h-5" />
      </div>
      <div>
        <h1 className="font-bold text-zinc-100 text-sm tracking-wide">AI SDLC Agent</h1>
        <p className="text-[10px] text-zinc-500 font-medium">Intelligent Code Analysis Pipeline</p>
      </div>
    </div>
    <div className="flex gap-3 items-center">
      {status && (
        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-[11px] font-semibold ${
          status === 'running' ? 'bg-orange-950/50 text-orange-400 border border-orange-800' :
          status === 'completed' ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-800' :
          status === 'error' ? 'bg-red-950/50 text-red-400 border border-red-800' :
          'bg-zinc-900 text-zinc-400 border border-zinc-800'
        }`}>
          {status === 'running' && <Spinner size={12} />}
          {status === 'completed' && <CheckCircle2 size={12} />}
          {status === 'error' && <AlertTriangle size={12} />}
          <span className="capitalize">{status}</span>
        </div>
      )}
    </div>
  </header>
);

// Code block with copy/download
const CodeBlock = ({ code, title, language = 'python' }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = title || 'code.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-xl">
      <div className="bg-zinc-900/80 px-4 py-2.5 border-b border-zinc-800 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <FileCode size={14} className="text-orange-500" />
          <span className="text-zinc-400 text-xs font-medium">{title}</span>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 transition-colors text-xs text-zinc-400 hover:text-zinc-200"
          >
            {copied ? <Check size={12} /> : <Copy size={12} />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button 
            onClick={handleDownload}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 transition-colors text-xs text-zinc-400 hover:text-zinc-200"
          >
            <Download size={12} />
            Download
          </button>
        </div>
      </div>
      <div className="p-4 overflow-x-auto max-h-[500px] overflow-y-auto">
        <pre className="text-xs leading-relaxed font-mono">
          {code.split('\n').map((line, i) => {
            const isAdded = line.startsWith('+') && !line.startsWith('+++');
            const isRemoved = line.startsWith('-') && !line.startsWith('---');
            return (
              <div key={i} className={`flex ${isAdded ? 'bg-emerald-950/30' : isRemoved ? 'bg-red-950/30' : ''}`}>
                <span className="w-10 shrink-0 text-zinc-700 text-right pr-4 select-none">{i + 1}</span>
                <code className={`${isAdded ? 'text-emerald-400' : isRemoved ? 'text-red-400' : 'text-zinc-400'}`}>
                  {line || ' '}
                </code>
              </div>
            );
          })}
        </pre>
      </div>
    </div>
  );
};

// Stats card
const StatCard = ({ icon: Icon, label, value, subtext }) => (
  <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
    <div className="flex items-center gap-3 mb-3">
      <div className="p-2 bg-orange-600/10 rounded-lg">
        <Icon size={16} className="text-orange-500" />
      </div>
      <span className="text-[11px] font-semibold text-zinc-500 uppercase tracking-wider">{label}</span>
    </div>
    <div className="text-2xl font-bold text-white">{value}</div>
    {subtext && <div className="text-xs text-zinc-600 mt-1">{subtext}</div>}
  </div>
);

// Agent card for selection
const AgentCard = ({ agent, selected, onToggle }) => (
  <button
    onClick={onToggle}
    className={`relative p-5 rounded-xl border-2 transition-all text-left w-full group ${
      selected 
        ? 'bg-orange-600/10 border-orange-600 shadow-lg shadow-orange-900/20' 
        : 'bg-zinc-900/30 border-zinc-800 hover:border-zinc-700'
    }`}
  >
    <div className="flex items-start gap-4">
      <div className={`p-3 rounded-xl ${selected ? 'bg-orange-600 text-white' : 'bg-zinc-800 text-zinc-400'}`}>
        <agent.icon size={22} />
      </div>
      <div className="flex-1">
        <h4 className={`font-semibold text-sm mb-1 ${selected ? 'text-orange-300' : 'text-zinc-300'}`}>
          {agent.name}
        </h4>
        <p className="text-xs text-zinc-500 leading-relaxed">{agent.desc}</p>
      </div>
      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
        selected ? 'bg-orange-600 border-orange-600' : 'border-zinc-600'
      }`}>
        {selected && <Check size={12} className="text-white" />}
      </div>
    </div>
  </button>
);

// Execution step indicator
const ExecutionStep = ({ agent, status, isActive, result }) => (
  <div className={`p-4 rounded-xl border transition-all ${
    status === 'completed' ? 'bg-emerald-950/20 border-emerald-800/50' :
    isActive ? 'bg-orange-950/20 border-orange-600 shadow-lg shadow-orange-900/20' :
    status === 'error' ? 'bg-red-950/20 border-red-800' :
    'bg-zinc-900/30 border-zinc-800 opacity-50'
  }`}>
    <div className="flex items-center gap-4">
      <div className={`p-2.5 rounded-xl ${
        status === 'completed' ? 'bg-emerald-600 text-white' :
        isActive ? 'bg-orange-600 text-white' :
        status === 'error' ? 'bg-red-600 text-white' :
        'bg-zinc-800 text-zinc-500'
      }`}>
        {status === 'completed' ? <CheckCircle2 size={20} /> :
         isActive ? <Spinner size={20} /> :
         <agent.icon size={20} />}
      </div>
      <div className="flex-1">
        <h4 className="font-semibold text-sm text-zinc-200">{agent.name}</h4>
        <p className="text-xs text-zinc-500 mt-0.5">
          {status === 'completed' ? 'Completed successfully' :
           isActive ? 'Processing...' :
           status === 'error' ? 'Failed' :
           'Waiting...'}
        </p>
      </div>
      {result && (
        <div className="text-right">
          <div className="text-xs text-zinc-500">Output</div>
          <div className="text-sm font-mono text-zinc-300">
            {Object.entries(result).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(', ')}
          </div>
        </div>
      )}
    </div>
  </div>
);

// Available OpenAI models - organized by capability tier
const OPENAI_MODELS = [
  // GPT-5.2 Series (Latest)
  { id: 'gpt-5.2', name: 'GPT-5.2', description: 'Latest & most capable' },
  { id: 'gpt-5.2-chat-latest', name: 'GPT-5.2 Chat', description: 'Latest chat model' },
  { id: 'gpt-5.2-codex', name: 'GPT-5.2 Codex', description: 'Code generation' },
  { id: 'gpt-5.2-pro', name: 'GPT-5.2 Pro', description: 'Premium tier' },
  
  // GPT-5.1 Series
  { id: 'gpt-5.1', name: 'GPT-5.1', description: 'Advanced capabilities' },
  { id: 'gpt-5.1-chat-latest', name: 'GPT-5.1 Chat', description: 'Chat optimized' },
  { id: 'gpt-5.1-codex', name: 'GPT-5.1 Codex', description: 'Code generation' },
  { id: 'gpt-5.1-codex-max', name: 'GPT-5.1 Codex Max', description: 'Max code context' },
  
  // GPT-5 Series
  { id: 'gpt-5', name: 'GPT-5', description: 'Next generation' },
  { id: 'gpt-5-chat-latest', name: 'GPT-5 Chat', description: 'Chat optimized' },
  { id: 'gpt-5-codex', name: 'GPT-5 Codex', description: 'Code generation' },
  { id: 'gpt-5-pro', name: 'GPT-5 Pro', description: 'Premium tier' },
  { id: 'gpt-5-mini', name: 'GPT-5 Mini', description: 'Fast & efficient' },
  { id: 'gpt-5-nano', name: 'GPT-5 Nano', description: 'Ultra-fast, low cost' },
  
  // GPT-4.1 Series
  { id: 'gpt-4.1', name: 'GPT-4.1', description: 'Enhanced GPT-4' },
  { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', description: 'Fast & affordable' },
  { id: 'gpt-4.1-nano', name: 'GPT-4.1 Nano', description: 'Ultra-fast' },
  
  // GPT-4o Series
  { id: 'gpt-4o', name: 'GPT-4o', description: 'Multimodal, fast' },
  { id: 'gpt-4o-2024-05-13', name: 'GPT-4o (May 2024)', description: 'Stable release' },
  { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Fast & affordable' },
];

export default function App() {
  // View state
  const [view, setView] = useState('input'); // input | executing | result
  
  // Form data
  const [formData, setFormData] = useState({
    jiraId: '',
    repoUrl: '',
    actions: ['req', 'code', 'test'],
    model: 'gpt-4o'
  });
  
  // API response and execution state
  const [apiResponse, setApiResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [executionStatus, setExecutionStatus] = useState('idle');
  const [currentAgent, setCurrentAgent] = useState(null);
  const [error, setError] = useState(null);
  
  // UI state
  const [activeTab, setActiveTab] = useState('requirements');
  const [toast, setToast] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileContent, setFileContent] = useState(null);
  const [loadingFile, setLoadingFile] = useState(false);

  // Agent definitions
  const agents = [
    { 
      id: 'req', 
      name: 'Requirement Analyzer', 
      icon: FileSearch, 
      desc: 'Extracts structured requirements, edge cases, and acceptance criteria from your codebase and tickets.'
    },
    { 
      id: 'code', 
      name: 'Code Generator', 
      icon: Code2, 
      desc: 'Generates production-ready code based on analyzed requirements with best practices.'
    },
    { 
      id: 'test', 
      name: 'Test Generator', 
      icon: TestTube2, 
      desc: 'Creates comprehensive test suites with boundary testing and edge case coverage.'
    },
  ];

  // Show toast
  const showToast = (message, type = 'info') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Toggle agent selection
  const toggleAgent = (agentId) => {
    setFormData(prev => ({
      ...prev,
      actions: prev.actions.includes(agentId)
        ? prev.actions.filter(a => a !== agentId)
        : [...prev.actions, agentId]
    }));
  };

  // Run the pipeline
  const runPipeline = async () => {
    if ((!formData.jiraId && !formData.repoUrl) || formData.actions.length === 0) {
      showToast('Please provide input and select at least one agent', 'error');
      return;
    }

    setView('executing');
    setIsLoading(true);
    setExecutionStatus('running');
    setError(null);

    // Determine action based on selected agents
    let action = 'analyze_requirements';
    const { actions } = formData;
    if (actions.includes('req') && actions.includes('code') && actions.includes('test')) {
      action = 'full_pipeline';
    } else if (actions.includes('req') && actions.includes('code')) {
      action = 'generate_code'; // Will run req + code
    } else if (actions.includes('req') && actions.includes('test')) {
      action = 'generate_tests'; // Will run req + test (skipping code)
    } else if (actions.includes('code') && actions.includes('test')) {
      action = 'full_pipeline'; // Need full pipeline for code + test
    } else if (actions.includes('code')) {
      action = 'generate_code';
    } else if (actions.includes('test')) {
      action = 'generate_tests';
    } else if (actions.includes('req')) {
      action = 'analyze_requirements';
    }

    // Simulate agent execution progress
    const selectedAgents = agents.filter(a => actions.includes(a.id));
    for (const agent of selectedAgents) {
      setCurrentAgent(agent.id);
      await new Promise(r => setTimeout(r, 500)); // Small delay for UI feedback
    }

    try {
      const response = await api.analyzeTicket({
        ticket_id: formData.jiraId || `MANUAL-${Date.now()}`,
        action,
        github_repo: formData.repoUrl || undefined,
        model: formData.model
      });

      setApiResponse(response);
      setExecutionStatus('completed');
      setCurrentAgent(null);
      setView('result');
      showToast('Pipeline completed successfully!', 'success');
    } catch (err) {
      setError(err.message || 'Pipeline execution failed');
      setExecutionStatus('error');
      showToast(err.message || 'Pipeline execution failed', 'error');
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch file content
  const fetchFile = async (path) => {
    if (!formData.repoUrl) return;
    setLoadingFile(true);
    setSelectedFile(path);
    try {
      const normalizeRepo = (r) => {
        try {
          const u = new URL(r);
          const parts = u.pathname.replace(/^\/+|\/+$/g, '').split('/');
          if (parts.length >= 2) return `${parts[0]}/${parts[1]}`;
        } catch (e) {}
        return r;
      };
      const repo = normalizeRepo(formData.repoUrl);
      const data = await api.getRepoFile(repo, path);
      setFileContent(data.content || '');
    } catch (e) {
      setFileContent(`Error loading file: ${e.message}`);
    } finally {
      setLoadingFile(false);
    }
  };

  // Reset and go back
  const handleBack = () => {
    if (view === 'executing' && isLoading) {
      if (!confirm('Pipeline is running. Are you sure you want to cancel?')) return;
    }
    setView('input');
    setApiResponse(null);
    setExecutionStatus('idle');
    setCurrentAgent(null);
    setError(null);
    setActiveTab('requirements');
  };

  // Start new analysis
  const startNew = () => {
    setFormData({ jiraId: '', repoUrl: '', actions: ['req', 'code', 'test'], model: 'gpt-4o' });
    handleBack();
  };

  // Copy all artifacts
  const copyAllArtifacts = async () => {
    const artifacts = {
      requirements: apiResponse?.requirements,
      code: apiResponse?.generated_code,
      tests: apiResponse?.generated_tests
    };
    await navigator.clipboard.writeText(JSON.stringify(artifacts, null, 2));
    showToast('All artifacts copied to clipboard!', 'success');
  };

  // Download bundle
  const downloadBundle = () => {
    const bundle = {
      metadata: {
        request_id: apiResponse?.request_id,
        ticket_id: apiResponse?.ticket_id,
        timestamp: new Date().toISOString()
      },
      requirements: apiResponse?.requirements,
      generated_code: apiResponse?.generated_code,
      generated_tests: apiResponse?.generated_tests,
      agents: apiResponse?.agents
    };
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sdlc-bundle-${apiResponse?.request_id || 'export'}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Bundle downloaded!', 'success');
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-zinc-950 to-black text-zinc-100 font-sans">
      {toast && <Toast {...toast} onClose={() => setToast(null)} />}
      
      <Header 
        showBack={view !== 'input'} 
        onBack={handleBack}
        status={view === 'executing' ? executionStatus : view === 'result' ? 'completed' : null}
      />

      <main className="max-w-6xl mx-auto py-8 px-6 pb-20">
        
        {/* INPUT VIEW */}
        {view === 'input' && (
          <div className="max-w-2xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Hero */}
            <div className="text-center space-y-4 py-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600/10 border border-orange-800/50 rounded-full text-orange-400 text-sm font-medium mb-4">
                <Sparkles size={14} />
                AI-Powered Analysis
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight">
                AI SDLC Agent
              </h1>
              <p className="text-zinc-400 text-lg max-w-md mx-auto">
                Analyze repositories, extract requirements, generate code, and create comprehensive tests.
              </p>
            </div>

            {/* Input Form */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8 space-y-8 shadow-xl">
              {/* Input Section */}
              <div className="space-y-6">
                <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
                  <Settings size={16} className="text-orange-500" />
                  Configuration
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="text-xs font-medium text-zinc-400 mb-2 block">
                      GitHub Repository URL
                    </label>
                    <div className="relative">
                      <Github size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600" />
                      <input
                        type="text"
                        value={formData.repoUrl}
                        onChange={(e) => setFormData({ ...formData, repoUrl: e.target.value })}
                        placeholder="https://github.com/owner/repo"
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-orange-600/50 focus:border-orange-600 transition-all text-zinc-200 placeholder:text-zinc-700"
                      />
                    </div>
                  </div>
                  
                  <div>
                    <label className="text-xs font-medium text-zinc-400 mb-2 block">
                      Jira Ticket ID <span className="text-zinc-600">(Optional)</span>
                    </label>
                    <div className="relative">
                      <Hash size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-600" />
                      <input
                        type="text"
                        value={formData.jiraId}
                        onChange={(e) => setFormData({ ...formData, jiraId: e.target.value })}
                        placeholder="PROJ-123"
                        className="w-full bg-zinc-950 border border-zinc-800 rounded-xl pl-12 pr-4 py-3.5 focus:outline-none focus:ring-2 focus:ring-orange-600/50 focus:border-orange-600 transition-all text-zinc-200 placeholder:text-zinc-700"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Agent Selection */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-zinc-300 flex items-center gap-2">
                  <Zap size={16} className="text-orange-500" />
                  Select Agents
                </h3>
                <div className="space-y-3">
                  {agents.map(agent => (
                    <AgentCard
                      key={agent.id}
                      agent={agent}
                      selected={formData.actions.includes(agent.id)}
                      onToggle={() => toggleAgent(agent.id)}
                    />
                  ))}
                </div>
              </div>

              {/* Model Selection & Run Button */}
              <div className="flex gap-3 items-stretch">
                {/* Model Dropdown */}
                <div className="relative">
                  <select
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    className="h-full appearance-none bg-zinc-950 border border-zinc-800 rounded-xl pl-4 pr-10 py-4 focus:outline-none focus:ring-2 focus:ring-orange-600/50 focus:border-orange-600 transition-all text-zinc-200 text-sm font-medium cursor-pointer hover:border-zinc-700"
                  >
                    {OPENAI_MODELS.map(model => (
                      <option key={model.id} value={model.id}>
                        {model.name}
                      </option>
                    ))}
                  </select>
                  <ChevronDown size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 pointer-events-none" />
                </div>
                
                {/* Run Button */}
                <button
                  onClick={runPipeline}
                  disabled={(!formData.jiraId && !formData.repoUrl) || formData.actions.length === 0}
                  className="flex-1 bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-500 hover:to-orange-400 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 text-white font-semibold py-4 rounded-xl transition-all shadow-lg shadow-orange-900/30 disabled:shadow-none flex items-center justify-center gap-3"
                >
                  <Play size={18} />
                  Run Analysis Pipeline
                </button>
              </div>
            </div>
          </div>
        )}

        {/* EXECUTING VIEW */}
        {view === 'executing' && (
          <div className="max-w-2xl mx-auto space-y-8 animate-in fade-in duration-500">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-white">Running Pipeline</h2>
              <p className="text-zinc-500">
                Analyzing <span className="text-orange-400 font-medium">{formData.repoUrl || formData.jiraId}</span>
              </p>
            </div>

            <div className="space-y-4">
              {agents.filter(a => formData.actions.includes(a.id)).map(agent => {
                const agentResult = apiResponse?.agents?.find(a => 
                  a.agent_name.toLowerCase().includes(agent.id)
                );
                const isCompleted = agentResult?.status === 'completed';
                const isActive = currentAgent === agent.id && !isCompleted;
                
                return (
                  <ExecutionStep
                    key={agent.id}
                    agent={agent}
                    status={isCompleted ? 'completed' : isActive ? 'running' : 'pending'}
                    isActive={isActive}
                    result={agentResult?.result}
                  />
                );
              })}
            </div>

            {error && (
              <div className="bg-red-950/30 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle size={16} />
                  <span className="font-semibold">Error</span>
                </div>
                {error}
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={handleBack}
                className="flex-1 py-3 border border-zinc-700 rounded-xl text-zinc-400 hover:text-zinc-200 hover:border-zinc-600 transition-colors flex items-center justify-center gap-2"
              >
                <ArrowLeft size={16} />
                Cancel
              </button>
            </div>
          </div>
        )}

        {/* RESULT VIEW */}
        {view === 'result' && apiResponse && (
          <div className="space-y-8 animate-in fade-in duration-500">
            {/* Result Header */}
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-2xl p-8">
              <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-6">
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <span className="flex items-center gap-1.5 text-xs font-medium text-zinc-500">
                      <Hash size={12} /> {apiResponse.request_id}
                    </span>
                    <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-400">
                      <CheckCircle2 size={12} /> Completed
                    </span>
                  </div>
                  <h2 className="text-3xl font-bold text-white mb-2">
                    Analysis Results
                  </h2>
                  <p className="text-zinc-500">
                    {formData.repoUrl || formData.jiraId}
                  </p>
                </div>
                <div className="flex gap-3 w-full lg:w-auto">
                  <button
                    onClick={downloadBundle}
                    className="flex-1 lg:flex-none px-5 py-3 bg-zinc-800 hover:bg-zinc-700 rounded-xl text-sm font-medium text-zinc-300 flex items-center justify-center gap-2 transition-colors"
                  >
                    <Download size={16} />
                    Download
                  </button>
                  <button
                    onClick={copyAllArtifacts}
                    className="flex-1 lg:flex-none px-5 py-3 bg-orange-600 hover:bg-orange-500 rounded-xl text-sm font-medium text-white flex items-center justify-center gap-2 transition-colors"
                  >
                    <Copy size={16} />
                    Copy All
                  </button>
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                icon={FileSearch}
                label="Requirements"
                value={apiResponse.requirements?.length || 0}
                subtext="Extracted"
              />
              <StatCard
                icon={Code2}
                label="Code Lines"
                value={apiResponse.generated_code?.split('\n').length || 0}
                subtext="Generated"
              />
              <StatCard
                icon={TestTube2}
                label="Tests"
                value={apiResponse.agents?.find(a => a.agent_name === 'TestGenerator')?.result?.tests_generated || 0}
                subtext="Created"
              />
              <StatCard
                icon={Activity}
                label="Confidence"
                value={`${Math.round((apiResponse.agents?.[0]?.result?.confidence || 0.85) * 100)}%`}
                subtext="Score"
              />
            </div>

            {/* Tabs */}
            <div className="border-b border-zinc-800">
              <nav className="flex gap-1 overflow-x-auto">
                {[
                  { id: 'requirements', label: 'Requirements', icon: FileSearch },
                  { id: 'code', label: 'Generated Code', icon: Code2 },
                  { id: 'tests', label: 'Test Suite', icon: TestTube2 },
                  { id: 'traceability', label: 'Traceability', icon: Layers },
                  { id: 'workflow', label: 'Workflow', icon: Activity },
                  { id: 'summary', label: 'Summary', icon: Activity }
                ].map(tab => (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-5 py-3 text-sm font-medium rounded-t-lg transition-colors flex items-center gap-2 ${
                      activeTab === tab.id
                        ? 'bg-zinc-900 text-orange-400 border-t border-l border-r border-zinc-800'
                        : 'text-zinc-500 hover:text-zinc-300'
                    }`}
                  >
                    <tab.icon size={14} />
                    {tab.label}
                  </button>
                ))}
              </nav>
            </div>

            {/* Tab Content */}
            <div className="min-h-[400px]">
              {/* Requirements Tab */}
              {activeTab === 'requirements' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in duration-300">
                  <div className="lg:col-span-2 space-y-6">
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                      <div className="px-5 py-4 border-b border-zinc-800 flex justify-between items-center">
                        <h3 className="font-semibold text-zinc-200">Extracted Requirements</h3>
                        <span className="text-xs bg-zinc-800 px-2 py-1 rounded text-zinc-400">
                          {apiResponse.requirements?.length || 0} items
                        </span>
                      </div>
                      <div className="divide-y divide-zinc-800">
                        {(apiResponse.requirements || []).map((req, idx) => (
                          <div key={req.id || idx} className="p-5 hover:bg-zinc-800/30 transition-colors">
                            <div className="flex items-start gap-4">
                              <span className={`px-2 py-1 rounded text-[10px] font-bold uppercase ${
                                req.type === 'functional' ? 'bg-blue-950 text-blue-400' :
                                req.type === 'non-functional' ? 'bg-purple-950 text-purple-400' :
                                'bg-zinc-800 text-zinc-400'
                              }`}>
                                {req.type || 'REQ'}
                              </span>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-mono text-orange-500 text-sm">{req.id}</span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    req.priority === 'high' ? 'bg-red-950 text-red-400' :
                                    req.priority === 'medium' ? 'bg-yellow-950 text-yellow-400' :
                                    'bg-zinc-800 text-zinc-400'
                                  }`}>
                                    {req.priority || 'medium'}
                                  </span>
                                </div>
                                <p className="text-zinc-300 text-sm leading-relaxed">{req.description}</p>
                                {req.acceptance_criteria && req.acceptance_criteria.length > 0 && (
                                  <div className="mt-3 space-y-1">
                                    {req.acceptance_criteria.map((ac, i) => (
                                      <div key={i} className="flex items-center gap-2 text-xs text-zinc-500">
                                        <CheckSquare size={12} className="text-emerald-500" />
                                        {ac}
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        ))}
                        {(!apiResponse.requirements || apiResponse.requirements.length === 0) && (
                          <div className="p-8 text-center text-zinc-600">
                            No requirements extracted
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="space-y-6">
                    {/* Edge Cases */}
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                      <h4 className="font-semibold text-zinc-300 mb-4 flex items-center gap-2">
                        <AlertTriangle size={14} className="text-orange-500" />
                        Edge Cases
                      </h4>
                      <div className="space-y-2">
                        {(apiResponse.requirements?.flatMap(r => r.edge_cases || []) || []).slice(0, 5).map((ec, i) => (
                          <div key={i} className="text-sm text-zinc-400 pl-3 border-l-2 border-orange-600/50">
                            {ec}
                          </div>
                        ))}
                        {!apiResponse.requirements?.some(r => r.edge_cases?.length) && (
                          <p className="text-sm text-zinc-600">No edge cases identified</p>
                        )}
                      </div>
                    </div>

                    {/* Acceptance Criteria */}
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                      <h4 className="font-semibold text-zinc-300 mb-4 flex items-center gap-2">
                        <CheckCircle2 size={14} className="text-emerald-500" />
                        Acceptance Criteria
                      </h4>
                      <div className="space-y-2">
                        {(apiResponse.requirements?.flatMap(r => r.acceptance_criteria || []) || []).slice(0, 5).map((ac, i) => (
                          <div key={i} className="flex items-start gap-2 text-sm text-zinc-400">
                            <Check size={14} className="text-emerald-500 mt-0.5 shrink-0" />
                            {ac}
                          </div>
                        ))}
                        {!apiResponse.requirements?.some(r => r.acceptance_criteria?.length) && (
                          <p className="text-sm text-zinc-600">No criteria listed</p>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Code Tab */}
              {activeTab === 'code' && (
                <div className="animate-in fade-in duration-300">
                  {/* Use DiffViewer for unified diffs, otherwise CodeArtifact */}
                  {apiResponse.generated_code && (apiResponse.generated_code.startsWith('diff --git') || apiResponse.generated_code.includes('@@')) ? (
                    <DiffViewer
                      diffContent={apiResponse.generated_code}
                      filesModified={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.files_generated || []}
                      reasoningTrace={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.reasoning_trace || []}
                      patternsApplied={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.patterns_used || []}
                      confidence={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.confidence || 0}
                    />
                  ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      <div className="lg:col-span-2">
                        <CodeArtifact
                          content={apiResponse.generated_code || '# No code generated'}
                          filename="generated_code.py"
                          language="python"
                          confidenceScore={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.confidence || 0}
                          patternsUsed={apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.patterns_used || []}
                        />
                      </div>
                  <div className="space-y-6">
                    {/* Files from repo */}
                    {apiResponse.github_files && apiResponse.github_files.length > 0 && (
                      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                        <h4 className="font-semibold text-zinc-300 mb-4 flex items-center gap-2">
                          <Github size={14} className="text-zinc-400" />
                          Repository Files
                        </h4>
                        <div className="space-y-1 max-h-60 overflow-y-auto">
                          {apiResponse.github_files.map((f, i) => (
                            <button
                              key={i}
                              onClick={() => fetchFile(f.path || f.name)}
                              className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-center justify-between group transition-colors ${
                                selectedFile === (f.path || f.name) ? 'bg-orange-600/20 text-orange-300' : 'hover:bg-zinc-800 text-zinc-400'
                              }`}
                            >
                              <span className="truncate flex items-center gap-2">
                                <FileCode size={12} />
                                {f.path || f.name}
                              </span>
                              {loadingFile && selectedFile === (f.path || f.name) ? (
                                <Spinner size={12} />
                              ) : (
                                <Eye size={12} className="opacity-0 group-hover:opacity-100" />
                              )}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Selected file content */}
                    {fileContent && (
                      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                        <div className="px-4 py-3 border-b border-zinc-800 flex items-center justify-between">
                          <span className="text-sm text-zinc-400 truncate">{selectedFile}</span>
                          <button onClick={() => { setFileContent(null); setSelectedFile(null); }}>
                            <X size={14} className="text-zinc-600 hover:text-zinc-400" />
                          </button>
                        </div>
                        <pre className="p-4 text-xs text-zinc-400 overflow-auto max-h-60 font-mono">
                          {fileContent}
                        </pre>
                      </div>
                    )}

                    {/* Code stats */}
                    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
                      <h4 className="font-semibold text-zinc-300 mb-4">Generation Stats</h4>
                      <div className="space-y-3 text-sm">
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Files</span>
                          <span className="text-zinc-300 font-mono">
                            {apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.files_generated || 1}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Patterns Used</span>
                          <span className="text-zinc-300 font-mono">
                            {(apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.patterns_used || []).join(', ') || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-zinc-500">Confidence</span>
                          <span className="text-zinc-300 font-mono">
                            {Math.round((apiResponse.agents?.find(a => a.agent_name === 'CodeGenerator')?.result?.confidence || 0.85) * 100)}%
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                  )}
                </div>
              )}

              {/* Tests Tab */}
              {activeTab === 'tests' && (
                <div className="animate-in fade-in duration-300">
                  <TestSuiteMatrix
                    tests={apiResponse.agents?.find(a => a.agent_name === 'TestGenerator')?.result?.tests || []}
                    coverage={{
                      method_coverage: apiResponse.agents?.find(a => a.agent_name === 'TestGenerator')?.result?.coverage_estimate || 0,
                      branch_coverage: 0,
                      line_coverage: 0
                    }}
                    coveredRequirements={apiResponse.requirements?.map(r => r.id) || []}
                  />
                  {/* Fallback: show generated test code */}
                  {apiResponse.generated_tests && (
                    <div className="mt-6">
                      <CodeArtifact
                        content={apiResponse.generated_tests}
                        filename="test_generated.py"
                        language="python"
                        confidenceScore={apiResponse.agents?.find(a => a.agent_name === 'TestGenerator')?.result?.confidence || 0}
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Traceability Tab */}
              {activeTab === 'traceability' && (
                <div className="animate-in fade-in duration-300">
                  <TraceabilityMatrix
                    requirements={apiResponse.requirements || []}
                    codeChanges={apiResponse.code_output?.changes || []}
                    tests={apiResponse.test_output?.tests || apiResponse.agents?.find(a => a.agent_name === 'TestGenerator')?.result?.tests || []}
                  />
                </div>
              )}

              {/* Workflow Tab */}
              {activeTab === 'workflow' && (
                <div className="animate-in fade-in duration-300">
                  <WorkflowVisualizer
                    nodes={(apiResponse.agents || []).map((agent, idx) => ({
                      id: `node-${idx}`,
                      name: agent.agent_name,
                      icon: idx === 0 ? FileSearch : idx === 1 ? Code2 : TestTube2,
                      status: agent.status === 'completed' ? 'completed' : agent.status === 'failed' ? 'error' : 'pending',
                      duration: agent.started_at && agent.completed_at 
                        ? ((new Date(agent.completed_at) - new Date(agent.started_at)) / 1000).toFixed(2)
                        : null,
                      result: agent.result
                    }))}
                    events={(apiResponse.agents || []).flatMap((agent, idx) => [
                      { event: 'node_start', node: agent.agent_name, timestamp: agent.started_at || new Date().toISOString() },
                      { event: agent.status === 'completed' ? 'node_complete' : 'node_error', node: agent.agent_name, timestamp: agent.completed_at || new Date().toISOString() }
                    ])}
                    threadId={apiResponse.request_id}
                  />
                </div>
              )}

              {/* Summary Tab */}
              {activeTab === 'summary' && (
                <div className="max-w-2xl mx-auto animate-in fade-in duration-300">
                  <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-zinc-800 flex justify-between items-center">
                      <h3 className="font-semibold text-zinc-200">Pipeline Summary</h3>
                      <span className="px-3 py-1 bg-emerald-600 text-white text-xs font-semibold rounded-full">
                        {apiResponse.status}
                      </span>
                    </div>
                    <div className="p-6 space-y-6">
                      <div className="grid grid-cols-2 gap-6">
                        <div>
                          <div className="text-xs text-zinc-500 mb-1">Request ID</div>
                          <div className="font-mono text-zinc-200">{apiResponse.request_id}</div>
                        </div>
                        <div>
                          <div className="text-xs text-zinc-500 mb-1">Ticket ID</div>
                          <div className="font-mono text-orange-400">{apiResponse.ticket_id}</div>
                        </div>
                      </div>

                      <div className="border-t border-zinc-800 pt-6">
                        <h4 className="text-sm font-semibold text-zinc-300 mb-4">Agent Execution</h4>
                        <div className="space-y-3">
                          {(apiResponse.agents || []).map((agent, i) => (
                            <div key={i} className="flex items-center justify-between p-4 bg-zinc-950 rounded-xl border border-zinc-800">
                              <div className="flex items-center gap-3">
                                <div className={`w-2 h-2 rounded-full ${
                                  agent.status === 'completed' ? 'bg-emerald-500' : 'bg-orange-500'
                                }`} />
                                <span className="text-sm text-zinc-300">{agent.agent_name}</span>
                              </div>
                              <div className="flex items-center gap-4">
                                {agent.result && (
                                  <span className="text-xs text-zinc-500 font-mono">
                                    {Object.entries(agent.result).slice(0, 2).map(([k, v]) => `${k}: ${v}`).join(' | ')}
                                  </span>
                                )}
                                <span className={`text-xs font-semibold uppercase ${
                                  agent.status === 'completed' ? 'text-emerald-400' : 'text-orange-400'
                                }`}>
                                  {agent.status}
                                </span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex justify-center pt-8 border-t border-zinc-900">
              <button
                onClick={startNew}
                className="flex items-center gap-3 px-6 py-3 text-zinc-500 hover:text-orange-400 transition-colors text-sm font-medium"
              >
                <RefreshCw size={16} />
                Start New Analysis
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 border-t border-zinc-900 bg-zinc-950/90 backdrop-blur-md px-6 py-2.5 flex justify-between items-center z-40">
        <div className="flex items-center gap-6 text-xs text-zinc-600">
          <span className="flex items-center gap-2">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            System Online
          </span>
          <span>v1.0.0</span>
        </div>
        <div className="text-xs text-zinc-700">
          AI SDLC Agent • Powered by OpenAI
        </div>
      </footer>
    </div>
  );
}
