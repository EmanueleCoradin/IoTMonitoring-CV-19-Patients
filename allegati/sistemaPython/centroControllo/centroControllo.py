import binascii
import random
from threading import Thread

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import telebot
from Crypto import Random
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util import Counter

import mysql.connector as dbm
import time

#------------------------------------------------------------------------------# 
#------------------------------VARIABILI GLOBALI-------------------------------#
#------------------------------------------------------------------------------#

userDB = "root"
passwordDB = ""
hostDB = "localhost"
db = "monitoraggioDB"
brokerHost = "localhost"
port = 1883
misMatr = []
costAggiornamento = 5
counter = 0
pubKey = ""
privKey = ""
# AES supports multiple key sizes: 16 (AES128), 24 (AES192), or 32 (AES256).
key_bytes = 16
symArray = []
connessione = dbm.connect(host=hostDB, user=userDB, passwd = passwordDB, database=db)
cursore = connessione.cursor(buffered=True)

bot = telebot.TeleBot('1211592304:AAGI5Saz_Xtas8p4CqVHsnLrXWyAE1SjLlc')

class teleThread (Thread):
    global bot
    def __init__ (self):
        Thread.__init__(self)
    def run(self):
        bot.polling() 

#------------------------------------------------------------------------------# 
#--------------------------- FUNZIONI BOT TELEGRAM ----------------------------#
#------------------------------------------------------------------------------#

def extract_unique_code(text):
    # Extracts the unique_code from the sent /start command.
    return text.split(" ")[1] if len(text.split()) > 1 else None
def extract_password(text):
    # Extracts the pass from the sent /start command.
    return text.split(" ")[2] if len(text.split()) > 2 else None
def in_storage(unique_code, password): 
    # Should check if a unique code exists in storage
    #query per ricavare l'IDpaziente
    query = "SELECT count(*) as cont FROM MEDICO WHERE CF = \"" + unique_code + "\" AND PASSWORD = \""+password+"\""
    #eseguo la query
    cursore.execute(query)
    #inizializzo check
    check = 0
    #ciclo sui risultati(sara sempre alpiu 1)
    for (cont) in cursore:
        check = cont
    if check == 0: 
        return False
    else:
        return True

def get_username_from_storage(unique_code, password): 
    if not in_storage(unique_code,password):
        return False
    #query per ricavare l'IDpaziente
    query = "SELECT MEDICO.cognome FROM MEDICO WHERE CF = \"" + unique_code + "\""
    #eseguo la query
    cursore.execute(query)
    #inizializzo l'id a -1
    username = ""
    #ciclo sui risultati(sara sempre alpiu 1)
    for cognome in cursore:
        username = str(cognome[0])
    return username

def save_chat_id(chat_id, unique_code):
    global connessione
    query = "UPDATE MEDICO SET idTelegram = " + str(chat_id) + " where CF = \"" + unique_code + "\""
    cursore = connessione.cursor(buffered=True)
    #eseguo la query
    cursore.execute(query) 
    connessione.commit()
    
@bot.message_handler(commands=['start'])
def send_welcome(message):
    unique_code = extract_unique_code(message.text)
    password = extract_password(message.text)
    if unique_code is not None and password is not None: # if the '/start' command contains a unique_code
        username = get_username_from_storage(unique_code, password)
        if username: # if the username exists in our database
            save_chat_id(message.chat.id, unique_code)
            reply = "Buongiorno dottor " + username + ". La avvisero nel caso la saturazione di un paziente scendesse sotto il 92%"
        else:
            reply = "Credenziali scorrette. La invito a riprovare."
    else:
        reply = "Inserisca 'codiceFiscale password' a fianco di /start, per favore"
    bot.reply_to(message, reply)

#------------------------------------------------------------------------------# 
#--------------------------- FUNZIONI CRITTOGRAFIA ----------------------------#
#------------------------------------------------------------------------------#

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

#------------------------------------------------------------------------------# 
#------------------------------- FUNZIONI MQTT --------------------------------#
#------------------------------------------------------------------------------#

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

def on_connect(client, userdsata, flags, rc):
    print("")
    print("-----------------------------")
    print("---------- Connesso ---------")
    print("-----------------------------")
    print("")
    client.subscribe("centroControllo/richieste")
    client.subscribe("centroControllo/richiesteRSA")
   
