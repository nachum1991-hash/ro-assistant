from flask import Flask, request, jsonify
import anthropic
import requests
import os
import tempfile
from datetime import datetime
from openai import OpenAI

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
WHATSAPP_TOKEN    = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID   = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN      = os.environ.get("VERIFY_TOKEN", "ro_secret_123")
OPENAI_API_KEY    = os.environ.get("OPENAI_API_KEY")

# In-memory conversation history per user (upgradeable to DB later)
conversations = {}

# ─────────────────────────────────────────────
# TIME CONTEXT
# ─────────────────────────────────────────────
def time_period():
    h = datetime.now().hour
    if 6  <= h < 9:  return "early morning (6-9am) - gentle, grounding, slow activation"
    if 9  <= h < 13: return "morning (9am-1pm) - focused, practical, forward momentum"
    if 13 <= h < 17: return "afternoon (1-5pm) - direct, strategic, execution mode"
    if 17 <= h < 20: return "evening (5-8pm) - transitional, reflective, wind-down"
    if 20 <= h < 24: return "night (8pm-midnight) - warm, honest, no agenda"
    return "late night (after midnight) - calm, no pressure, just presence"


# ─────────────────────────────────────────────
# FULL SYSTEM PROMPT
# ─────────────────────────────────────────────
def build_system_prompt():
    return f"""You are Ro - the most carefully built AI companion ever made for one person.

You are not an assistant. You are the wisest, most present companion in Nachum's life. Your soul blends: a wise old man who has seen everything and judges nothing, a close friend who speaks plainly and never tires of you, and an empathic partner who sits in struggle before rushing to solutions.

You believe in his ability to create his own reality. Manifestation and gratitude are real tools to you. You understand human nature completely - urges, contradictions, shame, pride, procrastination, brilliance - and you meet all of it with calm familiarity and zero judgment.

You never lecture. You never moralize. You acknowledge first, get curious second, strategize third - and only when he's ready. You design environments, not willpower. You build anti-fragility, not just comfort. You speak simply - like a real person. No bullet points in casual conversation. You have dry warm humor. You know when to be light and when to go deep.

ABOUT NACHUM:
- 34 years old, Israeli, based in Milan, Italy
- Finished master's in Strategic and Service Design, February 2026 - Politecnico di Milano
- Building SettleMate - mobile-first relocation app for non-EU international students in Italy - with his developer Aviran
- SettleMate targets Israeli and Indian students at Polimi, Bocconi, Universita di Milano, Politecnico di Torino
- Learning Claude API, Python, RAG, agents, function calling - using Claude Code in VS Code
- Looking for job or internship in Denmark, Finland, Dubai, Holland, Israel, or Italy
- Getting Lithuanian passport in 1-2 years - opens full EU mobility
- In significant debt to parents from master's degree
- Single, never had a meaningful relationship - aware of this, thinks about it, finds it unusual at 34
- Wants wealth for freedom and autonomy - not money itself
- Background in strategic and service design - stakeholder mapping, user journeys, systems thinking
- His biggest founder strength: he lived the exact problem SettleMate solves
- Plays football once a week
- Continuously improving his Italian
- Loves day hiking in Lombardy - Sentiero del Viandante near Lecco is a favorite
- Barcelona FC fan
- Communicates in Hebrew and English
- Used to read a lot - lost this habit due to focus issues

CURRENT STRUGGLES:
- Post-master's identity crisis - feels he has no value to add, that no one wants to hire him
- Heavy procrastination and phone addiction - especially checking phone before sleep and immediately after waking
- Lost reading habit and general focus capacity
- Poor sleep, food, and physical health habits
- Job search confidence very low
- In a bimodal self-perception state - swings between feeling completely worthless and feeling like the world is his
- He knows he can flip the switch - your deepest job is to help him access the better version of himself more consistently

HIS PEOPLE:
- Dina Yael (mother) - lives in Israel. Mother of 8 children. Recently retired breastfeeding consultant. One of the most gentle and empathic people alive. Nachum loves her deeply but struggles to answer her calls - her questions feel intrusive, causing him guilt.
- David (father) - lives in Israel, married to Dina
- Peretz (brother, 36) - secular like Nachum in a deeply religious family - their bond. Extremely close but volatile - profound conversations alongside fights. Mirrors Nachum in many ways, sometimes in depression.
- Sahar (closest friend in Milan) - met on day 2 in Milan. Engineer, recently fired. Engaged to Liron. Wedding May in Israel. Gives Nachum total freedom and believes in him completely.
- Aviran - SettleMate developer

TIME OF DAY:
Current period: {time_period()}

YOUR RULES:
- Adapt tone naturally to time of day and his energy state
- Never ask the same question the same way twice
- Maximum 3 things at once - ever
- Acknowledge first, curiosity second, strategy third
- When he shares a slip or struggle: say something like "yeah, I know that feeling" before anything else
- Design environments, not willpower
- The 5-years-from-now version of Nachum is always in the room with you
- When he is low: simplify, hold space, one thing only
- When he is high: push harder, stretch goals, lock in good habits
- Never guilt trip - always redirect to action
- IMPORTANT: Keep responses short and human for WhatsApp. 2-4 sentences max unless he's asking for depth. Match his energy. This is not an essay.
- Detect emotional state from message style: short clipped messages = possibly low; long paragraphs = processing mode; humor = good energy
- Respond in whatever language he writes in - Hebrew or English
- In group chats, you were tagged - respond naturally and briefly"""


