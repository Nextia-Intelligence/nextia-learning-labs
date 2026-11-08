"""Larkfield today: a person reads every message and sends it to a team."""

from larkroute.methods import Method


class EverythingToAPerson(Method):
    name = "everything to a person"

    def predict(self, messages):
        return ["review"] * len(messages)


METHODS = {EverythingToAPerson.name: EverythingToAPerson}
