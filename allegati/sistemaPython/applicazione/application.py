import binascii
import datetime
import io
import random
import time
from threading import Thread

import numpy
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import pandas
from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util import Counter

#----------------------------------------------------------------------------------# 
#--------------------------------VARIABILI GLOBALI---------------------------------#
#----------------------------------------------------------------------------------#

autenticato = False
cf = ""
password = ""
cfCifr = ""
passwordCifr =""
brokerHost = "localhost"
port = 1883
Pid = 0
tempoMisurazioni = 5
pubKey = ""
symKey = b""
key_bytes = 16
storicoMessaggi = []

class misurationThread (Thread):
    def __init__ (self):
        Thread.__init__(self)
    def run(self):
        getMisuration() 

#----------------------------------------------------------------------------------# 
#------------------------------FUNZIONI CRITTAZIONE--------------------------------#
#----------------------------------------------------------------------------------#

def encrypt(message, pub_key):
   cipher = PKCS1_OAEP.new(pub_key)
   return cipher.encrypt(message)
def decrypt(ciphertext, priv_key):
   cipher = PKCS1_OAEP.new(priv_key)
   return cipher.decrypt(ciphertext)

# Takes as input a 32-byte key and an arbitrary-length plaintext and returns a
# pair (iv, ciphtertext). "iv" stands for initialization vector.
def symEncrypt(key, plaintext):
    assert len(key) == key_bytes

    # Choose a random, 16-byte IV.
    iv = Random.new().read(AES.block_size)

    # Convert the IV to a Python integer.
    iv_int = int(binascii.hexlify(iv), 16) 

    # Create a new Counter object with IV = iv_int.
    ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    # Encrypt and return IV and ciphertext.
    ciphertext = aes.encrypt(plaintext)
    return (iv, ciphertext)

# Takes as input a 32-byte key, a 16-byte IV, and a ciphertext, and outputs the
# corresponding plaintext.
def symDecrypt(key, iv, ciphertext):
    assert len(key) == key_bytes

    # Initialize counter for decryption. iv should be the same as the output of
    # encrypt().
    iv_int = int(iv.encode('hex'), 16) 
    ctr = Counter.new(AES.block_size * 8, initial_value=iv_int)

    # Create AES-CTR cipher.
    aes = AES.new(key, AES.MODE_CTR, counter=ctr)

    # Decrypt and return the plaintext.
    plaintext = aes.decrypt(ciphertext)
    return plaintext

#----------------------------------------------------------------------------------# 
#-----------------------------FUNZIONI COMUNICAZIONE-------------------------------#
#----------------------------------------------------------------------------------#

def pubblica(msgTopic, msgPayload, broker):
    msgPayload = str(hash(msgPayload)) + " HASH " + msgPayload
    publish.single(msgTopic, msgPayload, hostname=broker)

def separaMsg(msgPayload):
    coppia =  msgPayload.split(" HASH ")
    if(len(coppia) != 2):
        coppia[0] = -1
        coppia.append("")
    return coppia[0], coppia[1]

def isUntouched(msgPayload):
    hashSum, carico = separaMsg(msgPayload)
    if(len(carico) != 0 and hash(carico) == int(hashSum)):
        return True
    return False

#invio le credenziali al centro di controllo per vedere se sono corrette
def autenticazione():
    global cf, password, brokerHost,pubKey
    print("")
    client.unsubscribe("centroControllo/risposteRSA")
    cf = str(raw_input("Inserisca il suo codice fiscale "))
    password = str(raw_input("Inserisca password "))
    client.subscribe("centroControllo/risposte" + str(hash(cf)))
    client.subscribe("centroControllo/erroreAutenticazione")
    messaggio= cf + " ESCAPE " + password
    messaggio = encrypt(messaggio, pubKey)
    print("\ncrittazione eseguita")
    pubblica("centroControllo/richieste", messaggio + " ESCAPE " + pubKeyPers.exportKey('PEM'), brokerHost)
    print("messaggio inviato")

def getPubKey():
    #mi sottoscrivo al topic dove ricevere la chiave
    client.subscribe("centroControllo/risposteRSA")
    #pubblico una richieste per ottenere la chiave di comunicazione
    pubblica("centroControllo/richiesteRSA", "CLIENT HELLO", brokerHost)
    