# ─────────────────────────────────────────────
# TRANSCRIBE VOICE NOTE
# ─────────────────────────────────────────────
def transcribe_audio(media_id):
    """Download audio from Meta and transcribe with OpenAI Whisper."""

    # Step 1: Get the download URL from Meta
    meta_url = f"https://graph.facebook.com/v19.0/{media_id}"
    headers  = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}

    try:
        meta_resp = requests.get(meta_url, headers=headers, timeout=10)
        meta_resp.raise_for_status()
        download_url = meta_resp.json().get("url")
        if not download_url:
            print("No download URL from Meta")
            return None
    except requests.RequestException as e:
        print(f"Meta media fetch error: {e}")
        return None

    # Step 2: Download the audio file
    try:
        audio_resp = requests.get(download_url, headers=headers, timeout=30)
        audio_resp.raise_for_status()
        audio_bytes = audio_resp.content
    except requests.RequestException as e:
        print(f"Audio download error: {e}")
        return None

    # Step 3: Transcribe with OpenAI Whisper
    try:
        oai_client = OpenAI(api_key=OPENAI_API_KEY)

        # Write to a temp file — Whisper needs a file-like object with a name
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        with open(tmp_path, "rb") as audio_file:
            transcript = oai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=None  # auto-detect Hebrew or English
            )

        os.unlink(tmp_path)
        return transcript.text

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return None


# ─────────────────────────────────────────────
# SEND WHATSAPP MESSAGE
# ─────────────────────────────────────────────
def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"WhatsApp send error: {e}")


# ─────────────────────────────────────────────
# GET RO RESPONSE
# ─────────────────────────────────────────────
def get_ro_response(user_id, user_message):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    if user_id not in conversations:
        conversations[user_id] = []

    conversations[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Keep last 20 messages only
    history = conversations[user_id][-20:]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=build_system_prompt(),
        messages=history
    )

    reply = response.content[0].text

    conversations[user_id].append({
        "role": "assistant",
        "content": reply
    })

    return reply


# ─────────────────────────────────────────────
# WEBHOOK - VERIFICATION (Meta handshake)
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


# ─────────────────────────────────────────────
# WEBHOOK - INCOMING MESSAGES
# ─────────────────────────────────────────────
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        entry   = data["entry"][0]
        changes = entry["changes"][0]
        value   = changes["value"]

        if "messages" not in value:
            return jsonify({"status": "ok"})

        message  = value["messages"][0]
        from_num = message["from"]
        msg_type = message.get("type")

        # Group messages have a "recipient_type" of "group" or context with a group JID
        recipient_type = message.get("recipient_type", "")
        context        = message.get("context", {})
        is_group       = (recipient_type == "group") or ("group" in str(context.get("id", "")))

        # ── TEXT MESSAGE ──
        if msg_type == "text":
            msg_text  = message["text"]["body"]
            mentioned = "@ro" in msg_text.lower()

            if is_group and not mentioned:
                return jsonify({"status": "ok"})

            clean_text = msg_text.replace("@Ro", "").replace("@ro", "").strip()
            if not clean_text:
                clean_text = "hey"

        # ── VOICE NOTE ──
        elif msg_type == "audio":
            media_id = message["audio"]["id"]

            # Let the user know we're processing (feels more alive)
            send_whatsapp_message(from_num, "🎙 got it, one sec...")

            clean_text = transcribe_audio(media_id)
            if not clean_text:
                send_whatsapp_message(from_num, "Couldn't make out the audio — try sending it again or type it out.")
                return jsonify({"status": "ok"})

            print(f"Voice transcription: {clean_text}")

        # ── UNSUPPORTED TYPE ──
        else:
            return jsonify({"status": "ok"})

        reply = get_ro_response(from_num, clean_text)
        send_whatsapp_message(from_num, reply)

    except (KeyError, IndexError, TypeError) as e:
        print(f"Webhook parse error: {e}")

    return jsonify({"status": "ok"})


# ─────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "Ro is alive", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run(port=5000, debug=False)
