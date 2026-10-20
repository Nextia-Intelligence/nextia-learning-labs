from django.db.models import BooleanField, ExpressionWrapper, Q
from django.test import TestCase

from .models import Author


class RewriteCheck(TestCase):
    """The acceptance criteria of the rewritten report, as tests."""

    @classmethod
    def setUpTestData(cls):
        for name in ("Ana", "Ben", "Chen"):
            Author.objects.create(name=name, age=30)

    def annotate(self, condition):
        return Author.objects.annotate(
            selected=ExpressionWrapper(condition, output_field=BooleanField()))

    def test_must_negated_empty_in_is_true_for_every_row(self):
        rows = list(self.annotate(~Q(pk__in=[])))
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(row.selected is True for row in rows))

    def test_must_keep_empty_in_false_for_every_row(self):
        rows = list(self.annotate(Q(pk__in=[])))
        self.assertTrue(all(row.selected is False for row in rows))

    def test_must_not_change_filter(self):
        self.assertEqual(Author.objects.filter(~Q(pk__in=[])).count(), 3)
        self.assertEqual(Author.objects.filter(Q(pk__in=[])).count(), 0)
