# V3 public seed-question audit pack v0

> Status: review-only. These rows are not approved SFT, RL, validation, or test data.

## Purpose

This pack freezes 30 public **train-split** candidates for human review before any
4B search screen. Arithmetic labels were independently replayed during extraction,
but replay agreement does not prove that a question is unambiguous or useful.

## Composition

- TAT-QA: 25
- FinQA: 5
- TabMWP: 0 (withheld because inspected candidates were heavily templated)

Relation-family counts:

- `aggregate_percent_change`: 4
- `aggregate_percent_change_with_loss`: 1
- `average_growth_rate`: 4
- `derived_value_percent_change`: 2
- `difference_of_averages`: 4
- `midpoint_rate_application`: 1
- `multi_period_interest`: 1
- `payout_ratio`: 1
- `ratio_of_aggregates`: 1
- `ratio_of_derived_values`: 2
- `signed_multi_value_average`: 3
- `signed_percent_change`: 3
- `sum_of_products`: 1
- `weighted_average`: 2

## Review checklist

For every row in `data/review/v3_public_seed_audit_v0.jsonl`, decide:

1. Is the question unambiguous without revealing the solution procedure?
2. Are the referenced table/text values sufficient?
3. Is the derivation mathematically and semantically correct?
4. Are units and percentage conventions explicit enough?
5. Is the relation meaningfully different from already accepted rows?
6. Should the row enter the 4B pass@1/pass@N search screen?

## Candidate index

