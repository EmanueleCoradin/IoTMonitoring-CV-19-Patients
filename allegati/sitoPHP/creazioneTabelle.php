<?php 

#----------------------------------------------------------------------#
#-------------------INIZIALIZZO CONNESSIONE DATABASE ------------------#
#----------------------------------------------------------------------#
$conn = 0;

include 'DBconnection.php';

#----------------------------------------------------------------------#
#------------------------- INIZIALIZZO TABELLE ------------------------#
#----------------------------------------------------------------------#

#-------------------------- TABELLA STATO  ----------------------------#
$sql="
    CREATE TABLE `STATO` (
        `IDstato` int(11) NOT NULL,
        `descrizione` varchar(32) NOT NULL,
        PRIMARY KEY(`IDstato`),
    )";

    $result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}

#------------------------ TABELLA STRUTTURA ---------------------------#

$sql="
    CREATE TABLE `STRUTTURA` (
    `IDstruttura` int(11) NOT NULL,
    `nome` varchar(32) NOT NULL,
    `via` varchar(32) NOT NULL,
    `numeroCivico` int(11) NOT NULL,
    `citta` varchar(32) NOT NULL,
    `provincia` varchar(32) NOT NULL,
    `regione` varchar(32) NOT NULL,
    `cap` varchar(5) NOT NULL,
    PRIMARY KEY(`IDstruttura`),
)";

$result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}

#-------------------------- TABELLA MEDICO  ----------------------------#

$sql="
CREATE TABLE `MEDICO` (
  `IDmedico` int(11) NOT NULL,
  `CF` varchar(32) NOT NULL,
  `nome` varchar(32) NOT NULL,
  `cognome` varchar(32) NOT NULL,
  `via` tinytext NOT NULL,
  `numeroCivico` int(11) NOT NULL,
  `citta` varchar(32) NOT NULL,
  `provincia` varchar(32) NOT NULL,
  `regione` varchar(32) NOT NULL,
  `cap` varchar(5) NOT NULL,
  `dataNascita` date NOT NULL,
  `sesso` varchar(1) NOT NULL,
  `email` tinytext NOT NULL,
  `password` varchar(32) NOT NULL,
  `idTelegram` int(11) DEFAULT NULL,
  PRIMARY KEY(`IDmedico`)
)";

$result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}

#-------------------------- TABELLA PAZIENTE  ----------------------------#

$sql="
CREATE TABLE `PAZIENTE` (
  `IDpaziente` int(11) NOT NULL,
  `CF` varchar(32) NOT NULL,
  `nome` varchar(32) NOT NULL,
  `cognome` varchar(32) NOT NULL,
  `stato` varchar(32) DEFAULT NULL,
  `via` tinytext NOT NULL,
  `numeroCivico` int(11) NOT NULL,
  `citta` varchar(32) NOT NULL,
  `provincia` varchar(32) NOT NULL,
  `regione` varchar(32) NOT NULL,
  `cap` varchar(5) NOT NULL,
  `dataNascita` date NOT NULL,
  `sesso` varchar(10) NOT NULL,
  `dataTrasferimento` date DEFAULT NULL,
  `email` tinytext NOT NULL,
  `password` varchar(32) NOT NULL,
  `cvIndex` int(11) DEFAULT NULL,
  `IDmedico` int(11) NOT NULL,
  `IDstruttura` int(11) DEFAULT NULL,
  PRIMARY KEY(`IDpaziente`),
  FOREIGN KEY `IDstruttura` REFERENCES `STRUTTURA`(`IDstruttura`)
)";

$result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}

#-------------------------- TABELLA MISURAZIONE  ----------------------------#

$sql="
CREATE TABLE `MISURAZIONE` (
  `IDmisurazione` int(11) NOT NULL,
  `data` date NOT NULL,
  `ora` time NOT NULL,
  `sp02` float DEFAULT NULL,
  `fr` float DEFAULT NULL,
  `fc` float DEFAULT NULL,
  `pi` float DEFAULT NULL,
  `IDpaziente` int(11) NOT NULL,
  PRIMARY KEY(`IDmisurazione`),
  FOREIGN KEY `IDpaziente` REFERENCES `PAZIENTE`(`IDpaziente`)
)";

$result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}

#-------------------------- TABELLA DIAGNOSI  ----------------------------#

$sql="
CREATE TABLE `DIAGNOSI` (
  `IDdiagnosi` int(5) NOT NULL,
  `IDpaziente` int(16) DEFAULT NULL,
  `dataDiagnosi` varchar(10) DEFAULT NULL,
  `CDC` varchar(7) DEFAULT NULL,
  PRIMARY KEY(`IDdiagnosi`),
  FOREIGN KEY `IDpaziente` REFERENCES `PAZIENTE`(`IDpaziente`)
)";

$result = $conn -> query($sql);

if(!$result){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore creazione tabella STATO: ".$conn -> error);
}


#----------------------------------------------------------------------#
#--------------------------------- FINE -------------------------------#
#----------------------------------------------------------------------#


print("<h1>Creazione tabelle avvenuta con successo</h1>");

$conn -> close();
               
?>
