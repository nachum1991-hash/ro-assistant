# Ro — Project Documentation

> Last updated: April 2026  
> Author: Nachum  
> Status: Live ✅

---

## What Is Ro?

Ro is a personal AI companion built specifically for one person — Nachum.  
It is not a generic chatbot. It knows Nachum's life, his people, his struggles, and his goals in detail.  
It is built to be the most present, honest, and useful AI companion possible — part life coach, part therapist, part strategic advisor, part friend.

Ro exists in **two forms**:

| | Ro Platform | Ro WhatsApp Bot |
|---|---|---|
| File | `index.html` | `app.py` |
| Where it runs | Browser (local) | Render cloud server |
| Memory | Full — persists everything to localStorage | RAM only — resets on restart |
| Modes | Now / Think / Build / Reflect / World | Single conversation |
| Voice | Gemini Live API (gemini-3.1-flash-live-preview) | WhatsApp voice notes → Whisper |
| Pomodoro | Yes (25/5 min) | No |
| My World panel | Yes | No |
| Google Calendar | Yes (OAuth, optional) | No |
| Web Search | Yes (Tavily API, optional) | No |
| Daily Brief | Yes (auto, mornings 6–12am) | No |
| Weekly Insight | Yes (auto, every 7 days) | No |
| Deep Onboarding | Yes (7-topic identity session) | No |
| Who can use it | Only Nachum (on his device) | Anyone with the WhatsApp number |

**The platform is the real Ro.** The WhatsApp bot is a lightweight version that lives where Nachum already is.

---

## File Structure

```
RO my asistant/
├── index.html        — Full Ro platform (browser app)
├── app.py            — WhatsApp bot server (Flask)
├── requirements.txt  — Python deps: flask, google-generativeai, requests, gunicorn, openai
├── manifest.json     — PWA manifest (makes it installable on phone)
├── sw.js             — Service worker (offline cache)
├── icon.svg          — App icon
└── RO_PROJECT.md     — This file
```

---

## Ro Platform — index.html

### How It Works

Single HTML file. No frameworks. No build step. Opens directly in any browser.  
Google Gemini API called via `fetch` directly from the browser.

```
User types/speaks → Gemini API → Ro replies
```

Every API call rebuilds the full system prompt with:
- Nachum's complete profile and background
- Current time of day (tone shifts accordingly)
- Last 7 check-ins from localStorage
- Last 5 wins
- Last 5 gratitude entries
- Detected behavioral patterns
- Key people and when they were last mentioned
- Last 3 × 90-day vision statements
- Last 5 session summaries (auto-generated)
- Latest weekly psychological insight
- Today's morning brief (if generated)
- Any custom rules Nachum has added
- Google Calendar events (if connected)
- Nachum's deep identity document (from onboarding)

### Models Used

| Task | Model | Method |
|------|-------|--------|
| All chat + background tasks | `gemini-2.5-flash` | REST (`generateContent`) |
| Voice chat | `gemini-3.1-flash-live-preview` | WebSocket (Live API) |

### Five Modes

| Mode | Purpose | Special behavior |
|------|---------|-----------------|
| **Now** | Daily companion | Time-aware greeting, fluid conversation |
| **Think** | Strategic depth | 5-years-from-now lens, systems thinking |
| **Build** | Execution | Pomodoro timer (25/5), one task at a time |
| **Reflect** | Inner work | Gratitude practice, manifestation, emotional processing |
| **World** | People & relationships | Tracks key people, nudges when someone hasn't been mentioned |

### localStorage Keys

| Key | What it stores |
|-----|---------------|
| `ro_api_key` | Google Gemini API key |
| `ro_conv_state` | Full conversation history per mode (persists across page reloads) |
| `ro_checkins` | Every session: date, mood, mode, note |
| `ro_wins` | Logged wins with date and text |
| `ro_gratitude` | Gratitude entries from Reflect mode |
| `ro_patterns` | Detected behavioral counts (sleep, exercise, job search, etc.) |
| `ro_struggles` | User-reported slips and challenges |
| `ro_people` | Key people with notes and last-mentioned date |
| `ro_vision` | 90-day vision statements over time |
| `ro_identity` | Deep identity documents from onboarding sessions |
| `ro_custom_rules` | User-edited instructions injected into every API call |
| `ro_conversations` | Auto-generated session summaries (2 sentences, written at 8 messages) |
| `ro_weekly` | Weekly psychological insight (auto-generated every 7 days) |
| `ro_daily_brief` | Morning brief entries (auto-generated 6–12am) |
| `ro_tavily_key` | Tavily web search API key (optional) |
| `ro_gcal_id` | Google OAuth Client ID |
| `ro_gcal_connected` | Whether Google Calendar is linked |

