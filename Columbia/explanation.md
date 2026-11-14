# Looks Good to Me! — Bogotá Sound Check

**Recovered flag: `SIGMOID_DATA_SANITIZATION`**

Run the complete recovery offline, using only Python's standard library:

```bash
python3 Columbia/solve.py
```

## Identifying the altered records

I first compared the characters in the suspect reviews with those in the 1,000
trusted reviews. The trusted texts use ASCII plus curly apostrophes (`’`) and
en dashes (`–`). Twelve suspects contain additional characters: six have an
invisible U+200B ZERO WIDTH SPACE, and six have Cyrillic letters that resemble
Latin `a`, `c`, `e`, or `o`.

These text changes occur at sample indices:

```text
36,119,216,273,357,367,462,478,513,685,752,1199
```

That list alone does **not** open a seal. There are also subtle rating changes
between 3 and 4 stars. Sentiment predictions cannot establish those original
ratings with certainty, so I used the public source corpus for exact verification:
[Amazon Musical Instruments 5-core reviews, Stanford SNAP](https://snap.stanford.edu/data/amazon/productGraph/categoryFiles/reviews_Musical_Instruments_5.json.gz).
A copy is included under `source_data/` so the recovery works offline. This is an
additional source, not a second file provided by the challenge.

To check that this is the right source, the solver locates and verifies **all
1,000 supplied trusted reviews**, including their summaries, full texts, and
ratings. Straight/curly apostrophes and hyphen/en-dash variants are treated as
equivalent because those differences already occur in the trusted records.

It then matches every suspect to its source review. A permissive lookup repairs
the observed invisible characters and homoglyphs to locate candidates; a strict
comparison against the original text identifies the actual changes. Ambiguous
matches fail explicitly. Ratings are compared as integers, without a classifier.
All 1,200 suspect reviews have source matches. The additional rating changes are:

| sample_index | Supplied rating | Original rating |
| ---: | ---: | ---: |
| 112 | 3 | 4 |
| 198 | 3 | 4 |
| 347 | 4 | 3 |
| 371 | 3 | 4 |
| 432 | 3 | 4 |
| 582 | 4 | 3 |
| 622 | 4 | 3 |
| 633 | 3 | 4 |
| 661 | 4 | 3 |
| 1018 | 4 | 3 |
| 1061 | 3 | 4 |
| 1112 | 4 | 3 |

The union contains **24 altered reviews**. `altered_reviews.csv` records each
change, its summary, relevant Unicode names, and source product/reviewer IDs.
Neither the challenge JSON nor the source corpus was modified.

## Opening the seals

Following `archive_note`, sort the altered `sample_index` values numerically and
join them with commas, without spaces:

```text
36,112,119,198,216,273,347,357,367,371,432,462,478,513,582,622,633,661,685,752,1018,1061,1112,1199
```

SHA-256 of that exact UTF-8 string gives the 32-byte mask:

```text
987ebbc5d29b5729853b35c5823ec932b2346afd6ee82b7296c3cc10cf900f00
```

Decode each hexadecimal `archive_tag`, XOR its 32 bytes with the mask, and remove
trailing zero bytes. Search both `samples` **and** `trusted_reference`, as the
archive note explicitly instructs.

The seal at **`trusted_reference[613]`** (zero-based position; the 614th trusted
review) decodes to:

```text
SIGMOID_DATA_SANITIZATION
```

The script does not hardcode the altered indices, corrected ratings, mask, seal
position, or flag. It derives them from the reviews and source corpus, and writes
`recovery.json`, `altered_reviews.csv`, and `altered_indices.txt`. The recovery
report includes SHA-256 hashes of both input files and the winning seal's hex
value for independent verification.

## Submission materials

Publish this explanation together with `solve.py`, `reviews.json`, the saved
`source_data/` corpus, and the generated evidence files. Submit the flag string
and the public URL of this explanation on the platform.
