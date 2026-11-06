# Summary format

`save_summary` takes one line per tagged subscription and a total.

- `merchant`: the same clean name you tagged it with.
- `monthly_saving`: what cancelling saves each month, which is its latest charge. Write it as a string with two decimals.
- `note`: one short sentence with what the reader should know, such as a price rise. Say "Price unchanged." if there is nothing to add.
- `total_monthly_saving`: the sum of the lines, as a string with two decimals.

```json
{
  "lines": [
    { "merchant": "Example Stream", "monthly_saving": "59.00", "note": "Rose from 49.00 in September." },
    { "merchant": "Example Music", "monthly_saving": "39.00", "note": "Price unchanged." }
  ],
  "total_monthly_saving": "98.00"
}
```
