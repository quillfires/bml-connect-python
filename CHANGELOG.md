# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2026-02-27

### Fixed

- `__version__` in `__init__.py` was not updated from `1.1.0` after the 1.2.0 release
- Docstring in `__init__.py` still referenced the old manual `client.close()` pattern instead of context managers

### Changed

- `examples/basic_sync.py` updated to use `with` context manager and added `cancel_transaction` example
- `examples/basic_async.py` updated to use `async with` context manager and added `cancel_transaction` example

## [1.2.0] - 2026-02-27

### Added

- `cancel_transaction(transaction_id)` on both `SyncClient` and `AsyncClient` — brings SDK to full API parity with the official BML Connect PHP SDK
- `REFUND_REQUESTED` and `REFUNDED` states to `TransactionState` enum — previously, webhooks containing these states would silently produce `state=None` on the `Transaction` object
- Context manager support (`with`/`async with`) on `BMLConnect`, `SyncClient`, and `AsyncClient` for automatic resource cleanup
- Configurable `timeout` parameter on `BMLConnect` (default: 30 seconds) — previously hardcoded and not overridable

### Fixed

- `AsyncClient` no longer creates `aiohttp.ClientSession` in `__init__`. Session is now created lazily on first request, which is the correct pattern for aiohttp and avoids runtime warnings and connection leaks
- `assert isinstance(payload, dict)` in `verify_webhook_signature` replaced with a proper `if/raise` guard — `assert` statements are stripped when Python is run with the `-O` flag
- Warning log in `SignatureUtils.generate_signature` now correctly logs the original invalid sign method value instead of the already-reassigned default
- `if not amount` check in `generate_signature` changed to `if amount is None` — the previous check would incorrectly reject `amount=0`
- `if state:` / `if provider:` / `if start_date:` / `if end_date:` filter checks in `list_transactions` changed to `is not None` — the previous checks silently ignored explicitly passed empty strings
- Redundant f-string `f"{self.api_key}"` in `_get_headers` simplified to `self.api_key`

## [1.1.2] - 2026-02-27

### Fixed

- Corrected release notes format in changelog

## [1.1.1] - 2026-02-27

### Fixed

- Migrated to Poetry for dependency management and lockfile
- Added aiohttp and requests as explicit dependencies
- Fixed all mypy type errors in client.py
- Fixed flake8 lint errors
- SDK version now reads automatically from package metadata
- Dropped EOL Python 3.7/3.8 support, minimum is now 3.9

## [1.1.0] - 2025-07-15

### Fixed

- **BREAKING**: Fixed signature generation to comply with official BML Connect API specification
- Signature now uses only `amount`, `currency`, and `apiKey` parameters as per BML documentation
- Corrected parameter order in signature string: `amount={amount}&currency={currency}&apiKey={api_key}`
- Webhook signature verification now uses correct parameter subset

### Breaking Changes

- Signature generation method has been updated to match BML Connect specification
- Previous signatures generated with additional parameters will no longer work
- Applications using this SDK will need to regenerate signatures after upgrade

### Documentation

- Improved README structure and clarity
