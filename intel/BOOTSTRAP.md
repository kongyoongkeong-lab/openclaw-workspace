# Bootstrap: @intel
**Sequence:** 02 (Sub-Process)

## Boot Directives
- Test DNS resolution for `api.tavily.com` and `api.github.com`.
- Initialize connection to Qdrant Vector DB (Port 6333).
- Verify `gh auth status` — check GitHub API access.
- Index the `.openclaw/workspace/intel/` directory into Qdrant.
- Verify Tavily search plugin is active.
- Load known repo list from workspace + config repos.

## Environment
- Set `SEARCH_DEPTH=advanced`
- Set `VECTOR_SYNC=real-time`
- Set `GITHUB_SEARCH=enabled`

## Known GitHub Repos
- `kongyoongkeong-lab/openclaw-workspace` — Agent configs + memory
- `kongyoongkeong-lab/openclaw-config` — Gateway + infra configs