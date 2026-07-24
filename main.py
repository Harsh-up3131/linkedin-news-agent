import os
import re
import time
import html
import requests
import feedparser
import random

from google.genai.errors import ServerError, ClientError
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=API_KEY)

# IMPORTANT:
# Keep the model that is currently working for your account.
GEMINI_MODEL = "gemini-3-flash-preview"

TOPICS = [
    "Artificial Intelligence",
    "Technology",
    "Software Engineering",
    "Cybersecurity",
]

ARTICLES_PER_TOPIC = 8
SHORTLIST_SIZE = 5

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 Chrome/150 Safari/537.36"
    )
}


# ---------------------------------------------------------
# 1. FETCH NEWS
# ---------------------------------------------------------

def get_news():
    articles = []

    for topic in TOPICS:
        query = topic.replace(" ", "%20")

        url = (
            "https://news.google.com/rss/search?"
            f"q={query}%20when:1d"
            "&hl=en-IN"
            "&gl=IN"
            "&ceid=IN:en"
        )

        feed = feedparser.parse(url)

        for entry in feed.entries[:ARTICLES_PER_TOPIC]:

            title = entry.get("title", "").strip()
            link = entry.get("link", "")
            published = entry.get("published", "Unknown")

            # RSS summary sometimes contains useful information.
            summary_html = entry.get("summary", "")
            summary = BeautifulSoup(
                summary_html,
                "html.parser"
            ).get_text(" ", strip=True)

            articles.append({
                "topic": topic,
                "title": title,
                "link": link,
                "published": published,
                "summary": summary,
            })

    return articles


# ---------------------------------------------------------
# 2. SIMPLE LOCAL DEDUPLICATION
# ---------------------------------------------------------

def normalize_title(title):
    title = title.lower()

    # Google News titles often end with "- Publication"
    title = re.sub(r"\s+-\s+[^-]+$", "", title)

    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title)

    return title.strip()


def deduplicate_articles(articles):
    seen = set()
    unique = []

    for article in articles:
        normalized = normalize_title(article["title"])

        if normalized not in seen:
            seen.add(normalized)
            unique.append(article)

    return unique


# ---------------------------------------------------------
# 3. ASK GEMINI TO SHORTLIST STORIES
# ---------------------------------------------------------

def shortlist_articles(articles):
    news_text = ""

    for i, article in enumerate(articles, 1):
        news_text += f"""
ID: {i}
Topic: {article['topic']}
Title: {article['title']}
Published: {article['published']}
Summary: {article['summary'][:500]}
"""

    prompt = f"""
You are a news editor.

Select the {SHORTLIST_SIZE} most meaningful stories from
the list below.

Prioritize:
- genuine current issues
- significant AI/technology developments
- cybersecurity incidents
- software industry developments
- issues affecting people, businesses or society
- stories worth discussing professionally on LinkedIn

Avoid:
- clickbait
- advertisements
- trivial product announcements
- celebrity stories
- nearly identical stories

Return ONLY the IDs.

Example:

3,7,12,15,20

NEWS:

{news_text}
"""

    response_text = call_gemini(prompt)

    numbers = re.findall(r"\d+", response_text)

    selected = []

    for number in numbers:
        index = int(number) - 1

        if 0 <= index < len(articles):
            article = articles[index]

            if article not in selected:
                selected.append(article)

    return selected[:SHORTLIST_SIZE]


# ---------------------------------------------------------
# 4. RESOLVE GOOGLE NEWS URL
# ---------------------------------------------------------

def resolve_url(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
            allow_redirects=True,
        )

        return response.url

    except requests.RequestException:
        return url


# ---------------------------------------------------------
# 5. EXTRACT ARTICLE TEXT
# ---------------------------------------------------------

def extract_article_text(url):
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

        # Remove irrelevant elements
        for element in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form",
        ]):
            element.decompose()

        paragraphs = soup.find_all("p")

        text_parts = []

        for paragraph in paragraphs:
            text = paragraph.get_text(
                " ",
                strip=True
            )

            if len(text) > 50:
                text_parts.append(text)

        text = " ".join(text_parts)

        text = html.unescape(text)

        # We don't need the entire article for the prototype.
        return text[:6000]

    except Exception:
        return ""


# ---------------------------------------------------------
# 6. ENRICH SHORTLIST
# ---------------------------------------------------------