### Intelligence Features

#### Pattern Detection
Every user message is scanned for keywords (Hebrew + English) and counts are stored:
- `sleep_mentions`, `exercise_mentions`, `food_mentions`
- `high_energy_mentions`, `low_energy_mentions`
- `procrastination_mentions`, `job_search_mentions`, `settlemate_mentions`
- `anxiety_mentions`, `positive_mentions`, `low_self_mentions`
- `reading_mentions`, `mindfulness_mentions`, `phone_mentions`
- People mentions → update `last` timestamp on the matching person

#### Session Summarization
When a conversation reaches 8 messages, a background API call fires and asks Gemini to write a 2-sentence summary. Stored in `ro_conversations`, injected into every future system prompt. How Ro builds longitudinal memory.

#### Weekly Psychological Synthesis
On every boot, checks if 7+ days have passed since last synthesis. If so, reads 14 days of check-ins, patterns, session summaries, and struggles → generates 3-sentence psychological insight. Stored in `ro_weekly`. Inject into every system prompt. Can be manually triggered from Settings → Weekly Insight → Regenerate Now.

#### Daily Brief
On first boot between 6–12am, auto-generates a 3-bullet morning brief. Uses calendar, patterns, wins, and optionally Tavily news. Appears as Ro's first message of the day.

#### Deep Onboarding
7-topic conversational session (not a form) where Ro gets to know Nachum at depth. Covers: daily reality, work & money, inner life & spirit, relationships & romance, health & body, fears & shadows, best version. Synthesized into a rich identity document stored in `ro_identity`, injected into every system prompt.

Monthly update session (4 topics) revisits what's changed. Triggered from Settings.

### Voice Chat — Gemini Live API

Two-way voice using `gemini-3.1-flash-live-preview`:
1. Mic audio captured via Web Audio API at 16kHz PCM
2. Streamed continuously over WebSocket to Gemini
3. Gemini understands speech natively (no browser STT)
4. Text response returned over WebSocket
5. Spoken aloud via browser TTS

Language toggle: English / Hebrew. Tap orb to interrupt Ro mid-sentence.

### Single-tap Mic (text chat)
Browser Speech Recognition API (Chrome/Edge). Tap 🎙, speak, auto-sends as text message.

### Google Calendar Integration

Optional. Requires:
1. Google Cloud project with Calendar API enabled
2. OAuth 2.0 Client ID (Web Application)
3. Authorized JavaScript Origin = the hosted URL

When connected, today's events are injected into the system prompt.

### Tavily Web Search

Optional. Get a free key at tavily.com. Save in Settings → Live Web Search.  
When Nachum asks something research-like ("search for…", "what's the latest on…"), Ro automatically fetches results and uses them as context.

### PWA — Install as Phone App

