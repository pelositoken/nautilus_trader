Circulating supply is available daily for PancakeSwap, OP Mainnet and Raydium across the whole window; no rows were returned for Polygon or Ether.fi in this period.

| Date | PancakeSwap | Raydium |
|:---|---:|---:|
| December 1, 2022 | 161M | 158M |
| December 2, 2022 | 162M | 159M |
| December 3, 2022 | 162M | 159M |
| December 4, 2022 | 162M | 160M |
| December 5, 2022 | 158M | 160M |
| December 6, 2022 | 157M | 160M |
| December 7, 2022 | 157M | 161M |
| December 8, 2022 | 161M | 161M |
| December 9, 2022 | 161M | 162M |
| December 10, 2022 | 161M | 162M |
| December 11, 2022 | 161M | 162M |
| December 12, 2022 | 158M | 162M |
| December 13, 2022 | 158M | 162M |
| December 14, 2022 | 158M | 162M |
| December 15, 2022 | 163M | 167M |
| December 16, 2022 | 163M | 167M |
| December 17, 2022 | 162M | 167M |
| December 18, 2022 | 162M | 167M |
| December 19, 2022 | 159M | 167M |
| December 20, 2022 | 159M | 167M |
| December 21, 2022 | 159M | 168M |
| December 22, 2022 | 159M | 168M |
| December 23, 2022 | 164M | 168M |
| December 24, 2022 | 164M | 168M |
| December 25, 2022 | 164M | 168M |
| December 26, 2022 | 168M | 169M |
| December 27, 2022 | 161M | 169M |
| December 28, 2022 | 161M | 169M |
| December 29, 2022 | 161M | 170M |
| December 30, 2022 | 166M | 170M |
| December 31, 2022 | 166M | 170M |
| January 1, 2023 | 165M | 170M |
| January 2, 2023 | 161M | 170M |
| January 3, 2023 | 163M | 170M |
| January 4, 2023 | 163M | 171M |
| January 5, 2023 | 163M | 171M |
| January 6, 2023 | 163M | 171M |
| January 7, 2023 | 162M | 171M |
| January 8, 2023 | 162M | 171M |
| January 9, 2023 | 163M | 171M |
| January 10, 2023 | 163M | 172M |
| January 11, 2023 | 162M | 172M |
| January 12, 2023 | 162M | 172M |
| January 13, 2023 | 168M | 172M |
| January 14, 2023 | 168M | 172M |
| January 15, 2023 | 168M | 172M |
| January 16, 2023 | 164M | 173M |
| January 17, 2023 | 164M | 173M |
| January 18, 2023 | 164M | 173M |
| January 19, 2023 | 163M | 173M |
| January 20, 2023 | 169M | 173M |
| January 21, 2023 | 169M | 173M |
| January 22, 2023 | 169M | 174M |
| January 23, 2023 | 165M | 174M |
| January 24, 2023 | 165M | 174M |
| January 25, 2023 | 165M | 174M |
| January 26, 2023 | 165M | 174M |
| January 27, 2023 | 171M | 174M |
| January 28, 2023 | 171M | 175M |
| January 29, 2023 | 171M | 175M |
| January 30, 2023 | 165M | 175M |
| January 31, 2023 | 165M | 175M |
| February 1, 2023 | 165M | 176M |
| February 2, 2023 | 165M | 176M |
| February 3, 2023 | 170M | 176M |
| February 4, 2023 | 170M | 176M |
| February 5, 2023 | 169M | 176M |
| February 6, 2023 | 166M | 176M |
| February 7, 2023 | 165M | 177M |
| February 8, 2023 | 165M | 177M |
| February 9, 2023 | 165M | 177M |
| February 10, 2023 | 170M | 177M |
| February 11, 2023 | 170M | 177M |
| February 12, 2023 | 170M | 177M |
| February 13, 2023 | 166M | 178M |
| February 14, 2023 | 167M | 178M |
| February 15, 2023 | 166M | 178M |
| February 16, 2023 | 166M | 178M |
| February 17, 2023 | 192M | 178M |
| February 18, 2023 | 192M | 178M |
| February 19, 2023 | 194M | 178M |
| February 20, 2023 | 187M | 179M |
| February 21, 2023 | 187M | 179M |
| February 22, 2023 | 191M | 179M |
| February 23, 2023 | 191M | 179M |
| February 24, 2023 | 191M | 179M |
| February 25, 2023 | 191M | 179M |
| February 26, 2023 | 191M | 180M |
| February 27, 2023 | 189M | 180M |
| February 28, 2023 | 189M | 180M |

Same in every row: OP Mainnet 215M.

### How this was built
- Cohort: the five named projects — Polygon, PancakeSwap, OP Mainnet, Raydium and Ether.fi.
- Window: 2022-12-01 to 2023-02-28, one row per calendar day, no aggregation, each day's value being that day's circulating supply reading.
- Metric: circulating supply (tokens currently available for trading, excluding locked, unvested or treasury-held tokens), read at project grain.
- PancakeSwap, OP Mainnet and Raydium each have a value on all 90 days of the window.
- Not reached: Polygon and Ether.fi — no query returned a circulating-supply row for either in this window (0 of 90 days observed).
