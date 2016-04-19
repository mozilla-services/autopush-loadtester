import base64
import time
import hashlib

import ecdsa
import logging
from jose import jws


logger = logging.getLogger()


class VapidException(Exception):
    pass


class Vapid(object):
    """Minimal VAPID signature generation library."""
    _private_key = None
    _public_key = None
    _hasher = hashlib.sha256

    def __init__(self, private_key_file=None, private_key=None):
        """Initialize VAPID using an optional file containing a private key
        in PEM format.

        :param private_key_file: The name of the file containing the
        private key

        """
        if private_key_file:
            with open(private_key_file) as f:
                private_key = f.read()
        if private_key:
            try:
                if "BEGIN EC" in private_key:
                    self._private_key = ecdsa.SigningKey.from_pem(private_key)
                else:
                    self._private_key = \
                        ecdsa.SigningKey.from_der(
                            base64.standard_b64decode(
                                private_key + '===='[len(private_key) % 4:]))
            except Exception, exc:
                logger.error("Could not open private key file: %s", repr(exc))
                raise VapidException(exc)
            self._publicKey = self._private_key.get_verifying_key()

    @property
    def private_key(self):
        """The private half of the VAPID ECDSA key."""
        if not self._private_key:
            raise VapidException(
                "No private key defined. Please import or generate a key.")
        return self._private_key

    @private_key.setter
    def private_key(self, value):
        self._private_key = value

    @property
    def public_key(self):
        """The public half of the VAPID ECDSA key. """
        if not self._public_key:
            self._public_key = self.private_key.get_verifying_key()
        return self._public_key

    def generate_keys(self):
        """Generate a valid ECDSA Key Pair."""
        self.private_key = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
        # init the public key using the above property function
        self.public_key

    def save_private_key(self, key_file):
        """Save the private key to a PEM file."""
        with open(key_file, "w") as f:
            if not self._private_key:
                self.generate_keys()
            f.write(self._private_key.to_pem())

    def save_public_key(self, key_file):
        """Save the public key to a PEM file.

        :param key_file: The name of the file to save the public key

        """
        with open(key_file, "w") as f:
            f.write(self.public_key.to_pem())

    def _encode(self, str):
        return base64.urlsafe_b64encode(str).strip('=')

    def _decode(self, str):
        return base64.urlsafe_b64decode(str + '===='[:len(str) % 4])

    def validate(self, token):
        """Sign a dashboard valdiation token using the private key.

        :token: is the token value provided from the developer dashboard.

        """
        sig = self.private_key.sign(token, hashfunc=self._hasher)
        token = self._encode(sig).strip('=')
        return token

    def verify_token(self, sig, token):
        """Verify the validation token has been signed correctly.

        This funciton replicates what the Developer dashboard does to
        verify that the token has been signed with the private key. This
        funciton is used only for debugging and testing purposes.

        :sig: the token signature value
        :token: the original token

        """
        hsig = self._decode(sig)
        return self.public_key.verify(hsig, token,
                                      hashfunc=self._hasher)

    def sign(self, claims, crypto_key=None):
        """Sign a set of claims.

        :param claims: JSON object containing the JWT claims to use.
        :param crypto_key: Optional existing crypto_key header content. The
            vapid public key will be appended to this data.
        :returns result: a hash containing the header fields to use in
            the subscription update.

        """
        if not claims.get('exp'):
            claims['exp'] = int(time.time()) + 86400
        if not claims.get('aud'):
            raise VapidException(
                "Missing 'aud' from claims. "
                "'aud' is your site's URL.")
        if not claims.get('sub'):
            raise VapidException(
                "Missing 'sub' from claims. "
                "'sub' is your admin email as a mailto: link.")
        sig = jws.sign(claims, self.private_key, algorithm="ES256")
        pkey = 'p256ecdsa='
        pkey += self._encode(
            self.public_key.to_string()).strip('=')
        if crypto_key:
            crypto_key = crypto_key + ',' + pkey
        else:
            crypto_key = pkey

        return {"Authorization": "Bearer " + sig.strip('='),
                "Crypto-Key": crypto_key}