Requires hosting (local file:// cannot be installed as PWA).  
Files needed: `index.html`, `manifest.json`, `sw.js`, `icon.svg`  
Recommended host: GitHub Pages (free, instant)  
Install: Chrome → ⋮ → Add to Home Screen | Safari → Share → Add to Home Screen

---

## Ro WhatsApp Bot — app.py

### Architecture

```
WhatsApp message
  → Meta servers
    → POST /webhook on Render
      → app.py processes it
        → Gemini API (gemini-2.5-flash)
          → reply sent back via Meta API
            → delivered to WhatsApp
```

### Deployment

| Service | Detail |
|---------|--------|
| Platform | Render.com (free tier) |
| Service name | ro-bot |
| URL | https://ro-bot-0jbv.onrender.com |
| Webhook | https://ro-bot-0jbv.onrender.com/webhook |

### Environment Variables (set in Render)

| Key | Value |
|-----|-------|
| `GEMINI_API_KEY` | Google Gemini API key from aistudio.google.com/apikey |
| `WHATSAPP_TOKEN` | From Meta Developer Console (expires ~24hrs on test) |
| `PHONE_NUMBER_ID` | `1037179846152493` |
| `VERIFY_TOKEN` | `ro_secret_123` |
| `OPENAI_API_KEY` | OpenAI key (for Whisper voice transcription) |

### Meta App Details

| Field | Value |
|-------|-------|
| App Name | RO |
| App ID | `1634515441190101` |
| WhatsApp Business Account ID | `1243305774539978` |
| Phone Number ID | `1037179846152493` |
| Test bot number | `+1 555 167 4779` |
| Approved recipient | `+972 54 223 2180` |

### Voice Notes

WhatsApp audio → downloaded from Meta → transcribed via OpenAI Whisper (`whisper-1`) → passed to Gemini as text.  
Auto-detects Hebrew/English. Sends "🎙 got it, one sec..." while processing.  
Cost: ~$0.003 per 30-second note.

### Known Limitations (free tier)

- **Token expires ~24hrs** — regenerate in Meta → copy → update `WHATSAPP_TOKEN` in Render
- **Render sleeps after 15min** — first message after sleep is slow (~30 sec wake-up)
- **Memory is RAM-only** — Render restarts clear all conversation history
- **Test mode only** — can only reply to approved numbers until you register a real number
- **Groups** — test sandbox numbers CANNOT join groups. Need a real registered number.

### How to Refresh Token When Bot Stops Working

1. developers.facebook.com → RO app → API Setup
2. Click **Generate access token** → Copy
3. render.com → ro-bot → Environment → update `WHATSAPP_TOKEN`
4. Save → Render redeploys in ~1 min

### Group Chat Behavior

- Private chat: always responds
- Group chat: only responds when someone writes `@Ro` or `@ro`
- Strips the @mention before sending to Gemini

---

## Ro's Personality

Built from a specific soul blueprint — not generic assistant behavior.

> A wise old man who has seen everything and judges nothing.  
> A close friend who speaks plainly and never tires of you.  
> An empathic partner who sits in struggle before rushing to solutions.  
> Someone who believes deeply in the ability to create your own reality.

**Core rules:**
- Acknowledge first. Curiosity second. Strategy third — only when ready.
- Never lecture. Never moralize. Never guilt trip.
- Design environments, not willpower.
- Maximum 3 things at once — ever.
- The 5-years-from-now version of Nachum is always in the room.
- When low: simplify, hold space, one thing only.
- When high: push harder, stretch goals.
- Tone shifts by time of day (6 different profiles).
- Responds in Hebrew or English — whichever Nachum uses.

---

## About Nachum (context injected into every API call)

- 34, Israeli, Milan
- Master's in Strategic & Service Design, Politecnico di Milano (Feb 2026)
- Building SettleMate with developer Aviran
- Learning: Gemini API, Python, RAG, agents, function calling (VS Code)
- Job search: Denmark, Finland, Dubai, Holland, Israel, Italy
- Lithuanian passport incoming (1-2 years)
- In debt to parents from master's
- Wants wealth for freedom, not money itself
- Plays football weekly, hikes Lombardy, Barcelona FC fan
- Hebrew + English
- Lost reading habit — wants to recover it

**Key people:** Dina Yael (mother), David (father), Peretz (brother, 36), Sahar (best friend Milan), Aviran (developer)

---

## Roadmap / Future Ideas

- [ ] Connect WhatsApp bot memory to platform localStorage (shared memory layer)
- [ ] Register Italian number for groups (remove test sandbox limitation)
- [ ] Persistent DB for WhatsApp bot (Redis or Supabase — replaces RAM)
- [ ] Weekly insight email/WhatsApp message from Ro
- [ ] Notion integration for tasks and notes
- [ ] Voice replies (text-to-speech) from Ro in WhatsApp
- [ ] Tavily search in WhatsApp bot

---

## Cost Estimates

| Usage | Cost |
|-------|------|
| 50 messages/day on platform | ~$0.02/day (Gemini 2.5 Flash) |
| 20 WhatsApp messages/day | ~$0.01/day |
| 5 voice notes/day (30s each) | ~$0.015/day (Whisper) |
| **Total daily** | **~$0.05/day (~$1.50/month)** |

Gemini has a free tier — costs only kick in above the free quota.  
Set a monthly cap in console.cloud.google.com → Billing.
