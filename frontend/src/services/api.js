import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

async function tryEndpoints(requests) {
  let lastError
  for (const request of requests) {
    try {
      const response = await request()
      return response.data
    } catch (error) {
      lastError = error
    }
  }
  throw lastError
}

export function getStock(ticker) {
  return tryEndpoints([
    () => api.get(`/stock/${ticker}`),
    () => api.get(`/api/stocks/quote/${ticker}`),
  ])
}

export function getNews(ticker) {
  return tryEndpoints([
    () => api.get(`/news/${ticker}`),
    () => api.get(`/api/stocks/news/${ticker}`),
  ])
}

export function analyze(query, ticker) {
  return tryEndpoints([
    () => api.post('/analyze', { query, ticker }),
    () => api.post('/api/query', {
      question: query,
      tickers: [ticker],
      filters: { ticker },
    }),
  ])
}

export async function getSentiment(ticker, fallback = null) {
  try {
    return await tryEndpoints([() => api.get(`/sentiment/${ticker}`)])
  } catch {
    if (fallback) return fallback
    throw new Error('Sentiment unavailable')
  }
}

export function chat(messages, ticker) {
  return tryEndpoints([
    () => api.post('/chat', { messages, ticker }),
    () => {
      const last = messages[messages.length - 1]
      return api.post('/api/query', {
        question: last?.content || '',
        tickers: [ticker],
        filters: { ticker },
      })
    },
  ])
}
