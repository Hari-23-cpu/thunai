# Processed Support Data

Output of `scripts/prepare_data.py`. Built from the sample of the Kaggle
["Customer Support on Twitter"](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
dataset.

> **Note:** this is built from a small sample in `data/raw/sample.csv`, used for
> initial development and structure exploration. It does **not** represent the
> full dataset (~800k tweets), and the numbers below only describe the sample.

## Source dataset

Each row is one tweet. Columns:

| Column | Meaning |
|---|---|
| `tweet_id` | Unique tweet id |
| `author_id` | Author: a brand handle (e.g. `AppleSupport`) or an anonymized customer id (numeric) |
| `inbound` | `True` = tweet from a customer (inbound), `False` = tweet from the brand (outbound) |
| `created_at` | Tweet timestamp, e.g. `Wed Oct 11 06:55:44 +0000 2017` |
| `text` | Tweet text |
| `response_tweet_id` | Id(s) of tweet(s) that replied to this one (can be comma-separated) |
| `in_response_to_tweet_id` | Id of the tweet this one replies to (single value) |

- Customers are **anonymous numeric ids** (`105834`); brands keep their handles.
- Customers @mention the brand; brands address customers by their numeric id.
- A tweet can get **multiple replies** (`response_tweet_id` like `"119249,119251"`).

## What the processing script does (`scripts/prepare_data.py`)

1. **Cleaning** (kept minimal):
   - Drops rows missing `tweet_id` or `text`, drops duplicate `tweet_id`s.
   - Removes URLs (noise for classification) and HTML-escapes (`&amp;` → `&`).
   - No other text normalization — the raw text is useful as-is.
2. **Conversation linking**: follows `in_response_to_tweet_id` from every tweet
   up to the first tweet of the conversation and stores it as `thread_id`.
   All tweets in a conversation share one `thread_id` (the root's tweet id).
3. **Brand selection**: counts outbound tweets per brand and keeps every
   conversation that involves the most active brand.
4. Saves the result to `data/processed/support_tweets.csv`.

## Sample statistics (sample only, not the full dataset)

- **93 rows**, 7 columns, no missing text, no duplicate tweet ids.
- 49 inbound (customer) / 44 outbound (brand) tweets.
- **13 brands** present. Outbound counts:

  | Brand | Tweets |
  |---|---|
  | AppleSupport | 13 |
  | SpotifyCares | 8 |
  | Tesco | 8 |
  | VirginTrains | 4 |
  | British_Airways | 3 |
  | (8 others, 1 each) | 1 |

- Conversation linking works well: 66 of 68 reply links resolve to a tweet
  present in the sample, so threads can be reconstructed from the columns.

## Brand analysis: why AppleSupport

- Most brand messages (13), and the most customer conversations that mention
  it. SpotifyCares and Tesco follow closely — the sample is small, so this
  ranking reflects the sample only.
- Its conversations form a clear, focused support theme: customers complain
  about the **iOS 11 update** — slow phone, battery drain, crashing apps,
  wifi drops, and one verification-code issue. Brand replies are helpful and
  concrete (asking for iOS versions, pointing to Settings, asking to DM).
- Longer multi-turn exchanges with a real back-and-forth, which is what the
  intent classifier and reply agent need.

## Recurring customer issues observed in the sample

- **AppleSupport**: iOS 11 update problems — slow performance, battery drain,
  app crashes, wifi disconnects; verification code not received.
- **SpotifyCares**: playback stopping midway / skipping on bluetooth speakers.
- **Tesco**: website not showing delivery slots; account/app usability
  complaints; over-18 ID checks at stores.
- **VirginTrains**: broken live chat / phone lines, unanswered contacts.

## Output: `support_tweets.csv`

All tweets from the 11 conversations that involve the selected brand
(29 tweets), with one added column:

- `thread_id` — tweet id of the first tweet of the conversation. Sort or group
  by it to rebuild each conversation.

What this gives downstream components:

- **Intent classification**: real, labeled-by-nothing customer texts
  (`inbound == True`) covering concrete issues — enough to *propose* an intent
  taxonomy from the data (not finalized yet).
- **Historical-response retrieval**: paired customer/brand messages within a
  `thread_id` — brand replies to a customer tweet are exactly the "past
  responses" a retrieval step would search over.
- **Evaluation** (later): conversation structure supports building
  message→official-reply pairs once the intent taxonomy is settled.
