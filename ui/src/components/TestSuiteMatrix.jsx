import React, { useState } from 'react';
import {
  TestTube2,
  CheckCircle2,
  XCircle,
  Clock,
  ChevronDown,
  ChevronRight,
  Target,
  Shield,
  AlertTriangle,
  Copy,
  Download,
  Eye,
  Zap,
  FileCode,
  Hash
} from 'lucide-react';

/**
 * TestSuiteMatrix Component
 * 
 * Interactive test matrix UI with:
 * - Matrix view of all tests
 * - Expandable test details with code preview
 * - Coverage summary metrics
 * - Status indicators
 * - Requirement traceability
 */

// Test status badge
const TestStatusBadge = ({ status }) => {
  const statusConfig = {
    passed: { icon: CheckCircle2, color: 'emerald', text: 'Passed' },
    failed: { icon: XCircle, color: 'red', text: 'Failed' },
    pending: { icon: Clock, color: 'zinc', text: 'Pending' },
    skipped: { icon: AlertTriangle, color: 'yellow', text: 'Skipped' }
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-semibold bg-${config.color}-950 text-${config.color}-400 border border-${config.color}-800`}>
      <Icon size={10} />
      <span>{config.text}</span>
    </div>
  );
};

// Coverage gauge component
const CoverageGauge = ({ value, target = 75, label }) => {
  const percentage = Math.round(value);
  const isAboveTarget = percentage >= target;
  
  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-medium text-zinc-400">{label}</span>
        <span className={`text-lg font-bold ${isAboveTarget ? 'text-emerald-400' : 'text-orange-400'}`}>
          {percentage}%
        </span>
      </div>
      <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
        <div 
          className={`h-full transition-all duration-500 ${isAboveTarget ? 'bg-emerald-500' : 'bg-orange-500'}`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
      <div className="flex justify-between mt-2 text-xs text-zinc-600">
        <span>0%</span>
        <span className="flex items-center gap-1">
          <Target size={10} />
          Target: {target}%
        </span>
        <span>100%</span>
      </div>
    </div>
  );
};

// Test type badge
const TestTypeBadge = ({ type }) => {
  const typeConfig = {
    unit: { color: 'blue', icon: TestTube2 },
    integration: { color: 'purple', icon: Shield },
    e2e: { color: 'orange', icon: Target },
    boundary: { color: 'yellow', icon: AlertTriangle }
  };

  const config = typeConfig[type] || typeConfig.unit;
  const Icon = config.icon;

  return (
    <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-${config.color}-950 text-${config.color}-400`}>
      <Icon size={10} />
      <span>{type}</span>
    </div>
  );
};

