"""Make the synthetic progress data of the case study "What to learn next" (recommendations course, M10-L04).

    python -I make_data.py OUT_DIR

Writes OUT_DIR/lessons.csv (the catalogue: 12 courses, 84 lessons, with prerequisites) and
OUT_DIR/completions.csv.gz (one row per lesson completed: learner, lesson, completed_at). CC0 1.0: the data is made
by this script. It is not real learner data, and it is not from Nextia Learning: the platform "Ridgeway Learning",
its courses and its learners are invented. Fixed seed (37): the same files every time with the same NumPy version.

The behaviour model (the documentation of the data; every rule here is a decision we made, not a measurement):

- Learners join between 6 January 2025 and 15 February 2026; more join later (the platform grows).
- Each learner has a goal, picked at joining: data analyst, machine-learning engineer, backend developer,
  AI app builder, or none ("browser"). A goal is an ordered list of courses (PATHS). The AI app builder goal
  becomes more common over time, so its courses become more popular late in the data (a trend).
- A learner with a goal takes the courses of the goal in order. Inside a course they take the lessons in order.
  They take an optional lesson with probability 0.45. They skip a required lesson with probability 0.02.
- 30% of the learners with a goal take two courses at a time: when they reach the middle of a course, they start
  the next course of their goal (if its prerequisites are met), and then alternate between the two at random.
- When they start a new course: with probability 0.07 they jump ahead to a later course of their goal although
  its prerequisites are not met (impatient), and with probability 0.10 they take a detour: a course outside their
  goal, picked by its current popularity, whose prerequisites are met.
- Browsers pick a course by its current popularity, ignore prerequisites, take 2 to 6 lessons in order and pick
  again.
- After each lesson, a learner stops for good with probability 0.05 (0.15 after their first lesson, 0.10 after the
  last lesson of a course). Time between two lessons: exponential, with a personal pace (median about 3 days);
  with probability 0.08 a long break of 20 to 60 days.
"""

import gzip
import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 37
START = pd.Timestamp("2025-01-06")
END = pd.Timestamp("2026-02-16")          # exclusive: the data ends on Sunday 15 February 2026
LEARNERS = 24000

# (code, title, lesson titles, optional positions (1-based), prerequisites of the first lesson)
COURSES = [
    ("GIT", "Git and the command line", ["The command line", "Files and folders", "Your first repository",
                                          "Branches", "Work with others"], [], []),
    ("PY", "Python basics", ["Values and variables", "Lists and loops", "Decisions", "Functions", "Dictionaries",
                             "Files", "Extra practice: a quiz game", "Modules and packages"], [7], []),
    ("SQL", "SQL for analysis", ["Tables and SELECT", "Filter rows", "Sort and limit", "Group and count", "Joins",
                                 "Subqueries", "Window functions"], [], []),
    ("STA", "Statistics with Python", ["Averages and spread", "Distributions", "Samples", "Confidence intervals",
                                       "Tests", "Correlation", "Regression"], [], ["PY-04"]),
    ("PD", "Data analysis with pandas", ["DataFrames", "Select and filter", "Clean data", "Group and aggregate",
                                         "Join tables", "Extra practice: a sales report", "Dates and time",
                                         "A small analysis"], [6], ["PY-08"]),
    ("VIZ", "Charts and dashboards", ["Choose a chart", "Bar and line charts", "Scatter plots", "Colour and labels",
                                      "A dashboard", "Tell a story"], [], ["PD-04"]),
    ("ML", "Machine learning", ["What a model learns", "Train and test", "Linear models", "Trees", "Metrics",
                                "Overfitting", "Features", "Extra practice: house prices", "A full project"], [8],
     ["PD-08", "STA-05"]),
    ("DL", "Deep learning", ["Neurons and layers", "Training", "Images", "Text", "Transfer learning", "Tuning",
                             "Extra practice: a classifier", "Serve a model"], [7], ["ML-06"]),
    ("WEB", "How the web works", ["Requests and responses", "HTML", "CSS", "JavaScript", "Extra practice: a page",
                                  "Forms"], [5], []),
    ("API", "Build APIs with Python", ["What an API is", "Your first endpoint", "Validate input", "A database",
                                       "Authentication", "Tests", "Errors and logs"], [], ["PY-08", "WEB-04"]),
    ("OPS", "Deploy to the cloud", ["Servers and containers", "Your first deployment", "Configuration", "Logs",
                                    "Scale", "Costs"], [], ["API-05", "GIT-03"]),
    ("LLM", "Build apps with language models", ["What a language model does", "Your first call", "Prompts",
                                                "Structured output", "Tools", "Retrieval", "Evaluate an app"], [],
     ["API-04"]),
]

PATHS = {
    "data analyst": ["PY", "SQL", "STA", "PD", "VIZ"],
    "machine-learning engineer": ["PY", "STA", "PD", "ML", "DL"],
    "backend developer": ["WEB", "GIT", "PY", "API", "OPS"],
    "AI app builder": ["PY", "WEB", "API", "LLM"],
    "browser": [],
}
BASE_POPULARITY = {"GIT": 1.0, "PY": 3.0, "SQL": 2.0, "STA": 1.0, "PD": 1.5, "VIZ": 1.0, "ML": 2.0, "DL": 1.0,
                   "WEB": 1.5, "API": 1.0, "OPS": 0.6, "LLM": 0.6}


