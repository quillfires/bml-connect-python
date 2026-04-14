# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.23] - 2026-04-14

### Changes
- Clean up CHANGELOG.md and update entries

Removed outdated changelog entries and adjusted formatting.


## [2.0.22] - 2026-04-14

### Changes
- Update dependabot-release.yml


## [2.0.21] - 2026-04-14

### Changes
- Update Dependabot workflow to include tagging


## [2.0.20] - 2026-04-14

### Changes
- Delete .github/workflows/tag-creator.yml


## [2.0.19] - 2026-04-14

### Changes
- Update tag creation workflow to use poetry version


## [2.0.18] - 2026-04-14

### Changes
- Add GitHub Actions workflow to create tags


## [2.0.17] - 2026-04-14

### Changes
- Simplify release workflow by removing tagging

Removed the tagging process from the release workflow.


## [2.0.16] - 2026-04-14

### Changes
- Add sleep before checking for existing tags

Added a sleep command to wait before checking for existing tags.


## [2.0.15] - 2026-04-14

### Changes
- Improve tag pushing in dependabot-release workflow

Refactor tag pushing logic to check for existing tags before creation.


## [2.0.14] - 2026-04-13

### Changes
- Remove unnecessary dependencies from requirements.txt

Removed several dependencies that are not needed for Python 3.10 and above.


## [2.0.13] - 2026-04-13

### Changes
- Update GitHub Actions workflow for release process


## [2.0.12] - 2026-04-13

### Changes
- Refactor dependabot-release workflow for clarity


### Changes
- Refactor dependabot release workflow for version bump


## [2.0.10] - 2026-04-13

### Changes
- Fix formatting and update changelog entries


## [2.0.9] - 2026-04-13

### Changes
- Fix formatting and update changelog entries


## [2.0.8] - 2026-04-13

### Changes
- Adjust changelog update logic in workflow

## [2.0.7] - 2026-04-13

### Changes
- Refactor Dependabot release workflow configuration

## [2.0.2] - 2026-03-28

- chore: pin requests>=2.33.0, bump version
- chore: pin cryptography>=46.0.6, bump version
- cchore: drop Python 3.9 support, require >=3.10

## [2.0.1] - 2026-03-28

- chore: pin requests>=2.32.4, bump version
- chore(deps-dev): bump pytest-cov in the dev-dependencies group

## [2.0.0] - 2026-02-28

### Added

- **V2 Transaction API** - `client.transactions.create()` now targets
  `POST /public/v2/transactions`. No request signature required. Supports
  all four integration methods in a single endpoint.

- **Redirect Method support**:
  - `paymentPortalExperience` object: `skipCustomerForm`, `skipProviderSelection`,
    `externalWebsiteTermsAccepted`, `externalWebsiteTermsUrl`
  - `allowRetry` flag - set `false` to permanently fail on first failure
  - `paymentAttemptFailureUrl` - merchant-handled failure redirect
  - `locale` field for payment portal language

- **Direct Method support**:
  - `Provider` enum with all valid values: `MPGS`, `DEBIT_CREDIT_CARD`,
    `ALIPAY`, `ALIPAY_ONLINE`, `UNIONPAY`, `WECHATPAY`, `BML_MOBILEPAY`, `CASH`
  - `Transaction.vendor_qr_code` - QR data string for in-store QR providers
  - QR providers return `vendor_qr_code`; card/online providers return `url`

- **Card-On-File / Tokenization support**:
  - `tokenizationDetails` object: `tokenize`, `paymentType`, `recurringFrequency`
  - `customerAsPayer` field on transaction creation
  - Single-call customer + transaction creation
  - `customers.charge()` fully documented with all three token options:
    by `tokenId`, by raw `token` string, or default token (no token specified)

- **PCI Merchant Tokenization** (new):
  - `PublicClientResource` / `AsyncPublicClientResource` - uses separate
    public key (`pk_...`) authentication transport
  - `client.public_client.get_tokens_public_key()` → `TokensPublicKey`
    (`GET /public-client/tokens-public-key`)
  - `client.public_client.add_card(card_data, key_id, customer_id, redirect, webhook)`
    → `ClientTokenResponse` (`POST /public-client/tokens`)
  - `CardEncryption.encrypt(pem, card_dict)` - RSA-OAEP SHA-256 encryption
    utility (requires `pip install cryptography`)
  - `CardEncryption.validate_card_payload(card_dict)` - pre-encryption validation
  - `BMLConnect` now accepts `public_key="pk_..."` constructor argument
  - `client.public_client` is `None` when `public_key` is not provided

