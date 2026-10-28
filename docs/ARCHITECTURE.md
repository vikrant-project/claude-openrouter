# 🏗 Architecture & Technical Design

`claude-openrouter` bridges the official **Claude Code CLI** to **OpenRouter's Free Tier** using an intelligent local proxy pattern. It enables seamless tool use, autonomous multi-turn reasoning, and infinite zero-downtime execution across 16+ free LLM backends.

---

## 🌟 High-Level Diagram

```
+-------------------------------------------------------------------------+
|                           Claude Code CLI                               |
|                  (Native Binary: ~/.local/bin/claude)                   |
+-------------------------------------------------------------------------+
                                    |
                    Anthropic Protocol (POST /v1/messages)
                    - Tools Definitions (JSON Schema)
                    - Chat History & Thinking Tokens
                    - Streaming SSE Request
                                    v
+-------------------------------------------------------------------------+
|                  Local Auto-Failover Proxy Bridge                       |
|                          (127.0.0.1:4141)                               |
|                                                                         |
|  +--------------------+   +-------------------+   +------------------+  |
|  | Protocol Converter |-->|  Failover Router  |-->|  SSE Formatter   |  |
|  | Anthropic <-> OAI  |   | Cooldown & Health |   | Content / Tools  |  |
|  +--------------------+   +-------------------+   +------------------+  |
+-------------------------------------------------------------------------+
                                    |
                        OpenAI Chat Completions API
                                    v
+-------------------------------------------------------------------------+
|                        OpenRouter Cloud Gateway                         |
|                   16+ Ranked Free Models (Pool)                         |
|                                                                         |
| [openrouter/free] -> [cohere/north-mini-code] -> [nvidia/nemotron] ... |
+-------------------------------------------------------------------------+
```

---

## 🔍 Core Subsystems

### 1. Protocol Adaptation (`src/sanitizers.py` & LiteLLM)
- **Anthropic Tools Mapping**: Claude Code exposes function tools (`Bash`, `FileRead`, `FileEdit`, `Glob`, `Grep`). The adapter converts Anthropic tool specs to standard OpenAI tool calls (`tool_calls`).
- **Response Normalization**: OpenRouter models return OpenAI completions. LiteLLM's `LiteLLMMessagesToCompletionTransformationHandler` maps them into Anthropic structured messages.
- **Thinking Token Protection**: When reasoning models output thinking tokens without text, the sanitizer ensures Claude Code always receives a valid content block so the CLI parser never panics.

### 2. Intelligent Auto-Failover Pool (`src/failover_pool.py`)
- **Health Tracking**: The bridge tracks request counts, successes, failures, and cooldown timestamps for every model in the pool.
- **Circuit Breaker & Cooldown**: When a model encounters:
  - `HTTP 429` (Rate limit reached)
  - `HTTP 402` (Daily free limit reached)
  - `HTTP 502/503/504` (Provider temporary outage)
  - Context window exceeded
  It is placed into a temporary **60-second cooldown** state.
- **Instant Fallback**: The request is instantly retried on the next available candidate in milliseconds without terminating the active terminal session.
- **Deadlock Prevention**: If all 16 models are simultaneously marked in cooldown, the cooldown on the model closest to expiration is automatically cleared, ensuring the loop never starves.

### 3. Server-Sent Events (SSE) Streaming (`src/bridge.py`)
Claude Code relies on real-time SSE streaming for interactive terminal updates. The bridge emits:
1. `event: ping` keepalive heartbeats every 10 seconds to prevent client timeout during long generations.
2. `event: message_start` with metadata matching the requested Claude model.
3. `event: content_block_start`, `event: content_block_delta`, `event: content_block_stop`.
4. `event: message_delta` with stop reasons (`end_turn`, `tool_use`, `max_tokens`).
5. `event: message_stop`.

---

## 🔒 Security & Local Isolation

- The bridge strictly listens on loopback (`127.0.0.1`). It does not bind to external network interfaces.
- Requests between Claude Code and the local proxy are authenticated via a cryptographically random token (`~/.claude/openrouter_token`), preventing unauthorized local process access.
- Configuration files containing keys are secured with `chmod 600`.
