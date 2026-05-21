# Bootstrap: @intel
**Sequence:** 02 (Sub-Process)

## Boot Directives
- Test DNS resolution for `api.tavily.com` and `api.telegram.org`.
- Initialize connection to Qdrant Vector DB (Port 6333).
- Index the `.openclaw/workspace/intel/knowledge` directory.
- Verify Tavily and DuckDuckGo search plugins are active.

## Environment
- Set `SEARCH_DEPTH=advanced`
- Set `VECTOR_SYNC=real-time`