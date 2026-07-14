# Vedant Merchant Assist

FastAPI submission bot for the final magicpin AI Challenge harness.

Submitted by Vedant Nehete (`nehetevedant9@gmail.com`). The supplied challenge package is available in `challenge/` for local simulation.

## Approach

The bot uses a custom deterministic trigger-dispatch composer for outbound actions. Replies can optionally use Gemini, while opt-outs, hostile replies, and auto-replies continue to use deterministic safety rules. Without a Gemini key, reply behavior falls back to built-in templates.

## Gemini (optional)

Create an API key in [Google AI Studio](https://aistudio.google.com/app/apikey), then set it in PowerShell before starting the server:

```powershell
$env:GEMINI_API_KEY = "your_key_here"
$env:GEMINI_MODEL = "gemini-2.5-flash"
```

Gemini 2.5 Flash supports Google's free API tier, subject to its current quotas and terms. Do not place the key in source code or commit it to the repository.

## Redis State (recommended for deployment)

Set `REDIS_URL` to use Redis for contexts, conversations, and suppression keys. Without it, the bot uses local in-memory state for development.

```text
REDIS_URL=rediss://default:password@your-redis-host:port
```

For Railway, provision a Redis service or use a managed provider, then add its connection URL as the `REDIS_URL` service variable. The bot fails fast at startup if a configured Redis instance is unreachable.
## Run

```bash
pip install -r requirements.txt
uvicorn bot:app --host 0.0.0.0 --port 8080
```

## Run LLM Judge

Start the bot in one PowerShell window:

```powershell
python -m uvicorn bot:app --host 127.0.0.1 --port 8080
```

In another PowerShell window, set the judge LLM key and run all scenarios:

```powershell
$env:JUDGE_LLM_PROVIDER = "gemini"
$env:JUDGE_LLM_API_KEY = "your_api_key_here"
$env:JUDGE_LLM_MODEL = "gemini-2.5-flash"
$env:JUDGE_TEST_SCENARIO = "full_evaluation"
python challenge/judge_simulator.py
```

Supported providers are `openai`, `anthropic`, `gemini`, `deepseek`, `groq`, `ollama`, and `openrouter`. Use `JUDGE_TEST_SCENARIO=all` for the quick flow, or `full_evaluation` for the LLM-scored batch run.

## Endpoints

- `GET /v1/healthz`
- `GET /v1/metadata`
- `POST /v1/context`
- `POST /v1/tick`
- `POST /v1/reply`
- `POST /v1/teardown`

## Tradeoffs

The deterministic composer avoids hallucinated facts by only using values present in context. It covers the key trigger families from the assessment and falls back to a conservative factual draft for unknown triggers. A frontier LLM would improve phrasing variety, but it would add latency and operational risk.