def enrich_articles(articles):
    enriched = []

    for i, article in enumerate(articles, 1):

        print(
            f"   Reading article {i}/{len(articles)}..."
        )

        original_url = resolve_url(article["link"])

        text = extract_article_text(original_url)

        article["original_url"] = original_url
        article["article_text"] = text

        enriched.append(article)

        # Be polite to websites.
        time.sleep(1)

    return enriched


# ---------------------------------------------------------
# 7. GENERATE LINKEDIN POSTS
# ---------------------------------------------------------

def create_linkedin_posts(articles):
    news_text = ""

    for i, article in enumerate(articles, 1):

        article_content = article["article_text"]

        if not article_content:
            article_content = article["summary"]

        news_text += f"""

================================
STORY {i}
================================

TITLE:
{article['title']}

TOPIC:
{article['topic']}

PUBLISHED:
{article['published']}

SOURCE:
{article['original_url']}

AVAILABLE CONTENT:
{article_content[:6000]}

"""

    prompt = f"""
You are a careful technology news analyst and
professional LinkedIn writer.

Below are {len(articles)} recent news stories.

Your job is to select the THREE strongest stories for
professional LinkedIn discussion.

For each selected story:

1. Explain what happened.
2. Explain why it matters.
3. Identify the broader technological, business or
   societal implication.
4. Write an engaging LinkedIn post.

IMPORTANT FACTUAL RULES:

- Use ONLY facts contained in the supplied material.
- Never invent numbers.
- Never invent quotations.
- Never invent company statements.
- Never invent dates.
- If information is uncertain, say so.
- Do not claim something was independently verified
  unless multiple supplied sources confirm it.
- Do not exaggerate the story.

LINKEDIN STYLE:

- 150-250 words
- professional but conversational
- strong opening hook
- short paragraphs
- explain why the reader should care
- provide thoughtful analysis
- avoid generic AI buzzwords
- avoid excessive emojis
- finish with a question that encourages discussion
- add 3-5 relevant hashtags

OUTPUT FORMAT:

================================
POST #1
================================

HEADLINE:
...

WHY IT MATTERS:
...

LINKEDIN POST:
...

SOURCE:
...


================================
POST #2
================================

...

NEWS MATERIAL:

{news_text}
"""

    return call_gemini(prompt)



def call_gemini(prompt, max_retries=5):
    """
    Call Gemini with exponential backoff.

    Retries temporary errors such as:
    - 503: model overloaded
    - 429: rate limit
    """

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            return response.text

        except (ServerError, ClientError) as e:

            status_code = getattr(e, "code", None)

            # Depending on SDK version, status may be stored differently
            if status_code is None:
                status_code = getattr(e, "status_code", None)

            # Retry temporary failures
            if status_code in [429, 503]:

                if attempt == max_retries - 1:
                    raise

                wait_time = (2 ** attempt) + random.uniform(0, 1)

                print(
                    f"⚠️ Gemini temporarily unavailable "
                    f"({status_code}). "
                    f"Retrying in {wait_time:.1f}s..."
                )

                time.sleep(wait_time)

            else:
                # Don't retry things like invalid API key / bad request
                raise

    raise RuntimeError("Gemini request failed after retries.")




BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_CHANNEL_ID = os.getenv("BUFFER_LINKEDIN_CHANNEL_ID")

BUFFER_API_URL = "https://api.buffer.com"

# KEEP FALSE WHILE TESTING

AUTO_POST = os.getenv(
    "AUTO_POST",
    "false"
).lower() == "true"

def publish_to_buffer(post_text):
    if not BUFFER_API_KEY:
        raise ValueError("BUFFER_API_KEY missing")

    if not BUFFER_CHANNEL_ID:
        raise ValueError("BUFFER_LINKEDIN_CHANNEL_ID missing")

    # Escape values safely for GraphQL
    import json

    text = json.dumps(post_text)
    channel_id = json.dumps(BUFFER_CHANNEL_ID)

    query = f"""
    mutation CreatePost {{
        createPost(
            input: {{
                text: {text}
                channelId: {channel_id}
                schedulingType: automatic
                mode: shareNow
            }}
        ) {{
            ... on PostActionSuccess {{
                post {{
                    id
                    text
                    dueAt
                    status
                }}
            }}

            ... on MutationError {{
                message
            }}
        }}
    }}
    """

    response = requests.post(
        "https://api.buffer.com",
        headers={
            "Authorization": f"Bearer {BUFFER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query": query
        },
        timeout=30,
    )

    print(f"Buffer HTTP status: {response.status_code}")

    # Important for debugging
    try:
        data = response.json()
    except ValueError:
        print("Buffer raw response:")
        print(response.text)
        response.raise_for_status()
        return

    print("Buffer response:")
    print(json.dumps(data, indent=2))

    if response.status_code >= 400:
        raise RuntimeError(
            f"Buffer HTTP {response.status_code}: {data}"
        )

    if "errors" in data:
        raise RuntimeError(
            f"Buffer GraphQL error: {data['errors']}"
        )

    result = data.get("data", {}).get("createPost")

    if not result:
        raise RuntimeError(
            f"Unexpected Buffer response: {data}"
        )

    if result.get("message"):
        raise RuntimeError(
            f"Buffer rejected post: {result['message']}"
        )

    return result




