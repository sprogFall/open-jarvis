"""GitHub 搜索工具。

优先使用本机已安装的 GitHub CLI（`gh`），不可用时回退到 GitHub REST Search API。
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Any, Literal
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.config import get_settings
from app.tools import ToolSpec

logger = logging.getLogger(__name__)

SearchType = Literal["repos", "code", "issues", "prs", "commits"]

# gh search 子命令与 REST API 路径映射
_GH_COMMAND: dict[SearchType, str] = {
    "repos": "repos",
    "code": "code",
    "issues": "issues",
    "prs": "prs",
    "commits": "commits",
}

_API_ENDPOINT: dict[SearchType, str] = {
    "repos": "https://api.github.com/search/repositories",
    "code": "https://api.github.com/search/code",
    "issues": "https://api.github.com/search/issues",
    "prs": "https://api.github.com/search/issues",
    "commits": "https://api.github.com/search/commits",
}

# 各类型 gh --json 字段
_GH_JSON_FIELDS: dict[SearchType, str] = {
    "repos": "fullName,description,url,stargazersCount,language,updatedAt",
    "code": "path,repository,url,textMatches",
    "issues": "number,title,url,state,repository,updatedAt,labels,author",
    "prs": "number,title,url,state,repository,updatedAt,author,isDraft",
    "commits": "sha,message,author,url,committedDate,repository",
}


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def _github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "open-jarvis",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = get_settings().github_token
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _format_repo(item: dict[str, Any]) -> str:
    name = item.get("fullName") or item.get("full_name") or "unknown"
    # gh CLI 返回 url；REST 同时有 html_url(网页) 与 url(API)，优先网页链接
    url = item.get("html_url") or item.get("url") or ""
    desc = item.get("description") or "无描述"
    stars = item.get("stargazersCount")
    if stars is None:
        stars = item.get("stargazers_count", 0)
    lang = item.get("language") or "N/A"
    updated = item.get("updatedAt") or item.get("updated_at") or ""
    return f"[{name}]({url})\nstars: {stars} | {lang} | updated: {updated}\n{desc}"


def _format_code(item: dict[str, Any]) -> str:
    path = item.get("path") or ""
    repo = item.get("repository") or {}
    if isinstance(repo, dict):
        repo_name = repo.get("fullName") or repo.get("full_name") or repo.get("name") or ""
    else:
        repo_name = str(repo)
    url = item.get("html_url") or item.get("url") or ""
    matches = item.get("textMatches") or item.get("text_matches") or []
    snippets: list[str] = []
    for m in matches[:3]:
        if isinstance(m, dict):
            frag = m.get("fragment") or m.get("text") or ""
            if frag:
                snippets.append(frag.strip())
    body = "\n".join(snippets) if snippets else "(无代码片段预览)"
    return f"[{repo_name}/{path}]({url})\n{body}"


def _format_issue_or_pr(item: dict[str, Any], kind: str) -> str:
    number = item.get("number", "")
    title = item.get("title") or "无标题"
    url = item.get("html_url") or item.get("url") or ""
    state = item.get("state") or ""
    repo = item.get("repository") or {}
    if isinstance(repo, dict):
        repo_name = repo.get("nameWithOwner") or repo.get("full_name") or repo.get("name") or ""
    else:
        repo_name = str(repo) if repo else ""
    # REST issues 搜索结果没有 repository 对象，从 repository_url 推断
    if not repo_name and item.get("repository_url"):
        repo_name = str(item["repository_url"]).rstrip("/").split("/")[-2:]
        repo_name = "/".join(repo_name) if isinstance(repo_name, list) else repo_name
    author = item.get("author") or item.get("user") or {}
    if isinstance(author, dict):
        author_name = author.get("login") or author.get("name") or ""
    else:
        author_name = str(author) if author else ""
    updated = item.get("updatedAt") or item.get("updated_at") or ""
    draft = item.get("isDraft")
    if draft is None and "draft" in item:
        draft = item.get("draft")
    draft_tag = " | draft" if draft else ""
    labels = item.get("labels") or []
    label_names: list[str] = []
    for lb in labels:
        if isinstance(lb, dict):
            label_names.append(str(lb.get("name") or ""))
        else:
            label_names.append(str(lb))
    label_names = [n for n in label_names if n]
    label_str = f" | labels: {', '.join(label_names)}" if label_names else ""
    return (
        f"[{kind} #{number}] {title} — {repo_name}\n"
        f"{url}\n"
        f"state: {state}{draft_tag} | by {author_name} | updated: {updated}{label_str}"
    )


def _format_commit(item: dict[str, Any]) -> str:
    sha = item.get("sha") or ""
    short_sha = sha[:7] if sha else ""
    # gh json 与 REST 结构不同
    message = item.get("message") or ""
    if not message:
        commit = item.get("commit") or {}
        if isinstance(commit, dict):
            message = commit.get("message") or ""
    message = message.split("\n", 1)[0] if message else "无提交信息"
    url = item.get("html_url") or item.get("url") or ""
    author = item.get("author") or {}
    if isinstance(author, dict):
        author_name = author.get("login") or author.get("name") or ""
        if not author_name:
            # REST: commit.author.name
            commit = item.get("commit") or {}
            if isinstance(commit, dict):
                ca = commit.get("author") or {}
                if isinstance(ca, dict):
                    author_name = ca.get("name") or ""
    else:
        author_name = str(author) if author else ""
    date = item.get("committedDate") or ""
    if not date:
        commit = item.get("commit") or {}
        if isinstance(commit, dict):
            ca = commit.get("author") or {}
            if isinstance(ca, dict):
                date = ca.get("date") or ""
    repo = item.get("repository") or {}
    if isinstance(repo, dict):
        repo_name = repo.get("fullName") or repo.get("full_name") or repo.get("name") or ""
    else:
        repo_name = str(repo) if repo else ""
    return f"[{repo_name}@{short_sha}]({url})\n{message}\nby {author_name} | {date}"


def _format_items(search_type: SearchType, items: list[dict[str, Any]]) -> list[str]:
    results: list[str] = []
    for item in items:
        if search_type == "repos":
            results.append(_format_repo(item))
        elif search_type == "code":
            results.append(_format_code(item))
        elif search_type == "issues":
            results.append(_format_issue_or_pr(item, "Issue"))
        elif search_type == "prs":
            results.append(_format_issue_or_pr(item, "PR"))
        elif search_type == "commits":
            results.append(_format_commit(item))
    return results


def _search_via_gh(query: str, search_type: SearchType, max_results: int) -> list[str]:
    cmd = [
        "gh",
        "search",
        _GH_COMMAND[search_type],
        query,
        "--limit",
        str(max_results),
        "--json",
        _GH_JSON_FIELDS[search_type],
    ]
    # Windows 默认用 GBK 解码，gh 输出为 UTF-8，必须显式指定
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        check=False,
    )
    if completed.returncode != 0:
        err = (completed.stderr or completed.stdout or "unknown error").strip()
        raise RuntimeError(f"gh CLI 搜索失败 (exit {completed.returncode}): {err}")

    raw = completed.stdout.strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise RuntimeError(f"gh CLI 返回了非预期结构: {type(data).__name__}")
    return _format_items(search_type, data)


def _search_via_http(query: str, search_type: SearchType, max_results: int) -> list[str]:
    q = query
    # REST 的 issues 搜索通过 is:pr 过滤 PR
    if search_type == "prs" and "is:pr" not in query:
        q = f"{query} is:pr"
    elif search_type == "issues" and "is:issue" not in query and "is:pr" not in query:
        q = f"{query} is:issue"

    params = urlencode({"q": q, "per_page": max(1, min(max_results, 100))})
    url = f"{_API_ENDPOINT[search_type]}?{params}"
    request = Request(url, headers=_github_headers(), method="GET")

    try:
        with urlopen(request, timeout=30) as resp:  # noqa: S310 — 固定 github.com API
            body = resp.read().decode("utf-8")
    except HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if e.fp else str(e)
        raise RuntimeError(f"GitHub API 错误 {e.code}: {detail}") from e
    except URLError as e:
        raise RuntimeError(f"GitHub API 网络错误: {e.reason}") from e

    payload = json.loads(body)
    items = payload.get("items") or []
    if not isinstance(items, list):
        raise RuntimeError("GitHub API 返回了非预期结构")
    return _format_items(search_type, items[:max_results])


class GitHubSearchInput(BaseModel):
    query: str = Field(
        description=(
            "GitHub 搜索关键词，支持 GitHub 搜索语法，"
            "例如 'langgraph stars:>100'、'repo:owner/name is:open label:bug'"
        ),
    )
    search_type: SearchType = Field(
        default="repos",
        description=(
            "搜索类型: 'repos'(仓库) / 'code'(代码) / 'issues'(议题) "
            "/ 'prs'(Pull Request) / 'commits'(提交)"
        ),
    )
    max_results: int = Field(default=5, description="返回结果最大数量，默认 5，最大 30")


@tool(
    args_schema=GitHubSearchInput,
    description=(
        "在 GitHub 上搜索仓库、代码、Issue、PR 或 Commit。"
        "适用于查找开源项目、代码示例、相关 issue/PR 等场景。"
        "支持 GitHub 搜索语法（如 language:python stars:>100）。"
    ),
)
async def github_search_tool(
    query: str,
    search_type: SearchType = "repos",
    max_results: int = 5,
) -> list[str]:
    max_results = max(1, min(int(max_results), 30))
    if search_type not in _GH_COMMAND:
        return [f"不支持的搜索类型: {search_type}"]

    try:
        if _gh_available():
            logger.debug("github_search: 使用 gh CLI")
            results = _search_via_gh(query, search_type, max_results)
        else:
            logger.debug("github_search: gh CLI 不可用，回退到 HTTP API")
            results = _search_via_http(query, search_type, max_results)
    except Exception as e:
        return [f"GitHub 搜索失败: {e}"]

    if not results:
        return ["未找到相关结果。"]
    return results


github_search_spec = ToolSpec(
    name="github_search",
    description=(
        "在 GitHub 上搜索仓库、代码、Issue、PR 或 Commit。"
        "适用于查找开源项目、代码示例、相关 issue/PR 等场景。"
        "支持 GitHub 搜索语法（如 language:python stars:>100）。"
    ),
    parameters_schema=github_search_tool.args_schema.model_json_schema(),
    idempotent=True,
    executor=github_search_tool,
)
