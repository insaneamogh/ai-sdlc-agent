import React, { useState } from 'react';
import {
  Package,
  FileText,
  GitBranch,
  TestTube2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Download,
  Copy,
  ChevronDown,
  ChevronRight,
  Zap,
  Activity,
  Target,
  AlertTriangle,
  FileJson,
  FileCode,
  Layers,
  Timer,
  Hash
} from 'lucide-react';
import DiffViewer from './DiffViewer';
import TestSuiteMatrix from './TestSuiteMatrix';

/**
 * OutputBundle Component
 * 
 * Enterprise-grade artifact bundle viewer that displays:
 * - Requirements Specification
 * - Code Diff with metadata
 * - Test Suite with coverage
 * - Execution Summary with decisions
 * 
 * This is the primary output visualization - NOT chat text.
 */

// Tab button component
const TabButton = ({ active, onClick, icon: Icon, label, badge }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 ${
      active
        ? 'text-orange-400 border-orange-500 bg-orange-950/20'
        : 'text-zinc-400 border-transparent hover:text-zinc-200 hover:bg-zinc-800/50'
    }`}
  >
    <Icon size={16} />
    {label}
    {badge !== undefined && (
      <span className={`px-1.5 py-0.5 text-xs rounded-full ${
        active ? 'bg-orange-500/20 text-orange-400' : 'bg-zinc-700 text-zinc-400'
      }`}>
        {badge}
      </span>
    )}
  </button>
);

// Confidence badge
const ConfidenceBadge = ({ value, size = 'md' }) => {
  const percentage = Math.round(value * 100);
  const color = percentage >= 80 ? 'emerald' : percentage >= 60 ? 'yellow' : 'red';
  
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5'
  };
  
  return (
    <span className={`inline-flex items-center gap-1 rounded-full font-semibold ${sizeClasses[size]} bg-${color}-950/50 text-${color}-400 border border-${color}-800`}>
      <Zap size={size === 'sm' ? 10 : size === 'md' ? 12 : 14} />
      {percentage}%
    </span>
  );
};

// Requirements tab content
const RequirementsTab = ({ spec }) => {
  const [expandedSections, setExpandedSections] = useState(new Set(['functional']));
  
  if (!spec) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <FileText size={32} className="mx-auto mb-3 opacity-50" />
        <p>No requirements specification available</p>
      </div>
    );
  }
  
  const toggleSection = (section) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };
  
  const RequirementItem = ({ req }) => (
    <div className="p-3 bg-zinc-900/50 rounded-lg border border-zinc-800">
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="px-2 py-0.5 bg-blue-950/50 text-blue-400 text-xs font-mono rounded border border-blue-800">
            {req.id}
          </span>
          <span className={`px-2 py-0.5 text-xs rounded border ${
            req.priority === 'high' ? 'bg-red-950/50 text-red-400 border-red-800' :
            req.priority === 'medium' ? 'bg-yellow-950/50 text-yellow-400 border-yellow-800' :
            'bg-zinc-800 text-zinc-400 border-zinc-700'
          }`}>
            {req.priority}
          </span>
        </div>
      </div>
      <p className="text-sm text-zinc-300 mb-2">{req.description}</p>
      
      {req.acceptance_criteria?.length > 0 && (
        <div className="mt-2">
          <h5 className="text-xs text-zinc-500 mb-1">Acceptance Criteria</h5>
          <ul className="space-y-1">
            {req.acceptance_criteria.map((ac, i) => (
              <li key={i} className="text-xs text-zinc-400 flex items-start gap-1">
                <CheckCircle2 size={12} className="text-emerald-500 mt-0.5 shrink-0" />
                {ac}
              </li>
            ))}
          </ul>
        </div>
      )}
      
      {req.edge_cases?.length > 0 && (
        <div className="mt-2">
          <h5 className="text-xs text-zinc-500 mb-1">Edge Cases</h5>
          <ul className="space-y-1">
            {req.edge_cases.map((ec, i) => (
              <li key={i} className="text-xs text-zinc-400 flex items-start gap-1">
                <AlertTriangle size={12} className="text-yellow-500 mt-0.5 shrink-0" />
                {ec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
  
  const Section = ({ title, items, type, icon: Icon }) => (
    <div className="border border-zinc-800 rounded-lg overflow-hidden">
      <button
        onClick={() => toggleSection(type)}
        className="w-full px-4 py-3 bg-zinc-900/80 flex items-center justify-between hover:bg-zinc-800/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className="text-orange-500" />
          <span className="text-sm font-medium text-zinc-200">{title}</span>
          <span className="px-1.5 py-0.5 bg-zinc-800 text-zinc-400 text-xs rounded">
            {items?.length || 0}
          </span>
        </div>
        {expandedSections.has(type) ? 
          <ChevronDown size={16} className="text-zinc-500" /> : 
          <ChevronRight size={16} className="text-zinc-500" />
        }
      </button>
      
      {expandedSections.has(type) && items?.length > 0 && (
        <div className="p-3 space-y-2">
          {items.map((req, i) => (
            <RequirementItem key={i} req={req} />
          ))}
        </div>
      )}
    </div>
  );
  
  return (
    <div className="space-y-4 p-4">
      <Section 
        title="Functional Requirements" 
        items={spec.functional_requirements} 
        type="functional"
        icon={Target}
      />
      <Section 
        title="Non-Functional Requirements" 
        items={spec.non_functional_requirements} 
        type="nonfunctional"
        icon={Activity}
      />
      <Section 
        title="Constraints" 
        items={spec.constraints} 
        type="constraints"
        icon={AlertCircle}
      />
      
      {/* Edge cases and assumptions */}
      {(spec.edge_cases?.length > 0 || spec.assumptions?.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {spec.edge_cases?.length > 0 && (
            <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <h4 className="text-sm font-medium text-zinc-200 mb-2 flex items-center gap-2">
                <AlertTriangle size={14} className="text-yellow-500" />
                Edge Cases
              </h4>
              <ul className="space-y-1">
                {spec.edge_cases.map((ec, i) => (
                  <li key={i} className="text-xs text-zinc-400">• {ec}</li>
                ))}
              </ul>
            </div>
          )}
          
          {spec.assumptions?.length > 0 && (
            <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
              <h4 className="text-sm font-medium text-zinc-200 mb-2 flex items-center gap-2">
                <FileText size={14} className="text-blue-500" />
                Assumptions
              </h4>
              <ul className="space-y-1">
                {spec.assumptions.map((a, i) => (
                  <li key={i} className="text-xs text-zinc-400">• {a}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// Code tab content
const CodeTab = ({ codeDiff }) => {
  if (!codeDiff) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <GitBranch size={32} className="mx-auto mb-3 opacity-50" />
        <p>No code changes available</p>
      </div>
    );
  }
  
  return (
    <div className="p-4">
      <DiffViewer
        diffContent={codeDiff.unified_diff}
        hunks={codeDiff.hunks}
        filesModified={codeDiff.files_modified}
        reasoningTrace={codeDiff.reasoning_trace}
        ragSourcesUsed={codeDiff.rag_sources_used}
        patternsApplied={codeDiff.patterns_applied}
        impactAnalysis={codeDiff.impact_analysis}
        confidence={codeDiff.confidence}
      />
    </div>
  );
};

// Tests tab content
const TestsTab = ({ testSuite }) => {
  if (!testSuite) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <TestTube2 size={32} className="mx-auto mb-3 opacity-50" />
        <p>No test suite available</p>
      </div>
    );
  }
  
  // Transform tests for TestSuiteMatrix
  const tests = testSuite.tests?.map(t => ({
    name: t.name,
    description: t.description,
    type: t.test_type,
    status: t.status || 'pending',
    requirement: t.covers_requirement,
    assertions: t.assertions
  })) || [];
  
  return (
    <div className="p-4">
      <TestSuiteMatrix
        tests={tests}
        coverage={testSuite.coverage_metrics}
        coveredRequirements={testSuite.covered_requirements}
      />
    </div>
  );
};

// Execution summary tab content
const ExecutionTab = ({ summary }) => {
  if (!summary) {
    return (
      <div className="p-8 text-center text-zinc-500">
        <Activity size={32} className="mx-auto mb-3 opacity-50" />
        <p>No execution summary available</p>
      </div>
    );
  }
  
  const statusColors = {
    success: 'text-emerald-400 bg-emerald-950/50 border-emerald-800',
    partial: 'text-yellow-400 bg-yellow-950/50 border-yellow-800',
    failed: 'text-red-400 bg-red-950/50 border-red-800'
  };
  
  return (
    <div className="p-4 space-y-4">
      {/* Summary header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
          <div className="text-xs text-zinc-500 mb-1">Status</div>
          <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-semibold border ${statusColors[summary.final_status] || statusColors.success}`}>
            {summary.final_status === 'success' ? <CheckCircle2 size={14} /> : <AlertCircle size={14} />}
            {(summary.final_status || 'success').toUpperCase()}
          </span>
        </div>
        
        <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
          <div className="text-xs text-zinc-500 mb-1">Execution Time</div>
          <div className="text-lg font-semibold text-zinc-200 flex items-center gap-1">
            <Timer size={16} className="text-orange-500" />
            {summary.execution_time_ms ? `${(summary.execution_time_ms / 1000).toFixed(2)}s` : 'N/A'}
          </div>
        </div>
        
        <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
          <div className="text-xs text-zinc-500 mb-1">Agents Executed</div>
          <div className="text-lg font-semibold text-zinc-200">
            {summary.agents_executed?.length || 0}
          </div>
        </div>
        
        <div className="p-4 bg-zinc-900/50 rounded-lg border border-zinc-800">
          <div className="text-xs text-zinc-500 mb-1">Retries</div>
          <div className="text-lg font-semibold text-zinc-200">
            {summary.retries || 0}
          </div>
        </div>
      </div>
      
      {/* Workflow ID and Thread ID */}
      <div className="flex flex-wrap gap-4 text-xs">
        <div className="flex items-center gap-2 px-3 py-2 bg-zinc-900/50 rounded border border-zinc-800">
          <Hash size={12} className="text-zinc-500" />
          <span className="text-zinc-500">Workflow:</span>
          <span className="font-mono text-zinc-300">{summary.workflow_id}</span>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 bg-zinc-900/50 rounded border border-zinc-800">
          <Hash size={12} className="text-zinc-500" />
          <span className="text-zinc-500">Thread:</span>
          <span className="font-mono text-zinc-300">{summary.thread_id}</span>
        </div>
      </div>
      
      {/* Decisions timeline */}
      {summary.decisions?.length > 0 && (
        <div className="border border-zinc-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-zinc-900/80 border-b border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-200">Workflow Decisions</h4>
          </div>
          <div className="p-4">
            <div className="space-y-3">
              {summary.decisions.map((decision, i) => (
                <div key={i} className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-zinc-800 flex items-center justify-center shrink-0">
                    <span className="text-xs text-zinc-400">{i + 1}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-zinc-200">{decision.node}</span>
                      <span className={`px-1.5 py-0.5 text-xs rounded ${
                        decision.decision === 'completed' || decision.decision === 'proceed'
                          ? 'bg-emerald-950/50 text-emerald-400 border border-emerald-800'
                          : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                      }`}>
                        {decision.decision}
                      </span>
                    </div>
                    <p className="text-xs text-zinc-500">{decision.reason}</p>
                    {decision.timestamp && (
                      <p className="text-xs text-zinc-600 mt-1">{decision.timestamp}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Quality gates */}
      {summary.quality_gates?.length > 0 && (
        <div className="border border-zinc-800 rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-zinc-900/80 border-b border-zinc-800">
            <h4 className="text-sm font-medium text-zinc-200">Quality Gates</h4>
          </div>
          <div className="p-4">
            <div className="space-y-2">
              {summary.quality_gates.map((gate, i) => (
                <div key={i} className="flex items-center justify-between p-2 bg-zinc-900/50 rounded">
                  <div className="flex items-center gap-2">
                    {gate.passed ? 
                      <CheckCircle2 size={14} className="text-emerald-400" /> :
                      <AlertCircle size={14} className="text-red-400" />
                    }
                    <span className="text-sm text-zinc-300">{gate.gate_name}</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <span className="text-zinc-500">
                      {gate.actual_value.toFixed(2)} / {gate.threshold.toFixed(2)}
                    </span>
                    <span className={gate.passed ? 'text-emerald-400' : 'text-red-400'}>
                      {gate.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      
      {/* Errors */}
      {summary.errors?.length > 0 && (
        <div className="border border-red-800 rounded-lg overflow-hidden bg-red-950/20">
          <div className="px-4 py-3 bg-red-950/50 border-b border-red-800">
            <h4 className="text-sm font-medium text-red-400 flex items-center gap-2">
              <AlertCircle size={14} />
              Errors
            </h4>
          </div>
          <div className="p-4">
            <ul className="space-y-2">
              {summary.errors.map((error, i) => (
                <li key={i} className="text-sm text-red-300">{error}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

// Main OutputBundle component
export default function OutputBundle({
  bundle,
  className = ''
}) {
  const [activeTab, setActiveTab] = useState('requirements');
  const [copied, setCopied] = useState(false);
  
  if (!bundle) {
    return (
      <div className={`bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 text-center ${className}`}>
        <Package size={48} className="mx-auto mb-4 text-zinc-600" />
        <h3 className="text-lg font-semibold text-zinc-400 mb-2">No Output Bundle</h3>
        <p className="text-sm text-zinc-500">Run the pipeline to generate artifacts</p>
      </div>
    );
  }
  
  // Copy bundle JSON
  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(bundle, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  
  // Download bundle
  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${bundle.bundle_id || 'output'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };
  
  // Count items for badges
  const reqCount = (bundle.requirements_spec?.functional_requirements?.length || 0) +
                   (bundle.requirements_spec?.non_functional_requirements?.length || 0) +
                   (bundle.requirements_spec?.constraints?.length || 0);
  const fileCount = bundle.code_diff?.files_modified?.length || 0;
  const testCount = bundle.test_suite?.tests?.length || 0;
  
  return (
    <div className={`bg-zinc-900/30 border border-zinc-800 rounded-xl overflow-hidden ${className}`}>
      {/* Header */}
      <div className="px-6 py-4 bg-zinc-900/80 border-b border-zinc-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center">
              <Package size={20} className="text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-zinc-100">Output Bundle</h2>
              <div className="flex items-center gap-3 text-xs text-zinc-500">
                <span className="font-mono">{bundle.bundle_id}</span>
                <span>•</span>
                <span>{bundle.ticket_id}</span>
                <span>•</span>
                <span>{bundle.created_at}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-3">
            {bundle.overall_confidence > 0 && (
              <ConfidenceBadge value={bundle.overall_confidence} size="md" />
            )}
            
            <div className="flex items-center gap-1">
              <button
                onClick={handleCopy}
                className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
                title="Copy JSON"
              >
                {copied ? 
                  <CheckCircle2 size={18} className="text-emerald-400" /> : 
                  <Copy size={18} className="text-zinc-400" />
                }
              </button>
              <button
                onClick={handleDownload}
                className="p-2 rounded-lg hover:bg-zinc-800 transition-colors"
                title="Download Bundle"
              >
                <Download size={18} className="text-zinc-400" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="flex border-b border-zinc-800 overflow-x-auto">
        <TabButton
          active={activeTab === 'requirements'}
          onClick={() => setActiveTab('requirements')}
          icon={FileText}
          label="Requirements"
          badge={reqCount}
        />
        <TabButton
          active={activeTab === 'code'}
          onClick={() => setActiveTab('code')}
          icon={GitBranch}
          label="Code Diff"
          badge={fileCount}
        />
        <TabButton
          active={activeTab === 'tests'}
          onClick={() => setActiveTab('tests')}
          icon={TestTube2}
          label="Test Suite"
          badge={testCount}
        />
        <TabButton
          active={activeTab === 'execution'}
          onClick={() => setActiveTab('execution')}
          icon={Activity}
          label="Execution"
        />
      </div>
      
      {/* Tab content */}
      <div className="min-h-[400px]">
        {activeTab === 'requirements' && (
          <RequirementsTab spec={bundle.requirements_spec} />
        )}
        {activeTab === 'code' && (
          <CodeTab codeDiff={bundle.code_diff} />
        )}
        {activeTab === 'tests' && (
          <TestsTab testSuite={bundle.test_suite} />
        )}
        {activeTab === 'execution' && (
          <ExecutionTab summary={bundle.execution_summary} />
        )}
      </div>
    </div>
  );
}
