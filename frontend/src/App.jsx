import { useState , useEffect } from 'react'
function App(){
  const[message,setMessage]=useState('Loading...')
  useEffect(()=>{
    fetch('http://127.0.0.1:8000/').then(res => res.json()).then(data => setMessage(data.message)).catch(err => setMessage('Error: '+ err.message))
  },[])
  return (
    <div>
      <h1>SoulSync</h1>
      <p>Backend says: {message}</p>
    </div>
  )
}

export default App
