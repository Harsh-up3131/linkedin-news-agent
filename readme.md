# 🤖 LinkedIn News Agent

An automated AI-powered news agent that discovers current technology-related issues, analyzes relevant stories, generates a professional LinkedIn post, and publishes it to a personal LinkedIn profile through Buffer.

The project is designed as a lightweight, mostly free prototype using Python, Google News RSS, Gemini, GitHub Actions, and Buffer.

---

## ✨ Features

* 📰 Fetches recent news using Google News RSS
* 🧹 Removes duplicate articles
* 📊 Ranks stories locally based on relevance
* 🌐 Extracts additional context from selected articles
* 🤖 Uses Gemini to analyze the strongest stories
* ✍️ Generates one professional LinkedIn post
* 💾 Saves generated posts locally
* 🚀 Publishes to a personal LinkedIn profile through Buffer
* ⏰ Supports fully automated daily execution using GitHub Actions
* 🔁 Handles temporary Gemini API failures with automatic retries
* 🛑 Supports dry-run mode to prevent accidental publishing

---

## 🏗️ Architecture

```text
GitHub Actions
      │
      ▼
Google News RSS
      │
      ▼
Fetch Recent News
      │
      ▼
Deduplication
      │
      ▼
Local Keyword Scoring
      │
      ▼
Top Relevant Stories
      │
      ▼
Article Context Extraction
      │
      ▼
Gemini
      │
      ├── Select Best Story
      │
      └── Generate LinkedIn Post
      │
      ▼
Save Generated Post
      │
      ▼
Buffer API
      │
      ▼
LinkedIn Personal Profile
```

---

## 🛠️ Tech Stack

**Language**

* Python 3.11+

**News**

* Google News RSS
* Feedparser
* BeautifulSoup

**AI**

* Google Gemini API

**Publishing**

* Buffer API
* LinkedIn Personal Profile

**Automation**

* GitHub Actions

---

## 📁 Project Structure

```text
linkedin-news-agent/
│
├── main.py
├── requirements.txt
├── .env
├── .gitignore
│
├── output/
│   └── generated-posts.txt
│
└── .github/
    └── workflows/
        └── daily-post.yml
```

> `.env` and generated output files should not be committed to GitHub.

---

# 🚀 Setup

## 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>

cd linkedin-news-agent
```

---

## 2. Create a virtual environment

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

The main dependencies are:

```text
feedparser
google-genai
python-dotenv
requests
beautifulsoup4
```

---

# 🔑 Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key

BUFFER_API_KEY=your_buffer_api_key

BUFFER_LINKEDIN_CHANNEL_ID=your_linkedin_channel_id

AUTO_POST=false
```

### Important

Never commit `.env`.

Make sure `.gitignore` contains:

```text
.env
venv/
__pycache__/
output/
.DS_Store
```

---

# 🤖 Gemini Setup

Create a Gemini API key using Google AI Studio.

Add the key to:

```env
GEMINI_API_KEY=your_key
```

The agent intentionally minimizes Gemini usage.

Instead of using Gemini for every stage:

```text
News
 ↓
Python ranking
 ↓
Top stories
 ↓
Gemini
```

Local Python scoring handles initial filtering, while Gemini is reserved for final analysis and content generation.

This reduces API usage and makes the prototype more suitable for free-tier usage.

---

# 📰 News Collection

The agent retrieves recent stories through Google News RSS.

Example topics include:

```python
TOPICS = [
    "Artificial Intelligence",
    "Technology",
    "Software Engineering",
    "Cybersecurity",
]
```

These can be modified inside `main.py`.

The agent then:

1. Fetches recent articles
2. Removes duplicates
3. Scores articles based on relevant keywords
4. Selects the strongest candidates
5. Attempts to extract additional article context

---

# 📊 Local News Ranking

To minimize LLM calls, the initial ranking is performed locally.

Example:

```python
KEYWORDS = {
    "artificial intelligence": 8,
    "generative ai": 8,
    "cybersecurity": 8,
    "data breach": 9,
    "ransomware": 9,
    "cloud": 5,
    "software": 4,
    "privacy": 6,
    "regulation": 6,
}
```

Articles containing important keywords receive higher relevance scores.

Only the highest-ranked stories are passed to the AI stage.

---

# ✍️ LinkedIn Post Generation

Gemini receives the strongest candidate stories and generates one final LinkedIn post.

The prompt instructs the model to:

* Choose a meaningful current issue
* Avoid sensationalism
* Use only supplied information
* Avoid invented statistics or quotations
* Explain why the issue matters
* Provide a professional perspective
* Use readable short paragraphs
* End with a discussion question
* Include relevant hashtags

If there is not enough reliable information, the model can return:

```text
SKIP_POST
```

and no post will be published.

---

# 🧪 Dry Run Mode

Automatic publishing should remain disabled while developing.

Set:

```env
AUTO_POST=false
```

Then run:

```bash
python main.py
```

The agent will generate and save the post without publishing it.

Example:

```text
============================================================
FINAL LINKEDIN POST
============================================================

Generated post...

============================================================

💾 Saved: output/post_2026-07-24_17-21.txt

🧪 DRY RUN
AUTO_POST=False — nothing was published.
```

