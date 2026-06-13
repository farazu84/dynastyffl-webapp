import config from './config';

// 30-second GET cache, mirroring the web app's utils/apiCache.js
const CACHE_TTL = 30 * 1000;
const cache = new Map();

export async function apiGet(path) {
  const url = `${config.API_BASE_URL}${path}`;
  const hit = cache.get(url);
  if (hit && Date.now() - hit.time < CACHE_TTL) return hit.data;

  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  const data = await res.json();
  cache.set(url, { time: Date.now(), data });
  return data;
}

export async function apiPost(path, body) {
  const res = await fetch(`${config.API_BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}
