## Daily circulating supply, June 1 – July 16, 2022

| Date | PancakeSwap | Raydium |
|:---|---:|---:|
| June 1, 2022 | 166M | 111M |
| June 2, 2022 | 165M | 111M |
| June 3, 2022 | 165M | 113M |
| June 4, 2022 | 165M | 112M |
| June 5, 2022 | 170M | 113M |
| June 6, 2022 | 163M | 112M |
| June 7, 2022 | 164M | 113M |
| June 8, 2022 | 164M | 113M |
| June 9, 2022 | 150M | 113M |
| June 10, 2022 | 150M | 113M |
| June 11, 2022 | 150M | 115M |
| June 12, 2022 | 150M | 115M |
| June 13, 2022 | 149M | 115M |
| June 14, 2022 | 151M | 115M |
| June 15, 2022 | 151M | 114M |
| June 16, 2022 | 150M | 115M |
| June 17, 2022 | 150M | 115M |
| June 18, 2022 | 150M | 116M |
| June 19, 2022 | 149M | 115M |
| June 20, 2022 | 149M | 114M |
| June 21, 2022 | 149M | 115M |
| June 22, 2022 | 149M | 115M |
| June 23, 2022 | 152M | 116M |
| June 24, 2022 | 152M | 116M |
| June 25, 2022 | 151M | 116M |
| June 26, 2022 | 151M | 116M |
| June 27, 2022 | 149M | 116M |
| June 28, 2022 | 150M | 116M |
| June 29, 2022 | 150M | 117M |
| June 30, 2022 | 144M | 117M |
| July 1, 2022 | 144M | 118M |
| July 2, 2022 | 143M | 118M |
| July 3, 2022 | 143M | 118M |
| July 4, 2022 | 142M | 118M |
| July 5, 2022 | 142M | 118M |
| July 6, 2022 | 145M | 118M |
| July 7, 2022 | 145M | 118M |
| July 8, 2022 | 144M | 119M |
| July 9, 2022 | 144M | 119M |
| July 10, 2022 | 144M | 119M |
| July 11, 2022 | 143M | 122M |
| July 12, 2022 | 143M | 122M |
| July 13, 2022 | 146M | 120M |
| July 14, 2022 | 146M | 122M |
| July 15, 2022 | 145M | 122M |
| July 16, 2022 | 145M | 121M |

Same in every row: Ether.fi —; OP Mainnet 215M; Polygon —.

### How this was built
- Cohort: the five named projects, resolved in the project registry to Polygon, PancakeSwap, OP Mainnet (registered as OP Mainnet), Raydium, and Ether.fi.
- Metric: circulating supply, the point-in-time count of tokens available for trading on the open market (locked, unvested and treasury-held tokens excluded); one value per project per calendar day, no aggregation.
- Window: 2022-06-01 to 2022-07-16, both ends included.
- Every requested calendar day is present as a row; a cell with no observation is left empty (a dash) rather than zero.
- PancakeSwap and OP Mainnet returned a value on every day of the window. Their circulating supplies are returned at their stored precision.
- Polygon and Ether.fi returned no value for this window; their circulating-supply series in the data begin later (Polygon's first observation is 2023-10-26, Ether.fi's is 2024-03-18).
- Raydium's values across the window are returned in the table; its circulating-supply series begins 2021-02-22.
- OP Mainnet's returned value is identical on every day of the window (214,748,364).
