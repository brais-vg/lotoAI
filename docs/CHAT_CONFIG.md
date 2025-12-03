# Chat Configuration Variables

The following environment variables can be added to your `.env` file to customize the chat behavior:

## Chat LLM Parameters

```bash
# Temperature for OpenAI responses (0.0-2.0, default: 0.7)
# Higher = more creative, Lower = more deterministic
CHAT_TEMPERATURE=0.7

# Maximum tokens for OpenAI responses (default: 1500)
CHAT_MAX_TOKENS=1500

# Number of previous messages to include in conversational context (default: 5)
CHAT_HISTORY_LENGTH=5
```

## RAG Context Configuration

```bash
# Minimum relevance score to use RAG context (0.0-1.0, default: 0.3)
# Sources below this score will be filtered out
RAG_MIN_SCORE=0.3

# Maximum characters to show per chunk in context (default: 1000)
RAG_CONTEXT_CHARS=1000
```

## Example `.env` Addition

Add these lines to your `.env` file to use custom values:

```bash
# Chat Configuration
CHAT_TEMPERATURE=0.7
CHAT_MAX_TOKENS=1500
CHAT_HISTORY_LENGTH=5
RAG_MIN_SCORE=0.3
RAG_CONTEXT_CHARS=1000
```

## What Changed

### Before
- Temperature: 0.5 (too conservative)
- Max tokens: 1000 (sometimes insufficient)
- No conversational history
- No score filtering (low-quality context passed to LLM)
- Limited context per chunk (500 chars)

### After
- Temperature: 0.7 (more natural responses)
- Max tokens: 1500 (room for detailed answers)
- Conversational history: last 5 messages
- Score filtering: only sources with score >= 0.3
- More context per chunk: 1000 chars
