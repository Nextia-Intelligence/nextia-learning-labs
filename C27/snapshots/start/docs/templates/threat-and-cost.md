# Threat and cost review: <your product's name>

Write this in Module 2 (*Threat and cost review*).

## Trust boundaries

| Boundary | What crosses it | What we check there |
|---|---|---|
| <browser -> API> | <cookie or token, question, uploaded file> | <identity, membership, size, type> |

## Threats

| Threat | Example | Mitigation | Test |
|---|---|---|---|
| <another shop's data> | <a member changes the shop in the URL> | <membership check + row-level security> | <isolation checks> |

## Tenant isolation rules

1. <Every table with shop data has a tenant column, and every query filters on it.>
2. <...>

## Budget

| Resource | Limit | How it is enforced |
|---|---|---|
| <model cost per shop and month> | <...> | <...> |
| <cloud resources> | <...> | <...> |
