# Group And Channel Memory

Store conversation-specific durable context by surface or group.

Recommended structure:

```text
groups/
  telegram/
    direct-jason.md
```

Keep only durable interaction preferences, channel constraints, and stable
workflow facts. Do not store raw chat transcripts, message IDs, access tokens,
or provider metadata unless a workflow explicitly needs a sanitized reference.
