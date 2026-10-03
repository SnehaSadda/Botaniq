# 🌱 Botaniq

**AI-powered plant identification and care assistant.**

Botaniq lets users upload a photo of a plant and uses **Google Gemini** to analyze it and provide useful plant-care information.

## ✨ Features

* 📸 Upload a plant photo
* 🌿 Identify the apparent plant type
* 👀 Describe visible plant characteristics
* ☀️ Get sunlight guidance
* 💧 Get watering recommendations
* 🌱 Get general plant-care tips
* ⚠️ Handles unclear images and uncertain identification
* 📱 Send plant-care summaries to WhatsApp

## 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **Google Gemini API**
* **Google GenAI SDK**
* **Twilio WhatsApp API**

## 🚀 How to Run

Clone the repository:

```bash
git clone https://github.com/your-username/botaniq.git
cd botaniq
```

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` and add your API keys.

Run the application:

```bash
streamlit run app.py
```

## 📁 Project Structure

```text
botaniq/
├── app.py
├── prompts.py
├── requirements.txt
├── .gitignore
└── README.md
```

## 🌱 How It Works

```text
Plant Photo
     ↓
Gemini AI
     ↓
Plant Analysis
     ↓
Care Recommendations
     ↓
WhatsApp Summary
```
