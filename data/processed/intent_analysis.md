# Intent Analysis — AppleSupport Sample (refined)

Based only on the 16 inbound (customer) messages in `support_tweets.csv`
(11 conversations). Not finalized — see validation note at the end.

## Final proposed taxonomy (5 intents)

Accounting for all 16 inbound messages: **11 labeled + 1 status + 4 ambiguous = 16**.

### 1. `battery_drain` — 4 messages
- [119268] "I used my fucking phone for 2 minutes and it drains it down 8 fucking percent"
- [119292] "#ios11update - is still killing my battery within 12 hours"

### 2. `slow_performance` — 2 messages
- [119253] "I just updated my phone and suddenly everything takes ages to load"
- [119250] "the latest ios is too slow on #iphone6"

### 3. `app_crash_freeze` — 2 messages
- [119326] "My apps stop working without warning and my phone freezes every five minutes!"
- [119263] "most of the apps are broken, wifi disconnects frequently"

### 4. `update_issue` — 2 messages
General update complaints / rollback requests with no specific measured symptom.
- [119270] "Can you get my iPhone 7plus back on the old iOS please?"
- [119301] "fix this update. It's horrible"

### 5. `verification_code` — 1 message
- [119299] "I need a new code for my I-store. I haven't recd any but msg is too many sent. Help!"

Only one example — thin support in this sample, kept because it is a genuinely
distinct problem type.

## Ambiguous (no forced label) — 4 messages

- [119249] "Me too am suffering , hope the can find a solution" — no issue stated.
- [119272] "You've paralysed my phone with your update" — symptom unclear (slow? frozen? just angry).
- [119280] "does not let me listen to music and go on whatsapp at the same time" — feature regression; fits none of the above.
- [119324] "I have the latest version iOS. It started immediately after I updated my phone." — follow-up; the symptom ("it") is only in the earlier tweet of the same thread.

## Outcome/status (not an intent) — 1 message

- [119291] "Super help - problem solved 😀 once again in love with Apple" — resolution confirmation.
- The other 15 messages report an open problem or lack issue context; the
  sample has no closure signal for them.

If status is useful later, track it as a separate label
(`resolved` / `unresolved` / `unknown`) alongside the intent.

## Changes from previous draft

- `resolved_positive` moved out of the taxonomy into outcome/status.
- `update_complaint` renamed `update_issue` and trimmed: vague/overlapping
  messages ([119272], [119280]) moved to ambiguous instead of forcing a label.
- [119294] (battery log) folded into `battery_drain`; counts now sum to 16.

## Validation note

This taxonomy is derived from a 16-message sample of one brand. It must be
validated (and likely extended) on the full dataset before the classifier
is finalized. Expect low-frequency intents like `verification_code` to be
more common in the full data, and new issue types to appear.
