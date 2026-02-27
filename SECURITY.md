# Security Policy

## Supported Versions

Only the latest release of `bml-connect-python` receives security fixes.
If you are on an older version, please upgrade before reporting.

| Version | Supported |
|---|---|
| Latest (1.x) | ✅ |
| Older versions | ❌ |

---

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

If you discover a security issue, including but not limited to credential exposure, signature bypass, improper input validation, or dependency vulnerabilities, please report it privately by emailing:

**fayaz.quill@gmail.com**

Include in your report:

- A description of the vulnerability
- Steps to reproduce it
- The potential impact
- Your suggested fix if you have one (optional but appreciated)

You will receive a response within **48 hours** acknowledging receipt. If the issue is confirmed, a fix will be prioritised and a patched release issued as soon as possible. You will be credited in the changelog unless you prefer to remain anonymous.

---

## Scope

This policy covers the `bml-connect-python` SDK itself. It does not cover:

- The Bank of Maldives Connect API - report API vulnerabilities directly to BML at [info@bml.com.mv](mailto:info@bml.com.mv)
- Third-party dependencies (`requests`, `aiohttp`) - report those to their respective maintainers
- Your own application code that uses this SDK

---

## Security Notes for Users

**API keys and app IDs** - never hardcode credentials in source code. Use environment variables:

```python
import os
from bml_connect import BMLConnect, Environment

client = BMLConnect(
    api_key=os.environ["BML_API_KEY"],
    app_id=os.environ["BML_APP_ID"],
    environment=Environment.PRODUCTION,
)
```

**Webhook verification** - always verify webhook signatures before processing payloads. The SDK provides `verify_webhook_signature()` for this. Never skip it.

```python
if not client.verify_webhook_signature(payload, payload.get("signature")):
    return {"error": "Invalid signature"}, 403
```

**Dependencies** - keep your installed version of `bml-connect-python` up to date. Check for new releases at [pypi.org/project/bml-connect-python](https://pypi.org/project/bml-connect-python/).
