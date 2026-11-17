Token Terminal doesn't track fees for Ondo Finance, so it is left out; the table below shows daily fees for the four named projects that do have data — Aave, Injective, Filecoin and Arbitrum One.

| Date | Aave | Injective | Filecoin | Arbitrum One |
|:---|---:|---:|---:|---:|
| June 1, 2025 | $1.80M | $4.07K | $1.26K | $29.1K |
| June 2, 2025 | $1.50M | $4.85K | $1.36K | $43.2K |
| June 3, 2025 | $1.52M | $5.19K | $1.37K | $39.9K |
| June 4, 2025 | $1.53M | $4.80K | $1.24K | $36.7K |
| June 5, 2025 | $2.49M | $5.07K | $4.34K | $110K |
| June 6, 2025 | $1.52M | $4.70K | $3.98K | $43.3K |
| June 7, 2025 | $1.55M | $4.31K | $2.55K | $23.2K |
| June 8, 2025 | $1.93M | $4.35K | $1.64K | $21.0K |
| June 9, 2025 | $1.78M | $5.16K | $3.36K | $43.1K |
| June 10, 2025 | $1.63M | $6.22K | $3.63K | $90.2K |
| June 11, 2025 | $1.65M | $5.94K | $2.68K | $64.5K |
| June 12, 2025 | $2.11M | $5.62K | $1.32K | $52.6K |
| June 13, 2025 | $1.76M | $6.16K | $1.40K | $130K |
| June 14, 2025 | $1.55M | $4.15K | $1.19K | $25.6K |
| June 15, 2025 | $1.94M | $4.20K | $1.91K | $24.5K |
| June 16, 2025 | $1.58M | $5.28K | $4.18K | $51.9K |
| June 17, 2025 | $1.52M | $5.09K | $7.33K | $68.2K |
| June 18, 2025 | $1.46M | $5.66K | $7.85K | $43.6K |
| June 19, 2025 | $1.90M | $4.01K | $11.7K | $28.4K |
| June 20, 2025 | $1.51M | $4.92K | $7.32K | $67.8K |
| June 21, 2025 | $1.72M | $3.65K | $6.06K | $86.1K |
| June 22, 2025 | $1.74M | $5.06K | $5.99K | $139K |
| June 23, 2025 | $1.63M | $5.72K | $24.8K | $115K |
| June 24, 2025 | $1.50M | $6.08K | $62.6K | $62.1K |
| June 25, 2025 | $1.45M | $5.91K | $10.1K | $54.0K |
| June 26, 2025 | $2.24M | $5.86K | $5.97K | $54.4K |
| June 27, 2025 | $1.40M | $5.26K | $5.91K | $31.7K |
| June 28, 2025 | $1.41M | $3.58K | $6.50K | $13.6K |
| June 29, 2025 | $1.79M | $3.95K | $9.94K | $30.3K |
| June 30, 2025 | $1.42M | $5.11K | $188K | $43.7K |
| July 1, 2025 | $1.41M | $5.57K | $13.6K | $31.6K |
| July 2, 2025 | $1.47M | $5.14K | $6.96K | $75.5K |
| July 3, 2025 | $4.99M | $6.00K | $8.99K | $46.6K |
| July 4, 2025 | $1.63M | $4.26K | $1.87K | $30.7K |
| July 5, 2025 | $1.57M | $3.31K | $2.77K | $16.3K |
| July 6, 2025 | $1.97M | $3.70K | $2.33K | $26.7K |
| July 7, 2025 | $1.63M | $4.85K | $3.68K | $33.7K |
| July 8, 2025 | $1.72M | $5.30K | $4.06K | $31.0K |
| July 9, 2025 | $1.71M | $5.02K | $162K | $83.1K |
| July 10, 2025 | $2.38M | $5.52K | $23.5K | $118K |
| July 11, 2025 | $1.89M | $6.73K | $3.43K | $70.0K |
| July 12, 2025 | $1.88M | $5.24K | $3.01K | $27.8K |
| July 13, 2025 | $1.88M | $5.21K | $2.80K | $28.9K |
| July 14, 2025 | $2.15M | $6.92K | $2.69K | $56.7K |
| July 15, 2025 | $2.40M | $8.07K | $4.18K | $89.1K |

### How this was built
- The cohort is the projects Token Terminal tracks among those named: Aave, Injective, Filecoin and Arbitrum One, each read at its own project grain (Arbitrum One through its own chain-project row).
- The metric is fees — the gross value users pay to use the protocol or chain — read as each day's own observation, with no aggregation across days.
- The window is 2025-06-01 to 2025-07-15, one row per calendar day; each of the four projects has an observation on every day, so no day is blank.
- Not reached: Ondo Finance — no query returned fees for it.

_Token Terminal doesn't track Ondo Finance's fees._
