import pytest

from commandflow import CommandFlow, InMemoryEmailService


@pytest.fixture
def mail():
    return InMemoryEmailService()


@pytest.fixture
def cf(mail):
    return CommandFlow(email_service=mail)
