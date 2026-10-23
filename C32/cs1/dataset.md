# Dataset card: public benchmark results and a public price file

Used by: the case study *A capability catalog from public evaluation results*, project `public-catalog` (`starter.zip`, `finished.zip`), folder `data/`.

The project joins two public sources. Each has its own row below.

## 1. Epoch AI, Capabilities & benchmarking

| Field | Value |
|---|---|
| Source | <https://epoch.ai/benchmarks>, download <https://epoch.ai/data/benchmark_data.zip> |
| Publisher / creator | Epoch AI |
| Licence | [Creative Commons Attribution 4.0 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/), as the `README.md` in the download says |
| Attribution text | Epoch AI, 'Capabilities & benchmarking'. Published online at epoch.ai. Retrieved from 'https://epoch.ai/benchmarks' [online resource]. |
| Version or access date | Downloaded on 2026-10-22 (the archive's files are dated 2026-10-23 01:28 UTC; Epoch AI updates it every day). SHA-256 of the whole archive: `6b1735af541a49b2daa7a3d2f32f5ac433f67725ab973a58c9ad344cc8706ced` |
| File used | `gpqa_diamond.csv`, `otis_mock_aime_2024_2025.csv`, `simpleqa_verified.csv` and Epoch AI's `README.md`, kept unchanged in `data/epoch/`: yes (CC BY 4.0 allows sharing with credit) |
| SHA-256 | `gpqa_diamond.csv` `9ef0b938bdd8406b029d595983ee8ad3a80bd9d64b82605b91b5ce39ba650c39` · `otis_mock_aime_2024_2025.csv` `b7c9da8c0587c82f1e0d814ceb496c24308380b997a16203b6e5d39eb07f4f50` · `simpleqa_verified.csv` `e2d3fae377f0ddd3d079bcc3971b9b9388a0a950289effe7b521177ea2e988cc` · `README.md` `43f5df3edacb9701b66626b13e78a52e2f823f0fa68db997e7fac40bacfa3e71` |
| Size | GPQA Diamond 325 results of 225 models; OTIS Mock AIME 2024-2025 305 results of 204 models; SimpleQA Verified 92 results of 83 models; 13 columns each; 0.34 MB in all |

### What one row means

One row is one model version on one benchmark, as Epoch AI ran it: `Model version` (the model and, after `_`, the reasoning setting, for example `gpt-5.6-luna_low`), `mean_score` (the share of questions answered correctly, 0 to 1), `stderr` (its standard error), the release date and the organisation. There is no target: the project uses the score as evidence about a model at one setting.

## 2. LiteLLM's model price file

| Field | Value |
|---|---|
| Source | <https://github.com/BerriAI/litellm/blob/159b5b2f7243bba757c08e4ddc45a2514e4cd037/model_prices_and_context_window.json> |
| Publisher / creator | Berri AI and the LiteLLM contributors |
| Licence | [MIT](https://github.com/BerriAI/litellm/blob/159b5b2f7243bba757c08e4ddc45a2514e4cd037/LICENSE) (the file is outside the repository's `enterprise/` folder); the licence is kept as `data/litellm/LICENSE` |
| Attribution text | Model prices and context windows from LiteLLM (github.com/BerriAI/litellm), MIT licence, commit 159b5b2. |
| Version or access date | Commit `159b5b2f7243bba757c08e4ddc45a2514e4cd037`, the last change of the file on 2026-10-21 (04:52 UTC); downloaded on 2026-10-22 |
| File used | `model_prices_and_context_window.json`, kept unchanged in `data/litellm/`: yes (MIT allows it) |
| SHA-256 | `91da1a98e194e0d7c436aaf970800c8e734d70cc78027cfe314d5b27dfaf9a4c` |
| Size | 2.97 MB; one entry per model and provider (2,873 chat entries with a price); the project uses 102 offers of 61 models at four providers |

### What one row means

One entry is one model at one provider (for example `azure/gpt-5.6-luna`): the list price per input and output token, the features that LiteLLM records (`supports_function_calling`, `supports_response_schema`, `supports_vision`), and sometimes a `deprecation_date`, the day the provider retires the model.

## Why these sources

The case study needs openly licensed scores of many current models, at named settings, and prices with retirement dates from one place. Candidates compared (details in the course repository's research note):

- **Epoch AI** (chosen for the scores): CC BY 4.0, current models, the reasoning setting in every row, standard errors. It changes every day, so a frozen copy is kept.
- **The Open LLM Leaderboard** (Hugging Face): open-weight models only, and it stopped updating; no hosted models, so no prices and no retirements.
- **Provider price pages** (for prices): the original source, but each page has its own terms and layout and no open licence; the case study links to them instead.
- **LiteLLM's price file** (chosen for the prices): MIT, one file with prices, features and deprecation dates for many providers, versioned by commit.

## Changes we made

None to the files. The project reads only the three benchmark files above of the 87 benchmark files in Epoch AI's archive, and only the entries of four providers from the price file (OpenAI, Azure OpenAI, Google Cloud Vertex AI and Anthropic, an assumption of the case study). Entries for a region or data zone (for example `azure/eu/...`) are left out.

## Limitations and cautions

- **Public benchmarks are proxies.** GPQA Diamond (graduate-level science questions), OTIS Mock AIME (competition mathematics) and SimpleQA Verified (short factual questions without search) are not anyone's real tasks. They make a shortlist; an organisation's own evaluation decides.
- **A score belongs to one setting.** The same model scores very differently at `none` and at `max`. A higher setting also uses more output tokens, and neither file has token counts per task.
- **Not every model is tested on every benchmark or setting.** A missing score is no evidence, not a zero.
- **Prices, features and dates are a third party's records.** LiteLLM collects them from providers' pages; they can be late or wrong. Check the provider's own pages before a decision. A missing `deprecation_date` does not mean that a model will never retire.
- **Benchmarks can leak into training data.** A high public score can partly reflect questions that a model saw while it was trained.
- The model and provider names are real; the company, its apps, its contracts and its workloads in the case study are made up.
