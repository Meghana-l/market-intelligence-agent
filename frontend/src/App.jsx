import { useState } from 'react'
import { askAria, getQuote } from './services/api'

const EXAMPLE_PROMPTS = [
  'How is the Iran war affecting my Tesla shares?',
  'Should I be worried about NVDA right now?',
  'What happened to Apple today?',
  'Explain what rising oil prices mean for my portfolio',
]

function App() {
  const [ticker, setTicker] = useState('AAPL')
  const [question, setQuestion] = useState('')
  const [quote, setQuote] = useState(null)
  const [answer, setAnswer] = useState('')
  const [dashboardVisible, setDashboardVisible] = useState(false)

  const runAnalysis = async () => {
    if (!question.trim()) return

    setDashboardVisible(true)
    const data = await askAria(question, ticker)
    setAnswer(data.answer)

    const marketQuote = await getQuote(ticker)
    setQuote(marketQuote)
  }

  const handlePromptClick = (prompt) => {
    setQuestion(prompt)
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    await runAnalysis()
  }

  if (!dashboardVisible) {
    return (
      <main className="landing">
        <h1>ARIA</h1>
        <p className="subtitle">Autonomous Research & Intelligence Agent</p>

        <form className="search-shell" onSubmit={handleSubmit}>
          <input
            className="search-input"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask ARIA anything about the market..."
          />
        </form>

        <div className="prompt-grid">
          {EXAMPLE_PROMPTS.map((prompt) => (
            <button key={prompt} className="prompt-chip" onClick={() => handlePromptClick(prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      </main>
    )
  }

  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <h1>ARIA Market Dashboard</h1>
        <form className="top-search" onSubmit={handleSubmit}>
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask ARIA anything about the market..."
          />
          <button type="submit">Refresh Briefing</button>
        </form>
      </header>

      <section className="panel">
        <h2>Price</h2>
        <div className="row">
          <input value={ticker} onChange={(event) => setTicker(event.target.value.toUpperCase())} />
          <button type="button" onClick={runAnalysis}>Update</button>
        </div>
        {quote ? <pre>{JSON.stringify(quote, null, 2)}</pre> : <p>Load a ticker to view live pricing.</p>}
      </section>

      <section className="panel">
        <h2>Agent Briefing</h2>
        <article>{answer || 'Run a query to generate an AI briefing.'}</article>
      </section>

      <section className="panel">
        <h2>Sentiment</h2>
        <p>Sentiment trend visualizations and factor breakdowns will render here.</p>
      </section>

      <section className="panel">
        <h2>News</h2>
        <p>Latest market headlines and source citations will appear here.</p>
      </section>

      <section className="panel">
        <h2>Calculator</h2>
        <p>Portfolio impact, exposure, and scenario calculators are shown in this panel.</p>
      </section>

      <section className="panel chat-panel">
        <h2>ARIA Chat</h2>
        <article>{answer || 'Start the conversation by asking ARIA a market question.'}</article>
      </section>
    </main>
  )
}

export default App
