//_______________This Code was generated using GenAI tool: Codify, Please check for accuracy_______________//

import React, { useState, useMemo } from 'react';
import {
  FileSearch,
  Code2,
  TestTube2,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  ChevronDown,
  Link2,
  Layers,
  Target,
  Shield
} from 'lucide-react';

/**
 * TraceabilityMatrix Component
 * 
 * Displays explicit requirement → code → test linkage for reviewability.
 * Shows coverage status and allows click-through navigation.
 * 
 * @param {Object} props
 * @param {Array} props.requirements - List of requirements with id, description, priority
 * @param {Array} props.codeChanges - List of code changes with implements_requirements
 * @param {Array} props.tests - List of tests with covers_requirement
 */
const TraceabilityMatrix = ({ requirements = [], codeChanges = [], tests = [] }) => {
  const [expandedReq, setExpandedReq] = useState(null);
  const [viewMode, setViewMode] = useState('matrix'); // matrix | list

  // Build traceability map
  const traceabilityData = useMemo(() => {
    const map = {};
    
    // Initialize with requirements
    requirements.forEach(req => {
      map[req.id] = {
        requirement: req,
        codeChanges: [],
        tests: [],
        status: 'uncovered'
      };
    });
    
    // Link code changes to requirements
    codeChanges.forEach(change => {
      const implementsReqs = change.implements_requirements || [];
      implementsReqs.forEach(reqId => {
        if (map[reqId]) {
          map[reqId].codeChanges.push(change);
        }
      });
    });
    
    // Link tests to requirements
    tests.forEach(test => {
      const coversReq = test.covers_requirement;
      if (coversReq && map[coversReq]) {
        map[coversReq].tests.push(test);
      }
    });
    
    // Calculate status for each requirement
    Object.keys(map).forEach(reqId => {
      const entry = map[reqId];
      const hasCode = entry.codeChanges.length > 0;
      const hasTests = entry.tests.length > 0;
      
      if (hasCode && hasTests) {
        entry.status = 'fully_covered';
      } else if (hasCode || hasTests) {
        entry.status = 'partially_covered';
      } else {
        entry.status = 'uncovered';
      }
    });
    
    return map;
  }, [requirements, codeChanges, tests]);

  // Calculate coverage statistics
  const stats = useMemo(() => {
    const entries = Object.values(traceabilityData);
    const total = entries.length;
    const fullyCovered = entries.filter(e => e.status === 'fully_covered').length;
    const partiallyCovered = entries.filter(e => e.status === 'partially_covered').length;
    const uncovered = entries.filter(e => e.status === 'uncovered').length;
    
    return {
      total,
      fullyCovered,
      partiallyCovered,
      uncovered,
      coveragePercent: total > 0 ? Math.round((fullyCovered / total) * 100) : 0,
      partialPercent: total > 0 ? Math.round(((fullyCovered + partiallyCovered) / total) * 100) : 0
    };
  }, [traceabilityData]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'fully_covered':
        return 'bg-emerald-950/50 border-emerald-800 text-emerald-400';
      case 'partially_covered':
        return 'bg-yellow-950/50 border-yellow-800 text-yellow-400';
      case 'uncovered':
        return 'bg-red-950/50 border-red-800 text-red-400';
      default:
        return 'bg-zinc-900 border-zinc-800 text-zinc-400';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'fully_covered':
        return <CheckCircle2 size={14} className="text-emerald-500" />;
      case 'partially_covered':
        return <AlertTriangle size={14} className="text-yellow-500" />;
      case 'uncovered':
        return <AlertTriangle size={14} className="text-red-500" />;
      default:
        return null;
    }
  };

  const toggleExpand = (reqId) => {
    setExpandedReq(expandedReq === reqId ? null : reqId);
  };

  if (requirements.length === 0) {
    return (
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-8 text-center">
        <Layers size={32} className="mx-auto text-zinc-600 mb-3" />
        <p className="text-zinc-500">No requirements to trace</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Coverage Summary */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-zinc-200 flex items-center gap-2">
            <Target size={16} className="text-orange-500" />
            Traceability Coverage
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('matrix')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                viewMode === 'matrix' 
                  ? 'bg-orange-600 text-white' 
                  : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
              }`}
            >
              Matrix
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                viewMode === 'list' 
                  ? 'bg-orange-600 text-white' 
                  : 'bg-zinc-800 text-zinc-400 hover:text-zinc-200'
              }`}
            >
              List
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div className="bg-zinc-950 rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-white">{stats.total}</div>
            <div className="text-xs text-zinc-500">Requirements</div>
          </div>
          <div className="bg-emerald-950/30 rounded-lg p-4 text-center border border-emerald-900/50">
            <div className="text-2xl font-bold text-emerald-400">{stats.fullyCovered}</div>
            <div className="text-xs text-emerald-600">Fully Covered</div>
          </div>
          <div className="bg-yellow-950/30 rounded-lg p-4 text-center border border-yellow-900/50">
            <div className="text-2xl font-bold text-yellow-400">{stats.partiallyCovered}</div>
            <div className="text-xs text-yellow-600">Partial</div>
          </div>
          <div className="bg-red-950/30 rounded-lg p-4 text-center border border-red-900/50">
            <div className="text-2xl font-bold text-red-400">{stats.uncovered}</div>
            <div className="text-xs text-red-600">Uncovered</div>
          </div>
        </div>

        {/* Coverage Bar */}
        <div className="h-3 bg-zinc-800 rounded-full overflow-hidden">
          <div className="h-full flex">
            <div 
              className="bg-emerald-500 transition-all duration-500"
              style={{ width: `${stats.coveragePercent}%` }}
            />
            <div 
              className="bg-yellow-500 transition-all duration-500"
              style={{ width: `${stats.partialPercent - stats.coveragePercent}%` }}
            />
          </div>
        </div>
        <div className="flex justify-between mt-2 text-xs text-zinc-500">
          <span>{stats.coveragePercent}% fully covered</span>
          <span>{stats.partialPercent}% with any coverage</span>
        </div>
      </div>

      {/* Matrix View */}
      {viewMode === 'matrix' && (
        <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-zinc-800">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    Requirement
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    <div className="flex items-center justify-center gap-1">
                      <Code2 size={12} />
                      Code
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    <div className="flex items-center justify-center gap-1">
                      <TestTube2 size={12} />
                      Tests
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-zinc-400 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {Object.entries(traceabilityData).map(([reqId, entry]) => (
                  <React.Fragment key={reqId}>
                    <tr 
                      className="hover:bg-zinc-800/30 cursor-pointer transition-colors"
                      onClick={() => toggleExpand(reqId)}
                    >
                      <td className="px-4 py-3">
                        <div className="flex items-center gap-2">
                          {expandedReq === reqId ? (
                            <ChevronDown size={14} className="text-zinc-500" />
                          ) : (
                            <ChevronRight size={14} className="text-zinc-500" />
                          )}
                          <span className="font-mono text-orange-400 text-sm">{reqId}</span>
                          <span className="text-zinc-400 text-sm truncate max-w-xs">
                            {entry.requirement.description?.substring(0, 50)}...
                          </span>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {entry.codeChanges.length > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-blue-950/50 text-blue-400 rounded text-xs">
                            <Code2 size={10} />
                            {entry.codeChanges.length}
                          </span>
                        ) : (
                          <span className="text-zinc-600">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        {entry.tests.length > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-950/50 text-purple-400 rounded text-xs">
                            <TestTube2 size={10} />
                            {entry.tests.length}
                          </span>
                        ) : (
                          <span className="text-zinc-600">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs ${getStatusColor(entry.status)}`}>
                          {getStatusIcon(entry.status)}
                          {entry.status.replace('_', ' ')}
                        </span>
                      </td>
                    </tr>
                    
                    {/* Expanded Details */}
                    {expandedReq === reqId && (
                      <tr>
                        <td colSpan={4} className="bg-zinc-950/50 px-4 py-4">
                          <div className="grid grid-cols-3 gap-4">
                            {/* Requirement Details */}
                            <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                              <div className="flex items-center gap-2 mb-3">
                                <FileSearch size={14} className="text-orange-500" />
                                <span className="text-xs font-semibold text-zinc-400 uppercase">Requirement</span>
                              </div>
                              <p className="text-sm text-zinc-300 mb-2">{entry.requirement.description}</p>
                              <div className="flex gap-2">
                                <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                  entry.requirement.priority === 'high' ? 'bg-red-950 text-red-400' :
                                  entry.requirement.priority === 'medium' ? 'bg-yellow-950 text-yellow-400' :
                                  'bg-zinc-800 text-zinc-400'
                                }`}>
                                  {entry.requirement.priority}
                                </span>
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400">
                                  {entry.requirement.type}
                                </span>
                              </div>
                            </div>
                            
                            {/* Code Changes */}
                            <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                              <div className="flex items-center gap-2 mb-3">
                                <Code2 size={14} className="text-blue-500" />
                                <span className="text-xs font-semibold text-zinc-400 uppercase">Code Changes</span>
                              </div>
                              {entry.codeChanges.length > 0 ? (
                                <div className="space-y-2">
                                  {entry.codeChanges.map((change, idx) => (
                                    <div key={idx} className="text-sm">
                                      <div className="font-mono text-blue-400 text-xs">{change.filepath}</div>
                                      <div className="text-zinc-500 text-xs">{change.purpose}</div>
                                      {change.additions !== undefined && (
                                        <div className="flex gap-2 mt-1 text-[10px]">
                                          <span className="text-emerald-400">+{change.additions}</span>
                                          <span className="text-red-400">-{change.deletions || 0}</span>
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-zinc-600 text-sm">No code changes linked</p>
                              )}
                            </div>
                            
                            {/* Tests */}
                            <div className="bg-zinc-900 rounded-lg p-4 border border-zinc-800">
                              <div className="flex items-center gap-2 mb-3">
                                <TestTube2 size={14} className="text-purple-500" />
                                <span className="text-xs font-semibold text-zinc-400 uppercase">Tests</span>
                              </div>
                              {entry.tests.length > 0 ? (
                                <div className="space-y-2">
                                  {entry.tests.map((test, idx) => (
                                    <div key={idx} className="text-sm">
                                      <div className="font-mono text-purple-400 text-xs">{test.name}</div>
                                      <div className="text-zinc-500 text-xs">{test.description}</div>
                                      <span className={`text-[10px] px-1.5 py-0.5 rounded mt-1 inline-block ${
                                        test.test_type === 'unit' ? 'bg-blue-950 text-blue-400' :
                                        test.test_type === 'integration' ? 'bg-purple-950 text-purple-400' :
                                        'bg-orange-950 text-orange-400'
                                      }`}>
                                        {test.test_type}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-zinc-600 text-sm">No tests linked</p>
                              )}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="space-y-4">
          {Object.entries(traceabilityData).map(([reqId, entry]) => (
            <div 
              key={reqId}
              className={`border rounded-xl p-4 ${getStatusColor(entry.status)}`}
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono text-orange-400 font-semibold">{reqId}</span>
                    {getStatusIcon(entry.status)}
                  </div>
                  <p className="text-sm text-zinc-300">{entry.requirement.description}</p>
                </div>
                <span className={`text-[10px] px-2 py-1 rounded ${
                  entry.requirement.priority === 'high' ? 'bg-red-950 text-red-400' :
                  entry.requirement.priority === 'medium' ? 'bg-yellow-950 text-yellow-400' :
                  'bg-zinc-800 text-zinc-400'
                }`}>
                  {entry.requirement.priority}
                </span>
              </div>
              
              {/* Trace Links */}
              <div className="flex items-center gap-4 text-xs">
                <div className="flex items-center gap-1">
                  <Link2 size={12} className="text-zinc-500" />
                </div>
                
                {entry.codeChanges.length > 0 && (
                  <div className="flex items-center gap-1 text-blue-400">
                    <Code2 size={12} />
                    <span>{entry.codeChanges.map(c => c.filepath.split('/').pop()).join(', ')}</span>
                  </div>
                )}
                
                {entry.codeChanges.length > 0 && entry.tests.length > 0 && (
                  <ChevronRight size={12} className="text-zinc-600" />
                )}
                
                {entry.tests.length > 0 && (
                  <div className="flex items-center gap-1 text-purple-400">
                    <TestTube2 size={12} />
                    <span>{entry.tests.map(t => t.name).join(', ')}</span>
                  </div>
                )}
                
                {entry.codeChanges.length === 0 && entry.tests.length === 0 && (
                  <span className="text-zinc-600 italic">No linked artifacts</span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TraceabilityMatrix;

//__________________________GenAI: Generated code ends here______________________________//
