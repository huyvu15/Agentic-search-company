from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import re

from chatbot import GeminiChatbot, create_chatbot
from main import search_internet
from deff.search import fn_search_company

import uvicorn

class SearchChatRequest(BaseModel):
    query: str
    max_results: int = 3
    temperature: float = 0.3
    max_tokens: int = 700


class AssistantRequest(BaseModel):
    message: str
    max_results: int = 5
    temperature: float = 0.3
    max_tokens: int = 700


class SourceItem(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None


class SearchChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    steps: List[str]


app = FastAPI(title="MobiWork Search Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SYSTEM_PROMPT = (
    "Bạn là trợ lý AI thông minh, trả lời bằng tiếng Việt, ngắn gọn, logic. "
    "Bạn có thể trả lời câu hỏi thường hoặc tìm kiếm thông tin khi cần thiết. "
    "Chỉ tìm kiếm khi người dùng hỏi về thông tin cụ thể, sự kiện, dữ liệu, hoặc yêu cầu tìm hiểu về chủ đề nào đó. "
    "Với câu chào hỏi, trò chuyện thường, câu hỏi lý thuyết cơ bản thì chỉ cần trả lời trực tiếp."
)

FUNCTION_DECISION_PROMPT = (
    "Phân tích câu hỏi sau và quyết định có cần tìm kiếm thông tin từ internet không. "
    "Trả lời chỉ 'YES' nếu cần tìm kiếm, 'NO' nếu không cần.\n\n"
    "Cần tìm kiếm khi:\n"
    "- Hỏi về thông tin cụ thể, sự kiện, dữ liệu mới nhất\n"
    "- Tìm hiểu về công ty, sản phẩm, dịch vụ cụ thể\n"
    "- Hỏi về tin tức, xu hướng hiện tại\n"
    "- Yêu cầu tìm kiếm, tra cứu thông tin\n\n"
    "Không cần tìm kiếm khi:\n"
    "- Chào hỏi, trò chuyện thường\n"
    "- Hỏi về khái niệm, lý thuyết cơ bản\n"
    "- Yêu cầu giải thích, hướng dẫn chung\n"
    "- Câu hỏi mang tính cá nhân, chủ quan\n\n"
    "Câu hỏi: {query}\n"
    "Quyết định:"
)

PROMPT_ANALYSIS_PROMPT = (
    "Phân tích prompt sau và trích xuất thông tin quan trọng để tìm kiếm. "
    "Trả lời theo định dạng JSON:\n"
    "{{\n"
    '  "company_name": "tên công ty nếu có",\n'
    '  "contact_name": "tên liên hệ nếu có",\n'
    '  "search_queries": ["câu truy vấn tìm kiếm 1", "câu truy vấn tìm kiếm 2"],\n'
    '  "search_type": "company_research" hoặc "general"\n'
    "}}\n\n"
    "Quy tắc:\n"
    "- Nếu có tên công ty, tạo search query: 'tên công ty + thông tin công ty'\n"
    "- Nếu có tên liên hệ, tạo search query: 'tên liên hệ + tên công ty'\n"
    "- Tạo nhiều search query khác nhau để tìm thông tin đa dạng\n"
    "- Nếu không có thông tin cụ thể, dùng search_type: 'general'\n\n"
    "Prompt: {prompt}\n"
    "Kết quả:"
)


_bot: Optional[GeminiChatbot] = None


def get_bot() -> GeminiChatbot:
    global _bot
    if _bot is None:
        _bot = create_chatbot()
    return _bot


def should_search(query: str) -> bool:
    bot = get_bot()
    decision_prompt = FUNCTION_DECISION_PROMPT.format(query=query)
    
    try:
        response = bot.chat(decision_prompt, temperature=0.1, max_tokens=10)
        decision = response.strip().upper()
        return decision == "YES"
    except Exception as e:
        print(f"Lỗi khi quyết định tìm kiếm: {e}")
        search_keywords = ["tìm kiếm", "tra cứu", "thông tin về", "search", "tìm hiểu", "công ty", "sản phẩm"]
        return any(keyword in query.lower() for keyword in search_keywords)


def analyze_prompt(prompt: str) -> Dict[str, Any]:
    """Phân tích prompt để trích xuất thông tin quan trọng cho tìm kiếm"""
    bot = get_bot()
    analysis_prompt = PROMPT_ANALYSIS_PROMPT.format(prompt=prompt)
    
    try:
        response = bot.chat(analysis_prompt, temperature=0.1, max_tokens=500)
        
        # Tìm JSON trong response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            return json.loads(json_str)
        else:
            # Fallback nếu không parse được JSON
            return {
                "company_name": None,
                "contact_name": None,
                "search_queries": [prompt[:100]],  # Dùng phần đầu của prompt
                "search_type": "general"
            }
    except Exception as e:
        print(f"Lỗi khi phân tích prompt: {e}")
        # Fallback
        return {
            "company_name": None,
            "contact_name": None,
            "search_queries": [prompt[:100]],
            "search_type": "general"
        }


@app.post("/api/search-chat", response_model=SearchChatResponse)
def search_chat(req: SearchChatRequest) -> SearchChatResponse:
    steps: List[str] = []
    steps.append(f"Nhận truy vấn: {req.query}")

    results = search_internet(req.query, max_results=req.max_results)
    steps.append(f"Tìm kiếm DuckDuckGo: lấy {len(results)} kết quả")
    print(results)

    context_snippets: List[str] = []
    for idx, r in enumerate(results, start=1):
        title = (r.get("title") or "").strip()
        url = (r.get("url") or "").strip()
        content = (r.get("content") or "").strip()
        if content:
            # rút gọn để giảm token
            snippet = content[:1200]
            context_snippets.append(f"[{idx}] {title} ({url})\n{snippet}")

    # 3) Gọi LLM tổng hợp
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Câu hỏi: {req.query}\n\n"
        "Các trích đoạn nguồn (đã đánh số):\n"
        + "\n\n".join(context_snippets)
        + "\n\nYêu cầu: Trả lời súc tích, dùng bullet khi phù hợp, chèn [n] tương ứng nguồn."
    )

    bot = get_bot()
    answer = bot.chat(prompt, temperature=req.temperature, max_tokens=req.max_tokens)
    steps.append("Tổng hợp câu trả lời từ các trích đoạn nguồn")

    return SearchChatResponse(
        answer=answer,
        sources=[SourceItem(**r) for r in results],
        steps=steps,
    )


