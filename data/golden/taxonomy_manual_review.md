# Taxonomy Manual Review

This report uses conservative heuristic evidence to identify taxonomy coverage, overlaps, no-match themes, and examples requiring manual review. It is not classifier accuracy.

## 1. Dataset and method

- Brand: `AmazonHelp`
- Taxonomy: `data/golden/intent_taxonomy.json`
- Discovery sample: `data/golden/intent_discovery_sample.csv`
- Sample size: 400
- Method: conservative intent-specific heuristic validation
- No LLM, embeddings, external APIs, or classifier training are used by this validator.

## 2. Summary

| Metric | Count |
|---|---:|
| total_messages | 400 |
| clear_matches | 15 |
| weak_matches | 42 |
| ambiguous_matches | 2 |
| no_matches | 341 |
| multilingual_messages | 120 |
| short_or_noisy_messages | 128 |

## 3. Intent coverage

| Intent | Best matches | Candidate matches | % best |
|---|---:|---:|---:|
| Delivery Delay | 14 | 15 | 3.5% |
| Package Marked Delivered But Not Received | 29 | 32 | 7.2% |
| Damaged or Defective Item | 7 | 7 | 1.8% |
| Refund and Billing Issue | 12 | 14 | 3.0% |
| Order Cancellation | 7 | 8 | 1.8% |
| Account and Login Issue | 5 | 11 | 1.2% |
| Prime Membership | 15 | 18 | 3.8% |
| Technical and Digital Content | 18 | 19 | 4.5% |
| Other / Unclear / Ambiguous | 2 | 3 | 0.5% |

## 4. Intent overlaps

No high-confidence overlap pairs met the reporting threshold.

## 5. Other / Unclear

- Count: 2
- Percentage: 0.5%

- Review these examples manually because Other / Unclear should not become a catch-all for messages containing generic words such as help.

### Examples

- **1115370**: @AmazonHelp No new message...
- **1033211**: @AmazonHelp I sent a message &amp; it says I'll hear back within 12hrs. I don't have time for this. I'm done with Amazon. Goodnight.

## 6. No-match analysis

- No-match count: 341
- Percentage: 85.2%

### Recurring themes

- `delivery` (19)
- `i'm` (18)
- `from` (18)
- `any` (14)
- `all` (14)
- `got` (14)
- `delivered` (13)
- `why` (13)
- `they` (12)
- `ordered` (12)
- `what` (12)
- `how` (12)
- `day` (12)
- `it's` (11)
- `time` (10)
- `got email` (3)
- `how long` (3)
- `day delivery` (3)
- `day shipping` (3)
- `die neue` (2)

These themes require manual review and should not automatically become new intents.

## 7. Multilingual analysis

- Multilingual examples: 120
- Percentage: 30.0%

| Status | Count |
|---|---:|
| no_match | 104 |
| weak_match | 11 |
| clear_match | 3 |
| ambiguous_multiple_matches | 2 |

## 8. Delivery delay review

- Candidate count: 15
- Best matches: 14
- Suspicious delivered-status examples: 0

Delivery delay should cover late, overdue, stuck, or not-yet-received orders without delivered-status language. Delivered-status complaints should normally be reviewed under missing_delivered.


## 9. Intent-by-intent review

### Delivery Delay (`delivery_delay`)

- Best matches: 14
- Candidate matches: 15
- Percentage: 3.5%
- Review note: 2 candidate examples have high-confidence overlap with another intent.

Representative examples:

- **1108240**: @138673 @115850 Expected delivery today .. status showing surprisingly not shipped yet but arriving today.When???👎
- **1007738**: @AmazonHelp Re-sending (which I requested to a different address) or a refund. But neither really solve the problem that it’s Prime and late.
- **1114866**: @AmazonHelp No explanation offered. It’s been sent back twice and estimate delivery date just changes. I have no clue what’s going on
- **1140841**: @AmazonHelp Case number 4513803001 called on 10/9 for reimbursement check  $39.99 still waiting for check. Put in request on 8/31/17.
- **1081743**: @115850  still Issue with you amazon delivery became to late more than two days am ordering product for me not for your hub
### Package Marked Delivered But Not Received (`missing_delivered`)

- Best matches: 29
- Candidate matches: 32
- Percentage: 7.2%

Representative examples:

- **1022541**: @115821 whyyyyyyy did you say you delivered my package an hour ago and it still isn’t here????!???????????????????????
- **1004663**: @115850 @AmazonHelp @115821 @15704 This is the product link
  
 
( This product can’t delivered to your place 600039 - pin code ) 

 Will I get this product to my home (Chennai) please tell me? I’m ready to pay 59$ if it delivers to my home. Help me
- **1055233**: @AmazonHelp 😡😡 second time in 4 days, I’m in the house and can confirm this item hasn’t been delivered, help!
- **1053584**: @AmazonHelp Just received a text saying it will be delivered on Wednesday. How’s that possible? Earlier it said it should be delivered today!!!
- **1022540**: @AmazonHelp That link supplies Literally no help and still the package isn’t here. Thanks
### Damaged or Defective Item (`damaged_item`)

- Best matches: 7
- Candidate matches: 7
- Percentage: 1.8%

Representative examples:

- **1064866**: The most painful thing about my broken/cracked devices is that I'm not the one doing the damage to them. My laptop, my Kindle &amp; now, phone.
- **1073280**: @115821 Help pls 1) item arrived damaged 2) No confirmatory email from amazon 3) No details on amazon acct! Looks fishey, I need to DM photo
- **1087751**: @AmazonHelp Yes, both times some of the K-Cups inside have been squished to the point of leaking their contents.
- **1104313**: @118919 @115850
My frnd ordered MotoG5 but U gave him old broken mob with Rin Soap bars.Diwali offer char raha hai kya? @380607
- **1033071**: @AmazonHelp Yesterday, after see that the product is wrong and that it is also defective. Amazon get all info. needed. I sent almost a report to you.
### Refund and Billing Issue (`refund_request`)

