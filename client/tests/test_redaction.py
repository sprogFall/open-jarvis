from client.redaction import LogRedactor


def test_redacts_passwords_and_tokens():
    redactor = LogRedactor()

    text = "password=hunter2 token=abcd1234 Authorization: Bearer top-secret"
    assert redactor.redact(text) == (
        "password=*** token=*** Authorization: Bearer ***"
    )
