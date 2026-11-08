"""The rules baseline: a rule decides when one matches; a person reads every other message."""

from larkroute import rules as rule_book
from larkroute.methods import Method


class RulesElsePerson(Method):
    name = "rules or a person"

    def __init__(self):
        self.rules = rule_book.load()

    def predict(self, messages):
        out = []
        for text in messages["text"]:
            r = rule_book.match(text, self.rules)
            out.append(r["route"] if r else "review")
        return out


METHODS = {RulesElsePerson.name: RulesElsePerson}
