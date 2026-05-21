# Tools: Retrieval & Analysis

## 🔍 External Tools
- `tavily_search(query, depth, topic)`: Primary tool for high-precision web data.
- `web_search(query)`: Secondary search engine (Brave backup).
- `web_fetch(url)`: Lightweight HTML-to-markdown extraction.
- `tavily_extract(urls, query)`: Deep content extraction from specific pages.

## 🐙 GitHub Search Tools
- `gh_search_issues(query, repo)`: Search GitHub issues across repos.
- `gh_search_code(query, repo)`: Search code snippets in repos.
- `gh_api(search/issues, params)`: Raw GitHub API for structured queries.
- `gh_repo_list(query)`: Discover repos by topic/description.

**Credentials:** `gh` CLI — PAT with `repo`, `read:org` scopes in `~/.config/gh/hosts.yml`

## 💾 Internal Tools
- `qdrant_query(vector)`: Retrieve long-term memory chunks.
- `qdrant_upsert(data)`: Save "Knowledge Gems" to permanent memory.
- `file_read(path)`: Deep parsing of local workspace documents.
- `memory_search(query)`: Semantic search across past sessions.

## 📋 Search Pipeline (priority order)

```
1. Qdrant memory  ←  Check if answer already stored
2. GitHub API     ←  Search issues/code/docs
3. Tavily search  ←  Web deep dive
4. Web_fetch      ←  Extract full content from specific URLs
5. Store result   ←  qdrant_upsert() for future reuse
```

## ⚙️ Optimization Rules
- **Token Efficiency:** Convert HTML to Clean Markdown before processing.
- **Cache Results:** Always `qdrant_upsert()` novel findings for next time.
- **Cite Everything:** Every fact needs a [Source Link] or [GitHub Issue Link].