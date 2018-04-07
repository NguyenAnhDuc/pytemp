import base64
import random
import string
import typing

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

DEFAULT_MODULUS = 4096

RSAKey = typing.TypeVar('RSAKey')


class SimpleCrypto:
    aes_cipher = None
    public_key = None
    private_key = None
    aes_key = None

    def __init__(self, aes_key=None, public_key=None, private_key=None):
        """ A class to encrypt and decrypt using Asymmetrical encryption.
        All kwargs are optional.

        :param aes_key: AES key used for symmetric encryption
        :param public_key: Public RSA key used for asymmetric encryption
        :param private_key: Private RSA key used for asymmetric decryption
        """

        if aes_key:
            self.set_aes_key(aes_key)
        self.set_public_key(public_key)
        self.set_private_key(private_key)

    @staticmethod
    def _get_padding():
        return padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )

    @staticmethod
    def _random_string(n: int) -> str:
        return ''.join(random.SystemRandom().choice(
            string.ascii_uppercase + string.digits) for _ in range(n))

    @staticmethod
    def _generate_key() -> bytes:
        return Fernet.generate_key()

    def _generate_pass_phrase(self, n=255) -> str:
        return self._random_string(n)

    @staticmethod
    def _force_bytes(text: typing.Union[str, bytes]) -> bytes:
        try:  # Encode if not already done
            text = text.encode()
        except AttributeError:
            pass
        return text

    def make_rsa_keys(self, pass_phrase=None, bits=DEFAULT_MODULUS) -> typing.Tuple[bytes, bytes]:
        """ Create new rsa private and public keys

        :param pass_phrase: Optional RSA private key passphrase. Returns encrypted
        version if set
        :param bits: Bits for pycrypto's generate function. Safe to ignore.
        :rtype: tuple of string version of keys (private, public) """
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=bits,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        if pass_phrase:
            encryption_alg = serialization.BestAvailableEncryption(
                pass_phrase.encode()
            )
            _format = serialization.PrivateFormat.PKCS8
        else:
            encryption_alg = serialization.NoEncryption()
            _format = serialization.PrivateFormat.TraditionalOpenSSL

        private = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=_format,
            encryption_algorithm=encryption_alg
        )

        public = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private, public

    def make_rsa_keys_with_pass_phrase(self, bits=DEFAULT_MODULUS) -> typing.Tuple[bytes, bytes, str]:
        """ Wrapper around make_rsa_keys that also generates a passphrase

        :param bits: Bits for pycrypto's generate function. Safe to ignore.
        :rtype: tuple (private, public, passphrase) """
        passphrase = self._generate_pass_phrase()
        private, public = self.make_rsa_keys(pass_phrase=passphrase, bits=bits)
        return private, public, passphrase

    def rsa_encrypt(self, text: typing.Union[str, bytes], use_base64=False) -> bytes:
        """ Convert plain text to ciphertext

        :param text: Plaintext to encrypt. Accepts str or bytes
        :param use_base64: set True to return a base64 encoded unicode string
        (just for convenience)
        :type use_base64: Boolean
        :rtype: cipher_text bytes
        """
        text = self._force_bytes(text)
        if not self.public_key:
            raise KeyError("missing RSA public Exception")
        cipher_text = self.public_key.encrypt(
            text,
            self._get_padding()
        )
        if use_base64 is True:
            cipher_text = base64.b64encode(cipher_text)
        return cipher_text

    def rsa_decrypt(self, ciphertext: bytes, use_base64=False) -> bytes:
        """ Convert ciphertext into plaintext

        :param ciphertext: Ciphertext to decrypt
        :param use_base64: set True to return a base64 encoded unicode string
        (just for convenience)
        :type use_base64: Boolean
        :rtype: plaintext bytes
        """

        if use_base64 is True:
            ciphertext = base64.b64decode(ciphertext)
        if not self.private_key:
            raise KeyError("missing RSA Private Exception")
        plaintext = self.private_key.decrypt(
            ciphertext,
            self._get_padding()
        )
        return plaintext

    def set_private_key(self, private_key: typing.Union[bytes, str, RSAKey], passphrase=None) -> RSAKey:
        """ Set private key

        :param private_key: String or RSAPrivateKey object
        :param passphrase: Optional passphrase for encrypting the RSA private key
        :rtype: private key
        """
        if isinstance(private_key, (bytes, str)):
            private_key = self._force_bytes(private_key)
            if passphrase:
                passphrase = self._force_bytes(passphrase)
            self.private_key = serialization.load_pem_private_key(
                private_key,
                password=passphrase,
                backend=default_backend()
            )
        else:
            self.private_key = private_key
        return self.private_key

    def set_public_key(self, public_key: typing.Union[bytes, str, RSAKey]) -> RSAKey:
        """ Set public key

        :param public_key: String or RSAPublicKey object
        :rtype: public key
        """
        if isinstance(public_key, (bytes, str)):
            public_key = self._force_bytes(public_key)
            self.public_key = serialization.load_pem_public_key(
                public_key,
                backend=default_backend()
            )
        else:
            self.public_key = public_key
        return self.public_key

    def set_aes_key(self, aes_key: bytes):
        self.aes_key = aes_key
        self.aes_cipher = Fernet(aes_key)

    def set_aes_key_from_encrypted(self, cipher_text: bytes, use_base64=False):
        """ Set aes_key from an encrypted key
        A shortcut method for receiving a AES key that was encrypted for our
        RSA public key

        :param cipher_text: Encrypted version of the key (bytes or base64 string)
        :param use_base64: If true, decode the base64 string
        """
        if use_base64 is True:
            cipher_text = base64.b64decode(cipher_text)
        aes_key = self.rsa_decrypt(cipher_text)
        self.set_aes_key(aes_key)

    def get_encrypted_aes_key(self,
                              public_key: typing.Union[bytes, str, RSAKey],
                              use_base64=False) -> bytes:
        """ Get encrypted aes_key using specified public_key
        A shortcut method for sharing a AES key.

        :param public_key: The public key we want to encrypt for
        :param use_base64: Will result in the returned key to be base64 encoded
        :rtype: encrypted key (bytes or base64 string"""
        public_asym = SimpleCrypto(public_key=public_key)
        encrypted_key = public_asym.rsa_encrypt(self.aes_key)
        if use_base64 is True:
            encrypted_key = base64.b64encode(encrypted_key)
        return encrypted_key

    def make_aes_key(self) -> bytes:
        """ Generate a new AES key

        :rtype: AES key string
        """
        key = self._generate_key()
        self.set_aes_key(key)
        return key

    def encrypt(self, plaintext: typing.Union[str, bytes]) -> bytes:
        """ Encrypt text using AES encryption.
        Requires public_key and aes_key to be set. aes_key may be generated with
        AsymCrypt.make_aes_key if you do not already have one.

        :param plaintext: text to encrypt
        :rtype: ciphertext string
        """
        plaintext = self._force_bytes(plaintext)
        if not self.aes_cipher:
            raise KeyError("missing AES exception")
        return self.aes_cipher.encrypt(plaintext)

    def decrypt(self, text: bytes):
        """ Decrypt ciphertext using AES encryption.
        Requires private_key and aes_key to be set. aes_key may have been
        generated with AsymCrypt.make_aes_key which should have been done at
        time or encryption.

        :param text: ciphertext to decrypt
        :rtype: decrypted text string
        """
        if not self.aes_cipher:
            raise KeyError("missing AES exception")
        return self.aes_cipher.decrypt(text)


