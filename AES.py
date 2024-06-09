from Crypto.Cipher import AES
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDFExpand


class ENCRYPTION:
    def __init__(self, private_num):
        key_material = private_num.to_bytes(int(private_num.bit_length() / 8) + 1, "big")
        hkdf = HKDFExpand(hashes.SHA256(), 16, None)
        self.key = hkdf.derive(key_material)

    def encrypt(self, data):
        cipher = AES.new(self.key, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode('ascii'))
        return nonce, ciphertext, tag

    def decrypt(self, ciphertext):
        print(ciphertext)
        cipher = AES.new(self.key, AES.MODE_EAX, nonce=ciphertext[0])
        plaintext = cipher.decrypt(ciphertext[1])
        try:
            cipher.verify(ciphertext[2])
            print("The message is authentic:", plaintext)
            return plaintext
        except ValueError:
            print("Key incorrect or message corrupted")
            return False
