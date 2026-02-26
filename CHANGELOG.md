# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