# --------------------------- TEST ---------------------------
if __name__ == '__main__':

    is_generates_key = False  # True
    if is_generates_key:
        print('----------------------generates key for RSA---------------------------')
        pri, pub = SimpleCrypto().make_rsa_keys()
        with open('rsa_key/private.key', 'w') as private_file:
            private_file.write(pri.decode('utf-8'))
        with open('rsa_key/public.key', 'w') as public_file:
            public_file.write(pub.decode('utf-8'))

    print('----------------------CRYPTO RSA---------------------------')
    ac = SimpleCrypto(private_key=open('rsa_key/private.key', 'r').read(),
                      public_key=open('rsa_key/public.key', 'r').read())
    bs = bytes("t_crypto = SimpleCrypto('1234567', algorithm)aaaaaaaaaa"
               "aeirgneiruhgvniernvinveliuhvneiluhvnieluvnhinvhaaaaaaaaa"
               "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaavlaeiruhaleirbaeirb"
               "liubariban;oribna;eoribnae;oribnaeo;ribnaero;binaero;bin", encoding='utf-8')
    t_text = ac.rsa_encrypt(bs)
    print(t_text)
    print(str(ac.rsa_decrypt(t_text), encoding='utf-8'))

    print('----------------------CRYPTO AES---------------------------')
    ac = SimpleCrypto()
    key = ac.make_aes_key()
    print("CRYPTO AES by key:", key)
    ac.set_aes_key(key)
    t_text = ac.encrypt(bs)
    print(t_text)
    print(ac.decrypt(t_text))
