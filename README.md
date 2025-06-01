# G1 Proactive AI

Smart Glasses with Proactive Speech Recognition, Context Awareness, and Real-Time Answer Generation


## Features

- Live audio capture from dual BLE-connected G1 smart glasses
- Speech-to-text using `whisper`
- Context recognition using lightweight NLP (`distilbert-base`)
- OpenAI GPT-4o API integration (o4-mini)
- Local caching of answers
- Fallback responses if the network/API fails
- Visual display to both left and right arms of G1


## Requirements

Install dependencies:

```bash
pip install openai
# And ensure these are present or mocked in testing
# bluetooth_ble, lc3_decoder, whisper, nlp_model
```


## OpenAI API Key Setup

Get your API key from [https://platform.openai.com/](https://platform.openai.com/).

Set the key in your environment:

**Linux/macOS:**
```bash
export OPENAI_API_KEY='your-api-key-here'
```

**Windows PowerShell:**
```powershell
$env:OPENAI_API_KEY='your-api-key-here'
```


## How It Works

1. BLE mic on right arm is activated and starts capturing audio.
2. Audio is received as LC3 packets, decoded into raw audio.
3. Whisper transcribes speech to text.
4. NLP model detects user intent (e.g., a question).
5. If confidence is high, it checks local cache for a matching question.
6. If no match, it sends a prompt to OpenAI's `gpt-4o` and caches the response.
7. Answer is displayed on both arms of the G1 glasses.


## Project Structure

```
G1-Proactive-AI/
├── proactive_ai.py       # Main logic file
├── cache/                # Auto-generated cache for question/answer pairs
└── README.md             # You're reading it
```

## Example Interaction

> 👓 User says: "What is AI?"
>
> 🤖 G1 sends: "User asked: What is AI? \n Provide a helpful, concise response."
>
> ✅ G1 displays: "AI is the simulation of human intelligence by machines."

## Fallback Handling

If OpenAI API call fails (e.g., no internet):
- G1 uses a fallback message: `"Sorry, I couldn't get a full answer right now. Here's what I understood: {topic}"`

## What Changed

- Integrated OpenAI `gpt-4o` API (Tiny variant for smart devices)
- Cached answers in `cache/` using MD5 hashes of question prompts
- Added robust fallback logic to keep UX consistent when offline

## Future Work

- Add offline model support for disconnected mode
- TTL (expiration) support for cache files
- Multilingual display integration
