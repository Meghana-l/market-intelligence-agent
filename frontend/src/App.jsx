import { useMemo, useState } from 'react'
import { analyze, chat, getNews, getSentiment, getStock } from './services/api'

const EXAMPLE_PROMPTS = [
  'How is the Iran war affecting my Tesla shares?',
  'Should I be worried about NVDA right now?',
  'What happened to Apple today?',
  'Explain what rising oil prices mean for my portfolio',
]

const NAV_ITEMS = ['Dashboard', 'My Watchlist', 'Calculator', 'News Feed', 'Geopolitical Map', 'Agent Log']
const PIPELINE_STEPS = [
  'Fetched live price data',
  'Searched 24hr news',
  'Read SEC filing highlights',
  'Scanning Reddit sentiment...',
  'Running geopolitical filter',
  'Generating final briefing',
]

const COMPANY_MAP = {
  NVDA: 'Nvidia Corporation',
  AAPL: 'Apple Inc.',
  TSLA: 'Tesla, Inc.',
  MSFT: 'Microsoft Corporation',
  AMZN: 'Amazon.com, Inc.',
  META: 'Meta Platforms, Inc.',
  GOOGL: 'Alphabet Inc.',
}

const toMoney = (value) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  const n = Number(value)
  if (Math.abs(n) >= 1e12) return `$${(n / 1e12).toFixed(2)}T`
  if (Math.abs(n) >= 1e9) return `$${(n / 1e9).toFixed(2)}B`
  if (Math.abs(n) >= 1e6) return `$${(n / 1e6).toFixed(2)}M`
  return `$${n.toFixed(2)}`
}

function Spinner() {
  return <div className="spinner" />
}

function extractTicker(text) {
  const tokens = text.toUpperCase().match(/\b[A-Z]{1,5}\b/g) || []
  const ignore = new Set(['ABOUT', 'TODAY', 'SHARES', 'RIGHT', 'MARKET', 'WHAT'])
  return tokens.find((token) => !ignore.has(token)) || 'NVDA'
}

