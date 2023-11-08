<?php 
#----------------------------------------------------------------------#
#-------------------INIZIALIZZO CONNESSIONE DATABASE ------------------#
#----------------------------------------------------------------------#


$dbname = "CORADIN";
$username = "CORADIN";
$password="DIN2020";
$host = "80.210.122.173";
$conn = new mysqli ($host, $username, $password, $dbname);

 /*
$dbname = "monitoraggioDB";
$username = "root";
$password="";
$host = "localhost";
$conn = new mysqli ($host, $username, $password, $dbname);
*/

if(!$conn){
    print("<h1>Error ".$conn -> errno."</h1>");
    die("Errore di connessione al db: ".$conn -> connect_error);
}

?>