| # | Source | Family | Source ID | Ground truth | Question |
|---:|---|---|---|---:|---|
| 1 | TAT-QA | `weighted_average` | `8bb54bf1-f6da-41ca-895d-602dbb88cfa3` | 187.38 | What is Accenture's average share price paid per share for June and July of 2019? |
| 2 | TAT-QA | `weighted_average` | `347e3b8b-1982-4c53-a585-ab3001baed32` | 53.42 | What was the Average Price Paid per Share from March 2019 to April 2019? |
| 3 | TAT-QA | `average_growth_rate` | `28b7f2b6-f15a-4390-b42c-310d7e727e14` | 15.16 percent | What was the average year-on-year percentage change in total net revenue from 2017-2019? |
| 4 | TAT-QA | `average_growth_rate` | `8ade1eac-5a92-41bd-8b03-a74ae2769a6f` | 27.81 percent | What is the average year-on-year increase in Research and development from 2017 to 2019? |
| 5 | TAT-QA | `average_growth_rate` | `072b176c-a53e-4e12-97e6-b129ceb92da9` | -57.23 percent | What is the average year-on-year change for Additions and adjustments from 2017-2019?  |
| 6 | TAT-QA | `average_growth_rate` | `8fb16496-4bed-4e19-b230-a83de9ee6a59` | 0.11 percent | What is the average annual growth rate of Carrying value for Food Care for years 2017-2019? |
| 7 | TAT-QA | `difference_of_averages` | `af742fab-b68a-43ac-bb2b-77ef9f2fdbdf` | -1634.0 million | What is the change between 2017-2018 and 2018-2019 average income tax expense? |
| 8 | TAT-QA | `difference_of_averages` | `2671e667-7692-483f-9710-2390e33cbcd2` | 82200.5 thousand | What is the change in the average revenue between 2017-2018 and 2018-2019? |
| 9 | TAT-QA | `difference_of_averages` | `ed480f2f-da8f-41b2-a68e-b837920a8a6f` | -621.5 million | What is the change of average net cash flow from operating activities between 2017-2018 and 2018-2019? |
| 10 | TAT-QA | `difference_of_averages` | `21da1beb-b4d6-4439-8a3d-d91a8270b27d` | 188489.5 | What is the difference between the average processing revenue and the average outsourcing & cloud revenue for 2018-2019? |
| 11 | TAT-QA | `aggregate_percent_change` | `d161e8c3-56f2-44bb-8c38-635fca79b1aa` | 3.68 percent | What is the percentage change in total net sales of International and Refrigerated & Frozen from the fiscal year 2017 to 2018? |
| 12 | TAT-QA | `aggregate_percent_change` | `7dd9e6c9-76f7-4600-8dd5-1d1820a42462` | 1.87 percent | What is the percentage change in total operating profit of International and Foodservice from the fiscal year 2018 to 2019? |
| 13 | TAT-QA | `aggregate_percent_change` | `2b937b8e-a4b1-425c-a381-d6eab14bcc09` | 333.58 percent | What is the percentage change of total balances of contract assets, including current and non-current, from 2018 to 2019? |
| 14 | TAT-QA | `aggregate_percent_change` | `74bc19b4-b4f2-474d-8800-7d645ea59a8f` | 31.68 percent | What is the percentage change in Bookings, excluding the settlement gains, of the first two quarters 2019 to last two quarters? |
| 15 | TAT-QA | `derived_value_percent_change` | `c1a00c0a-57ac-4370-a0dd-448fb21daf29` | 16.78 percent | What is the percentage change in the total price of nonvested shares from December 31, 2018, to 2019? |
| 16 | TAT-QA | `signed_percent_change` | `27c35832-3665-49c5-98df-e669b51effaf` | 7.14 percent | What was the percentage change in unfunded obligations between 2018 and 2019? |
| 17 | TAT-QA | `signed_percent_change` | `858940e9-21f1-45db-acf2-21f298e367e5` | 90.87 percent | What was the percentage change in Interest expense between 2017 and 2018? |
| 18 | TAT-QA | `signed_percent_change` | `bc009826-d4f1-4c53-9e3c-0e6349e8b527` | -15.38 percent | What was the percentage change in the Warranty costs incurred between 2018 and 2019? |
| 19 | TAT-QA | `signed_multi_value_average` | `dc0cf4b4-cb13-42b3-8280-06dedbf02128` | -295.7 million | What is the average net income from 2015 to 2019? |
| 20 | TAT-QA | `signed_multi_value_average` | `a018d9b5-a8ed-4b3d-b4cb-7fdf8692b17c` | 4.0 million | What is the average amount of amendments for all benefits for fiscal 2018 and 2019? |
| 21 | TAT-QA | `signed_multi_value_average` | `b11bd2c7-36da-437a-af89-face31263fee` | -1053.4 thousand | What is the average Rent expense related to build-to-suit facilities between 2015-2019? |
| 22 | TAT-QA | `ratio_of_derived_values` | `b160a76e-1ecf-4b21-9741-846d837e37f8` | 1.93 | What is the ratio of the price of RSUs that were granted to the price of RSUs that were settled between 2018 and 2019? |
| 23 | TAT-QA | `ratio_of_derived_values` | `529497d1-cff1-4784-bc46-2c6a6839ca20` | 21.92 percent | What is the total unrecognised compensation costs related to unvested stock awards as a percentage of the value of nonvested shares at March 31, 2019?  |
| 24 | TAT-QA | `payout_ratio` | `7b071ea4-9b6f-42cd-b50b-71f0845d4ce8` | 33.33 percent | What is the dividend payout ration in year ending June 2018? |
| 25 | TAT-QA | `aggregate_percent_change_with_loss` | `0ccce335-dd41-498d-938a-cf526b7f6357` | 13.91 percent | What is the percentage change in total operating profit in 2018 compared to 2017? |
| 26 | FinQA | `sum_of_products` | `RCL/2009/page_90.pdf-1` | 2376487.57 | what was the total value of all shares of common stock were issued under the espp from 2007-2009?[14] : shares of common stock of 65005 , 36836 and 20759 were issued under the espp at a weighted-average price of $ 12.78 , $ 20.97 and $ 37.25 during 2009 , 2008 and 2007 , respectively . |
| 27 | FinQA | `derived_value_percent_change` | `MRO/2009/page_137.pdf-3` | -33.8 percent | according to the above listed weighted average grant date fair value , by what percentage did the value of unvested restricted stock awards decrease from 2008 to 2009? |
| 28 | FinQA | `multi_period_interest` | `BLK/2015/page_123.pdf-2` | 262.5 | how much will the company pay in interest on the 2022 notes between 2012 and 2022 ? in millions $ . |
| 29 | FinQA | `midpoint_rate_application` | `AMT/2014/page_88.pdf-1` | 5.4 | assuming a midpoint interest rate in the range , what would be the annual interest expense on interest rate swap agreements based on the notional amounts , in millions? |
| 30 | FinQA | `ratio_of_aggregates` | `IPG/2014/page_37.pdf-1` | 81.09 | what percentage of total debt is from long-term debt , from 2013-2014? |

## Non-goals

- Passing arithmetic replay is not automatic approval.
- Source programs are references, not the only acceptable model trajectory.
- No validation/test examples are included.
- The 30 rows must not be used for SFT until human review and split-family design are complete.
