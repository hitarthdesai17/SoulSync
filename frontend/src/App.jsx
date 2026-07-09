import { useState } from 'react'
import './App.css'

function App() {
  const [companion, setCompanion] = useState(null)
  const [form, setForm] = useState({
    name: '', relationship_type: '', backstory: '', speaking_style: ''
  })

  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])

  const createCompanion = async () => {
    const res = await fetch('http://127.0.0.1:8000/companions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...form, core_traits: {} })
    })
    const data = await res.json()
    setCompanion(data)
  }

  const sendMessage = async () => {
    if (!input.trim()) return
    const userMessage = { role: 'user', text: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    const res = await fetch('http://127.0.0.1:8000/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input, companion_id: companion.id })
    })
    const data = await res.json()
    setMessages(prev => [...prev, { role: companion.name, text: data.reply }])
  }

  if (!companion) {
    return (
      <div className="screen">
        <div className="create-card">
          <h1 className="create-title">Who do you want to talk to?</h1>

          <div className="field">
            <label className="field-label">Name</label>
            <input value={form.name}
              onChange={e => setForm({ ...form, name: e.target.value })} />
          </div>

          <div className="field">
            <label className="field-label">Relationship</label>
            <input placeholder="e.g. close friend"
              value={form.relationship_type}
              onChange={e => setForm({ ...form, relationship_type: e.target.value })} />
          </div>

          <div className="field">
            <label className="field-label">Backstory</label>
            <textarea value={form.backstory}
              onChange={e => setForm({ ...form, backstory: e.target.value })} />
          </div>

          <div className="field">
            <label className="field-label">Speaking style</label>
            <input value={form.speaking_style}
              onChange={e => setForm({ ...form, speaking_style: e.target.value })} />
          </div>

          <button className="create-btn" onClick={createCompanion}>Begin</button>
        </div>
      </div>
    )
  }

  return (
    <div className="chat-screen">
      <div className="chat-header">
        <div className="avatar" />
        <div>
          <h1 className="companion-name">{companion.name}</h1>
          <p className="relationship-badge">{companion.relationship_type}</p>
        </div>
      </div>

      <div className="messages">
        {messages.map((msg, i) => (
          <div key={i} className={`bubble ${msg.role === 'user' ? 'user' : 'companion'}`}>
            {msg.text}
          </div>
        ))}
      </div>

      <div className="input-bar">
        <input value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && sendMessage()} />
        <button className="send-btn" onClick={sendMessage}>→</button>
      </div>
    </div>
  )
}

export default App