import json
import os
import dotenv
import base64
from io import BytesIO
import pandas as pd
from pandasai import SmartDataframe
import matplotlib.pyplot as plt

import praw

from dagster import asset, AssetExecutionContext, MetadataValue, MaterializeResult
from .resources import DataGeneratorResource

dotenv.load_dotenv()

# Initialize the Reddit instance
reddit = praw.Reddit(
    client_id=os.getenv("CLIENT_ID"),
    client_secret=os.getenv("CLIENT_SECRET"),
    password=os.getenv("REDDIT_PASSWORD"),
    username="basicallysejuani",
    user_agent="secret-llama-agent",
)

@asset
def topreddit_ids() -> None:
    # Specify the subreddit you want to fetch data from
    subreddit_name = "LocalLlama"
    subreddit = reddit.subreddit(subreddit_name)

    # Fetch the top posts from the subreddit
    top_posts = subreddit.top(limit=100)

    # Extract the post IDs
    top_post_ids = [post.id for post in top_posts]

    # Create the "data" directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    # Save the post IDs to a JSON file
    with open("data/top_post_ids.json", "w") as f:
        json.dump(top_post_ids, f)
        
@asset(deps=[topreddit_ids])  # this asset is dependent on topreddit_ids
def topstories(context: AssetExecutionContext) -> MaterializeResult:
    with open("data/top_post_ids.json", "r") as f:
        top_post_ids = json.load(f)

    results = []
    for item_id in top_post_ids:
        submission = reddit.submission(id=item_id)
        results.append({
            "title": submission.title,
            "score": submission.score,
            "url": submission.url,
            "comments": submission.num_comments,
        })

        if len(results) % 20 == 0:
           context.log.info(f"Processed {len(results)} submissions") 

    df = pd.DataFrame(results)
    df.to_csv("data/topstories.csv")
    
    return MaterializeResult(metadata={ 
                                    "num_submissions": len(df),
                                    "preview": MetadataValue.md(df.head().to_markdown()),
    })
    
@asset(deps=[topstories])
def most_frequent_words() -> None:
    stopwords = ["a", "the", "an", "of", "to", "in", "for", "and", "with", "on", "is"]

    topstories = pd.read_csv("data/topstories.csv")

    # loop through the titles and count the frequency of each word
    word_counts = {}
    for raw_title in topstories["title"]:
        title = raw_title.lower()
        for word in title.split():
            cleaned_word = word.strip(".,-!?:;()[]'\"-")
            if cleaned_word not in stopwords and len(cleaned_word) > 0:
                word_counts[cleaned_word] = word_counts.get(cleaned_word, 0) + 1

    # Get the top 25 most frequent words
    top_words = {
        pair[0]: pair[1]
        for pair in sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:25]
    }

    # Create a bar chart of the top 25 words
    plt.figure(figsize=(12, 8))
    plt.bar(top_words.keys(), top_words.values())
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Word')
    plt.ylabel('Frequency')
    plt.title('Top 25 Most Frequent Words in Reddit Titles')
    
    # Convert to saveable format
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    image_data = base64.b64encode(buffer.getvalue())
    
    md_content = f"![img](data:image/png;base64,{image_data.decode()})"

    with open("data/most_frequent_words.json", "w") as f:
        json.dump(top_words, f)
        
    return MaterializeResult(metadata={"plot": MetadataValue.md(md_content)})

@asset
def signups(reddit_api: DataGeneratorResource) -> MaterializeResult:
    signups = pd.DataFrame(reddit_api.get_signups())

    signups.to_csv("data/signups.csv")
    
    return MaterializeResult(metadata={ 
                                    "Record Count": len(signups),
                                    "Preview": MetadataValue.md(signups.head().to_markdown()),
                                    "Earliest Signup": signups["registered_at"].min(),
                                    "Latest Signup": signups["registered_at"].max(),
    })
    

