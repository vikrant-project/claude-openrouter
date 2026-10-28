# 📊 OpenRouter Free Models Catalog & Benchmarks

The pool includes **16 high-performance text and code generation free models** available through your OpenRouter API key.

---

## 🏆 Model Pool Priority Ranking

| Priority | Model ID | Context Window | Tool Use | Primary Specialty |
|:---:|---|:---:|:---:|---|
| **1** | `openrouter/free` | 200,000 | ✅ Yes | **Dynamic Meta-Router**: Balances across free models |
| **2** | `cohere/north-mini-code:free` | 256,000 | ✅ Yes | **Coding Specialist**: Multi-file refactoring & bug fixing |
| **3** | `nvidia/nemotron-3.5-lightning:free` | 1,000,000 | ✅ Yes | **Ultra Context**: 1M context with reasoning |
| **4** | `poolside/laguna-s-2.1:free` | 262,144 | ✅ Yes | **Software Engineering**: Code analysis & synthesis |
| **5** | `poolside/laguna-xs-2.1:free` | 262,144 | ✅ Yes | **Speed Specialist**: Rapid single-turn edits |
| **6** | `dots-studio/dots-3-note-preview:free` | 512,000 | ✅ Yes | **Long Form**: Architectural notes & documentation |
| **7** | `nvidia/nemotron-3.5-super-vl:free` | 1,000,000 | ✅ Yes | **Heavy Reasoning**: 1M context general reasoning |
| **8** | `nvidia/nemotron-3-ultra-550b-a55b:free` | 1,000,000 | ✅ Yes | **Massive Parameter**: Deep logical synthesis |
| **9** | `xingchen-agi/xing4.0-29b-a4b:free` | 262,144 | ✅ Yes | Instruction following & tool routing |
| **10** | `google/gemma-4-31b-it:free` | 262,144 | ⚠️ Chat | Google open instruction model |
| **11** | `google/gemma-4-26b-a4b-it:free` | 262,144 | ⚠️ Chat | Gemma Mixture of Experts |
| **12** | `recursive/flint-v1.0:free` | 262,144 | ⚠️ Chat | Code and text synthesis |
| **13** | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256,000 | ⚠️ Reasoning | Compact reasoning model |
| **14** | `liquid/lfm-2.5-2.6b:free` | 65,536 | ⚠️ Fast | Liquid neural network architecture |
| **15** | `thinkingmachines/inkling:free` | 1,048,576 | ⚠️ Long | 1M Context conversational |
| **16** | `thinkingmachines/inkling-small:free` | 1,048,576 | ⚠️ Long | Lightweight 1M model |

---

## ⚡ How Failover Chooses Models

1. When you run `claude`, `openrouter/free` receives the first attempt.
2. If the active model hits a rate limit (HTTP 429) or runs out of free requests, it immediately trips the circuit breaker for **60 seconds**.
3. The bridge instantly forwards your request to `cohere/north-mini-code:free`.
4. If that hits a limit, it jumps to `nvidia/nemotron-3.5-lightning:free`.
5. You never see an error in your terminal; your coding session proceeds seamlessly!
