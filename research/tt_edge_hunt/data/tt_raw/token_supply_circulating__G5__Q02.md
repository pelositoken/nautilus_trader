Circulating supply per project, 2022-09-01 to 2022-11-30 (one row per calendar day):

| Date | PancakeSwap | Raydium |
|:---|---:|---:|
| September 1, 2022 | 141M | 132M |
| September 2, 2022 | 142M | 132M |
| September 3, 2022 | 141M | 133M |
| September 4, 2022 | 141M | 133M |
| September 5, 2022 | 139M | 133M |
| September 6, 2022 | 139M | 133M |
| September 7, 2022 | 139M | 133M |
| September 8, 2022 | 142M | 133M |
| September 9, 2022 | 142M | 134M |
| September 10, 2022 | 142M | 134M |
| September 11, 2022 | 142M | 134M |
| September 12, 2022 | 140M | 134M |
| September 13, 2022 | 140M | 134M |
| September 14, 2022 | 140M | 135M |
| September 15, 2022 | 143M | 135M |
| September 16, 2022 | 143M | 135M |
| September 17, 2022 | 142M | 135M |
| September 18, 2022 | 142M | 135M |
| September 19, 2022 | 140M | 135M |
| September 20, 2022 | 140M | 136M |
| September 21, 2022 | 139M | 136M |
| September 22, 2022 | 143M | 136M |
| September 23, 2022 | 143M | 136M |
| September 24, 2022 | 143M | 136M |
| September 25, 2022 | 143M | 136M |
| September 26, 2022 | 140M | 137M |
| September 27, 2022 | 140M | 137M |
| September 28, 2022 | 139M | 137M |
| September 29, 2022 | 142M | 137M |
| September 30, 2022 | 143M | 137M |
| October 1, 2022 | 143M | 137M |
| October 2, 2022 | 143M | 137M |
| October 3, 2022 | 140M | 138M |
| October 4, 2022 | 140M | 138M |
| October 5, 2022 | 139M | 138M |
| October 6, 2022 | 143M | 139M |
| October 7, 2022 | 143M | 139M |
| October 8, 2022 | 145M | 139M |
| October 9, 2022 | 145M | 139M |
| October 10, 2022 | 141M | 139M |
| October 11, 2022 | 140M | 139M |
| October 12, 2022 | 143M | 140M |
| October 13, 2022 | 143M | 140M |
| October 14, 2022 | 143M | 140M |
| October 15, 2022 | 143M | 140M |
| October 16, 2022 | 143M | 140M |
| October 17, 2022 | 143M | 140M |
| October 18, 2022 | 142M | 141M |
| October 19, 2022 | 142M | 141M |
| October 20, 2022 | 147M | 142M |
| October 21, 2022 | 147M | 142M |
| October 22, 2022 | 146M | 142M |
| October 23, 2022 | 146M | 142M |
| October 24, 2022 | 144M | 142M |
| October 25, 2022 | 144M | 143M |
| October 26, 2022 | 144M | 143M |
| October 27, 2022 | 148M | 143M |
| October 28, 2022 | 148M | 144M |
| October 29, 2022 | 150M | 144M |
| October 30, 2022 | 148M | 144M |
| October 31, 2022 | 144M | 144M |
| November 1, 2022 | 146M | 144M |
| November 2, 2022 | 146M | 144M |
| November 3, 2022 | 146M | 144M |
| November 4, 2022 | 145M | 144M |
| November 5, 2022 | 145M | 145M |
| November 6, 2022 | 145M | 145M |
| November 7, 2022 | 145M | 145M |
| November 8, 2022 | 144M | 145M |
| November 9, 2022 | 144M | 145M |
| November 10, 2022 | 147M | 145M |
| November 11, 2022 | 147M | 146M |
| November 12, 2022 | 147M | 146M |
| November 13, 2022 | 147M | 146M |
| November 14, 2022 | 145M | 146M |
| November 15, 2022 | 146M | 155M |
| November 16, 2022 | 148M | 155M |
| November 17, 2022 | 147M | 155M |
| November 18, 2022 | 147M | 156M |
| November 19, 2022 | 147M | 156M |
| November 20, 2022 | 147M | 156M |
| November 21, 2022 | 146M | 156M |
| November 22, 2022 | 146M | 156M |
| November 23, 2022 | 146M | 156M |
| November 24, 2022 | 146M | 157M |
| November 25, 2022 | 150M | 157M |
| November 26, 2022 | 150M | 157M |
| November 27, 2022 | 150M | 157M |
| November 28, 2022 | 157M | 158M |
| November 29, 2022 | 157M | 158M |
| November 30, 2022 | 157M | 158M |

Same in every row: Polygon —; OP Mainnet 215M; Ether.fi —.

Two of the five requested projects returned no circulating-supply observation in this window, so their column is empty on every day:

- **Polygon** — no value in the window. A scoped read of this metric for Polygon returns its first observation on 2023-10-26.
- **Ether.fi** — no value in the window. A scoped read of this metric for Ether.fi returns its first observation on 2024-03-18.
- **OP Mainnet** — a value is returned on every day, but it is the same figure (214,748,364, i.e. 2^31) on all 91 days, a degenerate magnitude rather than a plausible daily circulating supply; treat the OP Mainnet column with caution.

### How this was built
- Metric: circulating supply (a point-in-time token count), read for each project at the project grain, one row per calendar day, no aggregation across days.
- Window: 2022-09-01 to 2022-11-30, all 91 calendar days; every day is present in the table (a day the query returned no value for a project shows "-").
- Projects: Polygon, PancakeSwap, OP Mainnet, Raydium and Ether.fi, resolved to their canonical project entries.
- Coverage: PancakeSwap and Raydium returned daily values across the window; Polygon and Ether.fi returned no observation in the window (their series begin later, 2023-10-26 and 2024-03-18 respectively).
- The OP Mainnet column is constant at 214,748,364 on every returned day.
- Polygon and Ether.fi are not inferred to be zero — no observation was returned for them here.
