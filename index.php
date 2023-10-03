<?php
    $showlast = 20;
    include ("dblogger.php");
    echo "The last ",$showlast," telemetry logs are:";
    echo DisplayTelemetryLog($showlast);
?>