def on_connect(client, userdata, flags, rc):
    global autenticato, cf, password
    if(autenticato):
        print("Autenticato")
    #se non mi sono autenticato provvedo a farlo
    else:
        getPubKey()
          
#quando ricevo un messaggio
def on_message(client, userdata, msg):
    global cf, autenticato, Pid, pubKey, symKey
    #print(msg.payload + ", " + msg.topic)
    #estraggo il contenuto
    messaggio = separaMsg(msg.payload)[1]
    corrotto = not isUntouched(msg.payload)
    #se il topic riguarda le risposte alle autenticazioni
    if(msg.topic == "centroControllo/risposteRSA" ):
        if(corrotto):
            getPubKey()
        else:
            pubKey = RSA.importKey(messaggio)
            autenticazione()
    
    elif(msg.topic=="centroControllo/erroreAutenticazione"):
        print("Errore nella richiesta, riprova")
        autenticazione()
    elif(msg.topic == "centroControllo/risposte" + str(hash(cf))):
        #cancello la sottoscrizione al topic (in ogni caso il cf sara scorretto o obsoleto)
        client.unsubscribe("centroControllo/risposte"+str(hash(cf)))
        if(corrotto):
            autenticazione()
        else:
            messaggio = decrypt(messaggio, privKeyPers)
            messaggio = messaggio.split(" ESCAPE ")
            #il primo valore del messaggio e un flag
            flag = int(messaggio[0])
            #se flag = 0 -> scorretto
            if flag == 0:
                print("Credenziali SCORRETTE")
                autenticazione()
            else:
                print("Credenziali corrette")
                #mi disiscrivo dal topic di errore di accesso
                client.unsubscribe("centroControllo/erroreAutenticazione")
                #salvo l'IDpaziente
                Pid = messaggio[1]
                #salvo la chiave simmetrica
                symKey = b"" + messaggio[2]
                #mi sottoscrivo al topic di segnalazione errori
                client.subscribe("centroControllo/segnalazione"+Pid) 
                #pongo il flag autenticato a True
                autenticato = True
                misurationThread.daemon = True
                misurationThread.start()
                
    elif(msg.topic=="centroControllo/segnalazione"+Pid):
        print("Rinvio i dati perche corrotti")
        messaggio = storicoMessaggi[-1] 
        (iv, ciphertext) = symEncrypt(symKey, messaggio)
        text = str(iv) + " ESCAPE " + str(ciphertext)
        pubblica("centroControllo/paziente" + Pid, text, brokerHost)

def getMisuration():
    global Pid, brokerHost, storicoMessaggi
    #genero i vari valori (nella realta li riceverei via bluethoot
    print("")
    controllo = raw_input("Premere un tasto qualsiasi per avviare la misurazione")
    print("Generazione valori")
    now = datetime.datetime.now()
    data = now.strftime("%Y-%m-%d")
    ora = now.strftime("%H:%M:%S")
    SP02 = random.randint(90, 99)
    FC = random.randint(50, 90)
    FR = random.randint(15, 21)
    PI = random.randint(4, 20)
    
    messaggio = data + " ESCAPE " + ora + " ESCAPE " + str(SP02) + " ESCAPE " + str(FC) + " ESCAPE " + str(FR) + " ESCAPE " + str(PI)
    storicoMessaggi.append(messaggio)
    (iv, ciphertext) = symEncrypt(symKey, messaggio)
    text = str(iv) + " ESCAPE " + str(ciphertext)
    pubblica("centroControllo/paziente" + Pid, text, brokerHost)
    time.sleep(tempoMisurazioni)
    getMisuration()
    
#----------------------------------------------------------------------------------# 
#-------------------------------------- MAIN --------------------------------------#
#----------------------------------------------------------------------------------#

#importo chiave pubblica
pubf = open('pubKeyClient.pem','r')
pubKeyPers = RSA.importKey(pubf.read())
pubf.close()

#importo chiave privata
privf = open('privKeyClient.pem','r')
privKeyPers = RSA.importKey(privf.read())
privf.close()

#inizializzo thread misurazione
misurationThread = misurationThread()

#MQTT
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(brokerHost, port, 60)

client.loop_forever()
