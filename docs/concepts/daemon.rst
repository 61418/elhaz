.. _daemon:

Daemon
======

elhaz uses a daemon process to manage temporary AWS credentials.
The daemon is responsible for initializing and caching AWS sessions (in a bounded LRU cache), refreshing temporary AWS credentials, and providing credentials to the CLI when requested.

To do this, elhaz uses a **Unix domain socket** for local inter-process communication between the CLI and the daemon.

The daemon enables a single, long-lived credential authority on the local machine. 
Instead of repeatedly creating new sessions or calling AWS STS from multiple processes, elhaz reuses existing sessions and refreshes them in the background using boto3-refresh-session.

This provides:

- Multiple role assumptions without redundant session creation
- Reduced redundant calls to AWS STS
- Consistent credential reuse across processes
- Immediate access to valid credentials
- Centralized lifecycle management for temporary sessions

Why not HTTP with ECS metadata emulation?
-----------------------------------------

The AWS CLI allows ECS metadata emulation via a locally hosted HTTP endpoint, configured using ``AWS_CONTAINER_CREDENTIALS_FULL_URI``.
This technique is native to the AWS ecosystem and is used by many tools to provide credentials to SDKs.

However, this approach has some tradeoffs for a local developer tool:

- Additional HTTP server complexity
- Optional TLS and authorization concerns
- Increased surface area for local networking and configuration
- Managing multiple endpoints or routing logic for multiple assumed roles

In contrast, elhaz uses a Unix domain socket, which is:

- Local-only by design (no network exposure)
- Simpler to implement and reason about
- Well-suited for single-machine coordination
- Naturally aligned with CLI-driven workflows

For local development, where both the CLI and daemon run on the same machine, a Unix domain socket provides a minimal and efficient communication mechanism without requiring HTTP semantics.

Notes
-----

- The daemon is an implementation detail of elhaz's credential coordination model.
- All CLI commands (e.g., ``exec``, ``shell``, ``export``) interact with the daemon transparently.
- The daemon maintains exactly one active session (until removed or the server is stopped) per configuration and refreshes credentials automatically based on expiration.
