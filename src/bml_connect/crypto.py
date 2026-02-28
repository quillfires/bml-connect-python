"""
BML Connect SDK - Card Encryption Utility
==========================================

Provides RSA-OAEP encryption for PCI Merchant Tokenization.

Used by the server-side component of the PCI Merchant Tokenization flow.
Card data is encrypted with the BML-provided RSA public key before being
sent to ``POST /public-client/tokens``.

.. note::
    Requires the ``cryptography`` package::

        pip install cryptography

Usage::

    from bml_connect import BMLConnect, CardEncryption, Environment

    with BMLConnect(api_key="sk_...", public_key="pk_...",
                    environment=Environment.SANDBOX) as client:

        # 1. Always fetch the latest encryption key - it can rotate
        enc_key = client.public_client.get_tokens_public_key()

        # 2. Encrypt card data
        card_b64 = CardEncryption.encrypt(enc_key.pem, {
            "cardNumberRaw":  "4111111111111111",
            "cardVDRaw":      "123",
            "cardExpiryMonth": 12,
            "cardExpiryYear":  29,
        })

        # 3. Submit encrypted data
        result = client.public_client.add_card(
            card_data=card_b64,
            key_id=enc_key.key_id,
            customer_id="CUSTOMER_ID",
            redirect="https://yourapp.com/tokenisation-callback",
        )

        # 4. Redirect customer for 3DS
        redirect_to(result.next_action.url)
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict


class CardEncryption:
    """RSA-OAEP encryption helpers for PCI Merchant Tokenization.

    Requires the ``cryptography`` package (``pip install cryptography``).
    This package is an optional dependency - it is only needed when using
    the PCI Merchant Tokenization flow.
    """

    @staticmethod
    def _load_crypto() -> Any:
        """Import cryptography lazily so it is optional for other flows."""
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding

            return hashes, serialization, padding
        except ImportError as exc:
            raise ImportError(
                "The 'cryptography' package is required for PCI Merchant Tokenization.\n"
                "Install it with:  pip install cryptography"
            ) from exc

    @staticmethod
    def encrypt(public_key_pem: str, card_data: Dict[str, Any]) -> str:
        """Encrypt card data with RSA-OAEP (SHA-256) and return Base64 ciphertext.

        This mirrors the algorithm used in the BML documentation's JavaScript
        example::

            crypto.publicEncrypt(
                { key: pem, padding: RSA_PKCS1_OAEP_PADDING, oaepHash: 'sha256' },
                Buffer.from(JSON.stringify(cardData))
            ).toString('base64')

        Args:
            public_key_pem: PEM-formatted RSA public key (SPKI).  Use
                :attr:`.TokensPublicKey.pem` which adds the header/footer
                automatically if the raw key was returned without them.
            card_data: Dict with the following keys:

                - ``cardNumberRaw`` (str) - 16-digit card number
                - ``cardVDRaw`` (str) - 3 or 4 digit CVV/CVC
                - ``cardExpiryMonth`` (int) - 1–12
                - ``cardExpiryYear`` (int) - 2-digit year, e.g. ``29``

        Returns:
            Base64-encoded RSA-OAEP ciphertext string ready to send as
            ``cardData`` in ``POST /public-client/tokens``.

        Raises:
            ImportError: If the ``cryptography`` package is not installed.
            ValueError: If the PEM key is malformed.

        Example::

            from bml_connect import CardEncryption

            card_b64 = CardEncryption.encrypt(enc_key.pem, {
                "cardNumberRaw":   "4111111111111111",
                "cardVDRaw":       "123",
                "cardExpiryMonth": 12,
                "cardExpiryYear":  29,
            })
        """
        hashes, serialization, padding = CardEncryption._load_crypto()

        plaintext = json.dumps(card_data, separators=(",", ":")).encode("utf-8")

        pem_bytes = public_key_pem.encode("utf-8")
        public_key = serialization.load_pem_public_key(pem_bytes)

        ciphertext = public_key.encrypt(
            plaintext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

        return base64.b64encode(ciphertext).decode("utf-8")

    @staticmethod
    def validate_card_payload(card_data: Dict[str, Any]) -> None:
        """Validate card data dict before encryption.

        Raises:
            ValueError: If required fields are missing or invalid.
        """
        required = ("cardNumberRaw", "cardVDRaw", "cardExpiryMonth", "cardExpiryYear")
        missing = [f for f in required if f not in card_data]
        if missing:
            raise ValueError(f"Missing required card fields: {missing}")

        number = str(card_data["cardNumberRaw"]).replace(" ", "")
        if not number.isdigit() or not (13 <= len(number) <= 19):
            raise ValueError("cardNumberRaw must be 13–19 digits")

        cvv = str(card_data["cardVDRaw"])
        if not cvv.isdigit() or not (3 <= len(cvv) <= 4):
            raise ValueError("cardVDRaw must be 3 or 4 digits")

        month = int(card_data["cardExpiryMonth"])
        if not 1 <= month <= 12:
            raise ValueError("cardExpiryMonth must be 1–12")


__all__ = ["CardEncryption"]
