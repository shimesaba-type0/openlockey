from fastapi import Request
from typing import Dict, Any

def get_template_context(request: Request) -> Dict[str, Any]:
    """
    テンプレートに渡すコンテキストを取得する
    """
    context = {
        "request": request,
        "is_authenticated": getattr(request.state, "is_authenticated", False),
        "user": getattr(request.state, "user", None),
    }
    return context