def catalogue():
    rows = []
    for code, title, lessons, optional, first_pre in COURSES:
        last_required = None
        for pos, name in enumerate(lessons, 1):
            lid = f"{code}-{pos:02d}"
            pre = list(first_pre) if pos == 1 else [last_required]
            opt = pos in optional
            rows.append({"lesson": lid, "course": code, "course_title": title, "position": pos, "title": name,
                         "optional": opt, "prerequisites": ";".join(pre)})
            if not opt:
                last_required = lid
    return pd.DataFrame(rows)


class World:
    def __init__(self, cat, rng):
        self.cat = cat
        self.rng = rng
        self.lessons = {c: cat[cat.course == c].lesson.tolist() for c in cat.course.unique()}
        self.optional = set(cat[cat.optional].lesson)
        self.pre = {r.lesson: [p for p in r.prerequisites.split(";") if p] for r in cat.itertuples()}
        self.first_pre = {c: self.pre[ls[0]] for c, ls in self.lessons.items()}

    def popularity(self, t):
        """Course weights at time t: the LLM and API courses become more popular (the trend)."""
        f = (t - START) / (END - START)
        w = dict(BASE_POPULARITY)
        w["LLM"] += 5.0 * f ** 2
        w["API"] += 1.5 * f
        return w

    def path_weights(self, t):
        f = (t - START) / (END - START)
        return {"data analyst": 0.28, "machine-learning engineer": 0.22, "backend developer": 0.18,
                "AI app builder": 0.08 + 0.25 * f, "browser": 0.16}

    def pick(self, weights):
        keys = list(weights)
        p = np.array([weights[k] for k in keys], float)
        return keys[self.rng.choice(len(keys), p=p / p.sum())]


def simulate_learner(w, learner, t):
    rng = w.rng
    goal = w.pick(w.path_weights(t))
    path = list(PATHS[goal])
    two_at_a_time = goal != "browser" and rng.random() < 0.30
    pace = np.exp(rng.normal(np.log(3.0), 0.6))           # mean days between lessons
    done, events = set(), []
    active = []                                            # [course, next position index]
    started = set()

    def can_start(c):
        return all(p in done for p in w.first_pre[c])

    def start_course(now):
        if goal == "browser":
            pop = {c: v for c, v in w.popularity(now).items() if c not in started}
            return w.pick(pop) if pop else None
        todo = [c for c in path if c not in started]
        if not todo:
            return None
        if rng.random() < 0.10:                             # a detour outside the goal
            pop = {c: v for c, v in w.popularity(now).items()
                   if c not in started and c not in path and can_start(c)}
            if pop:
                return w.pick(pop)
        ok = [c for c in todo if can_start(c)]
        if rng.random() < 0.07 and len(todo) > 1:           # impatient: jump ahead
            return todo[1 + rng.integers(len(todo) - 1)]
        return ok[0] if ok else todo[0]

    browse_left = 0
    first = True
    while t < END:
        if not active:
            c = start_course(t)
            if c is None:
                break
            active.append([c, 0])
            started.add(c)
            browse_left = rng.integers(2, 7)
        # which course now
        slot = active[rng.integers(len(active))] if len(active) > 1 else active[0]
        c, i = slot
        ls = w.lessons[c]
        lesson = ls[i]
        if lesson in w.optional and rng.random() > 0.45:
            i += 1
            lesson = ls[i]
        elif lesson not in w.optional and i + 1 < len(ls) and i > 0 and rng.random() < 0.02:
            i += 1                                          # skip a required lesson
            lesson = ls[i]
        events.append((learner, lesson, t))
        done.add(lesson)
        slot[1] = i + 1
        finished = slot[1] >= len(ls)
        if finished:
            active.remove(slot)
        # stop for good?
        hazard = 0.15 if first else (0.10 if finished else 0.05)
        first = False
        if rng.random() < hazard:
            break
        if goal == "browser":
            browse_left -= 1
            if browse_left <= 0 and active:
                active.clear()
        elif two_at_a_time and len(active) == 1 and slot in active and slot[1] >= len(ls) // 2:
            nxt = [x for x in path if x not in started]
            if nxt and can_start(nxt[0]):
                active.append([nxt[0], 0])
                started.add(nxt[0])
        gap = rng.exponential(pace)
        if rng.random() < 0.08:
            gap += rng.uniform(20, 60)
        t = t + pd.Timedelta(minutes=int(gap * 1440) + 5)
    return [e for e in events if e[2] < END]


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    cat = catalogue()
    w = World(cat, rng)
    span = (END - START).total_seconds()
    # more learners join later: density grows linearly from 1 to 2.5
    u = rng.random(LEARNERS)
    a, b = 1.0, 2.5
    x = (np.sqrt(a * a + (b * b - a * a) * u) - a) / (b - a)
    joins = np.sort(x) * span
    rows = []
    for n, s in enumerate(joins, 1):
        t = START + pd.Timedelta(seconds=int(s))
        rows += simulate_learner(w, f"R{n:05d}", t)
    ev = pd.DataFrame(rows, columns=["learner", "lesson", "completed_at"])
    ev = ev.sort_values(["completed_at", "learner"], kind="stable").reset_index(drop=True)
    ev["completed_at"] = ev["completed_at"].dt.strftime("%Y-%m-%d %H:%M")
    cat.to_csv(out / "lessons.csv", index=False, lineterminator="\n")
    buf = io.StringIO()
    ev.to_csv(buf, index=False, lineterminator="\n")
    with gzip.GzipFile(out / "completions.csv.gz", "wb", mtime=0, compresslevel=9) as f:
        f.write(buf.getvalue().encode())
    print(f"{len(cat)} lessons in {cat.course.nunique()} courses; {len(ev):,} completions by "
          f"{ev.learner.nunique():,} learners")


if __name__ == "__main__":
    main(sys.argv[1])
