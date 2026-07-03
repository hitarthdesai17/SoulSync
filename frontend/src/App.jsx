import { useState } from 'react'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([])

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = { role: 'user', text: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')

    const res = await fetch('http://127.0.0.1:8000/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: input })
    })
    const data = await res.json()

    const aiMessage = { role: 'HitMan', text: data.reply }
    setMessages(prev => [...prev, aiMessage])
  }

  return (
    <div>
      <h1>SoulSync</h1>
      <div>
        {messages.map((msg, i) => (
          <p key={i}><strong>{msg.role}:</strong> {msg.text}</p>
        ))}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>
    </div>
  )
}

export default App