---

# 🚀 Buffer + LinkedIn

Buffer is used as the publishing layer between the agent and a personal LinkedIn profile.

The flow is:

```text
Python Agent
     ↓
Buffer API
     ↓
LinkedIn Personal Profile
```

Connect your personal LinkedIn profile to Buffer and obtain:

```env
BUFFER_API_KEY=...
BUFFER_LINKEDIN_CHANNEL_ID=...
```

The API key must remain private.

---

# ⚠️ Automatic Publishing

To enable publishing:

```env
AUTO_POST=true
```

When enabled:

```text
Generated Post
      ↓
Buffer
      ↓
LinkedIn
```

During development, keeping this set to `false` is strongly recommended.

Generated news content should be reviewed carefully before enabling unattended publishing.

---

# ⏰ GitHub Actions Automation

The agent can run automatically using GitHub Actions.

Create:

```text
.github/workflows/daily-post.yml
```

Example workflow:

```yaml
name: Daily LinkedIn News Agent

on:
  workflow_dispatch:

  schedule:
    # 03:00 UTC = 08:30 IST
    - cron: "0 3 * * *"

jobs:
  generate-and-post:
    runs-on: ubuntu-latest

    timeout-minutes: 15

    steps:

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run LinkedIn news agent
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          BUFFER_API_KEY: ${{ secrets.BUFFER_API_KEY }}
          BUFFER_LINKEDIN_CHANNEL_ID: ${{ secrets.BUFFER_LINKEDIN_CHANNEL_ID }}

          # Change to true only when automatic
          # publishing is desired.
          AUTO_POST: "false"

        run: python main.py
```

---

# 🔐 GitHub Secrets

Go to:

```text
Repository
→ Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Add:

```text
GEMINI_API_KEY

BUFFER_API_KEY

BUFFER_LINKEDIN_CHANNEL_ID
```

Do not store API keys directly inside the workflow YAML.

`AUTO_POST` does not need to be a secret.

---

# ▶️ Manual GitHub Action

The workflow can also be triggered manually:

```text
GitHub Repository
      ↓
Actions
      ↓
Daily LinkedIn News Agent
      ↓
Run workflow
```

This is useful for testing before enabling the scheduled workflow.

---

# 🔄 Gemini Retry Handling

Gemini may occasionally respond with:

```text
503 UNAVAILABLE
```

when a model is temporarily overloaded.

The agent implements retry logic with exponential backoff.

For example:

```text
Gemini request
     ↓
503
     ↓
Wait
     ↓
Retry
     ↓
Success
```

A `429 RESOURCE_EXHAUSTED` response may indicate that the API quota has been reached.

The agent should avoid repeatedly retrying when the daily free-tier quota is exhausted.

---

# 💰 Cost

The prototype is designed to minimize infrastructure costs.

| Component              | Usage                                        |
| ---------------------- | -------------------------------------------- |
| Google News RSS        | Free                                         |
| Local Python filtering | Free                                         |
| Gemini                 | Free tier where available                    |
| GitHub Actions         | Free allowance subject to GitHub plan limits |
| Buffer                 | Subject to Buffer's current plan/API limits  |
| LinkedIn               | Personal profile                             |

API quotas and free-plan limits can change, so check the respective providers before relying on the workflow for production use.

---

# ⚠️ Important Limitations

This project is currently a prototype.

### News verification

Article extraction does **not** guarantee that a story has been independently verified.

A future version should compare multiple independent sources before automatically publishing factual claims.

### AI hallucinations

LLMs can misinterpret source material or introduce unsupported conclusions.

Automatic publishing should therefore be used cautiously.

### News website extraction

Some publishers block automated article extraction.

When this happens, the agent may have less context available.

### Duplicate stories

Different publications may report the same event using different headlines. Basic title deduplication may therefore fail to identify all duplicates.

---

# 🛣️ Future Improvements

Potential improvements include:

* Cross-source fact verification
* Semantic duplicate detection
* Trusted-source weighting
* Post history
* Duplicate-topic prevention
* Better article clustering
* Source credibility scoring
* LinkedIn post quality scoring
* Automatic image generation
* Analytics and engagement tracking
* Web dashboard
* Human approval workflow
* Multiple content niches

A stronger future pipeline could be:

```text
Google News
     ↓
Story Clustering
     ↓
Trusted Source Filtering
     ↓
Cross-Source Verification
     ↓
AI Analysis
     ↓
LinkedIn Draft
     ↓
Fact Validation
     ↓
Human Approval / Auto Publish
     ↓
Buffer
     ↓
LinkedIn
```

---

# 🛡️ Responsible Use

This project generates content based on current news.

Before enabling fully autonomous publishing:

* Verify important claims
* Avoid presenting speculation as fact
* Prefer reputable primary or established news sources
* Avoid automatically amplifying sensational headlines
* Clearly distinguish analysis from reported facts
* Monitor generated posts regularly

The goal is to automate **research and drafting**, not to sacrifice accuracy for posting frequency.

---

## License

This project is intended for educational and experimental use.
