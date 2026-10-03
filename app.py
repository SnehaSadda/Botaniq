from google import genai
from google.genai import types
import streamlit as st
import json

from twilio.rest import Client as TwilioClient

from prompts import (
    SYSTEM_PROMPT,
    WELCOME_MESSAGE_TEMPLATE,
    SUMMARY_REQUEST_PROMPT
)


# -----------------------------
# API KEYS
# -----------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]


# -----------------------------
# CLIENTS
# -----------------------------

@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


@st.cache_resource
def get_twilio_client():
    return TwilioClient(
        TWILIO_ACCOUNT_SID,
        TWILIO_AUTH_TOKEN
    )


gemini_client = get_gemini_client()
twilio_client = get_twilio_client()

MODEL_NAME = [    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",]


# -----------------------------
# WHATSAPP TEXT CLEANING
# -----------------------------

def clean_whatsapp_text(text):
    if not text:
        return "No plant care summary available."

    text = " ".join(text.split())

    return text[:1500] + "..." if len(text) > 1500 else text


# -----------------------------
# SEND WHATSAPP
# -----------------------------

def send_whatsapp(to_number, user_name, summary):

    try:
        content_variables = json.dumps(
            {
                "1": user_name,
                "2": clean_whatsapp_text(summary)
            },
            ensure_ascii=False
        )

        message = twilio_client.messages.create(
            from_=TWILIO_WHATSAPP_FROM,
            to=f"whatsapp:{to_number}",
            content_sid=TWILIO_CONTENT_SID,
            content_variables=content_variables,
        )

        return True, message.sid

    except Exception as error:
        return False, str(error)


# -----------------------------
# RENDER MESSAGE
# -----------------------------

def render_message(message):

    with st.chat_message(message["role"]):

        if message["kind"] == "text":
            st.write(message["content"])

        elif message["kind"] == "image":
            st.image(message["content"])


# -----------------------------
# ADD MESSAGE
# -----------------------------

def add_message(role, kind, content):

    st.session_state.messages.append(
        {
            "role": role,
            "kind": kind,
            "content": content
        }
    )

    render_message(st.session_state.messages[-1])


# -----------------------------
# ASK GEMINI
# -----------------------------

import time


def ask_gemini(parts):
    for model_name in MODEL_NAME:
        try:
            chat = gemini_client.chats.create(
                model=model_name,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

            response = chat.send_message(parts)

            return response.text

        except Exception as error:
            error_text = str(error)

            if "503" in error_text or "UNAVAILABLE" in error_text:
                continue

            return f"Sorry, something went wrong: {error}"

    return (
        "🌱 Gemini is temporarily busy right now.\n\n"
        "I tried multiple available Gemini models, "
        "but they are currently unavailable.\n\n"
        "Please wait a little and try your plant photo again."
    )


# ============================================================
# STEP 1: ONBOARDING
# ============================================================

if "onboarded" not in st.session_state:

    st.title("🌱 Botaniq")
    st.caption("Snap it. Understand it. Care for it.")

    with st.form("onboarding_form"):

        name = st.text_input("Your name")

        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
        )

        submitted = st.form_submit_button("Let's grow 🚀")

    if submitted:

        if not name.strip() or not whatsapp_number.strip():

            st.warning(
                "Please fill in both your name and WhatsApp number."
            )

        else:

            st.session_state.name = name.strip()

            st.session_state.whatsapp_number = (
                whatsapp_number.strip()
            )

            # Create Gemini chat
            st.session_state.chat = gemini_client.chats.create(

                model=MODEL_NAME,

                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT
                ),
            )

            st.session_state.messages = []

            st.session_state.onboarded = True

            st.rerun()

    st.stop()


# ============================================================
# STEP 2: CHAT INTERFACE
# ============================================================

header_col, button_col = st.columns(
    [5, 2],
    vertical_alignment="center"
)


# -----------------------------
# HEADER
# -----------------------------

with header_col:

    st.title("🌱 Botaniq")


# -----------------------------
# WHATSAPP BUTTON
# -----------------------------

with button_col:

    send_disabled = False

    if st.button(
        "📤 Send to WhatsApp",
        disabled=send_disabled,
        use_container_width=True
    ):

        with st.spinner(
            "Preparing your plant summary..."
        ):

            summary = ask_gemini(
                [SUMMARY_REQUEST_PROMPT]
            )

        success, info = send_whatsapp(
            st.session_state.whatsapp_number,
            st.session_state.name,
            summary
        )

        if success:

            st.success(
                "Sent! Check your WhatsApp 📲"
            )

        else:

            st.error(
                f"Couldn't send that: {info}"
            )


# -----------------------------
# USER INFO
# -----------------------------

st.caption(
    f"Logged in as {st.session_state.name} - "
    f"updates go to {st.session_state.whatsapp_number}"
)


# ============================================================
# STEP 3: WELCOME MESSAGE
# ============================================================

if not st.session_state.messages:

    add_message(
        "assistant",
        "text",
        WELCOME_MESSAGE_TEMPLATE.format(
            name=st.session_state.name
        )
    )


else:

    for message in st.session_state.messages:

        render_message(message)


# ============================================================
# STEP 4: USER INPUT
# ============================================================

user_input = st.chat_input(

    "Ask about your plant, or attach a photo",

    accept_file=True,

    file_type=[
        "jpg",
        "jpeg",
        "png"
    ],
)


# ============================================================
# STEP 5: PROCESS USER INPUT
# ============================================================

if user_input:

    photo = (
        user_input.files[0]
        if user_input.files
        else None
    )

    text = user_input.text

    parts = []


    # -----------------------------
    # PHOTO
    # -----------------------------

    if photo is not None:

        photo_bytes = photo.getvalue()

        # Show uploaded image in chat
        add_message(
            "user",
            "image",
            photo_bytes
        )

        # Send image to Gemini
        parts.append(
            types.Part.from_bytes(
                data=photo_bytes,
                mime_type=photo.type
            )
        )


    # -----------------------------
    # TEXT
    # -----------------------------

    if text:

        add_message(
            "user",
            "text",
            text
        )

        parts.append(text)


    # -----------------------------
    # PHOTO WITHOUT TEXT
    # -----------------------------

    elif photo is not None:

        parts.append(
            "Analyze this plant and identify the apparent plant type. "
            "Describe what is visibly observable, give the confidence "
            "level, sunlight guidance, watering guidance, care tips, "
            "and mention any visible signs of plant stress or damage."
        )


    # -----------------------------
    # GEMINI RESPONSE
    # -----------------------------

    with st.spinner(
        "Growing your answer... 🌱"
    ):

        answer = ask_gemini(parts)


    # -----------------------------
    # DISPLAY RESPONSE
    # -----------------------------

    add_message(
        "assistant",
        "text",
        answer
    )