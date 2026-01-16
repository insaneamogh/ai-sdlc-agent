import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Loader2,
  ChevronDown,
  ChevronRight,
  Play,
  Pause,
  RotateCcw
} from 'lucide-react';

/**
 * WorkflowVisualizer Component
 * 
 * Displays real-time LangGraph workflow progress with:
 * - Visual graph showing node states
 * - Timeline of events
 * - State inspector panel
 * - Support for SSE streaming events
 */

// Node status indicator
const NodeStatus = ({ status }) => {
  const statusConfig = {
    pending: { color: 'bg-zinc-700', icon: Clock, text: 'text-zinc-500' },
    running: { color: 'bg-orange-500 animate-pulse', icon: Loader2, text: 'text-orange-400' },
    completed: { color: 'bg-emerald-500', icon: CheckCircle2, text: 'text-emerald-400' },
    error: { color: 'bg-red-500', icon: AlertTriangle, text: 'text-red-400' }
  };

  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <div className={`w-3 h-3 rounded-full ${config.color}`}>
      {status === 'running' && (
        <Icon size={12} className="animate-spin text-white" />
      )}
    </div>
  );
};

// Workflow node component
const WorkflowNode = ({ node, isActive, onClick }) => {
  const statusStyles = {
    pending: 'border-zinc-700 bg-zinc-900/50',
    running: 'border-orange-500 bg-orange-950/30 shadow-lg shadow-orange-900/20',
    completed: 'border-emerald-600 bg-emerald-950/30',
    error: 'border-red-600 bg-red-950/30'
  };

  return (
    <button
      onClick={onClick}
      className={`relative p-4 rounded-xl border-2 transition-all w-full text-left ${
        statusStyles[node.status] || statusStyles.pending
      } ${isActive ? 'ring-2 ring-orange-500/50' : ''}`}
    >
      <div className="flex items-center gap-3">
        <div className={`p-2 rounded-lg ${
          node.status === 'completed' ? 'bg-emerald-600' :
          node.status === 'running' ? 'bg-orange-600' :
          node.status === 'error' ? 'bg-red-600' :
          'bg-zinc-800'
        }`}>
          <node.icon size={18} className="text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-sm text-zinc-200 truncate">{node.name}</h4>
          <p className="text-xs text-zinc-500 mt-0.5">
            {node.status === 'running' ? 'Processing...' :
             node.status === 'completed' ? `Completed in ${node.duration || '?'}s` :
             node.status === 'error' ? 'Failed' :
             'Waiting...'}
          </p>
        </div>
        <NodeStatus status={node.status} />
      </div>
      
      {/* Progress bar for running nodes */}
      {node.status === 'running' && node.progress !== undefined && (
        <div className="mt-3 h-1 bg-zinc-800 rounded-full overflow-hidden">
          <div 
            className="h-full bg-orange-500 transition-all duration-300"
            style={{ width: `${node.progress}%` }}
          />
        </div>
      )}
    </button>
  );
};

// Edge connector between nodes
const EdgeConnector = ({ animated, status }) => (
  <div className="flex items-center justify-center py-2">
    <div className={`w-0.5 h-8 ${
      status === 'completed' ? 'bg-emerald-600' :
      animated ? 'bg-gradient-to-b from-orange-500 to-transparent animate-pulse' :
      'bg-zinc-800'
    }`} />
  </div>
);

