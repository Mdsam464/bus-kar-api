# ChatGPT Integration Guide for Bus Kar! 🚌

This guide explains how to connect **Bus Kar!** to ChatGPT as a Custom GPT Action.

---

## 🚀 Setup Steps (5 Minutes)

1. Open **[chatgpt.com](https://chatgpt.com)** and ensure you are logged in.
2. In the left sidebar, click **Explore GPTs** $\rightarrow$ Click **+ Create** (top right corner).
3. Select the **Configure** tab:
   - Fill in **Name** and **Description** from [`instructions.md`](instructions.md).
   - Paste the System Prompt into the **Instructions** box.
4. Scroll to the bottom and click **Create new action**:
   - **Authentication:** Set to `None`.
   - **Schema:** Paste the entire contents of [`actions_schema.json`](actions_schema.json).
   - Update `servers[0].url` to your public backend URL (e.g., `https://bus-kar.onrender.com` or your ngrok tunnel).
5. Click **Save / Publish** (choose *Only me* or *Anyone with a link*).

---

## 💬 Example Test Prompts in ChatGPT
- *"Bus Kar! Kashmere Gate purane adde se Nehru Place ke liye koi AC bus hai abhi?"*
- *"Check upcoming arrivals at AIIMS hospital bus stop."*
- *"How much is the ticket from Nehru Place to Anand Vihar for a female passenger?"*
- *"Register a new nickname: Tag DTC_KG_01 as 'Old Kashmere Gate Bus Stand'."*
