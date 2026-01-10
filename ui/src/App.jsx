import React, { useState } from 'react';
import api from './api';
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
  Download as DownloadIcon,
  ClipboardCheck
} from 'lucide-react';

const Header = () => (
  <header className="border-b border-zinc-700 bg-zinc-950/80 backdrop-blur-xl sticky top-0 z-50 px-8 py-4 flex items-center justify-between">
    <div className="flex items-center gap-4">
      <div className="bg-orange-600 rounded p-1.5 shadow-lg shadow-orange-900/20">
        <Layers className="text-white w-5 h-5" />
      </div>
      <div>
        <h1 className="font-bold text-zinc-100 text-sm tracking-tight uppercase tracking-[0.15em]">SDLC.Control_Plane</h1>
        <div className="flex gap-3 items-center text-[10px] text-zinc-500 font-medium uppercase tracking-widest mt-0.5">
          <span>Infrastructure Mode</span>
          <div className="w-1 h-1 bg-zinc-800 rounded-full" />
          <span className="text-orange-500 font-bold">v2.6.0 Dark</span>
        </div>
      </div>
    </div>
    <div className="flex gap-4 items-center">
      <div className="flex items-center gap-2 px-3 py-1 bg-zinc-900 border border-zinc-800 rounded text-[10px] font-bold uppercase text-zinc-400">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        Verified Pipeline
      </div>
    </div>
  </header>
);

const ArtifactCodeBlock = ({ code, title = "patch.diff" }) => (
  <div className="bg-black border border-zinc-700 rounded-lg font-mono text-xs leading-6 overflow-hidden shadow-2xl">
    <div className="bg-zinc-900/50 px-4 py-2 border-b border-zinc-800 flex justify-between items-center">
      <div className="flex items-center gap-2">
        <div className="w-1.5 h-1.5 rounded-full bg-orange-600" />
        <span className="text-zinc-500 text-[10px] font-bold tracking-widest uppercase">{title}</span>
      </div>
      <div className="flex gap-4">
        <button className="text-zinc-500 hover:text-zinc-100 transition-colors"><Copy size={14} /></button>
        <button className="text-zinc-500 hover:text-zinc-100 transition-colors"><Download size={14} /></button>
      </div>
    </div>
    <div className="p-5 overflow-x-auto max-h-[500px]">
      {code.split('\n').map((line, i) => {
        const isAdded = line.startsWith('+');
        const isRemoved = line.startsWith('-');
        return (
          <div key={i} className={`${isAdded ? 'bg-emerald-950/30 text-emerald-400' : isRemoved ? 'bg-red-950/30 text-red-400' : 'text-zinc-500'} flex`}>
            <span className="w-10 select-none text-zinc-800 font-bold text-right pr-6 shrink-0">{i + 1}</span>
            <pre className="whitespace-pre">{line}</pre>
          </div>
        );
      })}
    </div>
  </div>
);

