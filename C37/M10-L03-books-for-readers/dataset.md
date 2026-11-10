# Dataset card: Goodbooks-10k

Used by: the case study *Books for readers* in the recommendations course, `C37/M10-L03-books-for-readers/books-for-readers.ipynb` (and the solution notebook)

| Field | Value |
|---|---|
| Source | <https://github.com/zygmuntz/goodbooks-10k> (files from release v1.0: <https://github.com/zygmuntz/goodbooks-10k/releases/tag/v1.0>) |
| Publisher / creator | Zygmunt Zając (GitHub `zygmuntz`), from public Goodreads data |
| Licence | [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/). The repository's `LICENSE` says: "This work is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License." |
| Attribution text | "goodbooks-10k" by Zygmunt Zając, <https://github.com/zygmuntz/goodbooks-10k>, licensed under CC BY-SA 4.0. |
| Version or access date | Release v1.0; the CSV files inside are identical to the repository's files at commit `6dd165b555a7b47b2dd36743a425776e641ff50c` (checked again on 2026-11-08) |
| File used | `ratings.zip`, `books.zip`, `book_tags.zip`, `tags.zip`, **not kept in labs** (ShareAlike: the course does not copy the data). The notebook downloads them from the GitHub release into its own folder and checks each checksum. |
| SHA-256 | ratings.zip `2dd0ea8e800860279d7305e88a481ff12090fe5bb54b1321a3854a3b651ebd2e` · books.zip `1e5e29f4037f2c4ccd99cb5f10d07316ec0e3c0fcefbcdf9698585c418f7bd4f` · book_tags.zip `13e9e76e2348676ed61301d1b2cd573c3554cb494cc572c21e99096e1703222f` · tags.zip `02302ad53982627b00d1fff79e48e58dd920f465eb89fb4895eb5ec358bda14f` |
| Size | ratings: 5,976,479 rows × 3 columns; books: 10,000 rows × 23 columns; book_tags: 999,912 rows × 3; tags: 34,252 rows × 2. 29 MB as zips (93 MB unzipped). |

## What one row means

In `ratings.csv`, one row is one reader's rating of one book, from 1 to 5 stars. There is no date. The README says the file "contains ratings sorted by time", and the whole file is in one order (readers are mixed together), so the case study uses the **position in the file** as its clock. There is no target column: the case study predicts, for each reader who rates books in a later part of the file, which books they rate there.

## Columns used

| File | Column | Meaning |
|---|---|---|
| ratings | `user_id` | The reader, a number from 1 to 53,424. |
| ratings | `book_id` | The book, a number from 1 to 10,000 (all editions of a book together). |
| ratings | `rating` | 1 to 5 stars. |
| books | `book_id`, `title`, `authors`, `original_publication_year`, `goodreads_book_id` | The book's title (with the series in brackets, such as `(Harry Potter, #1)`), its authors (the first one is used), its year, and the key to the tags. |
| book_tags | `goodreads_book_id`, `tag_id`, `count` | How many Goodreads users put the book on a shelf with this tag. |
| tags | `tag_id`, `tag_name` | The tag's name, such as `fantasy` or `to-read`. |

## Why this dataset

Real readers, real books and real text (titles, authors, tags), enough ratings for collaborative methods, and a licence that allows use with attribution. The alternatives: the UCSD Book Graph (academic use only, no redistribution: not allowed), Open Library's ratings and reading-log dumps (no reader identifier, so no personal history), and MovieLens (its own terms: not allowed by the course). Research notes: `nextia-learning/reference/c37/m10/cs3/DATASET-RESEARCH.md`.

## Changes we made

- None to the files. The notebook reads them from the zips.
- The notebook keeps **one reader in four** (reader numbers divisible by 4) so that it runs in a few minutes; each rating keeps its position in the whole file.
- For the content method, the notebook keeps the 8 most used tags of each book that describe the book, and drops shelves such as `to-read`, `owned` and `favorites`.

## Traps (the case study deals with each)

- **No dates.** Only the order of the file. A position is not a day, so "the last 5% of the file" is not a fixed number of weeks.
- **Popularity is extreme.** The 100 most read books get about 17% of all ratings. Harry Potter, The Hunger Games and Twilight are near everything.
- **Series.** Many books are part of a series. A suggestion of book 2 to a reader of book 1 is often right, but the reader would find it alone.
- **New releases.** Books from 2015 and 2016 appear only near the end of the file. A method that learns from the past knows little about them.

## Limitations and cautions

- The 10,000 books are the most rated books on Goodreads, and every reader has between 19 and 200 ratings. This is not a random sample of readers or of books: results say little about a real library or bookshop.
- A rating is not a reading event: readers often rate books they read years ago when they join.
- Reader IDs are numbers only. Do not try to identify readers or join the data with Goodreads profiles.
- ShareAlike: if you share the data or a changed version of it, use the same licence and the attribution above.
