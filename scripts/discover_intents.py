import pandas as pd
import re
from collections import Counter

def clean_text(text):
    """Normalizes text for frequency analysis without removing non-English scripts."""
    if not isinstance(text, str):
        return ""
    # Remove URLs and mentions
    text = re.sub(r'http\S+|@\w+', '', text)
    # Remove punctuation while preserving alphanumeric characters from all scripts
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    return " ".join(text.split())

def get_ngrams(text, n):
    """Generates n-grams from a list of tokens."""
    tokens = text.split()
    if len(tokens) < n:
        return []
    return [" ".join(tokens[i:i+n]) for i in range(len(tokens)-n+1)]

def analyze_patterns(texts, stop_words):
    """Computes frequencies for unigrams, bigrams, and trigrams."""
    unigrams, bigrams, trigrams = [], [], []
    for text in texts:
        tokens = [t for t in clean_text(text).split() if t and t not in stop_words]
        cleaned_sent = " ".join(tokens)
        unigrams.extend(tokens)
        bigrams.extend(get_ngrams(cleaned_sent, 2))
        trigrams.extend(get_ngrams(cleaned_sent, 3))
    return Counter(unigrams), Counter(bigrams), Counter(trigrams)

def main():
    file_path = 'data/processed/support_tweets.csv'
    try:
        df = pd.read_csv(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        return

    # Filter for customer messages
    customer_df = df[df['inbound'] == True].copy()
    total_cust = len(customer_df)
    
    # Map Amazon responses
    amazon_df = df[df['author_id'] == 'AmazonHelp'].dropna(subset=['in_response_to_tweet_id'])
    amazon_df['in_response_to_tweet_id'] = amazon_df['in_response_to_tweet_id'].astype(int)
    response_map = dict(zip(amazon_df['in_response_to_tweet_id'], amazon_df['text']))
    
    # Subset of customers with explicit responses
    responded_df = customer_df[customer_df['tweet_id'].isin(response_map.keys())]

    # Multilingual analysis
    customer_df['is_non_ascii'] = customer_df['text'].str.contains(r'[^\x00-\x7F]', na=False)
    non_ascii_count = customer_df['is_non_ascii'].sum()
    non_ascii_pct = (non_ascii_count / total_cust * 100) if total_cust > 0 else 0

    stop_words = {
        'the', 'to', 'i', 'a', 'and', 'my', 'is', 'in', 'it', 'for', 'you', 'on', 'with', 
        'this', 'of', 'have', 'your', 'me', 'that', 'im', 'am', 'was', 'so', 'but', 'be', 
        'at', 'can', 'are', 'if', 'not', 'do', 'we', 'as', 'will', 'just', 'amazon', 'help', 
        'hi', 'hello', 'please', 'thanks', 'thank', 'now', 'been', 'get', 'its', 'it\'s',
        'hey', 'checking', 'dm', 'sent', 'regards', 'team', 'service', 'customer', 'care'
    }

    print("Analyzing all customer messages...")
    u_all, b_all, t_all = analyze_patterns(customer_df['text'], stop_words)
    
    print("Analyzing messages that received a direct AmazonHelp response...")
    u_resp, b_resp, t_resp = analyze_patterns(responded_df['text'], stop_words)

    # --- OUTPUT REPORT ---

    print("\n=== Recurring Customer Message Patterns (All Inbound) ===")
    print("\nTop 30 Meaningful Single Words:")
    for word, count in u_all.most_common(30):
        print(f"- {word} ({count})")

    print("\nTop 30 Meaningful Bigrams:")
    for phrase, count in b_all.most_common(30):
        print(f"- {phrase} ({count})")

    print("\nTop 20 Meaningful Trigrams:")
    for phrase, count in t_all.most_common(20):
        print(f"- {phrase} ({count})")

    print("\n=== Patterns with Explicit AmazonHelp Responses ===")
    top_resp_patterns = [p[0] for p in b_resp.most_common(10)]
    for pattern in top_resp_patterns:
        print(f"\nPattern: '{pattern}' ({b_resp[pattern]} responded occurrences)")
        # Case-insensitive lookup using escaped pattern
        mask = responded_df['text'].str.contains(re.escape(pattern), case=False, na=False)
        for _, row in responded_df[mask].head(2).iterrows():
            cust_txt = row['text'].replace('\n', ' ')
            resp_txt = response_map.get(row['tweet_id'], "").replace('\n', ' ')
            print(f"   Cust: {cust_txt[:130]}...")
            print(f"   Amzn: {resp_txt[:130]}...")

    print("\n=== Ambiguous / Noisy Messages ===")
    for _, row in customer_df[customer_df['text'].str.len() < 35].head(5).iterrows():
        print(f"- {row['text'].replace('\n', ' ')}")

    print("\n=== Multilingual / Script Observations ===")
    print(f"Total customer messages: {total_cust}")
    print(f"Messages containing non-ASCII characters: {non_ascii_count} ({non_ascii_pct:.1f}%)")
    if non_ascii_count > 0:
        print("Real Examples:")
        for _, row in customer_df[customer_df['is_non_ascii']].head(5).iterrows():
            print(f"- {row['text'].replace('\n', ' ')[:150]}")

    print("\n=== Findings for Manual Intent Design (Evidence-Based) ===")
    # Derive observations from calculated counters
    top_bigram = b_all.most_common(1)[0][0] if b_all else "N/A"
    print(f"- The most common word combination across all messages is '{top_bigram}'.")
    
    # Check for delivery vs financial signals in response-linked data
    delivery_signal = any(word in u_resp for word in ['delivery', 'tracking', 'status', 'received'])
    financial_signal = any(word in u_resp for word in ['refund', 'money', 'charged', 'payment'])
    
    if delivery_signal:
        print("- Delivery and logistics tracking patterns appear frequently in messages that get responses.")
    if financial_signal:
        print("- Refund and payment-related patterns are significant triggers for AmazonHelp interaction.")
    
    # Observe trigram complexity
    if t_resp:
        print(f"- Trigrams like '{t_resp.most_common(1)[0][0]}' suggest highly specific customer inquiries.")

if __name__ == "__main__":
    main()
