import os
import feedparser
import smtplib
from email.mime.text import MIMEText
from datetime import date


RSS_FEEDS = {
    "World News": [
        "https://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.npr.org/1004/rss.xml"
    ],
    "Business News": [
        "https://www.cnbc.com/id/10001147/device/rss/rss.html",
        "https://feeds.marketwatch.com/marketwatch/topstories/"
    ],
    "Supply Chain News": [
        "https://www.supplychaindive.com/feeds/news/",
        "https://www.freightwaves.com/feed"
    ],
    "Technology & AI News": [
        "https://www.technologyreview.com/feed/",
        "https://www.theverge.com/rss/index.xml"
    ]
}

ARTICLES_PER_SECTION = 3


def clean_text(text):
    if not text:
        return "No summary available."

    replacements = {
        "<p>": "",
        "</p>": "",
        "<br>": "",
        "<br/>": "",
        "<br />": "",
        "&nbsp;": " ",
        "&amp;": "&",
        "&quot;": '"',
        "&#39;": "'"
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text.strip()


def summarize_article(entry):
    summary = entry.get("summary", "") or entry.get("description", "")
    summary = clean_text(summary)

    if len(summary) > 450:
        summary = summary[:450].rsplit(" ", 1)[0] + "..."

    return summary


def explain_why_it_matters(section):
    explanations = {
        "World News": "This story may affect international relations, public policy, security, or global stability.",
        "Business News": "This story may influence markets, companies, consumer behavior, jobs, or the broader economy.",
        "Supply Chain News": "This story may affect shipping costs, product availability, manufacturing, inventory planning, or consumer prices.",
        "Technology & AI News": "This story may shape innovation, privacy, regulation, workplace productivity, or digital competition."
    }

    return explanations.get(
        section,
        "This story may affect current events, public policy, business decisions, or everyday life."
    )


def collect_articles():
    briefing = {}

    for section, feeds in RSS_FEEDS.items():
        briefing[section] = []

        for feed_url in feeds:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", "Unknown Source")

            for entry in feed.entries[:ARTICLES_PER_SECTION]:
                article = {
                    "headline": entry.get("title", "No headline available"),
                    "source": source_name,
                    "summary": summarize_article(entry),
                    "link": entry.get("link", "#"),
                    "why_it_matters": explain_why_it_matters(section)
                }

                briefing[section].append(article)

        briefing[section] = briefing[section][:ARTICLES_PER_SECTION]

    return briefing


def build_email_html(briefing):
    today = date.today().strftime("%B %d, %Y")

    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">
        <h1>Daily News Briefing</h1>
        <p><strong>Date:</strong> {today}</p>
        <hr>
    """

    for section, articles in briefing.items():
        html += f"""
        <h2 style="color: #1a4f8b;">{section}</h2>
        """

        if not articles:
            html += "<p>No articles found for this section today.</p>"
            continue

        for article in articles:
            html += f"""
            <div style="margin-bottom: 24px;">
                <h3>{article['headline']}</h3>
                <p><strong>Source:</strong> {article['source']}</p>
                <p><strong>Summary:</strong> {article['summary']}</p>
                <p><strong>Why it matters:</strong> {article['why_it_matters']}</p>
                <p><a href="{article['link']}">Read full article</a></p>
            </div>
            """

        html += "<hr>"

    html += """
    </body>
    </html>
    """

    return html


def send_email(subject, html_body):
    sender_email = os.environ["SENDER_EMAIL"]
    app_password = os.environ["EMAIL_APP_PASSWORD"]
    recipient_email = os.environ["RECIPIENT_EMAIL"]

    message = MIMEText(html_body, "html")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = recipient_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, message.as_string())


if __name__ == "__main__":
    briefing = collect_articles()
    email_body = build_email_html(briefing)

    subject = f"Daily News Briefing — {date.today().strftime('%B %d, %Y')}"

    send_email(subject, email_body)

    print("Daily news briefing sent successfully.")
