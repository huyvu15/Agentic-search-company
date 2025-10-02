export type Source = { title?: string; url?: string; content?: string }
export type AssistantReq = { message: string; max_results?: number }
export type SearchChatRes = { answer: string; sources: Source[]; steps: string[] }

export async function searchChat(req: AssistantReq): Promise<SearchChatRes> {
  const res = await fetch('/api/assistant', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text)
  }
  return res.json()
}


