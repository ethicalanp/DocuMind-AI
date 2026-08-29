import { useEffect, useRef, useState } from 'react'
import axios from 'axios'
import './App.css'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000' })
const messageOf = (error) => error.response?.data?.detail || error.message || 'Something went wrong.'

function App() {
  const [token, setToken] = useState(localStorage.getItem('documind_token'))
  const [user, setUser] = useState(null)
  const [authMode, setAuthMode] = useState('login')
  const [auth, setAuth] = useState({ email: '', password: '' })
  const [error, setError] = useState('')
  const [documents, setDocuments] = useState([])
  const [conversations, setConversations] = useState([])
  const [active, setActive] = useState(null)
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [notice, setNotice] = useState('')
  const [busy, setBusy] = useState(false)
  const [search, setSearch] = useState('')
  const [results, setResults] = useState([])
  const fileInput = useRef(null)

  const request = (config) => api({ ...config, headers: { Authorization: `Bearer ${token}`, ...(config.headers || {}) } })

  useEffect(() => {
    if (!token) return
    request({ url: '/auth/me' }).then(({ data }) => setUser(data)).catch(logout)
    refresh()
  }, [token])

  async function refresh() {
    try {
      const [docs, chats] = await Promise.all([request({ url: '/documents/' }), request({ url: '/conversations/' })])
      setDocuments(docs.data.documents || [])
      const items = chats.data.conversations || []
      setConversations(items)
      if (!active && items[0]) chooseConversation(items[0])
    } catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function chooseConversation(conversation) {
    setActive(conversation)
    try { const { data } = await request({ url: `/conversations/${conversation.id}/messages` }); setMessages(data.messages || []) }
    catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function submitAuth(event) {
    event.preventDefault(); setError('')
    try {
      if (authMode === 'register') await api.post('/auth/register', auth)
      const { data } = await api.post('/auth/login', auth)
      localStorage.setItem('documind_token', data.access_token); setToken(data.access_token)
    } catch (requestError) { setError(messageOf(requestError)) }
  }

  function logout() { localStorage.removeItem('documind_token'); setToken(null); setUser(null) }

  async function newConversation() {
    try { const { data } = await request({ method: 'POST', url: '/conversations/', data: { title: 'New conversation' } }); setConversations((items) => [data.conversation, ...items]); chooseConversation(data.conversation) }
    catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function upload(event) {
    const file = event.target.files?.[0]; if (!file) return
    const body = new FormData(); body.append('file', file); setBusy(true); setNotice('Indexing your document...')
    try { await request({ method: 'POST', url: '/documents/upload', data: body }); setNotice('Document indexed and ready to query.'); refresh() }
    catch (requestError) { setNotice(messageOf(requestError)) } finally { setBusy(false); event.target.value = '' }
  }

  async function send(event) {
    event.preventDefault(); if (!question.trim() || !active || busy) return
    const text = question.trim(); setQuestion(''); setBusy(true); setMessages((items) => [...items, { role: 'user', content: text }])
    try { const { data } = await request({ method: 'POST', url: '/chat/', data: { conversation_id: active.id, question: text, top_k: 5 } }); setMessages((items) => [...items, { role: 'assistant', ...data }]) }
    catch (requestError) { setNotice(messageOf(requestError)) } finally { setBusy(false) }
  }

  async function semanticSearch(event) {
    event.preventDefault(); if (!search.trim()) return
    try { const { data } = await request({ url: '/documents/search', params: { query: search, top_k: 5 } }); setResults(data.results || []) }
    catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function deleteDocument(id) {
    if (!window.confirm('Delete this document and its indexed content?')) return
    try { await request({ method: 'DELETE', url: `/documents/${id}` }); setDocuments((items) => items.filter((item) => item.id !== id)) }
    catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function downloadDocument(document) {
    try {
      const { data } = await request({ url: `/documents/${document.id}/download`, responseType: 'blob' })
      const url = URL.createObjectURL(data)
      const link = window.document.createElement('a')
      link.href = url
      link.download = document.filename
      link.click()
      URL.revokeObjectURL(url)
    } catch (requestError) { setNotice(messageOf(requestError)) }
  }

  async function deleteConversation(id) {
    try { await request({ method: 'DELETE', url: `/conversations/${id}` }); const items = conversations.filter((item) => item.id !== id); setConversations(items); setActive(items[0] || null); setMessages([]) }
    catch (requestError) { setNotice(messageOf(requestError)) }
  }

  if (!token) return <AuthScreen mode={authMode} values={auth} error={error} setValues={setAuth} onSubmit={submitAuth} toggle={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setError('') }} />
  return <div className="app-shell">
    <aside className="sidebar"><div className="brand"><b>D</b> documind<span>.</span></div><p className="side-label">WORKSPACE</p><button className="new-chat" onClick={newConversation}>+ &nbsp; New conversation</button><div className="conversation-list">{conversations.map((conversation) => <div className={`conversation ${active?.id === conversation.id ? 'selected' : ''}`} key={conversation.id}><button onClick={() => chooseConversation(conversation)}>o &nbsp; {conversation.title}</button><button className="tiny" title="Delete" onClick={() => deleteConversation(conversation.id)}>x</button></div>)}</div><div className="profile"><i>{user?.email?.[0]?.toUpperCase() || 'U'}</i><span>{user?.email}</span><button className="tiny" onClick={logout}>out</button></div></aside>
    <main className="main"><header className="topbar"><div><p className="eyebrow">PERSONAL KNOWLEDGE STUDIO</p><h1>Good to see you, <em>{user?.email?.split('@')[0]}</em>.</h1></div><div className="connection"><i /> API connected</div></header>{notice && <div className="notice">{notice}<button onClick={() => setNotice('')}>x</button></div>}<div className="stats"><div><b>{documents.length}</b><span>Documents</span></div><div><b>{conversations.length}</b><span>Conversations</span></div><div><b className="coral">{documents.filter((item) => item.status === 'processed').length}</b><span>Ready to query</span></div></div>
      <div className="workspace"><section className="chat-area"><div className="heading"><div><p className="eyebrow">ASK YOUR LIBRARY</p><h2>{active?.title || 'Choose a conversation'}</h2></div>{active && <small><i /> Grounded answers</small>}</div><div className="chat-panel">{!active ? <Empty onStart={newConversation} /> : messages.length ? <div className="messages">{messages.map((message, index) => <Message message={message} key={index} />)}{busy && <div className="typing"><i /><i /><i /></div>}</div> : <div className="empty-chat"><b>*</b><strong>What would you like to understand?</strong><span>Ask about a decision, detail, or theme in your library.</span></div>}{active && <form className="composer" onSubmit={send}><textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask anything about your documents..." rows="1" onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); send(event) } }} /><button disabled={busy || !question.trim()}>Send {'->'}</button></form>}</div></section>
        <aside className="library"><div className="heading"><div><p className="eyebrow">YOUR LIBRARY</p><h2>Documents</h2></div><button className="add" onClick={() => fileInput.current?.click()} disabled={busy}>{busy ? 'Working...' : '+ Add'}</button><input ref={fileInput} hidden type="file" accept=".pdf,.docx,.txt" onChange={upload} /></div><div className="documents">{documents.length ? documents.map((document) => <div className="document" key={document.id}><b className={`file ${document.filename.split('.').pop()}`}>{document.filename.split('.').pop()}</b><div><strong title={document.filename}>{document.filename}</strong><span>{document.status === 'processed' ? 'Ready to query' : document.status}</span></div><button className="tiny" title="Download" onClick={() => downloadDocument(document)}>v</button><button className="tiny" title="Delete" onClick={() => deleteDocument(document.id)}>x</button></div>) : <div className="library-empty"><b>[ ]</b><span>Your library is empty</span><small>Add a PDF, DOCX, or TXT file to begin.</small></div>}</div><div className="search"><div className="heading"><div><p className="eyebrow">DISCOVER</p><h2>Semantic search</h2></div></div><form onSubmit={semanticSearch}><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search across your files" /><button>{'->'}</button></form>{results.map((result, index) => <article key={index}><strong>{result.metadata?.filename || 'Document match'}</strong><p>{result.text}</p></article>)}</div></aside></div>
    </main></div>
}

function AuthScreen({ mode, values, setValues, error, onSubmit, toggle }) { return <div className="auth-page"><div className="auth-art"><div className="art-grid" /><div className="art-copy"><div className="brand"> <b>D</b> documind<span>.</span></div><h1>Make your knowledge<br /><em>work harder.</em></h1><p>One intelligent place for the documents that move your work forward.</p><blockquote>"The fastest way to find the answer is to make every page searchable."</blockquote></div></div><div className="auth-card"><p className="eyebrow">WELCOME TO DOCUMIND</p><h2>{mode === 'login' ? 'Welcome back.' : 'Create your workspace.'}</h2><p className="subtitle">{mode === 'login' ? 'Sign in to continue to your library.' : 'Start asking better questions of your documents.'}</p><form onSubmit={onSubmit}><label>Email address<input required type="email" value={values.email} onChange={(event) => setValues({ ...values, email: event.target.value })} placeholder="you@company.com" /></label><label>Password<input required minLength="6" type="password" value={values.password} onChange={(event) => setValues({ ...values, password: event.target.value })} placeholder="At least 6 characters" /></label>{error && <div className="form-error">{error}</div>}<button className="primary full">{mode === 'login' ? 'Enter workspace' : 'Create account'} <span>{'->'}</span></button></form><p className="switch">{mode === 'login' ? 'New to DocuMind?' : 'Already have an account?'} <button onClick={toggle}>{mode === 'login' ? 'Create an account' : 'Sign in'}</button></p></div></div> }
function Empty({ onStart }) { return <div className="empty-state"><b className="orb">D</b><h3>Turn documents into answers</h3><p>Upload a document, start a conversation, and ask questions in plain language.</p><button className="primary" onClick={onStart}>Start exploring</button></div> }
function Message({ message }) { return <div className={`message ${message.role}`}><b className="message-avatar">{message.role === 'assistant' ? 'D' : 'U'}</b><div><small>{message.role === 'assistant' ? 'DOCUMIND' : 'YOU'}</small><p>{message.content || message.answer}</p>{message.sources?.length > 0 && <div className="sources">Grounded in: {message.sources.map((source, index) => <span key={index}>{source.filename}</span>)}</div>}</div></div> }

export default App
