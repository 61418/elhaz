# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Unit tests for elhaz.cli.output."""

from __future__ import annotations

import datetime
import json

from elhaz.cli.output import (
    SENSITIVE_FIELDS,
    obscure,
    print_error,
    print_json,
    print_success,
)


def test_print_json_non_tty_outputs_plain_json(capsys) -> None:
    data = {"key": "value", "num": 42}
    print_json(data)
    captured = capsys.readouterr()
    # In test environment stdout is not a TTY, so plain JSON expected.
    parsed = json.loads(captured.out)
    assert parsed == data


def test_print_json_non_tty_uses_indent_2(capsys) -> None:
    data = {"a": 1}
    print_json(data)
    captured = capsys.readouterr()
    assert "  " in captured.out  # indented


def test_print_json_serializes_non_native_types_via_str(capsys) -> None:
    dt = datetime.datetime(2030, 1, 1, tzinfo=datetime.timezone.utc)
    data = {"ts": dt}
    print_json(data)
    captured = capsys.readouterr()
    assert "2030" in captured.out


def test_print_json_nothing_to_stderr(capsys) -> None:
    print_json({"x": 1})
    captured = capsys.readouterr()
    assert captured.err == ""


def test_print_json_tty_calls_typer_echo(monkeypatch, capsys) -> None:
    """When stdout is a TTY, output goes through pygments highlight."""
    import sys

    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    # We just check that something is written to stdout without crashing
    print_json({"hello": "world"})
    captured = capsys.readouterr()
    # Highlighted output is non-empty (contains some content)
    assert len(captured.out) > 0


def test_print_error_goes_to_stderr(capsys) -> None:
    print_error("something broke")
    captured = capsys.readouterr()
    assert "Error: something broke" in captured.err


def test_print_error_nothing_to_stdout(capsys) -> None:
    print_error("oops")
    captured = capsys.readouterr()
    assert captured.out == ""


def test_print_error_has_error_prefix(capsys) -> None:
    print_error("my message")
    captured = capsys.readouterr()
    assert captured.err.startswith("Error:")


def test_print_success_goes_to_stdout(capsys) -> None:
    print_success("everything worked")
    captured = capsys.readouterr()
    assert "everything worked" in captured.out


def test_print_success_nothing_to_stderr(capsys) -> None:
    print_success("done")
    captured = capsys.readouterr()
    assert captured.err == ""


# ---------------------------------------------------------------------------
# obscure()
# ---------------------------------------------------------------------------


def test_obscure_redacts_role_arn() -> None:
    data = {"AssumeRole": {"RoleArn": "arn:aws:iam::123456789012:role/Dev"}}
    result = obscure(data)
    assert result["AssumeRole"]["RoleArn"] == "***"


def test_obscure_redacts_credentials() -> None:
    data = {
        "aws_access_key_id": "AKIATEST",
        "aws_secret_access_key": "SECRET",
        "aws_session_token": "TOKEN",
    }
    result = obscure(data)
    assert result["aws_access_key_id"] == "***"
    assert result["aws_secret_access_key"] == "***"
    assert result["aws_session_token"] == "***"


def test_obscure_redacts_export_credential_keys() -> None:
    data = {
        "access_key": "AKIATEST",
        "secret_key": "SUPERSECRET",
        "token": "TOKEN123",
        "expiry_time": "2030-01-01T00:00:00Z",
    }
    result = obscure(data)
    assert result["access_key"] == "***"
    assert result["secret_key"] == "***"
    assert result["token"] == "***"
    assert result["expiry_time"] == "2030-01-01T00:00:00Z"


def test_obscure_passes_through_non_sensitive_fields() -> None:
    data = {
        "region_name": "us-east-1",
        "RoleSessionName": "my-session",
        "DurationSeconds": 3600,
    }
    result = obscure(data)
    assert result == data


def test_obscure_handles_nested_dicts() -> None:
    data = {
        "STS": {
            "region_name": "us-west-2",
            "aws_secret_access_key": "SECRET",
        }
    }
    result = obscure(data)
    assert result["STS"]["region_name"] == "us-west-2"
    assert result["STS"]["aws_secret_access_key"] == "***"


def test_obscure_handles_list_of_dicts() -> None:
    data = {
        "PolicyArns": [
            "arn:aws:iam::123456789012:policy/Foo",
            "arn:aws:iam::123456789012:policy/Bar",
        ]
    }
    result = obscure(data)
    assert result["PolicyArns"] == "***"


def test_obscure_handles_non_dict_non_list_passthrough() -> None:
    assert obscure("hello") == "hello"
    assert obscure(42) == 42
    assert obscure(None) is None


def test_obscure_returns_new_object_does_not_mutate() -> None:
    data = {
        "RoleArn": "arn:aws:iam::123456789012:role/Dev",
        "region": "us-east-1",
    }
    original = dict(data)
    obscure(data)
    assert data == original


def test_sensitive_fields_is_frozenset() -> None:
    assert isinstance(SENSITIVE_FIELDS, frozenset)


def test_sensitive_fields_covers_key_names() -> None:
    expected = {
        "RoleArn",
        "ExternalId",
        "SerialNumber",
        "TokenCode",
        "PolicyArns",
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "aws_account_id",
        "access_key",
        "secret_key",
        "token",
        "AccessKeyId",
        "SecretAccessKey",
        "SessionToken",
        "Account",
        "Arn",
        "UserId",
    }
    assert expected.issubset(SENSITIVE_FIELDS)
