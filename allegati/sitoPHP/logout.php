<?php
   session_start();
   unset($_SESSION["CFmedico"]);
   unset($_SESSION["password"]);
   
   header('Refresh: 2; URL = login.php');
?>