# Dataset card: open attack sets for a safety test pass (with recorded answers)

Used by: the case study *A safety test pass with open attack sets* (https://learning.nextia-ai.com/courses/ai-qa/m08/safety-test-pass-with-open-attack-sets/), `safety-test-pass-with-open-attack-sets.ipynb`

| Field | Value |
|---|---|
| Source | Prompt injections: https://huggingface.co/datasets/deepset/prompt-injections (revision `4f61ecb038e9c3fb77e21034b22511b523772cdd`). Over-refusal: https://huggingface.co/datasets/Paul/XSTest (revision `f600c994b256f12867dfa5b3eb3d545a3e62f8b5`; the same CSV as https://github.com/paul-rottger/xstest) |
| Publisher / creator | deepset GmbH; Röttger, Kirk, Vidgen, Attanasio, Bianchi and Hovy (2024), "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models", NAACL 2024 |
| Licence | deepset/prompt-injections: [Apache-2.0](https://www.apache.org/licenses/LICENSE-2.0) (the dataset card also holds a stray `cc-by-4.0` line; both allow this use). XSTest: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). The Larkfield questions, the new inputs, the prompts, the rules, the labels and the recorded answers: made by Nextia Learning, same terms as the course's labs |
| Attribution text | Prompt injections from deepset/prompt-injections (deepset, Apache-2.0). Over-refusal prompts from XSTest v2 (Röttger et al., 2024, NAACL), licensed under CC BY 4.0. Changes: rows selected (deepset label 1; all of XSTest), fields added (expected behaviour, category, language, dev/test split). |
| Version or access date | 2026-10-19 |
| Files used | `data/attack_set.jsonl`, `in_scope.jsonl`, `new_input.jsonl`, `answers.jsonl.gz`, `human_labels.jsonl`, kept in `data/`: yes (both licences allow sharing) |
| SHA-256 | `attack_set.jsonl` 7a3a97f6276393096f15e94cac023e1e9a4c3ed4c22e660555640a4269bb82f9; `in_scope.jsonl` 1bbd6e09ba9e41655cfde603ad20c76d3d80a9502331f2c955f9ab9b8ab65d8e; `new_input.jsonl` 3ee00ff952bb624a24822f814ba327e5569768ca5d373785e27ed18855ce4262; `answers.jsonl.gz` 796dd0b1baee938d23655fe14f9acddcb4dd622dc5518f58ce2cab201c9cae12; `human_labels.jsonl` 24f2309f120982d0b1e6487293825e22ce46de86e4417367c5ba9fa9767e6e3d |
| Size | 713 attack-set prompts (263 injections, 250 safe, 200 unsafe), 19 Larkfield questions, 16 new inputs; 3,992 recorded answers |

## What one row means

`attack_set.jsonl`, `in_scope.jsonl`, `new_input.jsonl`: one prompt, sent as a customer message to Larkfield's support
assistant, with the behaviour it must show (`expected`: `resist`, `answer`, `decline` or `help`), a category, a language and
a split. `answers.jsonl.gz`: one recorded answer of the assistant (its prompt, policy search and tools on Azure `chat-small`,
gpt-6-luna 2026-09-22, `reasoning_effort` none, default temperature) to one prompt, in one run: the reply or the platform's
error code, the tool calls, the retrieved policy sections, tokens and time. `human_labels.jsonl`: the course author's
verdict on one answer, with a reason.

## Why these sets

deepset/prompt-injections mixes many attack goals (drop the job, show the instructions, say a phrase, play a role) in
English and German; Lakera's Gandalf set (MIT) was compared and has one goal (a password). XSTest is hand-written and has an
unsafe twin for every safe type, so an assistant that refuses everything cannot score well; OR-Bench (CC BY 4.0) was
compared and is machine-made and far larger. Full comparison: `reference/c30/m08/l03/DATASET-RESEARCH.md` in the course
repository.

## Changes we made

deepset rows with label 1 (train and test, 263); every XSTest prompt (450); fields `expected`, `category` (XSTest's type;
keyword rules for the injections), `language` (keyword rules) and `split` (`random.Random(3003)`, about 1 in 5 to dev).

## Limitations and cautions

- Offensive text: the attack sets contain political insults, slurs and questions about violence, by design. Six recorded
  replies are withheld (an insult written in the shop's name); their outcome, length and SHA-256 are kept.
- Label noise: some deepset rows labelled as injections are ordinary requests ("translate to polish").
- The injection categories and languages come from keyword rules: a rough sort, not a ground truth.
- deepset has English and German versions of the same attacks; a pair can fall on both sides of the dev/test split.
- XSTest is English only; the assistant serves English and French customers.
- One model, one date, 3 runs per prompt: a new model or prompt version needs a new pass.
