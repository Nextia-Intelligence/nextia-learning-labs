# Dataset card: Splink's simulated people (fake_1000) and GLEIF LEI records of Ireland

Used by: the case study *Find duplicate people and companies* of *Entity Resolution and Record Matching: Is This the Same Thing?*, `find-duplicate-people-and-companies.ipynb`

## Part 1: simulated people (`fake_1000.csv`)

| Field | Value |
|---|---|
| Source | https://github.com/moj-analytical-services/splink_datasets, file `data/fake_1000.csv` at commit `75876d806d9eff72072d21878150ee50a96d5f41` |
| Publisher / creator | MoJ Analytical Services (the Splink team, UK Ministry of Justice) |
| Licence | [MIT](https://github.com/moj-analytical-services/splink_datasets/blob/main/LICENSE) ("Copyright (c) 2023 MoJ Analytical Services") |
| Attribution text | `fake_1000` from moj-analytical-services/splink_datasets, MIT licence, Copyright (c) 2023 MoJ Analytical Services. |
| Version or access date | The commit above (the file was added on 25 July 2023 and has not changed since). |
| File used | `fake_1000.csv`, kept in `data/`: no (the notebook downloads it from the commit above and checks the checksum) |
| SHA-256 | `66f9b8f92b9b082ef982fe18c77030fbed8780f06ce1d40d7106be5a72392e2a` (55,983 bytes) |
| Size | 1,000 rows × 7 columns (unique_id, first_name, surname, dob, city, email, cluster) |

**What one row means.** One record of one simulated person. `cluster` is the true person (251 people, 1 to 7 records each, 2,031 true pairs). The case study predicts, for a pair of records, whether they are the same person. The records were made by a program from invented people, with typing errors, swapped names, changed dates and empty values. No real person is in this data. (The email domains are generated words; some of them may exist on the internet. Never send anything to them.)

## Part 2: GLEIF LEI records with a legal address in Ireland (`gleif-ie.csv.gz`)

| Field | Value |
|---|---|
| Source | GLEIF API, https://api.gleif.org/api/v1/lei-records?filter[entity.legalAddress.country]=IE (all pages, cursor pagination), plus the 5 surviving records of DUPLICATE records that are outside Ireland (`filter[lei]=…`), and the names of the legal-form codes from https://api.gleif.org/api/v1/entity-legal-forms/{code} |
| Publisher / creator | Global Legal Entity Identifier Foundation (GLEIF) and the LEI issuers (LOUs) |
| Licence | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). GLEIF's terms of use, section II (Access Service): "The data available through the Access Service are provided under the CC0 licence" (https://www.gleif.org/en/meta/lei-data-terms-of-use). |
| Attribution text | Not required by CC0. We write: "LEI data from GLEIF (www.gleif.org), CC0 1.0; a filtered extract by Nextia Learning." |
| Version or access date | A snapshot of the API: the records as the API returned them on 10 November 2026 (UTC). The register changes every day, so a new download gives other rows. |
| File used | `gleif-ie.csv.gz` and `elf-codes.csv`, kept in `data/`: yes (CC0 allows it; the API is not stable) |
| SHA-256 | `gleif-ie.csv.gz` `73f05300cd9be87a06953e04aa1006ee14d69720e094a492ee2285955ba67c2c` (2,049,066 bytes; the CSV inside: `5294c383fd6b671d60245bc77b3e8824efd97dbce5e67630f861a3877855bf9f`, 7,760,214 bytes); `elf-codes.csv` `af2960f554e193a741e1a0a78bc220018112ee2f9260362cb6b786735380fbb4` (1,751 bytes) |
| Size | 38,650 rows × 15 columns; 49 legal-form codes |

**What one row means.** One LEI record: one legal entity (a company, a fund, a branch …) with its legal name, other names, legal form, legal address, registration authority and number, the LEI issuer and its registration status. 180 records have the status DUPLICATE and name the LEI that stays (`duplicate_of`). The case study's labels are those links: records joined by a chain of links are one entity (173 entities with 2 or more LEIs, 191 true pairs). `registration_status` and `duplicate_of` are labels only, never inputs.

| Column | From the API field |
|---|---|
| `lei` | `lei` |
| `legal_name` | `entity.legalName.name` |
| `other_names` | `entity.otherNames[].name`, joined with ` \| ` |
| `legal_form` | `entity.legalForm.id` (ISO 20275 ELF code; 8888 = not on the list, 9999 = not given; names in `elf-codes.csv`) |
| `category` | `entity.category` |
| `address` | `entity.legalAddress.addressNumber` and `addressLines`, joined with `, ` |
| `city`, `postcode`, `country` | `entity.legalAddress.city`, `postalCode`, `country` |
| `registration_authority`, `registration_number` | `entity.registeredAt.id`, `entity.registeredAs` |
| `managing_lou` | `registration.managingLou` |
| `first_registered` | `registration.initialRegistrationDate` (the date only) |
| `registration_status` | `registration.status` |
| `duplicate_of` | `entity.successorEntity.lei`, only when the status is DUPLICATE |

## Why these datasets

The lead's decision for this case study: GLEIF (CC0) and Splink's `fake_1000` (MIT) only. `fake_1000` is small, simulated (no privacy question), labelled, and much noisier than Larkfield's records. GLEIF is a real register with real duplicates that GLEIF itself marked, and real look-alikes: thousands of funds share one administrator's address, and sub-funds of one umbrella share its name and registration number. Ireland is a mid-sized slice (about 39,000 records, 2 MB compressed) with English names, many funds and 180 marked duplicates. Compared and not used: see `reference/c39/m09/cs3/DATASET-RESEARCH.md` (FEBRL: ANU Open Source Licence; SIRENE: Licence Ouverte 2.0; UK Companies House: no licence stated; Splink's `historical_figures_with_errors_50k`: real people).

## Changes we made

`fake_1000.csv`: none. GLEIF: we kept the 15 columns above, joined the address lines and the other names, kept the date part of the first registration, wrote one UTF-8 CSV sorted by LEI, and compressed it with gzip. We left out the 6 records of the category SOLE_PROPRIETOR (a business run by one natural person; none is in a DUPLICATE link). We changed no value. Scripts: `reference/c39/m09/cs3/fetch_gleif.py` and `build_slice.py`.

## Limitations and cautions

- **The simulated people are not real.** Their errors come from a program; real lists have other errors (households, shared emails, moves). The results say little about a real list.
- **GLEIF's labels are incomplete.** Only the duplicates that GLEIF or an issuer found are marked. Many pairs with the same name and registration number are not marked, so a matcher's measured precision is lower than its true precision. Some marked links also look wrong (one DUPLICATE record points to a company with another name and another registration number).
- **One country, one day.** Ireland has many investment funds; another country's register looks different. The register changes every day.
- **Real organisations.** The records name real companies and funds. Nothing in the case study is a claim about any of them. A DUPLICATE status is GLEIF's data, not a judgement.
- **No private persons.** We left out the sole proprietors. The other records are legal entities: companies, funds, branches and public bodies.