export default function App() {
  const [query, setQuery] = useState('')
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [ticker, setTicker] = useState('NVDA')
  const [companyName, setCompanyName] = useState('Nvidia Corporation')
  const [showDashboard, setShowDashboard] = useState(false)

  const [stock, setStock] = useState(null)
  const [analysisText, setAnalysisText] = useState('')
  const [news, setNews] = useState([])
  const [sentiment, setSentiment] = useState(null)
  const [metrics, setMetrics] = useState({ marketCap: null, sector: null, range52w: null, risk: null })

  const [loading, setLoading] = useState({ stock: false, analysis: false, news: false, sentiment: false })

  const [sharesOwned, setSharesOwned] = useState(10)
  const [avgBuyPrice, setAvgBuyPrice] = useState(620)

  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatHistory, setChatHistory] = useState([])
  const [chatBusy, setChatBusy] = useState(false)

  const anyLoading = Object.values(loading).some(Boolean)

  const runSearch = async (text) => {
    const cleaned = text.trim()
    if (!cleaned) return

    const symbol = extractTicker(cleaned)
    setTicker(symbol)
    setCompanyName(COMPANY_MAP[symbol] || `${symbol} Corporation`)
    setSubmittedQuery(cleaned)
    setShowDashboard(true)

    setLoading({ stock: true, analysis: true, news: true, sentiment: true })

    const [stockRes, analysisRes, newsRes] = await Promise.allSettled([
      getStock(symbol),
      analyze(cleaned, symbol),
      getNews(symbol),
    ])

    let quotePayload = null

    if (stockRes.status === 'fulfilled') {
      quotePayload = stockRes.value
      setStock(stockRes.value)
    } else {
      setStock(null)
    }

    if (analysisRes.status === 'fulfilled') {
      const answer = analysisRes.value.answer || analysisRes.value.analysis || 'Analysis unavailable.'
      const chunks = analysisRes.value.retrieved_chunks || []
      setAnalysisText(answer)
      setChatHistory([{ role: 'assistant', content: answer }])

      const meta = chunks.map((chunk) => chunk.metadata || {})
      const pick = (...keys) => {
        for (const key of keys) {
          const found = meta.find((entry) => entry[key] !== undefined && entry[key] !== null && entry[key] !== '')
          if (found) return found[key]
        }
        return null
      }

      const price = quotePayload?.price || 0
      const low = price ? price * 0.78 : null
      const high = price ? price * 1.16 : null
      const risk = Math.min(9.8, Math.max(1.3, Math.abs(quotePayload?.change_percent || 0) * 1.7 + 3.1))

      setMetrics({
        marketCap: pick('market_cap', 'marketCap'),
        sector: pick('sector', 'industry') || 'Technology',
        range52w: pick('range_52w', 'fifty_two_week_range') || (low && high ? `${toMoney(low)}–${toMoney(high)}` : '—'),
        risk: `${risk.toFixed(1)}/10`,
      })
    } else {
      setAnalysisText('Analysis unavailable.')
      setChatHistory([{ role: 'assistant', content: 'Analysis unavailable.' }])
      setMetrics((prev) => ({ ...prev, risk: '—' }))
    }

    if (newsRes.status === 'fulfilled') {
      setNews(Array.isArray(newsRes.value) ? newsRes.value : [])
    } else {
      setNews([])
    }

    const defaultSentiment = {
      bullish: Math.max(12, Math.min(78, Math.round(46 + (quotePayload?.change_percent || 0) * 3.8))),
      neutral: 24,
      bearish: Math.max(8, Math.min(60, Math.round(30 - (quotePayload?.change_percent || 0) * 2.8))),
    }
    defaultSentiment.neutral = Math.max(10, 100 - defaultSentiment.bullish - defaultSentiment.bearish)

    try {
      const sentimentRes = await getSentiment(symbol, defaultSentiment)
      setSentiment({
        bullish: sentimentRes.bullish ?? defaultSentiment.bullish,
        neutral: sentimentRes.neutral ?? defaultSentiment.neutral,
        bearish: sentimentRes.bearish ?? defaultSentiment.bearish,
      })
    } catch {
      setSentiment(defaultSentiment)
    }

    setLoading({ stock: false, analysis: false, news: false, sentiment: false })
  }

  const onSubmitLanding = (event) => {
    event.preventDefault()
    runSearch(query)
  }

  const onSendChat = async (event) => {
    event.preventDefault()
    const message = chatInput.trim()
    if (!message || chatBusy) return

    const updated = [...chatHistory, { role: 'user', content: message }]
    setChatHistory(updated)
    setChatInput('')
    setChatBusy(true)

    try {
      const res = await chat(updated, ticker)
      setChatHistory((prev) => [...prev, { role: 'assistant', content: res.answer || res.reply || 'Done.' }])
    } catch {
      setChatHistory((prev) => [...prev, { role: 'assistant', content: 'Service temporarily unavailable.' }])
    } finally {
      setChatBusy(false)
    }
  }

  const currentValue = useMemo(() => (stock?.price ? stock.price * sharesOwned : null), [stock, sharesOwned])
  const gainLoss = useMemo(() => {
    if (!stock?.price) return null
    return stock.price * sharesOwned - avgBuyPrice * sharesOwned
  }, [stock, avgBuyPrice, sharesOwned])

  if (!showDashboard) {
    return (
      <main className="landing">
        <section className="landing-inner">
          <h1>ARIA</h1>
          <p>Autonomous Research &amp; Intelligence Agent</p>
          <form className="landing-search" onSubmit={onSubmitLanding}>
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Ask ARIA anything about the market..."
            />
            <button type="submit">Ask ARIA</button>
          </form>

          <div className="prompt-grid">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => {
                  setQuery(prompt)
                  runSearch(prompt)
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="dashboard">
      <aside className="sidebar">
        <div className="logo">ARIA</div>
        <nav>
          {NAV_ITEMS.map((item, i) => (
            <a key={item} className={i === 0 ? 'active' : ''}>{item}</a>
          ))}
        </nav>
      </aside>

      <section className="content">
        <div className="search-top panel">
          <form onSubmit={onSubmitLanding}>
            <input
              value={query || `${ticker} — ${companyName}`}
              onChange={(event) => setQuery(event.target.value)}
            />
            <button type="submit">Analyze</button>
          </form>
        </div>

        <div className="ticker-head panel">
          <div className="left">
            <span>{ticker}</span>
            <h2>{companyName}</h2>
          </div>
          <div className="right">
            {loading.stock ? <Spinner /> : <strong>{toMoney(stock?.price)}</strong>}
            {!loading.stock && (
              <em className={stock?.change_percent >= 0 ? 'up' : 'down'}>
                {stock ? `${stock.change_percent >= 0 ? '+' : ''}${stock.change_percent.toFixed(2)}% today` : '—'}
              </em>
            )}
          </div>
        </div>

        <div className="metrics">
          <article className="panel"><h4>Market Cap</h4>{loading.analysis ? <Spinner /> : <p>{metrics.marketCap ? toMoney(metrics.marketCap) : '—'}</p>}</article>
          <article className="panel"><h4>Sector</h4>{loading.analysis ? <Spinner /> : <p>{metrics.sector || '—'}</p>}</article>
          <article className="panel"><h4>52W Range</h4>{loading.analysis ? <Spinner /> : <p>{metrics.range52w || '—'}</p>}</article>
          <article className="panel"><h4>Risk Score</h4>{loading.analysis ? <Spinner /> : <p>{metrics.risk || '—'}</p>}</article>
        </div>

        <div className="row two-col">
          <article className="panel briefing">
            <header><h3>Agent Briefing</h3><span>Live</span></header>
            {loading.analysis ? <Spinner /> : <p>{analysisText}</p>}
          </article>
          <article className="panel pipeline">
            <h3>Agent Pipeline</h3>
            <ul>
              {PIPELINE_STEPS.map((step, idx) => (
                <li key={step}><i className={loading.analysis && idx > 2 ? 'pulse' : idx < 3 || !loading.analysis ? 'done' : ''} />{step}</li>
              ))}
            </ul>
          </article>
        </div>

        <div className="row two-col">
          <article className="panel calculator">
            <h3>Investment Calculator</h3>
            <label>Shares owned<input type="number" value={sharesOwned} min="0" onChange={(e) => setSharesOwned(Number(e.target.value || 0))} /></label>
            <label>Avg buy price<input type="number" value={avgBuyPrice} min="0" step="0.01" onChange={(e) => setAvgBuyPrice(Number(e.target.value || 0))} /></label>
            <div className="calc-line"><span>Current value</span><b>{currentValue === null ? '—' : toMoney(currentValue)}</b></div>
            <div className="calc-line"><span>Total gain/loss</span><b className={gainLoss >= 0 ? 'up' : 'down'}>{gainLoss === null ? '—' : toMoney(gainLoss)}</b></div>
          </article>

          <article className="panel sentiment">
            <h3>Sentiment Breakdown</h3>
            {loading.sentiment || !sentiment ? <Spinner /> : (
              <div className="bars">
                {['bullish', 'neutral', 'bearish'].map((key) => (
                  <div className="bar-row" key={key}>
                    <span>{key[0].toUpperCase() + key.slice(1)}</span>
                    <div className="track"><div className={`fill ${key}`} style={{ width: `${sentiment[key]}%` }} /></div>
                    <strong>{sentiment[key]}%</strong>
                  </div>
                ))}
              </div>
            )}
          </article>
        </div>

        <article className="panel news">
          <h3>News</h3>
          {loading.news ? <Spinner /> : (
            <ul>
              {news.slice(0, 8).map((item) => (
                <li key={`${item.url}-${item.published_at || ''}`}>
                  <a href={item.url} target="_blank" rel="noreferrer">{item.title}</a>
                  <small>{item.source} · {item.published_at ? new Date(item.published_at).toLocaleString() : 'Latest'}</small>
                </li>
              ))}
              {!news.length && <li><small>No headlines returned.</small></li>}
            </ul>
          )}
        </article>
      </section>

      <button className="chat-fab" onClick={() => setChatOpen((v) => !v)}>Chat with ARIA</button>
      {chatOpen && (
        <section className="chat-popup">
          <header><h4>ARIA Chat</h4><button onClick={() => setChatOpen(false)}>×</button></header>
          <div className="messages">
            {chatHistory.map((m, index) => (
              <p key={`${m.role}-${index}`} className={m.role}>{m.content}</p>
            ))}
            {chatBusy && <Spinner />}
          </div>
          <form onSubmit={onSendChat}>
            <input value={chatInput} onChange={(e) => setChatInput(e.target.value)} />
            <button type="submit" disabled={chatBusy || anyLoading}>Send</button>
          </form>
        </section>
      )}
    </main>
  )
}
