import pandas as pd
import re
from collections import Counter

def clean_text(text):
    """Normalizes text for keyword analysis by removing noise and stopwords."""
    if not isinstance(text, str):
        return ""
    # Remove URLs, mentions, and non-alphabetic characters
    text = re.sub(r'http\S+|@\w+|[^a-zA-Z\s]', '', text).lower()
    
    stopwords = {
        'the', 'to', 'i', 'a', 'and', 'my', 'is', 'in', 'it', 'for', 'you', 'on', 'with', 
        'this', 'of', 'have', 'your', 'me', 'that', 'im', 'am', 'was', 'so', 'but', 'be', 
        'at', 'can', 'are', 'if', 'not', 'do', 'we', 'as', 'will', 'just', 'amazon', 'help', 
        'hi', 'hello', 'please', 'thanks', 'thank', 'now', 'been', 'get', 'it\'s', 'its'
    }
    
    words = [w for w in text.split() if w and w not in stopwords]
    return " ".join(words)

def main():
    file_path = 'data/processed/support_tweets.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found. Please run the data preparation script first.")
        return

    # 1. Data Quality Check
    print("=== Data Quality Check ===")
    print(f"Missing Tweet IDs: {df['tweet_id'].isna().sum()}")
    print(f"Missing Text: {df['text'].isna().sum()}")
    print(f"Duplicate Tweet IDs: {df['tweet_id'].duplicated().sum()}")
    print(f"Missing Thread IDs: {df['thread_id'].isna().sum()}")
    
    # Drop rows with critical missing data for analysis
    df = df.dropna(subset=['text', 'tweet_id', 'thread_id'])

    # 2. General Statistics
    print("\n=== General Statistics ===")
    inbound_mask = df['inbound'] == True
    outbound_mask = df['author_id'] == 'AmazonHelp'
    
    print(f"Total tweets: {len(df)}")
    print(f"Unique conversation threads: {df['thread_id'].nunique()}")
    print(f"Customer/inbound messages: {inbound_mask.sum()}")
    print(f"AmazonHelp/outbound messages: {outbound_mask.sum()}")

    # 3. Thread Statistics
    print("\n=== Thread Statistics ===")
    thread_counts = df['thread_id'].value_counts()
    
    # Identify which threads have which type of message
    thread_has_customer = df[inbound_mask]['thread_id'].unique()
    thread_has_amazon = df[outbound_mask]['thread_id'].unique()
    
    print(f"Threads with at least one customer message: {len(thread_has_customer)}")
    print(f"Threads with at least one AmazonHelp message: {len(thread_has_amazon)}")
    print(f"Average tweets per conversation: {thread_counts.mean():.2f}")
    print(f"Median tweets per conversation: {thread_counts.median():.0f}")
    print(f"Minimum conversation length: {thread_counts.min()}")
    print(f"Maximum conversation length: {thread_counts.max()}")

    # 4. Conversation Length Distribution
    print("\n=== Conversation Length Distribution ===")
    total_threads = len(thread_counts)
    dist = thread_counts.value_counts().sort_index()
    
    lengths = [1, 2, 3, 4]
    for length in lengths:
        count = dist.get(length, 0)
        print(f"{length} tweet: {count} ({count/total_threads*100:.1f}%)")
    
    five_plus = thread_counts[thread_counts >= 5].count()
    print(f"5+ tweets: {five_plus} ({five_plus/total_threads*100:.1f}%)")

    # 5. Customer Message Topic Analysis
    print("\n=== Top 20 Customer Message Keywords ===")
    customer_texts = df[inbound_mask]['text'].apply(clean_text)
    all_words = [word for text in customer_texts for word in text.split()]
    top_keywords = Counter(all_words).most_common(20)
    for i, (word, count) in enumerate(top_keywords, 1):
        print(f"{i}. {word}: {count}")

    # 6. Response Mapping
    # Find customer tweets that have a corresponding response from AmazonHelp
    amazon_replies_to = set(df[outbound_mask]['in_response_to_tweet_id'].dropna().unique())
    customer_tweet_ids = df[inbound_mask]['tweet_id']
    responded_mask = customer_tweet_ids.isin(amazon_replies_to)
    responded_count = responded_mask.sum()
    
    print("\n=== Response Mapping ===")
    print(f"Customer messages with an explicit linked AmazonHelp response: {responded_count}")
    print(f"Response coverage: {responded_count/len(customer_tweet_ids)*100:.1f}%")

    # 7. Representative Examples
    print("\n=== Representative Examples (Customer -> AmazonHelp) ===")
    # Map customer tweet IDs to Amazon responses for quick lookup
    amazon_responses = df[outbound_mask].dropna(subset=['in_response_to_tweet_id'])
    response_lookup = dict(zip(amazon_responses['in_response_to_tweet_id'], amazon_responses['text']))
    
    # Get 10 customer tweets that actually have a response
    responded_customers = df[inbound_mask & df['tweet_id'].isin(amazon_replies_to)].head(10)
    
    for _, row in responded_customers.iterrows():
        tid = row['thread_id']
        cust_text = row['text'].replace('\n', ' ')
        resp_text = response_lookup.get(row['tweet_id'], "").replace('\n', ' ')
        
        print(f"\n[Thread {tid}]")
        print(f"  Customer: {cust_text[:147]}...")
        print(f"  Amazon:   {resp_text[:147]}...")

if __name__ == "__main__":
    main()