- **New models**:
  - `TokensPublicKey` - `key_id`, `public_key`, `.pem` property
  - `ClientTokenNextAction` - `url`, `client_side_token_id`
  - `ClientTokenResponse` - wraps `next_action`
  - `WebhookEvent` - parsed webhook notification body with `event_type`,
    `transaction_id`, `state`, `tokenisation_status`, etc.
  - `WebhookEventType` enum - `NOTIFY_TRANSACTION_CHANGE`,
    `NOTIFY_TOKENISATION_STATUS`
  - `TokenisationStatus` enum - `TOKENISATION_SUCCESS`, `TOKENISATION_FAILURE`

- **`TransactionState` enum expanded**:
  - `INITIATED` - payment created, QR not yet ready
  - `VOIDED` - payment reversed
  - `REFUND_REQUESTED` - refund under review
  - `REFUNDED` - refund completed
  - `AUTHORIZED` - pre-auth approved, funds not yet captured

- **`Transaction` model enriched** with all Redirect Method response fields:
  `can_refund_if_confirmed`, `can_incremental_partial_refund_if_confirmed`,
  `can_partial_refund_if_confirmed`, `can_void`, `available_balance`,
  `amount_as_decimal`, `amount_formatted`, `amount_fractional`,
  `amount_before_discount`, `amount_discounted`, `is_tap_to_pay`,
  `self_topup`, `on_hold`, `send_customer_email_receipt`, `external_import`,
  `billing_info_provided_via_api`, `payment_attempt_failure_url`,
  `refund_expiry_date`, `refund_transactions`, `refund_transaction_ids`,
  `parent_transaction_id`, `loop_count`, `rating`, `url_hash`, `vendor_url`,
  `external_id`, `external_source`, `preauthorized_amount`,
  `preauthorized_expiry_date`, `provider_display_name`, `eci_indicator`, `avsr`,
  `original_signature`, `security_word`, `attachments`, `custom_providers`,
  `payment_links`, `provider_history`, `history`, `payment_error_history`,
  `shift_id`, `remittance_id`, `implicit_dcc`.

- **New example files**:
  - `examples/direct_method.py` - QR and card direct payments with Flask
  - `examples/card_on_file.py` - tokenisation and recurring charge
  - `examples/pci_tokenization.py` - PCI Merchant Tokenization server-side

- **Transaction update** - `client.transactions.update(id, ...)` maps to
  `PATCH /public/transactions/{id}`. Updatable fields: `customerReference`,
  `localData`, `pnr`.

- **SMS sharing** - `client.transactions.send_sms(id, mobile)`.
  Rate-limited to once/min.

- **Email sharing** - `client.transactions.send_email(id, emails)`.
  Accepts string or list. Rate-limited to once/min.

- **Webhooks registration** - `client.webhooks.create(hook_url)` and
  `client.webhooks.delete(hook_url)`.

- **Company resource** - `client.company.get()` → `GET /public/me`.

- **Shops resource** - full CRUD for shops, products, categories, taxes,
  order fields, and custom fees.

- **Customers resource** - `list`, `create`, `get`, `update`, `delete`,
  `list_tokens`, `get_token`, `delete_token`, `charge`.

- **Context manager support** - both sync (`with`) and async (`async with`).

- **Webhook signature verification** - SHA-256 header scheme:
  - `SignatureUtils.verify_webhook_signature(nonce, timestamp, sig, api_key)`
  - `SignatureUtils.verify_webhook_headers(headers, api_key)`
  - `client.verify_webhook_signature(nonce, timestamp, sig)`
  - `client.verify_webhook_headers(headers)`

### Changed

- **`BMLConnect` constructor** - `app_id` is now optional; new `public_key`
  parameter for PCI tokenization.
- **`client.transactions`** renamed methods: `create`, `get`, `update`,
  `send_sms`, `send_email`, `list`, `create_v1`.
- **SDK split into modules** - `models.py`, `exceptions.py`, `signature.py`,
  `transport.py`, `resources.py`, `client.py`, `crypto.py`.
- Version bumped to `2.0.0`.

### Deprecated

- **`originalSignature` body field** - superseded by header-based SHA-256.
  Preserved in `SignatureUtils.verify_legacy_signature()` and
  `client.verify_legacy_webhook_signature()`.
- **`create_transaction()` / `get_transaction()` / `list_transactions()`** -
  aliases preserved; renamed to `create` / `get` / `list`.
- **`TransactionsResource.create_v1()`** - legacy v1 endpoint only.

### Removed

- **`SignatureUtils.generate_legacy_signature()` / `generate_signature()`** -
  now raises `NotImplementedError` with migration message.
- **`SignatureUtils.verify_webhook_payload()`** (HMAC-body scheme) - removed;
  replaced by header-based verification.
- `SignMethod` retained for export compatibility only; no longer used.

---

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
