import { useEffect, useRef, useState } from 'react'
import './index.css'
import { searchChat, type SearchChatRes } from './lib/api'

type Role = 'user' | 'assistant'
type Message = { id: string; role: Role; content: string }
type Panel = { answer: string; sources: { title?: string; url?: string; content?: string }[]; steps: string[] }

function Sidebar(
  { items }: { items: { id: string; title: string }[] }
) {
  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 border-r border-gray-200 bg-gradient-to-b from-blue-50 to-indigo-50">
      <div className="p-4 text-gray-700 text-sm font-semibold">Lịch sử</div>
      <div className="flex-1 overflow-y-auto">
        {items.length === 0 ? (
          <div className="p-4 text-gray-500 text-sm">Chưa có hội thoại</div>
        ) : (
          <ul className="p-2 space-y-1">
            {items.map(i => (
              <li key={i.id} className="px-3 py-2 rounded-lg hover:bg-white hover:shadow-sm cursor-pointer text-gray-600 text-sm truncate transition-all duration-200">
                {i.title}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="p-3 border-t border-gray-200 text-xs text-gray-500">MobiWork AI Assistant</div>
    </aside>
  )
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user'
  return (
    <div className="w-full">
      <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
        {!isUser && (
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
            AI
          </div>
        )}
        <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap shadow-sm ${isUser ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white' : 'bg-white text-gray-800 border border-gray-200'}`}>
          {msg.content}
        </div>
        {isUser && (
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-gray-400 to-gray-600 flex items-center justify-center text-xs font-bold text-white shadow-lg">
            U
          </div>
        )}
      </div>
    </div>
  )
}

function ChatInput({ onSend, loading }: { onSend: (text: string) => void; loading: boolean }) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim()) {
        onSend(value.trim())
        setValue('')
      }
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-6">
      <div className="rounded-2xl border border-gray-200 bg-white shadow-lg backdrop-blur">
        <textarea
          ref={inputRef}
          rows={1}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Hỏi bất cứ điều gì..."
          className="w-full resize-none bg-transparent outline-none p-4 text-gray-800 placeholder:text-gray-500"
        />
        <div className="flex items-center justify-between border-t border-gray-200 p-2">
          <div className="text-xs text-gray-500 px-2">Nhấn Enter để gửi • Shift+Enter để xuống dòng</div>
          <button
            onClick={() => { if (value.trim()) { onSend(value.trim()); setValue('') } }}
            disabled={loading || !value.trim()}
            className="mx-2 my-1 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:bg-gray-300 disabled:text-gray-500 px-4 py-2 text-sm font-medium text-white shadow-sm transition-all duration-200"
          >
            {loading ? 'Đang xử lý...' : 'Gửi'}
          </button>
        </div>
      </div>
    </div>
  )
}

function Header() {
  return (
    <header className="sticky top-0 z-10 border-b border-gray-200 bg-white/80 backdrop-blur shadow-sm">
      <div className="mx-auto max-w-6xl px-4 h-14 flex items-center justify-between">
        <div className="text-lg font-semibold text-gray-800">MobiWork AI Assistant</div>
        <div className="text-xs text-gray-500 bg-gray-100 px-3 py-1 rounded-full">Answer • Sources • Steps</div>
      </div>
    </header>
  )
}

function App() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [panel, setPanel] = useState<Panel | null>(null)

  async function sendMessage(text: string) {
    const userMsg: Message = { id: crypto.randomUUID(), role: 'user', content: text }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)
    try {
      const res: SearchChatRes = await searchChat({ message: text, max_results: 5 })
      const assistantMsg: Message = { id: crypto.randomUUID(), role: 'assistant', content: res.answer }
      setMessages(prev => [...prev, assistantMsg])
      setPanel({ answer: res.answer, sources: res.sources, steps: res.steps })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="h-full flex bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Sidebar items={[]} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-5xl px-4 py-6 grid md:grid-cols-3 gap-6">
            {messages.length === 0 ? (
              <div className="md:col-span-3 text-center text-gray-500 text-sm py-24">
                <div className="text-4xl mb-4">🤖</div>
                <div>Hãy bắt đầu cuộc trò chuyện với AI Assistant…</div>
              </div>
            ) : (
              <>
                <div className="md:col-span-2 space-y-4">
                  {messages.map(m => (
                    <ChatMessage key={m.id} msg={m} />
                  ))}
                </div>
                <div className="md:col-span-1 space-y-4">
                  <section className="rounded-2xl border border-gray-200 bg-white shadow-sm p-4">
                    <div className="text-sm font-semibold text-gray-700 mb-3">📚 Sources</div>
                    <div className="mt-2 space-y-2">
                      {panel?.sources?.slice(0,6).map((s, i) => (
                        <a key={i} className="block text-xs text-blue-600 hover:text-blue-800 hover:underline truncate p-2 rounded-lg hover:bg-blue-50 transition-colors" href={s.url} target="_blank" rel="noreferrer">[{i+1}] {s.title || s.url}</a>
                      )) || <div className="text-xs text-gray-500 p-2">Không có nguồn</div>}
                    </div>
                  </section>
                  <section className="rounded-2xl border border-gray-200 bg-white shadow-sm p-4">
                    <div className="text-sm font-semibold text-gray-700 mb-3">⚡ Steps</div>
                    <ol className="mt-2 list-decimal list-inside text-xs text-gray-600 space-y-1">
                      {panel?.steps?.map((s, i) => (<li key={i} className="p-1">{s}</li>)) || <li className="p-1">Đang chờ…</li>}
                    </ol>
                  </section>
                </div>
              </>
            )}
          </div>
        </main>
        <ChatInput onSend={sendMessage} loading={loading} />
      </div>
    </div>
  )
}

export default App
