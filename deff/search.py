from typing import List, Dict, Optional, Union
from main import search_internet


def fn_search_company(query: Union[str, List[str]], max_results: int = 5) -> List[Dict[str, Optional[str]]]:
    """Tìm kiếm thông tin công ty với query đơn hoặc nhiều queries"""
    if isinstance(query, str):
        return search_internet(query=query, max_results=max_results)
    elif isinstance(query, list):
        all_results = []
        for q in query:
            results = search_internet(query=q, max_results=max_results)
            all_results.extend(results)
        return all_results
    else:
        return []


