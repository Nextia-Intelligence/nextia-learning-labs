# Method choice for three hardware budgets (worked example)

Larkfield's task: read one ticket, answer `{"team": ..., "needs_human": ...}`. Kwame asked which method
fits which computer. The numbers come from `python -m adapt memory` and `python -m adapt params`: they are
ESTIMATES of the weights, the gradients and the optimizer's states. Activations come on top, so we keep
30% of the memory free for them and for the system. Model sizes other than SmolLM2-135M are round sizes,
an assumption.

| Budget | What fits (estimate) | Our choice | Why |
|---|---|---|---|
| A laptop with 16 GB and no GPU (the course's computer) | Full tuning of SmolLM2-135M (2.15 GB) or LoRA (0.54 GB); LoRA on a 1.7B model (6.87 GB) | **LoRA, rank 8, on SmolLM2-135M** | It trains 460,800 numbers (0.34%) instead of 134,515,008, so the file is 1.8 MB instead of 538 MB and each training step is cheaper. A 1.7B model would fit in memory, but it has about 12 times as many weights to compute with in every step (an estimate, not measured). QLoRA needs a GPU library. |
| One GPU with 24 GB | LoRA on a 7B model with the base in bfloat16 (14.3 GB); QLoRA on a 7B model (3.8 GB) | QLoRA or LoRA on a 1.7B to 7B model, only if the small model is not good enough | A larger base model knows more language. It is worth it only if the evaluation shows that the small one fails on cases that matter. |
| One GPU with 80 GB | Full tuning of a 1.7B model (27.2 GB); QLoRA on a 70B model (37.9 GB) | Do not start here | The cost is real (hosting and training hours) and the evidence must come first. Full tuning changes every weight: a new 7 GB copy for each version, and more risk of forgetting what the model knew. |

Other methods, and the data they need (none of them is used in this course):

- **Distillation**: a large "teacher" model labels many tickets, and a small "student" model is trained on
  its answers. It needs many unlabelled tickets and the teacher's cost; it copies the teacher's mistakes too.
- **Preference tuning** (for example DPO): the training data are pairs of replies, one preferred. It
  changes how a model writes (tone, length), not which team a ticket goes to. Our task has one right
  answer, so it does not fit.
