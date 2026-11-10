"""
yeoncompany 법령정보 MCP 서버
법제처 국가법령정보 공동활용 API
"""
import os
import httpx
import xmltodict
from mcp.server.fastmcp import FastMCP

API_KEY = os.environ.get("LAW_API_KEY", "994eae20ad767d8efa52e9133f8fd7dd01188a72b27bf7acc643a3ce681347ad")
BASE_URL = "https://www.law.go.kr/DRF"

mcp = FastMCP("yeoncompany-법령정보")


def _get(path: str, params: dict) -> dict:
    params = {"OC": API_KEY, "type": "XML", **params}
    resp = httpx.get(f"{BASE_URL}/{path}", params=params, timeout=15)
    resp.raise_for_status()
    return xmltodict.parse(resp.text)


@mcp.tool()
def search_law(query: str, page: int = 1, display: int = 10) -> str:
    """법령명 또는 키워드로 법령을 검색합니다.

    Args:
        query: 검색할 법령명 또는 키워드 (예: "근로기준법", "개인정보")
        page: 페이지 번호 (기본값 1)
        display: 한 페이지 결과 수 (기본값 10)
    """
    data = _get("lawSearch.do", {
        "target": "law",
        "query": query,
        "page": page,
        "display": display,
    })
    root = data.get("LawSearch", {})
    total = root.get("totalCnt", "0")
    laws = root.get("law", [])
    if isinstance(laws, dict):
        laws = [laws]

    if not laws:
        return f"'{query}'에 대한 검색 결과가 없습니다."

    lines = [f"[법령 검색] '{query}' — 총 {total}건\n"]
    for law in laws:
        lines.append(
            f"• {law.get('법령명한글', '')} "
            f"[ID: {law.get('법령ID', '')}] "
            f"[시행: {law.get('시행일자', '')}] "
            f"[소관: {law.get('소관부처명', '')}]"
        )
    return "\n".join(lines)


@mcp.tool()
def get_law(law_id: str) -> str:
    """법령 ID로 법령 전문을 조회합니다. law_id는 search_law로 먼저 확인하세요.

    Args:
        law_id: 법령 ID (예: "001489")
    """
    data = _get("lawService.do", {"target": "law", "ID": law_id})
    root = data.get("law", {})
    if not root:
        return f"법령 ID '{law_id}'를 찾을 수 없습니다."

    basic = root.get("기본정보", {})
    lines = [
        f"■ {basic.get('법령명_한글', '')}",
        f"  시행: {basic.get('시행일자', '')}  |  소관: {basic.get('소관부처명', '')}",
        "",
    ]

    articles = root.get("조문", {}).get("조문단위", [])
    if isinstance(articles, dict):
        articles = [articles]

    for art in articles[:50]:
        num = art.get("조문번호", "")
        title = art.get("조문제목", "")
        content = art.get("조문내용", "") or ""
        lines.append(f"제{num}조 {title}")
        if content:
            lines.append(f"  {content}")
        items = art.get("항", [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            item_content = item.get("항내용", "") or ""
            if item_content:
                lines.append(f"  · {item_content}")
        lines.append("")

    if len(articles) > 50:
        lines.append(f"... 총 {len(articles)}조 중 50조까지 표시")

    return "\n".join(lines)


@mcp.tool()
def search_precedent(query: str, page: int = 1, display: int = 10) -> str:
    """키워드로 판례를 검색합니다.

    Args:
        query: 검색 키워드 (예: "해고", "손해배상")
        page: 페이지 번호
        display: 결과 수
    """
    data = _get("lawSearch.do", {
        "target": "prec",
        "query": query,
        "page": page,
        "display": display,
    })
    root = data.get("PrecSearch", {})
    total = root.get("totalCnt", "0")
    precs = root.get("prec", [])
    if isinstance(precs, dict):
        precs = [precs]

    if not precs:
        return f"'{query}'에 대한 판례가 없습니다."

    lines = [f"[판례 검색] '{query}' — 총 {total}건\n"]
    for p in precs:
        lines.append(
            f"• {p.get('사건명', '')} ({p.get('사건번호', '')})\n"
            f"  법원: {p.get('법원명', '')}  |  선고일: {p.get('선고일자', '')}\n"
            f"  ID: {p.get('판례일련번호', '')}"
        )
    return "\n".join(lines)


@mcp.tool()
def get_precedent(prec_id: str) -> str:
    """판례 ID로 판례 전문을 조회합니다. prec_id는 search_precedent로 먼저 확인하세요.

    Args:
        prec_id: 판례일련번호 (예: "67462")
    """
    data = _get("lawService.do", {"target": "prec", "ID": prec_id})
    root = data.get("PrecService", {})
    if not root:
        return f"판례 ID '{prec_id}'를 찾을 수 없습니다."

    return "\n".join([
        f"■ {root.get('사건명', '')}",
        f"  사건번호: {root.get('사건번호', '')}",
        f"  법원: {root.get('법원명', '')}  |  선고일: {root.get('선고일자', '')}",
        "",
        "【판시사항】",
        root.get("판시사항", "") or "(없음)",
        "",
        "【판결요지】",
        root.get("판결요지", "") or "(없음)",
        "",
        "【참조조문】",
        root.get("참조조문", "") or "(없음)",
    ])


@mcp.tool()
def search_interpretation(query: str, page: int = 1, display: int = 10) -> str:
    """키워드로 법령해석례를 검색합니다.

    Args:
        query: 검색 키워드 (예: "근로시간", "계약 해지")
        page: 페이지 번호
        display: 결과 수
    """
    data = _get("lawSearch.do", {
        "target": "expc",
        "query": query,
        "page": page,
        "display": display,
    })
    root = data.get("ExpcSearch", {})
    total = root.get("totalCnt", "0")
    items = root.get("expc", [])
    if isinstance(items, dict):
        items = [items]

    if not items:
        return f"'{query}'에 대한 법령해석례가 없습니다."

    lines = [f"[법령해석례] '{query}' — 총 {total}건\n"]
    for item in items:
        lines.append(
            f"• {item.get('안건명', '')} (회신번호: {item.get('회신번호', '')})\n"
            f"  회신일: {item.get('회신일자', '')}  |  소관: {item.get('소관부처명', '')}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    mcp.run(transport="sse", host="0.0.0.0", port=port)
