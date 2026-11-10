import pandas as pd
import pytest

from larkroute import data


@pytest.fixture(scope="session")
def train():
    return data.messages("train")


@pytest.fixture(scope="session")
def small_train(train):
    """300 training messages: enough for tests that only need a working model."""
    return train.groupby("route").head(45).reset_index(drop=True)


@pytest.fixture
def tiny():
    """Four messages whose labels the tests know."""
    return pd.DataFrame({
        "message_id": ["M-1", "M-2", "M-3", "M-4"],
        "text": ["where is my parcel", "I was charged twice", "my account was hacked", "the heater is smoking"],
        "route": ["delivery", "billing", "account", "needs_person"],
        "topic": ["late_delivery", "double_charge", "account_takeover", "safety_issue"],
        "priority": ["normal", "urgent", "urgent", "urgent"],
        "language": ["en", "en", "en", "en"],
        "channel": ["chat", "email", "email", "social"],
    })