def create_final_linkedin_post(articles):
    news_text = ""

    for i, article in enumerate(articles, 1):
        content = article.get("article_text") or article.get("summary", "")

        news_text += f"""
=========================
STORY {i}
=========================

TITLE:
{article['title']}

PUBLISHED:
{article['published']}

SOURCE:
{article['original_url']}

CONTENT:
{content[:6000]}
"""

    prompt = f"""
You are a careful technology news analyst and professional
LinkedIn writer.

From the stories below, select ONE story that is the strongest
topic for a LinkedIn post today.

Choose based on:
- real-world importance
- credibility of available information
- relevance to technology professionals
- discussion value
- freshness
- enough factual information being available

Do NOT simply choose the most sensational story.

Then write ONE final LinkedIn post.

STRICT FACTUAL RULES:

- Use only information supplied below.
- Never invent statistics.
- Never invent quotations.
- Never invent dates.
- Never invent company statements.
- Never add facts from your memory.
- If the available information is insufficient, return exactly:
  SKIP_POST
- Do not present speculation as fact.

WRITING STYLE:

- 150-220 words
- professional but natural
- strong first 1-2 lines
- short readable paragraphs
- explain what happened
- explain why it matters
- include a thoughtful perspective
- avoid clickbait
- avoid generic AI buzzwords
- avoid excessive emojis
- end with a meaningful discussion question
- include 3-5 relevant hashtags

IMPORTANT:

Return ONLY the text that should appear on LinkedIn.

Do not write:
"LinkedIn Post:"
"Headline:"
"Source:"
"Why it matters:"

STORIES:

{news_text}
"""

    return call_gemini(prompt).strip()

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():

    print("\n🔎 Finding recent news...")

    articles = get_news()

    print(f"Found {len(articles)} articles.")

    print("🧹 Removing duplicates...")

    articles = deduplicate_articles(articles)

    print(
        f"{len(articles)} unique articles remaining."
    )

    print("🤖 Shortlisting meaningful stories...")

    shortlisted = shortlist_articles(articles)

    print(
        f"Selected {len(shortlisted)} stories."
    )

    if not shortlisted:
        print("No suitable stories found.")
        return

    print("🌐 Gathering more information...")

    enriched = enrich_articles(shortlisted)


    print("\n✍️ Creating final LinkedIn post...")

    final_post = create_final_linkedin_post(enriched)

    # ---------------------------------------------------------
    # SKIP IF GEMINI DOESN'T HAVE ENOUGH RELIABLE INFORMATION
    # ---------------------------------------------------------

    if final_post.strip() == "SKIP_POST":
        print("\n⏭️ No sufficiently reliable story found today.")
        print("Nothing will be published.")
        return


    # ---------------------------------------------------------
    # DISPLAY FINAL POST
    # ---------------------------------------------------------

    print("\n")
    print("=" * 60)
    print("FINAL LINKEDIN POST")
    print("=" * 60)
    print(final_post)
    print("=" * 60)


    # ---------------------------------------------------------
    # SAVE LOCALLY
    # ---------------------------------------------------------

    from datetime import datetime

    os.makedirs("output", exist_ok=True)

    filename = datetime.now().strftime(
        "output/post_%Y-%m-%d_%H-%M.txt"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(final_post)

    print(f"\n💾 Saved: {filename}")


    # ---------------------------------------------------------
    # PUBLISH
    # ---------------------------------------------------------

    if AUTO_POST:

        print("\n🚀 Sending post to Buffer...")

        try:
            buffer_result = publish_to_buffer(final_post)

            print("✅ Successfully sent to Buffer!")
            print(buffer_result)

        except Exception as e:

            print("❌ Buffer publishing failed:")
            print(e)

    else:

        print("\n🧪 DRY RUN")
        print("AUTO_POST=False — nothing was published.")

if __name__ == "__main__":
    main()