// Individual test row component
const TestRow = ({ test, expanded, onToggle }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = async (e) => {
    e.stopPropagation();
    await navigator.clipboard.writeText(test.code || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border-b border-zinc-800 last:border-b-0">
      {/* Row header */}
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center gap-4 hover:bg-zinc-800/30 transition-colors text-left"
      >
        <div className="shrink-0">
          {expanded ? 
            <ChevronDown size={16} className="text-zinc-500" /> : 
            <ChevronRight size={16} className="text-zinc-500" />
          }
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-zinc-200 truncate">{test.name}</span>
            <TestTypeBadge type={test.test_type || 'unit'} />
          </div>
          <p className="text-xs text-zinc-500 mt-0.5 truncate">{test.description}</p>
        </div>
        
        <div className="hidden sm:flex items-center gap-4 shrink-0">
          {/* Target method */}
          {test.covers_method && (
            <div className="flex items-center gap-1.5 text-xs text-zinc-500">
              <Target size={12} />
              <span className="font-mono">{test.covers_method}</span>
            </div>
          )}
          
          {/* Assertions count */}
          <div className="flex items-center gap-1.5 text-xs text-zinc-500">
            <Shield size={12} />
            <span>{test.assertions || 0} assertions</span>
          </div>
          
          {/* Requirement link */}
          {test.covers_requirement && (
            <div className="flex items-center gap-1.5 text-xs text-orange-400">
              <Hash size={12} />
              <span>{test.covers_requirement}</span>
            </div>
          )}
        </div>
        
        <div className="shrink-0">
          <TestStatusBadge status={test.status || 'pending'} />
        </div>
      </button>
      
      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 pl-12 space-y-4">
          {/* Test details */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <span className="text-xs text-zinc-600 block mb-1">Test Type</span>
              <span className="text-sm text-zinc-300 capitalize">{test.test_type || 'unit'}</span>
            </div>
            <div>
              <span className="text-xs text-zinc-600 block mb-1">Assertions</span>
              <span className="text-sm text-zinc-300">{test.assertions || 0}</span>
            </div>
            {test.covers_requirement && (
              <div>
                <span className="text-xs text-zinc-600 block mb-1">Covers Requirement</span>
                <span className="text-sm text-orange-400 font-mono">{test.covers_requirement}</span>
              </div>
            )}
            {test.covers_method && (
              <div>
                <span className="text-xs text-zinc-600 block mb-1">Target Method</span>
                <span className="text-sm text-zinc-300 font-mono">{test.covers_method}</span>
              </div>
            )}
          </div>
          
          {/* Code preview */}
          {test.code && (
            <div className="bg-zinc-950 border border-zinc-800 rounded-lg overflow-hidden">
              <div className="px-3 py-2 bg-zinc-900/80 border-b border-zinc-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileCode size={12} className="text-zinc-500" />
                  <span className="text-xs text-zinc-400">Test Code</span>
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 px-2 py-1 rounded text-xs text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800 transition-colors"
                >
                  {copied ? <CheckCircle2 size={12} /> : <Copy size={12} />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
              <pre className="p-3 text-xs text-zinc-400 font-mono overflow-x-auto max-h-60">
                {test.code}
              </pre>
            </div>
          )}
          
          {/* Coverage map placeholder */}
          {test.covered_lines && test.covered_lines.length > 0 && (
            <div className="bg-zinc-900/50 border border-zinc-800 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Eye size={12} className="text-zinc-500" />
                <span className="text-xs text-zinc-400">Covered Lines</span>
              </div>
              <div className="flex flex-wrap gap-1">
                {test.covered_lines.map((line, i) => (
                  <span key={i} className="px-1.5 py-0.5 bg-emerald-950 text-emerald-400 text-xs font-mono rounded">
                    L{line}
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

// Coverage summary component
const CoverageSummary = ({ metrics }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <CoverageGauge 
        value={metrics.methodCoverage || 0} 
        target={75} 
        label="Method Coverage" 
      />
      <CoverageGauge 
        value={metrics.branchCoverage || 0} 
        target={70} 
        label="Branch Coverage" 
      />
      <CoverageGauge 
        value={metrics.lineCoverage || 0} 
        target={80} 
        label="Line Coverage" 
      />
      <CoverageGauge 
        value={metrics.assertionDensity || 0} 
        target={60} 
        label="Assertion Density" 
      />
    </div>
  );
};

// Main TestSuiteMatrix component
export default function TestSuiteMatrix({
  tests = [],
  coverageMetrics = {},
  targetFiles = [],
  coveredRequirements = [],
  confidenceScore = 0,
  onTestClick = () => {},
  className = ''
}) {
  const [expandedTests, setExpandedTests] = useState(new Set());
  const [filterType, setFilterType] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Toggle test expansion
  const toggleTest = (testName) => {
    const newExpanded = new Set(expandedTests);
    if (newExpanded.has(testName)) {
      newExpanded.delete(testName);
    } else {
      newExpanded.add(testName);
    }
    setExpandedTests(newExpanded);
    onTestClick(tests.find(t => t.name === testName));
  };

  // Filter tests
  const filteredTests = tests.filter(test => {
    if (filterType !== 'all' && test.test_type !== filterType) return false;
    if (filterStatus !== 'all' && test.status !== filterStatus) return false;
    return true;
  });

  // Calculate stats
  const totalTests = tests.length;
  const passedTests = tests.filter(t => t.status === 'passed').length;
  const failedTests = tests.filter(t => t.status === 'failed').length;
  const totalAssertions = tests.reduce((sum, t) => sum + (t.assertions || 0), 0);

  // Get unique test types
  const testTypes = [...new Set(tests.map(t => t.test_type || 'unit'))];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Coverage Summary */}
      <CoverageSummary metrics={coverageMetrics} />

      {/* Stats bar */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <TestTube2 size={16} className="text-orange-500" />
              <span className="text-sm font-medium text-zinc-300">{totalTests} Tests</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 size={14} className="text-emerald-500" />
              <span className="text-sm text-zinc-400">{passedTests} Passed</span>
            </div>
            {failedTests > 0 && (
              <div className="flex items-center gap-2">
                <XCircle size={14} className="text-red-500" />
                <span className="text-sm text-zinc-400">{failedTests} Failed</span>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Shield size={14} className="text-blue-500" />
              <span className="text-sm text-zinc-400">{totalAssertions} Assertions</span>
            </div>
          </div>
          
          {confidenceScore > 0 && (
            <div className="flex items-center gap-2 px-3 py-1.5 bg-orange-950/50 border border-orange-800 rounded-full">
              <Zap size={12} className="text-orange-400" />
              <span className="text-xs font-semibold text-orange-400">
                {Math.round(confidenceScore * 100)}% Confidence
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Type:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-2 focus:ring-orange-600/50"
          >
            <option value="all">All Types</option>
            {testTypes.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-500">Status:</span>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-1.5 text-xs text-zinc-300 focus:outline-none focus:ring-2 focus:ring-orange-600/50"
          >
            <option value="all">All Status</option>
            <option value="passed">Passed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
            <option value="skipped">Skipped</option>
          </select>
        </div>
        
        <div className="flex-1" />
        
        <span className="text-xs text-zinc-600">
          Showing {filteredTests.length} of {totalTests} tests
        </span>
      </div>

      {/* Test matrix */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 bg-zinc-900/80 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="font-semibold text-zinc-200 flex items-center gap-2">
            <TestTube2 size={16} className="text-orange-500" />
            Test Suite
          </h3>
          <div className="flex items-center gap-2">
            {targetFiles.length > 0 && (
              <span className="text-xs text-zinc-500">
                Targets: {targetFiles.join(', ')}
              </span>
            )}
          </div>
        </div>

        {/* Test list */}
        <div className="divide-y divide-zinc-800">
          {filteredTests.length > 0 ? (
            filteredTests.map((test, index) => (
              <TestRow
                key={test.name || index}
                test={test}
                expanded={expandedTests.has(test.name)}
                onToggle={() => toggleTest(test.name)}
              />
            ))
          ) : (
            <div className="p-8 text-center text-zinc-600">
              <TestTube2 size={32} className="mx-auto mb-3 opacity-50" />
              <p>No tests match the current filters</p>
            </div>
          )}
        </div>
      </div>

      {/* Covered requirements */}
      {coveredRequirements.length > 0 && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4">
          <h4 className="text-sm font-medium text-zinc-300 mb-3 flex items-center gap-2">
            <Hash size={14} className="text-orange-500" />
            Covered Requirements
          </h4>
          <div className="flex flex-wrap gap-2">
            {coveredRequirements.map((req, i) => (
              <span key={i} className="px-2 py-1 bg-orange-950/50 text-orange-400 text-xs font-mono rounded border border-orange-800">
                {req}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
