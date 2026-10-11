# Project file: delivery-delay warnings

*Everything in this file is **constructed** for the course: the project, the documents, the people's words and the numbers. Larkfield's regular team appears as in the other courses; Victor (the former sponsor) and Dana (a contract data engineer) are written for this case.*

## 1. The project charter (month 0)

> **Project:** Delivery-delay warnings
> **Sponsor:** Victor, head of operations
> **Goal:** Use machine learning to predict which deliveries will be late, and reduce "Where is my order?" tickets.
> **Team:** Priya (data scientist, 60% of her time), Tomás (AI engineer, 50%), Dana (contract data engineer, 3 months).
> **Budget:** 6 months.
> **Success:** an accurate model in production.

There is no other charter text. There is no document that says who will use the prediction, or what happens when a delivery is predicted to be late.

## 2. Monthly status reports (written by Tomás)

| Month | Status | Reported result | Notes from the report |
|---|---|---|---|
| 1 | Green | — | "Data pipeline from the carrier's tracking feed and our orders is built. Dana did great work." |
| 2 | Green | "accuracy 81%" | "First model works. Demo to Victor and Grace went well. Grace asked how customers would get the warning: next step." |
| 3 | Green | "accuracy 86%" | "Added weather data. Better model. Test set changed to the last two months, which are more relevant." |
| 4 | Amber | "accuracy 84%" | "The carrier changed its tracking feed format. Pipeline partly broken; we use a copy of the old data for now. Dana's contract ended." |
| 5 | Green | "AUC 0.88" | "Switched to a better measure (AUC). Built a dashboard so operations can see risky deliveries. Victor left the company." |
| 6 | Green | "AUC 0.91" | "Tried a new model type. Nearly ready for production. Need two more weeks to connect it to the website." |

## 3. What was spent (constructed)

| Item | Amount |
|---|---|
| Priya's and Tomás's time (6 months at their share) | about 1,700 hours |
| Dana's contract | 3 months |
| Cloud and data services | about US$2,900 |
| Weather data subscription (12 months, paid in month 3) | US$4,800 |

## 4. What people say now

- **Grace (support lead):** "We saw a demo in month 2. Nobody told us what the warning would say, or when. My agents still answer about 120 'Where is my order?' tickets a day."
- **Luis (delivery team lead):** "Nobody from the project spoke to us. Half the late deliveries are late because a parcel is held at a depot. We know that the day it happens: the carrier's status says 'held'."
- **Priya (data scientist):** "Every month the test set or the measure changed, so the numbers are not comparable. I am not sure the model is better than a simple rule. We never agreed what 'accurate enough' means."
- **Tomás (AI engineer):** "The model is good. We just need to deploy it. The dashboard is a bonus."
- **Kwame (solution architect):** "The live pipeline has been broken since month 4. The model runs on old data. Connecting it to the website is more than two weeks of work."
- **Omar (product manager):** "It's not on my roadmap. I thought operations owned it."

## 5. What exists today

- A notebook with the latest model, trained on data that ends in month 4.
- A data pipeline that worked until the carrier changed its feed in month 4.
- A dashboard prototype that nobody outside the team has opened.
- Six months of the team's knowledge of the data, and the carrier's tracking statuses.
- No evaluation set that anyone agreed on, no definition of done, no plan for how a customer receives a warning, no owner in support or delivery.
