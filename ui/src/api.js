import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8001/api/v1';

const client = axios.create({
  baseURL: BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

/**
 * Analyze a ticket using the standard synchronous endpoint
 */
export async function analyzeTicket({ ticket_id, action, github_repo, github_pr, model }) {
  const payload = {
    ticket_id,
    action,
    github_repo,
    github_pr,
    model
  };

  const res = await client.post('/analyze', payload);
  return res.data;
}

/**
 * Analyze a manually provided ticket (without Jira integration)
 */
export async function analyzeManual(ticket, action = 'analyze_requirements') {
  const res = await client.post('/analyze/manual', { ticket, action });
  return res.data;
}

/**
 * Stream analysis with Server-Sent Events for real-time progress
 * 
 * @param {Object} params - Analysis parameters
 * @param {Function} onEvent - Callback for each SSE event
 * @param {Function} onError - Callback for errors
 * @param {Function} onComplete - Callback when stream completes
 * @returns {Function} Cleanup function to close the connection
 */
export function analyzeStream({ 
  ticket_id, 
  title,
  description,
  action, 
  acceptance_criteria,
  github_repo, 
  github_pr,
  thread_id,
  model
}, onEvent, onError, onComplete) {
  const payload = {
    ticket_id,
    title,
    description,
    action,
    acceptance_criteria,
    github_repo,
    github_pr,
    thread_id,
    model
  };

  // Use fetch for SSE since axios doesn't support streaming well
  const controller = new AbortController();
  
  fetch(`${BASE}/analyze/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    signal: controller.signal
  })
    .then(async (response) => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          if (onComplete) onComplete();
          break;
        }
        
        buffer += decoder.decode(value, { stream: true });
        
        // Parse SSE events from buffer
        const lines = buffer.split('\n');
        buffer = lines.pop() || ''; // Keep incomplete line in buffer
        
        let currentEvent = null;
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            const data = line.slice(6);
            try {
              const parsed = JSON.parse(data);
              if (onEvent) onEvent(parsed, currentEvent);
            } catch (e) {
              console.warn('Failed to parse SSE data:', data);
            }
          }
        }
      }
    })
    .catch((error) => {
      if (error.name !== 'AbortError') {
        if (onError) onError(error);
      }
    });
  
  // Return cleanup function
  return () => controller.abort();
}

/**
 * Get the status of a previous analysis request
 */
export async function getRequestStatus(request_id) {
  const res = await client.get(`/status/${request_id}`);
  return res.data;
}

/**
 * List all available agents and their capabilities
 */
export async function listAgents() {
  const res = await client.get('/agents');
  return res.data;
}

/**
 * Fetch a file from a GitHub repository
 */
export async function getRepoFile(repo, path) {
  const res = await client.post('/github/file', { repo, path });
  return res.data;
}

/**
 * Get the current state of a workflow by thread ID
 */
export async function getWorkflowState(thread_id) {
  const res = await client.get(`/workflow/${thread_id}/state`);
  return res.data;
}

/**
 * Get the state history of a workflow by thread ID
 */
export async function getWorkflowHistory(thread_id) {
  const res = await client.get(`/workflow/${thread_id}/history`);
  return res.data;
}

/**
 * Resume a paused or interrupted workflow
 */
export async function resumeWorkflow(thread_id) {
  const res = await client.post('/workflow/resume', { thread_id });
  return res.data;
}

/**
 * Get the Mermaid diagram representation of the workflow
 */
export async function getWorkflowDiagram() {
  const res = await client.get('/workflow/diagram');
  return res.data;
}

export default { 
  analyzeTicket, 
  analyzeManual, 
  analyzeStream,
  getRequestStatus, 
  listAgents, 
  getRepoFile,
  getWorkflowState,
  getWorkflowHistory,
  resumeWorkflow,
  getWorkflowDiagram
};