#se ricevo un messaggio 
def on_message(client, userdata, msg):
    global connessione, counter, misMatr, pubKey, privKey, bot
    
    try: 
        cursore = connessione.cursor(buffered=True)
        messaggio = separaMsg(msg.payload)[1]
        messaggio = messaggio.split(" ESCAPE ")
        corrotto = not isUntouched(msg.payload)
        #se il messaggio arriva da richiesteRSA, allora spedisco la chiave pubblica
        if(msg.topic == "centroControllo/richiesteRSA"):
            pubblica("centroControllo/risposteRSA", pubKey.exportKey('PEM'), brokerHost)
            print("Chiave inviata")
        #se il messaggio arriva dalle richieste -> devo controllare credenziali
        elif(msg.topic == "centroControllo/richieste"):
            if(not corrotto):
                #estraggo il codice fiscale e la password
                print("\nHo ricevuto credenziali")
                pubKeyClient = RSA.importKey(messaggio[1])
                messaggio = messaggio[0]
                print("decritto le credenziali")
                messaggio = decrypt(messaggio, privKey)
                messaggio = messaggio.split(" ESCAPE ")
                cf = messaggio[0]
                pPass = messaggio[1]
                #query per ricavare l'IDpaziente
                query = "SELECT IDpaziente FROM PAZIENTE WHERE CF = \"" + cf + "\" AND password = \"" + pPass + "\""
                #eseguo la query
                cursore.execute(query)
                #inizializzo l'id a -1
                Pid = -1
                #ciclo sui risultati(sara sempre alpiu 1)
                for (IDpaziente) in cursore:
                    Pid = int(IDpaziente[0])
                output = ""
                #se Pid = -1 -> non sono mai entrato nel ciclo -> le credenziali sono scorrette
                if(Pid == -1):
                    #stampo il messaggio sulla console
                    print("Credenziali " + cf + " " + pPass + " sono SCORRETTE")
                    #scrivo al client che le credenziali sono sbagliate (il primo valore e 0)
                    output = "0 ESCAPE -1"
                #altrimenti le credenziali sono corrette
                else:
                    #le stampo sulla console
                    print("Credenziali " + cf + " " + pPass + " sono corrette")
                    #mi sottoscrivo al topic col quale ricevero i valori
                    client.subscribe("centroControllo/paziente" + str(Pid))
                    #scrivo al client che le credenziali sono corrette e gli invio il Pid
                    output = "1 ESCAPE " + str(Pid) + " ESCAPE " + str(symArray[Pid])
                output = encrypt(output, pubKeyClient)
                pubblica("centroControllo/risposte" + str(hash(cf)), output, brokerHost)    
                connessione.commit()
            else:
                print("Credenziali corrotte")
                time.sleep(10)
                pubblica("centroControllo/erroreAutenticazione", "ERRORE", brokerHost)
            
        elif ("centroControllo/paziente") in msg.topic:
            print("\nelaborazione dati paziente")
            Pid = msg.topic[24:]
            print("Pid: " + Pid)
            iv = b"" + messaggio[0]
            ciphertext = b"" + messaggio[1]
            if(corrotto):
                print("Messaggio corrotto. Chiedo il reinvio")
                pubblica('centroControllo/segnalazione'+Pid, "Messaggio corrotto", brokerHost)
            else:
                messaggio = symDecrypt(symArray[int(Pid)], iv, ciphertext)
                messaggio = str(messaggio)
                messaggio = messaggio.split(" ESCAPE ")
                data = messaggio[0]
                ora = messaggio[1]
                SP02 = messaggio[2]
                FC = messaggio[3]
                FR = messaggio[4]
                PI = messaggio[5]
                misMatr.append([data, ora, SP02, FC, FR, PI, Pid])
                counter+=1
                #se SP02 e <= 92 devo inviare un messaggio al medico su telegram
                if int(SP02) <= 92:
                    query = "SELECT M.idTelegram, P.nome, P.cognome FROM PAZIENTE P INNER JOIN MEDICO M ON P.IDmedico = M.IDmedico WHERE P.IDpaziente = " + str(Pid)
                    cursore.execute(query)
                    chat_id = 0
                    nomeP = ""
                    cognomeP = ""
                    for row in cursore:
                        chat_id = row[0]
                        nomeP = row[1]
                        cognomeP = row[2]
                    bot.send_message(chat_id, "Il paziente " + nomeP + " " + cognomeP + " ha lo SP02 al " + SP02 + "%")
                if counter > costAggiornamento:
                    counter = 0
                    print("\nInserendo dati nel database")
                    query = "INSERT INTO MISURAZIONE(data, ora, SP02, FC, FR, PI, IDpaziente) VALUES"
                    for row in misMatr:
                        query+="(\""+ row[0] + "\", \"" + row[1] + "\", " + row[2] + ", " + row[3] + ", " + row[4] + ", " + row[5] + ", " + row[6] + "),"
                    query = query[:-1]
                    cursore.execute(query)
                    connessione.commit()
                    cursore.close()
                    print("inserimento completato")
                    misMatr = []
    #gestione delle eccezioni
    except dbm.Error as err:
        print("Errore nell'esecuzione della query: {}".format(err))
        print("Invio messaggio di errore")
        pubblica('centroControllo/segnalazione'+Pid, "Messaggio corrotto", brokerHost)


def on_disconnect():
    print()
    print("-----------------------------")
    print("-------- Disconnesso --------")
    print("-----------------------------")
    print()

#------------------------------------------------------------------------------# 
#----------------------------------- MAIN -------------------------------------#
#------------------------------------------------------------------------------#

thread = teleThread()
thread.daemon = True
thread.start()

#importo chiave pubblica
pubf = open('pubKey.pem','r')
pubKey = RSA.importKey(pubf.read())
pubf.close()

#importo chiave privata
privf = open('privKey.pem','r')
privKey = RSA.importKey(privf.read())
privf.close()

query = "SELECT count(*) as nPazienti FROM PAZIENTE"
#eseguo la query
cursore.execute(query)
#inizializzo l'id a -1
numP = -1
#ciclo sui risultati(sara sempre alpiu 1)
for (nPazienti) in cursore:
    numP = int(nPazienti[0])
print("sono presenti " + str(numP) + " pazienti")
for i in range(numP):
    symArray.append(Random.new().read(key_bytes))

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_disconnect = on_disconnect
client.connect(brokerHost, port, 600)
print("Centro di controllo attivo")

client.loop_forever()
