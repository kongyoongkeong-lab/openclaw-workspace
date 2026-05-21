# Tools: Retrieval & Analysis

## 🔍 External Tools
- `tavily_search(query)`: Your primary tool for high-precision web data.
- `ddg_search(query)`: Secondary tool for broad/news data.
- `browser_fetch(url)`: Used to scrape specific technical documentation.

## 💾 Internal Tools
- `qdrant_query(vector)`: Retrieve long-term memory chunks.
- `qdrant_upsert(data)`: Save new "Knowledge Gems" to permanent memory.
- `file_read(path)`: Deep parsing of local workspace documents.

## ⚙️ Optimization Rules
- **Token Efficiency:** Convert HTML to Clean Markdown before processing.