# Google Gemini Integration Guide for Bus Kar! 🚌✨

This guide explains how to connect **Bus Kar!** to Google Gemini models using the official `google-genai` Python SDK or Google AI Studio Extensions.

---

## 🐍 Option 1: Python with `google-genai` SDK

Install the Google GenAI SDK:
```bash
pip install google-genai
```

### Quick Code Example:
```python
from google import genai
from integrations.gemini.gemini_tools import bus_kar_gemini_tools, execute_gemini_tool_call

client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# Ask Gemini a Delhi transit question with Bus Kar tools attached
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Nehru Place se Kashmere Gate purane adde tak AC bus milegi?",
    config={"tools": bus_kar_gemini_tools}
)

# Gemini will automatically invoke the tool
if response.function_calls:
    for call in response.function_calls:
        print(f"Calling: {call.name} with {call.args}")
        result = execute_gemini_tool_call(call.name, dict(call.args))
        print("API Result:", result)
```

---

## 🌐 Option 2: Google AI Studio / Vertex AI Extensions

1. Open **[Google AI Studio](https://aistudio.google.com/)** or **Vertex AI**.
2. Go to **Extensions** $\rightarrow$ **Create Custom Extension**.
3. Import the schema file: [`gemini_extension.json`](gemini_extension.json).
4. Update `servers[0].url` to your public URL (`https://bus-kar.onrender.com`).
5. Now any Gemini model in your workspace or chat session can invoke Bus Kar transit tools automatically!

---

## 🛠️ Supported Tools for Gemini:
- `resolve_stop`: Resolves colloquial nicknames and landmarks into canonical GTFS stop IDs.
- `get_live_bus_eta`: Returns live vehicle count, ETA in minutes, crowd occupancy, and tracking link.
- `plan_transit_trip`: Calculates travel route, transfer stops, and duration.
- `get_fare_and_ticketing`: Calculates fares with DTC Pink Pass free rules for women.
- `suggest_colloquial_tag`: Registers public nicknames for any bus stop.