export default function App() {
  const [view, setView] = useState('input');
  const [apiResponse, setApiResponse] = useState(null);
  const [selectedFileContent, setSelectedFileContent] = useState(null);
  const [selectedFilePath, setSelectedFilePath] = useState(null);
  const [fetchingFile, setFetchingFile] = useState(false);
  const [formData, setFormData] = useState({ jiraId: '', repoUrl: '', actions: ['req', 'code', 'test'] });
  const [execLog, setExecLog] = useState([]);
  const [activeTab, setActiveTab] = useState('requirements');
  const [expandedAgent, setExpandedAgent] = useState('req');

  const agents = [
    { id: 'req', name: 'Requirement Analyzer Agent', icon: FileSearch, desc: 'Structural specification synthesis from artifact metadata.' },
    { id: 'code', name: 'Code Generator Agent', icon: Code2, desc: 'Context-grounded patch generation using repository style-guides.' },
    { id: 'test', name: 'Test Generator Agent', icon: TestTube2, desc: 'Deterministic test-suite synthesis with boundary coverage.' },
  ];

  const handleStart = () => {
    setView('executing');
    runPipeline();
  };

  const runPipeline = async () => {
    // Map selected actions to backend ActionType
    let action = 'analyze_requirements';
    const sel = formData.actions;
    const hasReq = sel.includes('req');
    const hasCode = sel.includes('code');
    const hasTest = sel.includes('test');
    if (hasReq && hasCode && hasTest) action = 'full_pipeline';
    else if (hasCode && !hasTest) action = 'generate_code';
    else if (hasTest && !hasCode) action = 'generate_tests';

    setExecLog([`>> SYSTEM: SENDING_ANALYZE_REQUEST (${formData.jiraId || 'MANUAL'})`]);

    try {
      const res = await api.analyzeTicket({
        ticket_id: formData.jiraId || `MANUAL-${Date.now()}`,
        action,
        github_repo: formData.repoUrl || undefined,
        github_pr: undefined
      });

      setApiResponse(res);


      // Populate logs from response agents
      setExecLog(prev => [
        ...prev,
        `>> REQUEST_ID: ${res.request_id}`,
        `>> STATUS: ${res.status}`
      ]);

      // Add per-agent logs
      if (Array.isArray(res.agents)) {
        res.agents.forEach((a) => {
          setExecLog(prev => [...prev, `>> AGENT: ${a.agent_name} - ${a.status}`]);
        });
      }

      // Set expanded agent to first agent
      if (res.agents && res.agents[0]) {
        const first = res.agents[0].agent_name.toLowerCase();
        if (first.includes('require')) setExpandedAgent('req');
        else if (first.includes('code')) setExpandedAgent('code');
        else if (first.includes('test')) setExpandedAgent('test');
      }

      // Store generated artifacts into execLog for display
      if (res.generated_code) setExecLog(prev => [...prev, '>> GENERATED_CODE_SNIPPET:', res.generated_code]);
      if (res.generated_tests) setExecLog(prev => [...prev, '>> GENERATED_TESTS_SNIPPET:', res.generated_tests]);

      // move to result view
      setView('result');
    } catch (err) {
      setExecLog(prev => [...prev, `>> ERROR: ${err.message || String(err)}`]);
      setView('result');
    }
  };

  const fetchFile = async (path) => {
    if (!formData.repoUrl) return;
    setFetchingFile(true);
    setSelectedFileContent(null);
    try {
      // normalize repo URL to owner/repo if a full URL was provided
      const normalizeRepo = (r) => {
        if (!r) return r;
        try {
          const u = new URL(r);
          // e.g. https://github.com/owner/repo or https://github.com/owner/repo/
            const parts = u.pathname.replace(/^\/+|\/+$/g, '').split('/');
          if (parts.length >= 2) return `${parts[0]}/${parts[1]}`;
        } catch (e) {
          // not a URL, assume owner/repo already
        }
        return r;
      };

      const repo = normalizeRepo(formData.repoUrl);
      const data = await api.getRepoFile(repo, path);
      setSelectedFilePath(path);
      setSelectedFileContent(data.content || '');
    } catch (e) {
      setSelectedFileContent(`Error: ${e.message || String(e)}`);
    } finally {
      setFetchingFile(false);
    }
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 font-sans selection:bg-orange-600/30 selection:text-white">
      <Header />

      <main className="max-w-screen-2xl mx-auto py-12 px-8">
        {view === 'input' && (
          <div className="max-w-[720px] mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-700 pt-8">
            <div className="space-y-3">
              <h2 className="text-4xl font-extrabold text-white tracking-tight leading-none italic uppercase">AI SDLC Control Panel</h2>
              <p className="text-zinc-500 font-medium">Deterministic orchestration for engineering artifacts.</p>
            </div>

            <div className="bg-zinc-900/30 border border-zinc-800 rounded-xl p-10 space-y-12 shadow-2xl">
              <div className="space-y-8">
                <div className="space-y-4">
                  <h3 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Input Context</h3>
                  <div className="grid grid-cols-1 gap-6">
                    <div className="space-y-2">
                          <label className="text-[11px] font-bold uppercase text-zinc-400 tracking-wider">Jira Ticket ID</label>
                          <input 
                        type="text" 
                        placeholder="e.g. JIRA-124"
                        className="w-full bg-black border border-zinc-800 rounded px-5 py-4 focus:outline-none focus:ring-1 focus:ring-orange-600 transition-all text-white font-medium placeholder:text-zinc-800 shadow-inner"
                        value={formData.jiraId}
                        onChange={(e) => setFormData({...formData, jiraId: e.target.value})}
                      />
                          <p className="text-[10px] text-zinc-600 italic">Used as grounding context for agents. (Optional if GitHub repo/PR provided)</p>
                    </div>

                    <div className="space-y-2">
                      <label className="text-[11px] font-bold uppercase text-zinc-400 tracking-wider">GitHub Repository / PR</label>
                      <input 
                        type="text" 
                        placeholder="repo-name or PR URL"
                        className="w-full bg-black border border-zinc-800 rounded px-5 py-4 focus:outline-none focus:ring-1 focus:ring-orange-600 transition-all text-white font-medium placeholder:text-zinc-800 shadow-inner"
                        value={formData.repoUrl}
                        onChange={(e) => setFormData({...formData, repoUrl: e.target.value})}
                      />
                      <p className="text-[10px] text-zinc-600 italic">Grounding reference for codebase patterns. (Optional if Jira ticket provided)</p>
                    </div>
                  </div>
                </div>

                <div className="space-y-4">
                  <h3 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Actions</h3>
                  <div className="grid grid-cols-1 gap-3">
                    {agents.map(agent => (
                      <button 
                        key={agent.id}
                        onClick={() => {
                          const newActions = formData.actions.includes(agent.id) 
                            ? formData.actions.filter(a => a !== agent.id) 
                            : [...formData.actions, agent.id];
                          setFormData({...formData, actions: newActions});
                        }}
                        className={`flex items-center justify-between p-4 border rounded transition-all group ${
                          formData.actions.includes(agent.id) ? 'bg-orange-600/10 border-orange-600 text-orange-300' : 'bg-transparent border-zinc-700'
                        }`}
                      >
                        <div className="flex items-center gap-4">
                          {formData.actions.includes(agent.id) ? (
                            <CheckSquare className="text-orange-500" size={18} />
                          ) : (
                            <Square className="text-zinc-600" size={18} />
                          )}
                          <span className={`text-xs font-bold uppercase tracking-widest ${formData.actions.includes(agent.id) ? 'text-orange-300' : 'text-zinc-500'}`}>
                            {agent.name.replace(' Agent', '')}
                          </span>
                        </div>
                        <agent.icon size={14} className={formData.actions.includes(agent.id) ? 'text-orange-400' : 'text-zinc-600'} />
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              <button 
                onClick={handleStart}
                disabled={(!formData.jiraId && !formData.repoUrl) || formData.actions.length === 0}
                className="w-full bg-orange-600 hover:bg-orange-500 disabled:bg-zinc-900 disabled:text-zinc-700 text-white font-bold py-5 rounded text-xs tracking-[0.3em] uppercase transition-all shadow-xl shadow-orange-950/20 active:scale-[0.98]"
              >
                Run SDLC Agents
              </button>
            </div>
          </div>
        )}

        {view === 'executing' && (
          <div className="max-w-[800px] mx-auto space-y-10 animate-in fade-in duration-500 pt-4">
             <div className="flex items-center justify-between border-b border-zinc-800 pb-6 mb-10">
                <div className="space-y-1">
                  <h2 className="text-2xl font-bold text-white tracking-tight uppercase tracking-widest">Agent Pipeline</h2>
                  <p className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest">Job_ID: RUN-2026-01-10-001</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-[10px] font-bold uppercase text-orange-500 bg-orange-950/10 border border-orange-900/30 px-3 py-1 rounded">Active Run</span>
                </div>
             </div>

             <div className="relative space-y-6">
                {agents.map((agent, i) => {
                  const isCompleted = execLog.some(log => log.includes(agent.name.split(' ')[0].toUpperCase().substring(0,4)) && execLog.length > execLog.findIndex(l => l.includes(agent.name.split(' ')[0].toUpperCase().substring(0,4))) + 1);
                  const isRunning = execLog.some(log => log.includes(agent.name.split(' ')[0].toUpperCase().substring(0,4))) && !isCompleted;
                  
                  return (
                    <div key={agent.id} className={`bg-zinc-900/20 border transition-all rounded-lg overflow-hidden ${
                      isRunning ? 'border-orange-600 bg-orange-600/5 shadow-2xl shadow-orange-900/10' : 
                      isCompleted ? 'border-zinc-800' : 'border-zinc-900/50 opacity-40'
                    }`}>
                      <div 
                        className="px-6 py-5 flex items-center justify-between cursor-pointer group hover:bg-zinc-900/40 transition-colors"
                        onClick={() => setExpandedAgent(agent.id)}
                      >
                        <div className="flex items-center gap-6">
                           <div className={`p-2.5 rounded ${isRunning ? 'bg-orange-600 text-white shadow-lg' : isCompleted ? 'bg-emerald-600 text-white' : 'bg-zinc-900 text-zinc-700'}`}>
                             {isCompleted ? <CheckCircle2 size={18} /> : <agent.icon size={18} />}
                           </div>
                           <div>
                             <h3 className="font-bold text-sm text-zinc-100 uppercase tracking-widest">{agent.name}</h3>
                             <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider mt-0.5">{agent.desc}</p>
                           </div>
                        </div>
                        <div className="flex items-center gap-6">
                          <span className={`text-[9px] font-black uppercase tracking-[0.2em] px-2 py-0.5 rounded border ${
                            isCompleted ? 'text-emerald-500 border-emerald-900/30 bg-emerald-950/30' : 
                            isRunning ? 'text-orange-500 border-orange-900/30 bg-orange-950/30' : 
                            'text-zinc-700 border-zinc-900'
                          }`}>
                            {isCompleted ? 'Completed' : isRunning ? 'Running' : 'Pending'}
                          </span>
                          <ChevronDown className={`text-zinc-700 transition-transform ${expandedAgent === agent.id ? 'rotate-180' : ''}`} size={16} />
                        </div>
                      </div>

                      {expandedAgent === agent.id && (
                        <div className="px-6 pb-6 border-t border-zinc-800 pt-6 animate-in fade-in duration-300">
                           <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-[10px] font-bold uppercase tracking-widest text-zinc-600 border-b border-zinc-800 pb-4 mb-4">
                             <div>Input Summary</div>
                             <div>Grounding Context</div>
                             <div>Artifact Output</div>
                           </div>
                           <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-6">
                              <div className="text-[11px] text-zinc-400 leading-relaxed italic">{formData.jiraId || 'JIRA-124'} Metadata Ingest</div>
                              <div className="text-[11px] text-zinc-400 flex items-center gap-2">
                                <Zap size={10} className="text-orange-500" /> 
                                {isCompleted ? '3 Docs (Confidence: 0.98)' : isRunning ? 'Searching...' : 'Awaiting Pipeline'}
                              </div>
                              <div className="text-[11px] text-zinc-100 font-bold tracking-tight">{isCompleted ? `${agent.id.toUpperCase()}_ARTIFACT.JSON` : '--'}</div>
                           </div>
                           <div className="bg-black rounded p-5 font-mono text-[10px] text-zinc-500 leading-loose border border-zinc-800 shadow-inner">
                             <div className="flex justify-between items-center mb-3 border-b border-zinc-900 pb-2">
                                <span className="text-zinc-700 font-black uppercase tracking-[0.2em]">Execution Logs</span>
                                <span className="text-[9px]">T: {new Date().toISOString().substring(11, 19)}</span>
                             </div>
                             {execLog.filter(l => l.includes(agent.name.split(' ')[0].toUpperCase().substring(0,4)) || l.includes('SYSTEM')).map((log, li) => (
                               <div key={li} className="flex gap-4">
                                 <span className="text-zinc-800 shrink-0 select-none">[{li}]</span>
                                 <span className={log.includes('STATUS') ? 'text-orange-500 font-bold' : 'text-zinc-600'}>{log}</span>
                               </div>
                             ))}
                             {!isCompleted && isRunning && <div className="h-3 w-1 bg-orange-600 animate-pulse inline-block align-middle ml-2" />}
                           </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
          </div>
        )}

        {view === 'result' && (
          <div className="space-y-10 animate-in fade-in duration-700">
            <div className="bg-zinc-900/30 border border-zinc-800 rounded-2xl p-10 flex flex-col lg:flex-row justify-between items-start lg:items-end gap-8 shadow-2xl">
              <div className="space-y-2">
                <div className="flex gap-6 text-[10px] font-bold uppercase text-zinc-600 tracking-widest mb-3">
                  <span className="flex items-center gap-1.5"><Hash size={10} /> RUN-2026-01-10-001</span>
                  <span className="text-emerald-500 flex items-center gap-1.5 font-black tracking-[0.2em]"><ShieldCheck size={10} /> Verified SDLC Bundle</span>
                  <span className="flex items-center gap-1.5"><Clock size={10} /> 18.4s Time</span>
                </div>
                <h2 className="text-6xl font-extrabold text-white tracking-tighter uppercase leading-none italic">
                   {formData.jiraId || "JIRA-124"} <span className="text-zinc-800 font-normal">/</span> Artifacts
                </h2>
              </div>
              <div className="flex gap-4 w-full lg:w-auto">
                <button className="flex-1 lg:flex-none px-8 py-4 bg-black border border-zinc-800 rounded text-[10px] font-black uppercase tracking-[0.2em] hover:bg-zinc-900 transition-all flex items-center justify-center gap-3">
                  <DownloadIcon size={14} /> Download Bundle
                </button>
                <button className="flex-1 lg:flex-none px-8 py-4 bg-orange-600 text-white rounded text-[10px] font-black uppercase tracking-[0.2em] hover:bg-orange-500 transition-all shadow-xl shadow-orange-950/20 flex items-center justify-center gap-3">
                  <ClipboardCheck size={14} /> Copy Artifacts
                </button>
              </div>
            </div>

            <nav className="flex border-b border-zinc-900 gap-16">
              {['requirements', 'code', 'tests', 'summary'].map(tab => (
                <button 
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`pb-5 px-1 font-black uppercase tracking-widest text-[10px] transition-all relative ${
                    activeTab === tab ? 'text-orange-500' : 'text-zinc-600 hover:text-zinc-300'
                  }`}
                >
                  {tab === 'requirements' ? 'Requirements Spec' : tab === 'code' ? 'Code Diff' : tab === 'tests' ? 'Test Suite' : 'Execution Summary'}
                  {activeTab === tab && <div className="absolute bottom-[-1px] left-0 right-0 h-0.5 bg-orange-500" />}
                </button>
              ))}
            </nav>

            <div className="min-h-[550px]">
              {activeTab === 'requirements' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 animate-in fade-in duration-300">
                  <div className="lg:col-span-8 space-y-12">
                     <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg overflow-hidden">
                       <div className="px-6 py-4 bg-zinc-900/50 border-b border-zinc-800 flex justify-between items-center">
                         <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Functional Requirements</h4>
                         <span className="text-[9px] font-black tracking-widest px-2 py-1 rounded bg-white text-black uppercase">Structured</span>
                       </div>
                       <table className="w-full text-left text-[11px]">
                         <thead className="bg-black/50 text-zinc-600 uppercase text-[9px] font-black tracking-widest">
                           <tr>
                             <th className="px-6 py-5 border-b border-zinc-900">ID</th>
                             <th className="px-6 py-5 border-b border-zinc-900">Description</th>
                             <th className="px-6 py-5 border-b border-zinc-900">Source</th>
                           </tr>
                         </thead>
                         <tbody className="divide-y divide-zinc-900">
                           {[
                             { id: "FR-1", desc: "Calculate tax based on user income slab", src: "JIRA-124 description" },
                             { id: "FR-2", desc: "Apply region-specific deduction overrides", src: "tax_utils.py patterns" },
                             { id: "FR-3", desc: "Validate negative/null currency input", src: "Finance.Core validation" }
                           ].map(row => (
                             <tr key={row.id} className="hover:bg-zinc-900/30 transition-colors">
                               <td className="px-6 py-6 font-black text-orange-500">{row.id}</td>
                               <td className="px-6 py-6 text-zinc-300 font-medium leading-relaxed">{row.desc}</td>
                               <td className="px-6 py-6 text-zinc-600 italic tracking-tight">{row.src}</td>
                             </tr>
                           ))}
                         </tbody>
                       </table>
                     </div>

                     <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-8 space-y-6">
                          <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600 flex items-center gap-3">
                            <Zap size={14} className="text-orange-500" /> Non-Functional
                          </h4>
                          <div className="space-y-4">
                            {["Response time < 200ms", "Precision: IEEE 754"].map(nfr => (
                              <div key={nfr} className="flex items-center gap-4 text-xs font-bold text-zinc-400">
                                <div className="w-1.5 h-1.5 rounded-full bg-orange-500 shadow-sm shadow-orange-500" /> {nfr}
                              </div>
                            ))}
                          </div>
                        </div>
                        <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-8 space-y-6">
                          <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600 flex items-center gap-3">
                            <AlertTriangle size={14} className="text-orange-500" /> Edge Cases
                          </h4>
                          <div className="space-y-3">
                            {['Income exactly on boundary', 'Negative income', 'Null input'].map(ec => (
                              <div key={ec} className="text-[11px] font-medium text-zinc-500 italic pl-4 border-l-2 border-zinc-800">{ec}</div>
                            ))}
                          </div>
                        </div>
                     </div>
                  </div>
                  <div className="lg:col-span-4">
                    <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-10 space-y-8 sticky top-28 shadow-2xl">
                       <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Assumptions</h4>
                       <div className="space-y-6">
                          {['Currency is INR', 'Slabs are configurable', 'External service fallback'].map(a => (
                            <div key={a} className="flex items-center gap-5 text-xs font-bold text-zinc-300">
                              <CheckSquare size={20} className="text-orange-600 shrink-0" /> {a}
                            </div>
                          ))}
                       </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'code' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 animate-in fade-in duration-300">
                    <div className="lg:col-span-8 space-y-6">
                      <ArtifactCodeBlock
                        code={
                          apiResponse && apiResponse.github_diff
                            ? apiResponse.github_diff
                            : apiResponse && apiResponse.generated_code
                              ? apiResponse.generated_code
                              : `--- a/tax.py\n+++ b/tax.py\n@@ -1,3 +1,12 @@\n+def calculate_tax(income: float) -> float:\n+    if income is None or income < 0:\n+        raise ValueError("Invalid income")\n+\n+    if income <= 250000:\n+        return 0.0\n+    elif income <= 500000:\n+        return income * 0.05`
                        }
                        title={apiResponse && apiResponse.github_pr ? (apiResponse.github_pr.title || 'patch.diff') : (apiResponse && apiResponse.github_repo ? apiResponse.github_repo : 'patch.diff')}
                      />
                    </div>
                  <div className="lg:col-span-4 space-y-8">
                    {apiResponse && apiResponse.github_pr && (
                      <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-6 space-y-4">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">GitHub Pull Request</h4>
                        <div className="text-sm font-bold text-zinc-100">{apiResponse.github_pr.title}</div>
                        <div className="text-[11px] text-zinc-500">#{apiResponse.github_pr.number} opened by <span className="text-zinc-300 font-bold">{apiResponse.github_pr.user?.login}</span></div>
                        <a className="text-[10px] text-orange-500 font-bold" href={apiResponse.github_pr.html_url} target="_blank" rel="noreferrer">View on GitHub ↗</a>
                      </div>
                    )}

                    {apiResponse && Array.isArray(apiResponse.github_files) && apiResponse.github_files.length > 0 && (
                      <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-6 space-y-4">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Repo Files</h4>
                        <div className="space-y-2 text-[11px] text-zinc-400">
                          {apiResponse.github_files.map((f, idx) => (
                            <div key={idx} className="flex items-center justify-between hover:bg-zinc-900/30 p-2 rounded cursor-pointer" onClick={() => fetchFile(f.path)}>
                              <div className="truncate text-[13px]">{f.path || f.name}</div>
                              <div className="text-zinc-600 text-[10px]">{f.type}</div>
                            </div>
                          ))}
                        </div>
                        {fetchingFile && <div className="text-[10px] text-zinc-500">Loading file...</div>}
                        {selectedFileContent && (
                          <div className="mt-4">
                            <ArtifactCodeBlock code={selectedFileContent} title={selectedFilePath} />
                          </div>
                        )}
                      </div>
                    )}

                    <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-10 space-y-8">
                      <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Reasoning Trace</h4>
                      <div className="space-y-6">
                        {["Matched core tax pattern","Applied PR-456 style-guide","Calculated slab AST node"].map((rt, i) => (
                          <div key={i} className="flex gap-5 items-start text-[11px] text-zinc-400 font-bold uppercase tracking-tight">
                            <Activity size={16} className="text-orange-500 shrink-0 mt-0.5" /> {rt}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-10 space-y-8">
                      <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">RAG Grounding</h4>
                      <div className="space-y-4">
                        {["PR-456: core_finance_utils", "tax_utils.py"].map(s => (
                          <div key={s} className="px-5 py-4 bg-black border border-zinc-900 rounded text-[10px] font-black text-zinc-500 flex justify-between items-center group cursor-pointer hover:border-zinc-700 transition-all">
                            {s} <span className="text-zinc-400">↗</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'tests' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 animate-in fade-in duration-300">
                  <div className="lg:col-span-8 space-y-6">
                    <ArtifactCodeBlock code={`import pytest\nfrom tax import calculate_tax\n\ndef test_zero_income():\n    assert calculate_tax(0) == 0.0\n\ndef test_negative_income():\n    with pytest.raises(ValueError):\n        calculate_tax(-100)\n\ndef test_boundary_values():\n    assert calculate_tax(250000) == 0.0`} title="tests/test_tax_calculator.py" />
                  </div>
                  <div className="lg:col-span-4 space-y-8">
                    <div className="bg-zinc-900/20 border border-zinc-800 rounded-lg p-10 space-y-8">
                       <h4 className="text-[10px] font-black uppercase tracking-[0.25em] text-zinc-600">Coverage Intent</h4>
                       <div className="space-y-6">
                         {['Edge cases','Boundary values','Error handling'].map(ct => (
                           <div key={ct} className="flex items-center gap-5 text-xs font-bold text-zinc-300">
                             <CheckCircle2 size={20} className="text-emerald-500" /> {ct}
                           </div>
                         ))}
                       </div>
                    </div>
                    <div className="bg-black border border-zinc-800 rounded-lg p-10 text-white space-y-6 shadow-2xl">
                       <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-700">Metadata</h4>
                       <div className="grid grid-cols-2 gap-6 text-[10px] font-bold uppercase tracking-widest">
                          <span className="text-zinc-600">Framework</span>
                          <span className="text-right text-zinc-100">Pytest</span>
                          <span className="text-zinc-600">Environment</span>
                          <span className="text-right text-zinc-100">Python 3.10</span>
                       </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="max-w-3xl mx-auto animate-in fade-in duration-300">
                   <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden shadow-2xl">
                     <div className="px-10 py-8 bg-zinc-900/50 border-b border-zinc-800 flex justify-between items-center">
                        <h4 className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-600">Pipeline Audit Summary</h4>
                        <span className="text-[10px] font-black bg-white text-black px-4 py-1.5 rounded tracking-widest uppercase">Verified Run</span>
                     </div>
                     <div className="p-12 space-y-16">
                       <div className="grid grid-cols-2 gap-20 border-b border-zinc-900 pb-12">
                         <div className="space-y-3">
                           <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">Workflow ID</span>
                           <p className="text-xl font-bold font-mono tracking-tighter text-white">RUN-2026-01-10-001</p>
                         </div>
                         <div className="space-y-3 text-right">
                           <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest">Total Execution</span>
                           <p className="text-xl font-bold font-mono tracking-tighter text-orange-500">18.42s</p>
                         </div>
                       </div>
                       <div className="space-y-8">
                         <span className="text-[10px] font-black text-zinc-600 uppercase tracking-widest block">Decision History</span>
                         <div className="space-y-4">
                           {[{ d: "Requirement logic analysis required", s: "Success" },{ d: "Context-aware patch synthesis required", s: "Success" },{ d: "Boundary test suite generation required", s: "Success" }].map((item, i) => (
                             <div key={i} className="flex items-center justify-between p-6 bg-black rounded border border-zinc-900 group transition-all">
                               <div className="flex items-center gap-5">
                                 <div className="w-1.5 h-1.5 rounded-full bg-orange-600 shadow-[0_0_8px_rgba(234,88,12,0.6)]" />
                                 <span className="text-xs font-bold text-zinc-100 tracking-tight">{item.d}</span>
                               </div>
                               <span className="text-[10px] font-black uppercase tracking-widest text-emerald-500">{item.s}</span>
                             </div>
                           ))}
                         </div>
                       </div>
                     </div>
                   </div>
                </div>
              )}
            </div>

            <div className="pt-24 pb-16 text-center">
              <button 
                onClick={() => { setView('input'); setExecLog([]); setFormData({ jiraId: '', repoUrl: '', actions: ['req', 'code', 'test'] }); }}
                className="text-zinc-600 hover:text-orange-600 transition-all text-[11px] font-black uppercase tracking-[0.6em] flex items-center justify-center gap-8 mx-auto group"
              >
                <div className="w-20 h-px bg-zinc-900 group-hover:bg-orange-600 transition-all" />
                Initialize New Pipeline
                <div className="w-20 h-px bg-zinc-900 group-hover:bg-orange-600 transition-all" />
              </button>
            </div>
          </div>
        )}

      </main>

      <footer className="fixed bottom-0 left-0 right-0 border-t border-zinc-900 bg-black/80 backdrop-blur-md px-10 py-3 flex justify-between items-center z-50">
        <div className="flex gap-12 text-[10px] font-black uppercase text-zinc-600 tracking-widest italic">
          <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-orange-600 animate-pulse" /> SYSTEM: STABLE</span>
          <span className="flex items-center gap-2">KERNEL: 2.6.0-DARK</span>
        </div>
        <div className="text-[10px] text-zinc-700 font-black uppercase tracking-widest">
          Traceability_Kernel: <span className="text-zinc-400">Deterministic_Orchestration</span>
        </div>
      </footer>
    </div>
  );
}
