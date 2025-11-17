import ijson
import argparse
import time
import sqlite3
import re
from datetime import datetime
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup
import pandas as pd
from tqdm import tqdm
from sklearn.linear_model import LinearRegression
import numpy as np

from flask import Flask, render_template_string

# ---------------------------------------------
# Database Setup
# ---------------------------------------------

DB_PATH = 'data/news_jobs.db'


def get_db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute('''
                CREATE TABLE IF NOT EXISTS articles
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    title
                    TEXT,
                    snippet
                    TEXT,
                    url
                    TEXT
                    UNIQUE,
                    content
                    TEXT,
                    publication_date
                    TEXT,
                    scraped_at
                    TEXT
                )
                ''')

    cur.execute('''
                CREATE TABLE IF NOT EXISTS job_changes
                (
                    id
                    INTEGER
                    PRIMARY
                    KEY
                    AUTOINCREMENT,
                    year
                    INTEGER,
                    jobs
                    INTEGER
                )
                ''')

    conn.commit()
    conn.close()


# ---------------------------------------------
# Crawling DuckDuckGo News
# ---------------------------------------------

def crawl_duckduckgo_news(query, pages=10, pause=1.0):
    """Crawl DuckDuckGo news result pages for a query."""
    results = []
    base_url = "https://duckduckgo.com/html/"

    for page in range(pages):
        params = {"q": query, "s": page * 30}
        url = base_url + "?" + urlencode(params)

        print("Fetching:", url)
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
        soup = BeautifulSoup(html, "html.parser")

        items = soup.select(".result__body")

        for item in items:
            title = item.select_one(".result__a")
            snippet = item.select_one(".result__snippet")
            link = title["href"] if title else None

            if title:
                results.append({
                    "title": title.text.strip(),
                    "snippet": snippet.text.strip() if snippet else "",
                    "url": link,
                })
        time.sleep(pause)
    return results


# ---------------------------------------------
# Fetch Article Content
# ---------------------------------------------

def fetch_full_article(url):
    try:
        html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")

        paragraphs = soup.find_all("p")
        text = "\n\n".join([p.get_text(" ", strip=True) for p in paragraphs])
        return text

    except Exception as e:
        print("ERR fetching:", url, e)
        return ""


# ---------------------------------------------
# Store Articles
# ---------------------------------------------

def store_articles(articles):
    conn = get_db_conn()
    cur = conn.cursor()

    for a in articles:
        cur.execute("""
                    INSERT
                    OR IGNORE INTO articles (title, snippet, url, content, publication_date, scraped_at)
            VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        a.get("title"),
                        a.get("snippet"),
                        a.get("url"),
                        a.get("content", ""),
                        a.get("publication_date", ""),
                        datetime.utcnow().isoformat()
                    ))

    conn.commit()
    conn.close()


# ---------------------------------------------
# Load Brazilian CSV
# ---------------------------------------------

def load_brazil_csv(path):
    df = pd.read_csv(path)
    df.columns = [c.lower().strip() for c in df.columns]
    return df


# ---------------------------------------------
# Analysis + Prediction
# ---------------------------------------------

def analyze_and_compare(brazil_df=None):
    conn = get_db_conn()
    df_articles = pd.read_sql_query("SELECT * FROM articles", conn)
    conn.close()

    df_articles["year"] = df_articles["scraped_at"].apply(lambda x: int(x[:4]))

    stats = df_articles.groupby("year").size().reset_index(name="articles")

    if brazil_df is not None and "year" in brazil_df.columns:
        merged = pd.merge(stats, brazil_df, on="year", how="left")
    else:
        merged = stats

    return merged


def predict_trends(df, target_col="jobs", years_ahead=5):
    if target_col not in df.columns:
        return pd.DataFrame()

    df = df.dropna(subset=[target_col])
    if len(df) < 2:
        return pd.DataFrame()

    X = df["year"].values.reshape(-1, 1)
    y = df[target_col].values

    model = LinearRegression()
    model.fit(X, y)

    last_year = df["year"].max()
    future_years = np.arange(last_year + 1, last_year + years_ahead + 1).reshape(-1, 1)
    preds = model.predict(future_years)

    return pd.DataFrame({"year": future_years.flatten(), "prediction": preds})


# ---------------------------------------------
# Flask Web UI
# ---------------------------------------------

app = Flask(__name__)

ARTICLES_LIST_TEMPLATE = """
<h1>News Articles</h1>
<ul>
{% for a in articles %}
  <li>
    <a href="/article/{{a.id}}">{{a.title}}</a><br>
    <small>{{a.snippet}}</small>
  </li>
{% endfor %}
</ul>
"""

ARTICLE_VIEW_TEMPLATE = """
<h1>{{title}}</h1>
<p><em>{{scraped_at}}</em></p>
<div id="content" style="height:500px; overflow-y:scroll; border:1px solid #ccc;">
  {{content|safe}}
</div>
"""


@app.route("/articles")
def articles_list():
    conn = get_db_conn()
    df = conn.execute("SELECT id, title, snippet FROM articles ORDER BY scraped_at DESC").fetchall()
    conn.close()
    return render_template_string(ARTICLES_LIST_TEMPLATE, articles=df)


@app.route("/article/<int:article_id>")
def article_view(article_id):
    conn = get_db_conn()
    row = conn.execute(
        "SELECT id, title, content, scraped_at FROM articles WHERE id=?",
        (article_id,)
    ).fetchone()
    conn.close()

    if not row:
        return "Not found", 404

    content_html = "<p>" + "</p><p>".join(row["content"].split("\n\n")) + "</p>"
    return render_template_string(
        ARTICLE_VIEW_TEMPLATE,
        title=row["title"],
        content=content_html,
        scraped_at=row["scraped_at"]
    )


# ---------------------------------------------
# Command Line Interface
# ---------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", default="tecnologia Brasil")
    parser.add_argument("--pages", type=int, default=10)
    parser.add_argument("--brazil-csv", default=None)
    parser.add_argument("--predict", type=int, default=5)
    parser.add_argument("--serve", action="store_true")
    args = parser.parse_args()

    init_db()

    print("Crawling DuckDuckGo…")
    results = crawl_duckduckgo_news(args.query, pages=args.pages)

    unique_urls = {}
    for r in results:
        if r["url"] not in unique_urls:
            unique_urls[r["url"]] = r

    articles = list(unique_urls.values())

    print("Fetching full text…")
    for a in tqdm(articles):
        a["content"] = fetch_full_article(a["url"])

    store_articles(articles)

    brazil_df = None
    if args.brazil_csv:
        brazil_df = load_brazil_csv(args.brazil_csv)

    merged = analyze_and_compare(brazil_df)
    preds = predict_trends(merged, years_ahead=args.predict)

    preds.to_csv("data/predictions.csv", index=False)
    print("Saved predictions.csv")

    if args.serve:
        print("Starting web server at http://127.0.0.1:5000/articles")
        app.run(host="0.0.0.0", port=5000)


if __name__ == "__main__":


    main()

from config import (
    DB_PATH,
    DUCKDUCKGO_URL,
    DEFAULT_QUERY,
    DEFAULT_PAGES,
    CRAWL_PAUSE,
    HEADERS,
    PREDICTIONS_OUTPUT,
    BRAZIL_CSV_DEFAULT,
)

html = requests.get(url, headers=HEADERS, timeout=10).text
preds.to_csv(PREDICTIONS_OUTPUT, index=False)