- Best matches: 12
- Candidate matches: 14
- Percentage: 3.0%
- Review note: 1 candidate examples have high-confidence overlap with another intent.

Representative examples:

- **1125124**: @115850 you always continue to gain my reliability and I am highly impressed with the service, within couple of hours of pick up of the return product, am refunded. You r truly consumer centric😎😎😎
- **1173909**: @AmazonHelp hi, you've cancelled and refunded my order of £16.15 without asking me. To reorder will cost me £20.48 - bit of a piss take no 🤔
- **103080**: @AmazonHelp my friend has had money taken out of her bank and she hasn't bought anything and isn't signed up for anything @138670
- **1043560**: @116928 Trying to claim refund for the government funded bank of books, ,( banco de llibres) please advise
- **1124526**: @AmazonHelp I have shared my order details many times with Amazon and your system is showing two types of payment mode bt i have done only one
### Order Cancellation (`cancellation_request`)

- Best matches: 7
- Candidate matches: 8
- Percentage: 1.8%

Representative examples:

- **1020067**: @115850 I ordered something now I cancelled it bt it has already display n pickup N delivery dates r same.wat shall I do? Help me!
- **1103677**: @228164 @115850  buying amazon email gift card n paying thru indusind amex card, bank approves d transaction yet order cancelled.
- **1119124**: @AmazonHelp I didn't any link . It just said if you want to cancel it
- **109935**: @AmazonHelp y u guys cancelled my order 407-0880525-1284313 without any intimation.
- **1053490**: @AmazonHelp Tried placing an order on amazon.fr and amazon.es for snes classic. Order cancelled and accounts closed. Multiple times.
### Account and Login Issue (`account_access`)

- Best matches: 5
- Candidate matches: 11
- Percentage: 1.2%
- Review note: 3 candidate examples have high-confidence overlap with another intent.

Representative examples:

- **1112584**: Hi @AmazonHelp I am still getting these weird emails after someone stole my password 😳
- **1135907**: Hello @AmazonHelp still waiting for someone to call me about my hacked account please 🙃🙃🙃🙃 haven’t got the spare money to just give away tnx
- **1102334**: @AmazonHelp I have no idea whether it is on hold or no.Tried changing the password stll showing incorrect password.regstrd id __email__
- **115960**: Hey @AmazonHelp @116316  

Normaler, deutscher Account hier in Deutschland ohne VPN - was ist da falsch?! 
Neuinstallation inkl. Neuem Login hilft nicht.
- **1070002**: @AmazonHelp The link takes me to login to amazon.in account. The CS exec there has already asked me to contact @115821  for resolution
### Prime Membership (`prime_membership`)

- Best matches: 15
- Candidate matches: 18
- Percentage: 3.8%
- Review note: 3 candidate examples have high-confidence overlap with another intent.

Representative examples:

- **1104587**: @115830 why has £7.99 taken out off my account AMAZON UK PRIME   LU. not a prime customer
- **1152632**: @AmazonHelp Y por otro lado he comprado un producto en preventa con prime que aún no se le conoce fecha de entrega, pero que puedo comprar en stock...
- **1176293**: @AmazonHelp Lmao become a prime member ...uhh I am since I’m signed into the app.
- **1076380**: @AmazonHelp Pero es el crédito que disteis con la promoción de prime video. No es un código en si.
- **1128650**: @115830 I need help I have an account which has randomly had the email address changed. I have a prime subscription on the account. HELP!!
### Technical and Digital Content (`technical_support`)

- Best matches: 18
- Candidate matches: 19
- Percentage: 4.5%
- Review note: 2 candidate examples have high-confidence overlap with another intent.

Representative examples:

- **1146940**: @AmazonHelp recentemente, fiz duas compras na amazon: um livro e o kindle paperwhite
na caso do livro, recebi uma cobrança de R$1 além do preço do livro
- **1166760**: @123813 Cuando lanzaran alguna App para Roku TV en México????
- **108217**: @117086 Obrigado por colocar o Kindle em promoção
- **1068511**: @AmazonHelp Up to date. Here’s the message - same on iOS or computer via
- **1167702**: @AmazonHelp Ugh! I’m in the UK now, where, for some paranoid reason, laws are in place that make every website have a cookie acceptance clause.
### Other / Unclear / Ambiguous (`other_unclear`)

- Best matches: 2
- Candidate matches: 3
- Percentage: 0.5%
- Review note: Low representation in this discovery sample; manual review is required.

Representative examples:

- **1115370**: @AmazonHelp No new message...
- **1033211**: @AmazonHelp I sent a message &amp; it says I'll hear back within 12hrs. I don't have time for this. I'm done with Amazon. Goodnight.

## 10. Recommendations

- The heuristic validator is intentionally conservative. Do not interpret the low clear-match count as poor taxonomy quality; use it to identify examples for manual review.
- Review Other / Unclear examples manually and ensure generic words such as help, please, or there are not driving intent assignment.
- Review no-match examples for recurring actionable customer problems before adding any new intent.
- Include multilingual examples in the manual golden-set review so taxonomy decisions are not English-only.
- Do not use this heuristic report as classifier accuracy. The final taxonomy should be validated through manual labeling of the 150–250 example golden evaluation set.

## 11. Important limitation

This validator is for taxonomy discovery and manual review. It must not be reported as intent-classifier accuracy. The final classifier evaluation should use the manually labeled 150–250 example golden set.
