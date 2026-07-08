import { useState } from 'react'

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
      <div>
        <h1>Create Your Companion</h1>
        <input placeholder="Name" value={form.name}
          onChange={e => setForm({ ...form, name: e.target.value })} />
        <input placeholder="Relationship (e.g. close friend)" value={form.relationship_type}
          onChange={e => setForm({ ...form, relationship_type: e.target.value })} />
        <textarea placeholder="Backstory" value={form.backstory}
          onChange={e => setForm({ ...form, backstory: e.target.value })} />
        <input placeholder="Speaking style" value={form.speaking_style}
          onChange={e => setForm({ ...form, speaking_style: e.target.value })} />
        <button onClick={createCompanion}>Create</button>
      </div>
    )
  }

  return (
    <div>
      <h1>{companion.name}</h1>
      <div>
        {messages.map((msg, i) => (
          <p key={i}><strong>{msg.role}:</strong> {msg.text}</p>
        ))}
      </div>
      <input value={input} onChange={e => setInput(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && sendMessage()} />
      <button onClick={sendMessage}>Send</button>
    </div>
  )
}

export default App