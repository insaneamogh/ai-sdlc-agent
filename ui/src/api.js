import axios from 'axios';

const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8001/api/v1';

const client = axios.create({
  baseURL: BASE,
  headers: {
    'Content-Type': 'application/json'
  }
});

export async function analyzeTicket({ ticket_id, action, github_repo, github_pr }) {
  const payload = {
    ticket_id,
    action,
    github_repo,
    github_pr
  };

  const res = await client.post('/analyze', payload);
  return res.data;
}

export async function analyzeManual(ticket, action = 'analyze_requirements') {
  const res = await client.post('/analyze/manual', { ticket, action });
  return res.data;
}

export async function getRequestStatus(request_id) {
  const res = await client.get(`/status/${request_id}`);
  return res.data;
}

export async function listAgents() {
  const res = await client.get('/agents');
  return res.data;
}

export async function getRepoFile(repo, path) {
  const res = await client.post('/github/file', { repo, path });
  return res.data;
}

export default { analyzeTicket, analyzeManual, getRequestStatus, listAgents, getRepoFile };
