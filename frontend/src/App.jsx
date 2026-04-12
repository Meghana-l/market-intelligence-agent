import { useEffect, useMemo, useState } from 'react'
import { askAria, getNews, getQuote } from './services/api'

const EXAMPLE_PROMPTS = [
  'How is the Iran war affecting my Tesla shares?',
  'Should I be worried about NVDA right now?',
  'What happened to Apple today?',
  'Explain what rising oil prices mean for my portfolio',
]

const SIDEBAR_LINKS = ['Dashboard', 'My watchlist', 'Calculator', 'News feed', 'Geopolitical map', 'Agent log']

const PIPELINE_STEPS = [
  'Fetched live price data',
  'Scanned latest market headlines',
  'Retrieved vector intelligence',
  'Applied portfolio impact filter',
  'Generated ARIA final briefing',
]

function extractTicker(query) {
  const matches = query.toUpperCase().match(/\b[A-Z]{1,5}\b/g)
  if (!matches?.length) return 'AAPL'
  const blacklist = new Set(['ABOUT', 'RIGHT', 'TODAY', 'SHARES', 'MARKET'])
  return matches.find((word) => !blacklist.has(word)) || 'AAPL'
}

function formatMoney(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return '—'
  const numeric = Number(value)
  if (Math.abs(numeric) >= 1_000_000_000_000) return `$${(numeric / 1_000_000_000_000).toFixed(2)}T`
  if (Math.abs(numeric) >= 1_000_000_000) return `$${(numeric / 1_000_000_000).toFixed(2)}B`
  if (Math.abs(numeric) >= 1_000_000) return `$${(numeric / 1_000_000).toFixed(2)}M`
  return `$${numeric.toFixed(2)}`
}

function LoadingSpinner() {
  return <div className="spinner" aria-label="Loading" />
}

