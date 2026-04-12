import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
})

export async function getQuote(ticker) {
  const response = await api.get(`/api/stocks/quote/${ticker}`)
  return response.data
}

export async function getNews(ticker) {
  const response = await api.get(`/api/stocks/news/${ticker}`)
  return response.data
}

export async function askAria(question, ticker) {
  const response = await api.post('/api/query', {
    question,
    tickers: [ticker],
    filters: { ticker },
  })
  return response.data
}
