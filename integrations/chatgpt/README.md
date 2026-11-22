# ChatGPT Custom GPT Integration Guide for Bus Kar! 🚌

This guide explains how to configure and brand **Bus Kar!** as an official Custom GPT.

---

## 🚀 Setup Steps (2 Minutes)

1. Open **[chatgpt.com](https://chatgpt.com)** and log in.
2. In the left sidebar, click **Explore GPTs** $\rightarrow$ Click **+ Create** (top right corner).
3. Select the **Configure** tab:
   - **Profile Picture / Icon:** Click the circle icon, choose **Upload Photo**, and select [`integrations/chatgpt/icon.png`](icon.png).
   - **Name:** `Bus Kar! 🚌`
   - **Description:** `Real-time Indian city bus tracking, live GPS arrivals, crowdsourced colloquial stop tags, and DTC Pink Scheme fare calculation.`
   - **Instructions:** Paste the full contents of [`instructions.md`](instructions.md).
4. Scroll down to **Actions** $\rightarrow$ Click **Create new action**:
   - Click **Import from URL**.
   - Enter: `https://bus-kar-api.vercel.app/openapi.json` and click **Import**.
   - **Authentication:** Set to `None`.
   - **Privacy Policy:** `https://bus-kar-api.vercel.app/`
5. Click **Create / Publish** (top right) $\rightarrow$ Choose **Public** or **Anyone with a link**.

---

## 💬 Example Test Prompts in ChatGPT
- *"Bus Kar! Kashmere Gate purane adde se Nehru Place ke liye koi AC bus hai abhi?"*
- *"Check upcoming arrivals at AIIMS hospital bus stop."*
- *"How much is the ticket from Nehru Place to Anand Vihar for a female passenger?"*
- *"Register a new nickname: Tag DTC_KG_01 as 'Old Kashmere Gate Bus Stand'."*
