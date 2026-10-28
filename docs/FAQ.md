# ❓ Frequently Asked Questions (FAQ)

### Q: Is this 100% free?
**A:** Yes! It utilizes the verified `:free` models on OpenRouter. As long as you have an OpenRouter account with an API key, you will not be charged.

### Q: What happens when an OpenRouter free model hits its rate limit?
**A:** OpenRouter free models have individual rate limits (requests per minute or daily quota). When a model hits HTTP 429, our bridge catches it, marks that model on cooldown for 60 seconds, and immediately transparently retries on the next working model.

### Q: Can Claude Code still edit files and execute bash commands?
**A:** Yes! Models ranked 1 through 9 in the pool are thoroughly verified for function and tool calling. Claude Code can read, write, edit, run terminal commands, and inspect project directories normally.

### Q: How do I check which model is currently answering?
**A:** Run:
```bash
claude-openrouter --status
```
This displays a real-time table of all models, their success counts, failure counts, and cooldown countdowns.

### Q: Can I add custom or paid models to the pool?
**A:** Absolutely. Edit `~/.claude/openrouter-config.json` and add any model slug supported by OpenRouter (e.g. `anthropic/claude-3.5-sonnet`, `meta-llama/llama-3.3-70b-instruct`) to the `"models"` list.

### Q: How do I change my OpenRouter API key?
**A:** Run:
```bash
claude-openrouter --set-key <YOUR_NEW_KEY>
```
Or edit `~/.claude/openrouter-config.json`.
