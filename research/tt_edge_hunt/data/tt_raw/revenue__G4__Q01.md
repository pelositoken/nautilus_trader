Render Network's revenue is not tracked by Token Terminal, so it is left out of the table below.

| Date | Curve |
|:---|---:|
| June 1, 2022 | $85.1K |
| June 2, 2022 | $43.7K |
| June 3, 2022 | $43.3K |
| June 4, 2022 | $44.6K |
| June 5, 2022 | $43.9K |
| June 6, 2022 | $138K |
| June 7, 2022 | $62.8K |
| June 8, 2022 | $103K |
| June 9, 2022 | $102K |
| June 10, 2022 | $52.0K |
| June 11, 2022 | $165K |
| June 12, 2022 | $106K |
| June 13, 2022 | $150K |
| June 14, 2022 | $344K |
| June 15, 2022 | $241K |
| June 16, 2022 | $202K |
| June 17, 2022 | $878K |
| June 18, 2022 | $108K |
| June 19, 2022 | $227K |
| June 20, 2022 | $93.2K |
| June 21, 2022 | $146K |
| June 22, 2022 | $72.5K |
| June 23, 2022 | $62.3K |
| June 24, 2022 | $56.2K |
| June 25, 2022 | $67.8K |
| June 26, 2022 | $38.1K |
| June 27, 2022 | $44.2K |
| June 28, 2022 | $42.5K |
| June 29, 2022 | $101K |
| June 30, 2022 | $71.2K |
| July 1, 2022 | $55.2K |
| July 2, 2022 | $66.1K |
| July 3, 2022 | $43.3K |
| July 4, 2022 | $27.0K |
| July 5, 2022 | $60.0K |
| July 6, 2022 | $85.7K |
| July 7, 2022 | $68.2K |
| July 8, 2022 | $46.8K |
| July 9, 2022 | $49.2K |
| July 10, 2022 | $24.5K |
| July 11, 2022 | $27.5K |
| July 12, 2022 | $27.8K |
| July 13, 2022 | $82.8K |
| July 14, 2022 | $50.9K |
| July 15, 2022 | $52.5K |
| July 16, 2022 | $65.0K |
| July 17, 2022 | $58.0K |
| July 18, 2022 | $55.5K |
| July 19, 2022 | $84.8K |
| July 20, 2022 | $120K |
| July 21, 2022 | $79.5K |
| July 22, 2022 | $55.8K |
| July 23, 2022 | $57.7K |
| July 24, 2022 | $38.9K |
| July 25, 2022 | $37.3K |
| July 26, 2022 | $58.2K |
| July 27, 2022 | $93.9K |
| July 28, 2022 | $76.5K |
| July 29, 2022 | $96.9K |
| July 30, 2022 | $58.3K |
| July 31, 2022 | $47.6K |
| August 1, 2022 | $33.8K |
| August 2, 2022 | $47.2K |
| August 3, 2022 | $94.6K |
| August 4, 2022 | $42.8K |
| August 5, 2022 | $35.0K |
| August 6, 2022 | $53.0K |
| August 7, 2022 | $25.9K |
| August 8, 2022 | $28.0K |
| August 9, 2022 | $35.3K |
| August 10, 2022 | $48.0K |
| August 11, 2022 | $58.6K |
| August 12, 2022 | $56.0K |
| August 13, 2022 | $43.1K |
| August 14, 2022 | $38.1K |
| August 15, 2022 | $28.9K |
| August 16, 2022 | $50.7K |
| August 17, 2022 | $47.0K |
| August 18, 2022 | $58.9K |
| August 19, 2022 | $31.1K |
| August 20, 2022 | $120K |
| August 21, 2022 | $59.0K |
| August 22, 2022 | $44.7K |
| August 23, 2022 | $56.9K |
| August 24, 2022 | $57.1K |
| August 25, 2022 | $60.3K |
| August 26, 2022 | $75.6K |
| August 27, 2022 | $69.1K |
| August 28, 2022 | $32.3K |
| August 29, 2022 | $37.7K |
| August 30, 2022 | $49.9K |
| August 31, 2022 | $42.9K |

Same in every row: Aptos —; Jupiter —; Celestia —.

### How this was built
- Window: 2022-06-01 through 2022-08-31, one row per calendar day (92 days), each day the sum of revenue recorded for that project on that day.
- Curve returned a revenue value on every day in the window.
- Aptos, Jupiter and Celestia returned no revenue value for any day in this window in the query that built this table; those cells are empty rather than zero.
- Render Network is not tracked for revenue and was not queried.
- The days shown are the days of the requested window; they are taken from Curve's own daily observations across the window.

_Token Terminal doesn't track Render Network's revenue._
