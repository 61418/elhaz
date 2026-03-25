# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Output helpers: pygments-highlighted JSON and status messages."""

import json
import sys
from typing import Any

import typer
from pygments import highlight
from pygments.formatters import Terminal256Formatter
from pygments.lexers import JsonLexer

_FORMATTER = Terminal256Formatter(style="monokai")

_REDACTED = "***"

#: Field names whose values are redacted when ``--obscure`` is requested.
#: Covers credential-bearing and ARN-bearing fields across ConfigModel
#: sections (AssumeRole, STS, Session) and the raw export credential dict.
SENSITIVE_FIELDS: frozenset[str] = frozenset(
    {
        # AssumeRole — contains account ID or shared secrets
        "RoleArn",
        "ExternalId",
        "SerialNumber",
        "TokenCode",
        "PolicyArns",
        # STS / Session — static credentials supplied to boto3
        "aws_access_key_id",
        "aws_secret_access_key",
        "aws_session_token",
        "aws_account_id",
        # Raw export credential keys returned by the daemon
        "access_key",
        "secret_key",
        "token",
        # credential-process JSON shape (CredentialProcessModel)
        "AccessKeyId",
        "SecretAccessKey",
        "SessionToken",
        # STS GetCallerIdentity (whoami) response fields
        "Account",
        "Arn",
        "UserId",
    }
)


def obscure(data: Any) -> Any:
    """Recursively redact sensitive field values in *data*.

    Traverses dicts and lists. Any dict key present in
    :data:`SENSITIVE_FIELDS` has its value replaced with ``"***"``.
    All other values are returned unchanged.

    Parameters
    ----------
    data : Any
        JSON-serializable value, typically a ``dict`` or ``list``.

    Returns
    -------
    Any
        A new structure with sensitive values replaced by ``"***"``.
    """

    if isinstance(data, dict):
        return {
            k: _REDACTED if k in SENSITIVE_FIELDS else obscure(v)
            for k, v in data.items()
        }
    if isinstance(data, list):
        return [obscure(item) for item in data]
    return data


def print_json(data: Any) -> None:
    """Pretty-print *data* as syntax-highlighted JSON.

    Falls back to plain JSON when stdout is not a TTY (e.g. pipes).

    Parameters
    ----------
    data : Any
        JSON-serializable value to display.
    """

    formatted = json.dumps(data, indent=2, default=str)
    if sys.stdout.isatty():
        typer.echo(
            highlight(formatted, JsonLexer(), _FORMATTER),
            nl=False,
        )
    else:
        typer.echo(formatted)


def print_error(message: str) -> None:
    """Print *message* to stderr in red.

    Parameters
    ----------
    message : str
        Error description.
    """

    typer.secho(f"Error: {message}", fg=typer.colors.RED, err=True)


def print_success(message: str) -> None:
    """Print *message* to stdout in green.

    Parameters
    ----------
    message : str
        Success description.
    """

    typer.secho(message, fg=typer.colors.GREEN)