// Timeline event component
const TimelineEvent = ({ event }) => {
  const eventStyles = {
    workflow_start: { icon: Play, color: 'text-blue-400', bg: 'bg-blue-950' },
    node_start: { icon: Activity, color: 'text-orange-400', bg: 'bg-orange-950' },
    node_complete: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-950' },
    node_error: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-950' },
    workflow_complete: { icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-950' },
    workflow_error: { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-950' }
  };

  const style = eventStyles[event.event] || eventStyles.node_start;
  const Icon = style.icon;

  return (
    <div className="flex items-start gap-3 py-2">
      <div className={`p-1.5 rounded-lg ${style.bg}`}>
        <Icon size={12} className={style.color} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-zinc-300">
            {event.event.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </span>
          {event.node && (
            <span className="text-xs text-zinc-600">• {event.node}</span>
          )}
        </div>
        <span className="text-[10px] text-zinc-600 font-mono">
          {new Date(event.timestamp).toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

// State inspector panel
const StateInspector = ({ state, expanded, onToggle }) => {
  if (!state) return null;

  return (
    <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-zinc-800/50 transition-colors"
      >
        <span className="text-sm font-medium text-zinc-300">State Inspector</span>
        {expanded ? <ChevronDown size={16} className="text-zinc-500" /> : <ChevronRight size={16} className="text-zinc-500" />}
      </button>
      {expanded && (
        <div className="px-4 pb-4">
          <pre className="text-xs text-zinc-500 font-mono overflow-auto max-h-60 bg-zinc-950 rounded-lg p-3">
            {JSON.stringify(state, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

// Main WorkflowVisualizer component
export default function WorkflowVisualizer({
  nodes = [],
  events = [],
  currentState = null,
  threadId = null,
  onNodeClick = () => {},
  onRetry = () => {},
  className = ''
}) {
  const [selectedNode, setSelectedNode] = useState(null);
  const [stateExpanded, setStateExpanded] = useState(false);
  const [timelineExpanded, setTimelineExpanded] = useState(true);

  // Find the currently running node
  const runningNode = nodes.find(n => n.status === 'running');

  // Calculate overall progress
  const completedCount = nodes.filter(n => n.status === 'completed').length;
  const totalCount = nodes.length;
  const overallProgress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  // Determine overall status
  const hasError = nodes.some(n => n.status === 'error');
  const isComplete = completedCount === totalCount && totalCount > 0;
  const isRunning = nodes.some(n => n.status === 'running');

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header with progress */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-semibold text-zinc-200">Workflow Progress</h3>
            {threadId && (
              <p className="text-xs text-zinc-600 font-mono mt-1">Thread: {threadId}</p>
            )}
          </div>
          <div className="flex items-center gap-3">
            {hasError && (
              <button
                onClick={onRetry}
                className="flex items-center gap-2 px-3 py-1.5 bg-orange-600 hover:bg-orange-500 rounded-lg text-xs font-medium text-white transition-colors"
              >
                <RotateCcw size={12} />
                Retry
              </button>
            )}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold ${
              hasError ? 'bg-red-950 text-red-400 border border-red-800' :
              isComplete ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
              isRunning ? 'bg-orange-950 text-orange-400 border border-orange-800' :
              'bg-zinc-900 text-zinc-400 border border-zinc-800'
            }`}>
              {hasError ? <AlertTriangle size={12} /> :
               isComplete ? <CheckCircle2 size={12} /> :
               isRunning ? <Loader2 size={12} className="animate-spin" /> :
               <Clock size={12} />}
              <span>
                {hasError ? 'Error' :
                 isComplete ? 'Complete' :
                 isRunning ? 'Running' :
                 'Pending'}
              </span>
            </div>
          </div>
        </div>

        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs">
            <span className="text-zinc-500">Progress</span>
            <span className="text-zinc-400 font-mono">{completedCount}/{totalCount} nodes</span>
          </div>
          <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
            <div 
              className={`h-full transition-all duration-500 ${
                hasError ? 'bg-red-500' :
                isComplete ? 'bg-emerald-500' :
                'bg-orange-500'
              }`}
              style={{ width: `${overallProgress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Graph visualization */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-5">
        <h4 className="text-sm font-medium text-zinc-400 mb-4">Workflow Graph</h4>
        <div className="space-y-1">
          {nodes.map((node, index) => (
            <React.Fragment key={node.id}>
              <WorkflowNode
                node={node}
                isActive={selectedNode === node.id}
                onClick={() => {
                  setSelectedNode(node.id);
                  onNodeClick(node);
                }}
              />
              {index < nodes.length - 1 && (
                <EdgeConnector
                  animated={node.status === 'completed' && nodes[index + 1]?.status === 'running'}
                  status={node.status}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Timeline */}
      <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden">
        <button
          onClick={() => setTimelineExpanded(!timelineExpanded)}
          className="w-full px-5 py-4 flex items-center justify-between hover:bg-zinc-800/50 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Activity size={16} className="text-orange-500" />
            <span className="text-sm font-medium text-zinc-300">Event Timeline</span>
            <span className="text-xs text-zinc-600">({events.length} events)</span>
          </div>
          {timelineExpanded ? <ChevronDown size={16} className="text-zinc-500" /> : <ChevronRight size={16} className="text-zinc-500" />}
        </button>
        {timelineExpanded && (
          <div className="px-5 pb-4 max-h-60 overflow-y-auto">
            {events.length > 0 ? (
              <div className="space-y-1">
                {events.slice().reverse().map((event, index) => (
                  <TimelineEvent key={index} event={event} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-600 py-4 text-center">No events yet</p>
            )}
          </div>
        )}
      </div>

      {/* State inspector */}
      <StateInspector
        state={currentState}
        expanded={stateExpanded}
        onToggle={() => setStateExpanded(!stateExpanded)}
      />
    </div>
  );
}
