# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This project mostly adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html);

## [1.1.1] - 2026-02-27

### 🔧 Fixed

- Migrated to Poetry for dependency management and lockfile
- Added aiohttp and requests as explicit dependencies
- Fixed all mypy type errors in client.py
- Fixed flake8 lint errors
- SDK version now reads automatically from package metadata
- Dropped EOL Python 3.7/3.8 support, minimum is now 3.9

## [1.1.0] - 2025-07-15

### 🔧 Fixed

- **BREAKING**: Fixed signature generation to comply with official BML Connect API specification
- Signature now uses only `amount`, `currency`, and `apiKey` parameters as per BML documentation
- Corrected parameter order in signature string: `amount={amount}&currency={currency}&apiKey={api_key}`
- Webhook signature verification now uses correct parameter subset

### 🚨 Breaking Changes

- Signature generation method has been updated to match BML Connect specification
- Previous signatures generated with additional parameters will no longer work
- Applications using this SDK will need to regenerate signatures after upgrade

### 📝 Documentation

- Improved README structure and clarity

---

# Release Notes - v1.1.0

## 🎯 What's New

This release contains a **critical fix** for signature generation that ensures full compatibility with the Bank of Maldives Connect API specification.

## 🔴 Important: Breaking Changes

**This is a breaking change release.** If you're upgrading from a previous version:

1. **Regenerate all signatures** - Previous signatures will no longer work
2. **Update webhook verification** - Webhook signature verification now uses the correct parameters
3. **Test thoroughly** - Verify all payment flows in sandbox before deploying to production

## 🛠 What Was Fixed

### Signature Generation Issue

Previous versions included additional parameters in signature generation that weren't part of the official BML Connect specification. This caused signature mismatches and authentication failures.

**Before (Incorrect):**

```python
# Used additional parameters like localId, customerReference, etc.
signature_string = f"amount={amount}&currency={currency}&localId={localId}&apiKey={api_key}"
```

**After (Correct):**

```python
# Uses only the 3 required parameters as per BML specification
signature_string = f"amount={amount}&currency={currency}&apiKey={api_key}"
```

## 🔍 Technical Details

This fix addresses the signature generation to match the exact specification from BML Connect API documentation:

- **MD5 Method**: `md5('amount=2000&currency=MVR&apiKey=mysecretkey').digest('base64')`
- **SHA1 Method**: `sha1('amount=2000&currency=MVR&apiKey=mysecretkey').digest('hex')`

## 📋 Recommended Actions

1. **Backup your current implementation** before upgrading
2. **Test in sandbox environment** thoroughly
3. **Update to this version** during a maintenance window
4. **Monitor payment flows** after deployment
5. **Contact BML support** if you encounter any issues

## 💡 Why This Change Was Necessary

The previous implementation included additional parameters that weren't part of the official BML Connect signature specification. This caused:

- Authentication failures
- Webhook verification issues
- Incompatibility with BML's server-side validation

This fix ensures 100% compatibility with the Bank of Maldives Connect API specification.

## 🆘 Support

If you encounter any issues after upgrading:

1. Check the [GitHub Issues](https://github.com/quillfires/bml-connect-python/issues)
2. Review the updated documentation
3. Test in sandbox environment first
4. Contact BML support for API-specific issues