function App() {
  const [queryInput, setQueryInput] = useState('')
  const [activeQuery, setActiveQuery] = useState('')
  const [hasSearched, setHasSearched] = useState(false)
  const [ticker, setTicker] = useState('AAPL')

  const [quote, setQuote] = useState(null)
  const [news, setNews] = useState([])
  const [analysis, setAnalysis] = useState('')
  const [retrievedChunks, setRetrievedChunks] = useState([])
  const [errors, setErrors] = useState({})

  const [isFetchingQuote, setIsFetchingQuote] = useState(false)
  const [isFetchingNews, setIsFetchingNews] = useState(false)
  const [isFetchingAnalysis, setIsFetchingAnalysis] = useState(false)

  const [sharesOwned, setSharesOwned] = useState(10)
  const [avgBuyPrice, setAvgBuyPrice] = useState(250)

  const [chatOpen, setChatOpen] = useState(false)
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [chatLoading, setChatLoading] = useState(false)

  const busy = isFetchingQuote || isFetchingNews || isFetchingAnalysis

  const runSearch = async (queryText) => {
    const cleaned = queryText.trim()
    if (!cleaned) return

    const detectedTicker = extractTicker(cleaned)
    setTicker(detectedTicker)
    setHasSearched(true)
    setActiveQuery(cleaned)
    setErrors({})

    setIsFetchingQuote(true)
    setIsFetchingNews(true)
    setIsFetchingAnalysis(true)

    const [quoteRes, newsRes, analysisRes] = await Promise.allSettled([
      getQuote(detectedTicker),
      getNews(detectedTicker),
      askAria(cleaned, detectedTicker),
    ])

    if (quoteRes.status === 'fulfilled') {
      setQuote(quoteRes.value)
    } else {
      setQuote(null)
      setErrors((prev) => ({ ...prev, quote: 'Unable to load live quote right now.' }))
    }
    setIsFetchingQuote(false)

    if (newsRes.status === 'fulfilled') {
      setNews(newsRes.value || [])
    } else {
      setNews([])
      setErrors((prev) => ({ ...prev, news: 'Unable to load headlines right now.' }))
    }
    setIsFetchingNews(false)

    if (analysisRes.status === 'fulfilled') {
      setAnalysis(analysisRes.value.answer || '')
      setRetrievedChunks(analysisRes.value.retrieved_chunks || [])
      setChatMessages([{ role: 'assistant', text: analysisRes.value.answer || 'Analysis completed.' }])
    } else {
      setAnalysis('')
      setRetrievedChunks([])
      setErrors((prev) => ({ ...prev, analysis: 'Unable to generate ARIA briefing right now.' }))
    }
    setIsFetchingAnalysis(false)
  }

  const handleLandingSubmit = async (event) => {
    event.preventDefault()
    await runSearch(queryInput)
  }

  const handleChatSend = async (event) => {
    event.preventDefault()
    const message = chatInput.trim()
    if (!message || chatLoading) return

    setChatMessages((prev) => [...prev, { role: 'user', text: message }])
    setChatInput('')
    setChatLoading(true)

    try {
      const response = await askAria(message, ticker)
      setChatMessages((prev) => [...prev, { role: 'assistant', text: response.answer || 'Done.' }])
    } catch {
      setChatMessages((prev) => [...prev, { role: 'assistant', text: 'I hit a temporary issue. Please try again.' }])
    } finally {
      setChatLoading(false)
    }
  }

  const inferredMeta = useMemo(() => {
    const metadata = retrievedChunks.map((chunk) => chunk.metadata || {})
    const pick = (keys) => {
      for (const key of keys) {
        const found = metadata.find((item) => item[key] !== undefined && item[key] !== null && item[key] !== '')
        if (found) return found[key]
      }
      return null
    }

    const currentPrice = quote?.price || 0
    const lower = currentPrice ? currentPrice * 0.8 : null
    const upper = currentPrice ? currentPrice * 1.2 : null

    return {
      companyName: pick(['company_name', 'company']) || `${ticker} Corporation`,
      marketCap: pick(['market_cap', 'marketCap']),
      sector: pick(['sector', 'industry']) || 'Market Intelligence',
      range52w: pick(['range_52w', 'fifty_two_week_range']) || (lower && upper ? `${formatMoney(lower)} - ${formatMoney(upper)}` : '—'),
    }
  }, [retrievedChunks, quote, ticker])

  const riskScore = useMemo(() => {
    if (!quote) return '—'
    const score = Math.min(9.9, Math.max(1.2, Math.abs(quote.change_percent || 0) * 1.8 + 3.4))
    return `${score.toFixed(1)}/10`
  }, [quote])

  const sentiment = useMemo(() => {
    const basis = quote?.change_percent || 0
    const bullish = Math.max(12, Math.min(78, Math.round(45 + basis * 4)))
    const bearish = Math.max(8, Math.min(60, Math.round(28 - basis * 3)))
    const neutral = Math.max(10, 100 - bullish - bearish)
    return { bullish, neutral, bearish }
  }, [quote])

  const currentValue = useMemo(() => (quote?.price ? sharesOwned * quote.price : null), [sharesOwned, quote])
  const gainLoss = useMemo(() => {
    if (!quote?.price) return null
    const costBasis = sharesOwned * avgBuyPrice
    return currentValue - costBasis
  }, [sharesOwned, avgBuyPrice, currentValue, quote])

  useEffect(() => {
    const interval = setInterval(() => {
      if (hasSearched && ticker && !isFetchingQuote) {
        getQuote(ticker).then(setQuote).catch(() => undefined)
      }
    }, 25000)
    return () => clearInterval(interval)
  }, [hasSearched, ticker, isFetchingQuote])

  if (!hasSearched) {
    return (
      <main className="landing-page">
        <div className="landing-shell">
          <h1>ARIA</h1>
          <p className="landing-subtitle">Autonomous Research &amp; Intelligence Agent</p>

          <form className="landing-search" onSubmit={handleLandingSubmit}>
            <input
              value={queryInput}
              onChange={(event) => setQueryInput(event.target.value)}
              placeholder="Ask ARIA anything about the market..."
            />
            <button type="submit">Ask ARIA</button>
          </form>

          <div className="chip-grid">
            {EXAMPLE_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                type="button"
                className="chip"
                onClick={() => {
                  setQueryInput(prompt)
                  runSearch(prompt)
                }}
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>
      </main>
    )
  }

  return (
    <main className="dashboard-page">
      <aside className="sidebar">
        <div className="brand">ARIA</div>
        <nav>
          {SIDEBAR_LINKS.map((item, index) => (
            <button key={item} className={index === 0 ? 'nav-link active' : 'nav-link'} type="button">
              {item}
            </button>
          ))}
        </nav>
      </aside>

      <section className="dashboard-content">
        <header className="topbar">
          <form
            className="query-form"
            onSubmit={(event) => {
              event.preventDefault()
              runSearch(queryInput || activeQuery)
            }}
          >
            <input value={queryInput} onChange={(event) => setQueryInput(event.target.value)} />
            <button type="submit" disabled={busy}>
              {busy ? 'Analyzing...' : 'Re-analyze'}
            </button>
          </form>
        </header>

        <div className="ticker-row card">
          <div>
            <span className="ticker-pill">{ticker}</span>
            <h2>{inferredMeta.companyName}</h2>
          </div>
          <div className="price-wrap">
            {isFetchingQuote ? (
              <LoadingSpinner />
            ) : (
              <>
                <strong>{quote ? formatMoney(quote.price) : '—'}</strong>
                <span className={quote?.change_percent >= 0 ? 'change up' : 'change down'}>
                  {quote ? `${quote.change_percent >= 0 ? '+' : ''}${quote.change_percent.toFixed(2)}%` : '—'}
                </span>
              </>
            )}
          </div>
        </div>

        <section className="metrics-grid">
          {[{ label: 'Market Cap', value: inferredMeta.marketCap ? formatMoney(inferredMeta.marketCap) : '—' },
            { label: 'Sector', value: inferredMeta.sector },
            { label: '52W Range', value: inferredMeta.range52w },
            { label: 'Risk Score', value: riskScore }].map((metric) => (
            <article key={metric.label} className="metric card">
              <p>{metric.label}</p>
              {busy ? <LoadingSpinner /> : <h3>{metric.value}</h3>}
            </article>
          ))}
        </section>

        <section className="panel-grid">
          <article className="panel card">
            <div className="panel-head">
              <h3>Agent Briefing</h3>
              <span className="live-badge">Live</span>
            </div>
            {isFetchingAnalysis ? <LoadingSpinner /> : <p>{analysis || errors.analysis || 'Live briefing unavailable at the moment.'}</p>}
          </article>

          <article className="panel card">
            <h3>Agent Pipeline</h3>
            <ul className="pipeline-list">
              {PIPELINE_STEPS.map((step, index) => {
                const active = isFetchingAnalysis && index >= 2
                const completed = !isFetchingAnalysis || index < 2
                return (
                  <li key={step}>
                    <span className={`dot ${completed ? 'done' : active ? 'active' : ''}`} />
                    {step}
                  </li>
                )
              })}
            </ul>
          </article>

          <article className="panel card">
            <h3>Investment Calculator</h3>
            <div className="calculator-grid">
              <label>
                Shares owned
                <input type="number" min="0" value={sharesOwned} onChange={(e) => setSharesOwned(Number(e.target.value || 0))} />
              </label>
              <label>
                Avg buy price
                <input type="number" min="0" step="0.01" value={avgBuyPrice} onChange={(e) => setAvgBuyPrice(Number(e.target.value || 0))} />
              </label>
              <div className="calc-result">
                <span>Current value</span>
                <strong>{currentValue === null ? '—' : formatMoney(currentValue)}</strong>
              </div>
              <div className="calc-result">
                <span>Gain / Loss</span>
                <strong className={gainLoss >= 0 ? 'up' : 'down'}>{gainLoss === null ? '—' : formatMoney(gainLoss)}</strong>
              </div>
            </div>
          </article>

          <article className="panel card">
            <h3>Sentiment Breakdown</h3>
            {isFetchingQuote ? (
              <LoadingSpinner />
            ) : (
              <div className="sentiment-bars">
                {['bullish', 'neutral', 'bearish'].map((tone) => (
                  <div key={tone} className="sentiment-row">
                    <span>{tone[0].toUpperCase() + tone.slice(1)}</span>
                    <div className="bar-track">
                      <div className={`bar-fill ${tone}`} style={{ width: `${sentiment[tone]}%` }} />
                    </div>
                    <strong>{sentiment[tone]}%</strong>
                  </div>
                ))}
              </div>
            )}
          </article>

          <article className="panel card news-panel">
            <h3>News</h3>
            {isFetchingNews ? (
              <LoadingSpinner />
            ) : (
              <ul>
                {(news || []).slice(0, 6).map((item) => (
                  <li key={`${item.url}-${item.published_at}`}>
                    <a href={item.url} target="_blank" rel="noreferrer">
                      {item.title}
                    </a>
                    <p>
                      {item.source} · {item.published_at ? new Date(item.published_at).toLocaleString() : 'Latest'}
                    </p>
                  </li>
                ))}
                {!news.length && <li className="news-fallback">{errors.news || 'No headlines available right now.'}</li>}
              </ul>
            )}
          </article>
        </section>
      </section>

      <button className="chat-fab" type="button" onClick={() => setChatOpen((prev) => !prev)}>
        Chat with ARIA
      </button>

      {chatOpen && (
        <div className="chat-popup">
          <header>
            <h4>ARIA Chat</h4>
            <button type="button" onClick={() => setChatOpen(false)}>
              ×
            </button>
          </header>
          <div className="chat-body">
            {chatMessages.map((msg, idx) => (
              <p key={`${msg.role}-${idx}`} className={`chat-msg ${msg.role}`}>
                {msg.text}
              </p>
            ))}
            {chatLoading && <LoadingSpinner />}
          </div>
          <form onSubmit={handleChatSend} className="chat-input">
            <input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Ask a follow-up..." />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </main>
  )
}

export default App
