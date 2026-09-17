import csv
import os
from collections import Counter

def format_size(bytes_size):
    """Formats file size in MB."""
    return f"{bytes_size / (1024 * 1024):.2f} MB"

def analyze_brands():
    """
    Analyzes the Twitter dataset to select a suitable brand for the Hiver assignment.
    Processes the file in two passes to maintain a low memory footprint.
    """
    file_path = 'data/raw/twcs.csv'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    file_size = os.path.getsize(file_path)
    
    # PASS 1: Identify major brands by counting total outbound messages.
    # This helps us filter down to a manageable list of brands for deeper analysis.
    print("Reading dataset (Pass 1/2: Finding major brands)...")
    outbound_counts = Counter()
    total_rows = 0
    
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            if row['inbound'].lower() == 'false':
                outbound_counts[row['author_id']] += 1

    # Select the top 20 brands for detailed analysis.
    # This allows us to keep the mapping of tweet_ids to brands in memory for only these brands.
    top_brand_names = {name for name, count in outbound_counts.most_common(20)}
    
    # PASS 2: Collect interaction statistics for the top brands.
    # tweet_to_brand: tweet_id (int) -> brand_name (str)
    # We only store mappings for outbound tweets belonging to our candidate brands.
    tweet_to_brand = {}
    
    # Initialize statistics for selected brands
    brand_stats = {brand: {
        'outbound': 0,
        'inbound_associated': 0,
        'unique_customers': set(),
        'responded_inbound': 0,
        'conversation_starts': 0
    } for brand in top_brand_names}

    print(f"Reading dataset (Pass 2/2: Deep analysis for {len(top_brand_names)} brands)...")
    # We need a second pass to attribute customer messages based on response links
    # First, populate tweet_to_brand mapping for our candidates
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            tid = int(row['tweet_id'])
            aid = row['author_id']
            if aid in top_brand_names and row['inbound'].lower() == 'false':
                tweet_to_brand[tid] = aid
                brand_stats[aid]['outbound'] += 1

    # Now, process all customer messages to link them to our candidate brands
    with open(file_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['inbound'].lower() == 'true':
                tid = int(row['tweet_id'])
                aid = row['author_id']
                
                target_brand = None
                
                # Check 1: Did a brand respond to this message?
                resp_ids = row['response_tweet_id']
                if resp_ids:
                    for rid in resp_ids.split(','):
                        rid_int = int(rid.strip())
                        if rid_int in tweet_to_brand:
                            target_brand = tweet_to_brand[rid_int]
                            brand_stats[target_brand]['responded_inbound'] += 1
                            break
                
                # Check 2: Is this message a response to a brand?
                if not target_brand:
                    pid_str = row['in_response_to_tweet_id']
                    if pid_str:
                        pid = int(pid_str)
                        if pid in tweet_to_brand:
                            target_brand = tweet_to_brand[pid]
                
                # If associated with a brand, update stats
                if target_brand:
                    brand_stats[target_brand]['inbound_associated'] += 1
                    brand_stats[target_brand]['unique_customers'].add(aid)
                    # Approximation: Count as a conversation start if it's not a response to anything
                    if not row['in_response_to_tweet_id']:
                        brand_stats[target_brand]['conversation_starts'] += 1

    # Prepare data for report and ranking
    results = []
    for brand, data in brand_stats.items():
        in_count = data['inbound_associated']
        responded = data['responded_inbound']
        
        # Calculate response rate for associated messages
        rate = (responded / in_count * 100) if in_count > 0 else 0.0
        
        results.append({
            'brand': brand,
            'outbound': data['outbound'],
            'inbound': in_count,
            'customers': len(data['unique_customers']),
            'conversations': data['conversation_starts'],
            'responded': responded,
            'rate': rate
        })

    # Ranking Strategy:
    # We want a brand with high "responded" counts because those represent complete 
    # interaction pairs needed for training an AI agent.
    # Tie-breakers: total inbound, then total outbound, then alphabetical.
    results.sort(key=lambda x: (-x['responded'], -x['inbound'], -x['outbound'], x['brand']))

    # Print Final Report
    print(f"\nDataset")
    print(f"-------")
    print(f"Filename: {os.path.basename(file_path)}")
    print(f"File size: {format_size(file_size)}")
    print(f"Total rows processed: {total_rows}")

    print(f"\nTop 10 Candidate Brands")
    print(f"-----------------------")
    for i, res in enumerate(results[:10], 1):
        print(f"Rank {i}")
        print(f"Brand: {res['brand']}")
        print(f"Outbound messages: {res['outbound']}")
        print(f"Inbound customer messages: {res['inbound']}")
        print(f"Unique customers: {res['customers']}")
        print(f"Conversation starts (approx): {res['conversations']}")
        print(f"Inbound messages with outbound response: {res['responded']}")
        print(f"Response rate: {res['rate']:.2f}%")
        print("-" * 30)

    if results:
        best = results[0]
        print(f"\nRecommended Brand")
        print(f"-----------------")
        print(f"Brand: {best['brand']}")
        print(f"Why this brand was selected:")
        print(f"- It has the highest number of customer messages ({best['responded']}) with confirmed brand responses.")
        print(f"  This is crucial for building an AI that drafts replies based on historical ground truth.")
        print(f"- The brand interacts with {best['customers']} unique customers, ensuring a diverse range of intents.")
        print(f"- There are approximately {best['conversations']} new conversation threads to analyze for historical patterns.")
        print(f"- Note: Conversation starts are approximated by counting associated inbound messages that have no parent tweet.")

if __name__ == "__main__":
    analyze_brands()