@app.post("/api/assistant", response_model=SearchChatResponse)
def assistant(req: AssistantRequest) -> SearchChatResponse:
    steps: list[str] = [f"Nhận yêu cầu: {req.message}"]
    
    needs_search = should_search(req.message)
    steps.append(f"Phân tích yêu cầu: {'Cần tìm kiếm thông tin' if needs_search else 'Trả lời trực tiếp'}")
    
    sources: list[dict] = []
    if needs_search:
        # Phân tích prompt để trích xuất thông tin quan trọng
        analysis = analyze_prompt(req.message)
        steps.append(f"Phân tích prompt: tìm thấy công ty '{analysis.get('company_name', 'N/A')}', liên hệ '{analysis.get('contact_name', 'N/A')}'")
        
        # Sử dụng search queries đã được phân tích
        search_queries = analysis.get('search_queries', [req.message])
        steps.append(f"Tạo {len(search_queries)} câu truy vấn tìm kiếm")
        
        sources = fn_search_company(search_queries, max_results=req.max_results)
        steps.append(f"Thu thập {len(sources)} nguồn thông tin")
        
        context = "\n\n".join(
            [
                f"[{i+1}] {(s.get('title') or '').strip()} ({(s.get('url') or '').strip()})\n{(s.get('content') or '')[:1200]}"
                for i, s in enumerate(sources)
                if s.get('content')
            ]
        )
        
        # Tạo prompt phù hợp với loại tìm kiếm
        if analysis.get('search_type') == 'company_research':
            company_name = analysis.get('company_name', '')
            contact_name = analysis.get('contact_name', '')
            
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Yêu cầu nghiên cứu công ty: {req.message}\n\n"
                f"Thông tin đã trích xuất:\n"
                f"- Tên công ty: {company_name}\n"
                f"- Tên liên hệ: {contact_name}\n\n"
                + ("Nguồn tham khảo:\n" + context + "\n\n" if context else "")
                + "Trả lời chi tiết về thông tin công ty, sản phẩm/dịch vụ, thông tin liên hệ. "
                + "Nếu tìm thấy thông tin CEO/người đại diện pháp luật trùng với tên liên hệ, hãy highlight điều này. "
                + "Dùng bullet khi phù hợp, kèm [n] chỉ tới nguồn."
            )
        else:
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"Yêu cầu người dùng: {req.message}\n\n"
                + ("Nguồn tham khảo:\n" + context + "\n\n" if context else "")
                + "Trả lời rõ ràng, dùng bullet khi phù hợp, kèm [n] chỉ tới nguồn."
            )
    else:
        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Yêu cầu người dùng: {req.message}\n\n"
            "Trả lời trực tiếp, thân thiện và hữu ích."
        )

    bot = get_bot()
    answer = bot.chat(prompt, temperature=req.temperature, max_tokens=req.max_tokens)
    steps.append("Tổng hợp trả lời từ model")

    return SearchChatResponse(
        answer=answer,
        sources=[SourceItem(**r) for r in sources],
        steps=steps,
    )


if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)


