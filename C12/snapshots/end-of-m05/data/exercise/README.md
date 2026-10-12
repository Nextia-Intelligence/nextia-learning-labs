# Exercise: find the problems before you train

`extra_records.jsonl` holds 4 records that a colleague wants to add to the training data. They were made
up for this exercise. Three of them must not be used. Before you run anything, read them and decide which
three, and why. Then run:

    python -m adapt prepare --extra data/exercise/extra_records.jsonl

and compare the rejections with your answer. Run `python -m adapt prepare` again afterwards, so that
data/prepared/ is the course's data again.
