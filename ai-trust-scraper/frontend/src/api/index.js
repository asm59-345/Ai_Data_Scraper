/**
 * src/api/index.js
 * ----------------
 * All FastAPI calls live here.  The Vite dev-server proxies /api → http://localhost:8000
 * so every axios call uses the relative base URL "/api".
 */

import axios from 'axios'

const BASE_URL = '/api'

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
  headers: { 'Content-Type': 'application/json' },
})

// ── Response interceptor — surface error messages nicely ─────────────────
client.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg =
      err?.response?.data?.detail ||
      err?.response?.data?.message ||
      err?.message ||
      'Unknown error'
    return Promise.reject(new Error(msg))
  }
)

// ── Endpoints ─────────────────────────────────────────────────────────────

/** Health check */
export const healthCheck = () => client.get('/')

/**
 * Trigger the scraping pipeline.
 * @param {Object} payload  { sources, pubmed_max, blog_sources, youtube_ids }
 */
export const triggerScrape = (payload) => client.post('/scrape', payload)

/** Poll pipeline status */
export const getScrapeStatus = () => client.get('/scrape/status')

/**
 * Fetch paginated results.
 * @param {Object} params  { limit, offset, min_score, tag }
 */
export const getResults = (params = {}) =>
  client.get('/results', { params })

/**
 * Fetch results for a single source.
 * @param {string} source  e.g. "pubmed" | "openai" | "youtube"
 */
export const getResultsBySource = (source, limit = 50) =>
  client.get(`/results/${source}`, { params: { limit } })

/** Aggregated statistics */
export const getStats = () => client.get('/stats')

/** All unique tags */
export const getTags = () => client.get('/tags')

/** Clear all results */
export const clearResults = () => client.delete('/results')
