import pandas as pd
import random
import os

def main():
    # Setup
    input_file = 'data/processed/support_tweets.csv'
    output_file = 'data/golden/intent_discovery_sample.csv'
    random.seed(42)

    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # Load data ensuring IDs are strings to maintain precision
    df = pd.read_csv(input_file, dtype={
        'tweet_id': str, 
        'response_tweet_id': str, 
        'in_response_to_tweet_id': str
    })

    # Prepare Amazon responses mapping
    amazon_df = df[df['author_id'] == 'AmazonHelp'].dropna(subset=['in_response_to_tweet_id'])
    response_map = dict(zip(amazon_df['in_response_to_tweet_id'], amazon_df['text']))
    
    # Filter for customer messages that have a linked AmazonHelp response
    customer_df = df[df['inbound'] == True].copy()
    customer_df = customer_df[customer_df['tweet_id'].isin(response_map.keys())]
    
    # Add response column
    customer_df['amazon_response'] = customer_df['tweet_id'].map(response_map)
    customer_df = customer_df.dropna(subset=['amazon_response'])

    # Sampling strategy:
    # 1. Non-ASCII (multilingual) examples
    non_ascii = customer_df[customer_df['text'].str.contains(r'[^\x00-\x7F]', na=False)]
    # 2. Short/noisy examples
    short_msgs = customer_df[customer_df['text'].str.len() < 35]
    # 3. Everything else (general pool)
    remaining = customer_df[~customer_df['tweet_id'].isin(pd.concat([non_ascii, short_msgs])['tweet_id'])]

    # Select representative sample (target ~400)
    samples = []
    # Add ~100 multilingual, ~100 short, ~200 from general
    samples.append(non_ascii.sample(n=min(len(non_ascii), 100), random_state=42))
    samples.append(short_msgs.sample(n=min(len(short_msgs), 100), random_state=42))
    samples.append(remaining.sample(n=min(len(remaining), 200), random_state=42))
    
    full_sample = pd.concat(samples).drop_duplicates(subset=['tweet_id'])

    # Save output
    os.makedirs('data/golden', exist_ok=True)
    full_sample.to_csv(output_file, index=False)

    # Statistics
    print("=== Sampling Summary ===")
    print(f"Total customer messages with explicit responses: {len(customer_df)}")
    print(f"Final sample size: {len(full_sample)}")
    
    multi_count = full_sample['text'].str.contains(r'[^\x00-\x7F]', na=False).sum()
    print(f"Number of multilingual/non-ASCII examples: {multi_count} ({multi_count/len(full_sample)*100:.1f}%)")
    
    short_count = full_sample['text'].str.len() < 35
    print(f"Number of short/noisy examples: {short_count.sum()}")
    
    # Thread check: Prepared CSV does not have 'thread_id' column
    print("Explicit thread ID not available in prepared dataset.")

    # 20 Random Representative Samples
    print("\n=== 20 Random Representative Samples (Customer -> Amazon) ===")
    for _, row in full_sample.sample(n=min(20, len(full_sample)), random_state=42).iterrows():
        print(f"\n[Tweet {row['tweet_id']}]")
        print(f"  Cust: {row['text'].replace('\n', ' ')[:100]}...")
        print(f"  Amzn: {row['amazon_response'].replace('\n', ' ')[:100]}...")

if __name__ == "__main__":
    main()
