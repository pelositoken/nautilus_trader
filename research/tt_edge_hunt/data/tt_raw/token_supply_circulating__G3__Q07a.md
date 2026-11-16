Daily circulating supply (token count) for the four of the five requested entities that have observations in this window, one row per calendar day from 2023-12-01 to 2024-01-15. Ondo Finance returned no rows for the metric in this window.

| Date | Aave | Injective | Filecoin |
|:---|---:|---:|---:|
| December 1, 2023 | 14.7M | 84.3M | 475M |
| December 2, 2023 | 14.7M | 84.3M | 475M |
| December 3, 2023 | 14.7M | 84.3M | 475M |
| December 4, 2023 | 14.7M | 84.3M | 475M |
| December 5, 2023 | 14.7M | 84.3M | 476M |
| December 6, 2023 | 14.7M | 84.3M | 476M |
| December 7, 2023 | 14.7M | 84.3M | 476M |
| December 8, 2023 | 14.7M | 84.3M | 477M |
| December 9, 2023 | 14.7M | 84.3M | 478M |
| December 10, 2023 | 14.7M | 84.3M | 478M |
| December 11, 2023 | 14.7M | 84.3M | 479M |
| December 12, 2023 | 14.7M | 84.3M | 480M |
| December 13, 2023 | 14.7M | 84.3M | 480M |
| December 14, 2023 | 14.7M | 84.3M | 480M |
| December 15, 2023 | 14.7M | 84.3M | 481M |
| December 16, 2023 | 14.7M | 84.3M | 482M |
| December 17, 2023 | 14.7M | 84.3M | 482M |
| December 18, 2023 | 14.7M | 84.3M | 483M |
| December 19, 2023 | 14.7M | 84.3M | 483M |
| December 20, 2023 | 14.7M | 84.3M | 484M |
| December 21, 2023 | 14.7M | 84.3M | 484M |
| December 22, 2023 | 14.7M | 84.3M | 485M |
| December 23, 2023 | 14.7M | 84.3M | 485M |
| December 24, 2023 | 14.7M | 84.3M | 485M |
| December 25, 2023 | 14.7M | 84.3M | 485M |
| December 26, 2023 | 14.7M | 84.3M | 486M |
| December 27, 2023 | 14.7M | 84.3M | 486M |
| December 28, 2023 | 14.7M | 84.3M | 486M |
| December 29, 2023 | 14.7M | 84.3M | 488M |
| December 30, 2023 | 14.7M | 84.3M | 489M |
| December 31, 2023 | 14.7M | 84.3M | 490M |
| January 1, 2024 | 14.7M | 84.3M | 491M |
| January 2, 2024 | 14.7M | 84.3M | 491M |
| January 3, 2024 | 14.7M | 84.3M | 491M |
| January 4, 2024 | 14.7M | 84.3M | 492M |
| January 5, 2024 | 14.7M | 84.3M | 492M |
| January 6, 2024 | 14.7M | 84.3M | 492M |
| January 7, 2024 | 14.7M | 84.3M | 492M |
| January 8, 2024 | 14.7M | 84.3M | 493M |
| January 9, 2024 | 14.7M | 84.3M | 493M |
| January 10, 2024 | 14.7M | 84.3M | 493M |
| January 11, 2024 | 14.7M | 84.7M | 496M |
| January 12, 2024 | 14.7M | 84.7M | 496M |
| January 13, 2024 | 14.7M | 84.7M | 497M |
| January 14, 2024 | 14.7M | 84.7M | 497M |
| January 15, 2024 | 14.7M | 84.7M | 497M |

Same in every row: Arbitrum One 1.27B.

### How this was built
- Scope: circulating supply (number of tokens available to trade, excluding locked, unvested, or treasury-held tokens) read at project grain.
- Window: every calendar day from 2023-12-01 through 2024-01-15; the first and last day are returned day cells.
- Entities: Aave, Injective, Filecoin, Arbitrum One — each returned one value for each of the 46 days in the window, so there are no gap days to fill for them.
- Ondo Finance: Not reached — no query returned a circulating-supply row for Ondo Finance in this window, so it has no column in the table.
- Values are per-day point-in-time token counts and are not summed across days.
