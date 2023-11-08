#https://cryptobook.nakov.com/asymmetric-key-ciphers/rsa-encrypt-decrypt-examples
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii

def encrypt(message, pub_key):
   cipher = PKCS1_OAEP.new(pub_key)
   return cipher.encrypt(message)

def decrypt(ciphertext, priv_key):
   cipher = PKCS1_OAEP.new(priv_key)
   return cipher.decrypt(ciphertext)

#generazione delle chiavi 
keyPair = RSA.generate(2048)

#scrivo la chiave privata su file
privf = open('privKey.pem','wb')
privf.write(keyPair.exportKey('PEM'))
privf.close()

#estraggo la chiave pubblica e la scrivo su file
pubKey = keyPair.publickey()
pubf = open('pubKey.pem','wb')
pubf.write(pubKey.exportKey('PEM'))
pubf.close()

#stampo le chiavi su terminale
'''
print(f"Public key:  (n={hex(pubKey.n)}, e={hex(pubKey.e)})")
pubKeyPEM = pubKey.exportKey()
print(pubKeyPEM.decode('ascii'))

print(f"Private key: (n={hex(pubKey.n)}, d={hex(keyPair.d)})")
privKeyPEM = keyPair.exportKey()
print(privKeyPEM.decode('ascii'))
'''
