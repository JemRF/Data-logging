<?php
function DisplayTelemetryLog($num_rows_to_display){
	$mysqli = new mysqli("localhost", 
						 "dblogger", 
						 "password", 
						 "sensor_logs");
						 
	if ($mysqli->connect_errno) {
	    echo "Failed to connect to MySQL: (" . 
	         $mysqli->connect_errno . 
	         ") " . $mysqli->connect_error;
	}
	
	$sql = "SELECT * FROM telemetry_log ORDER BY date DESC LIMIT $num_rows_to_display";
	$res = $mysqli->query($sql);
	if (!$res) {
	    echo "Table query failed: (" . 
	    $mysqli->errno . 
	    ") " . $mysqli->error;
	}

	if ($res->num_rows==0)
		{
		echo "No data in log";	
		return(0);
		}
	
	echo "<div class='telemetry_div'>";
	echo "<table class='telemetry_table'>";
	echo "<tr>";
	echo "<th>Date</th>";
	echo "<th>Device ID</th>";
	echo "<th>Type</th>";
	echo "<th>Value</th>";
	echo "<th>UOM</th>";
	echo "</tr>";
	
	for ($row_no = 0; 
	     $row_no < $res->num_rows && $row_no < $num_rows_to_display; 
	     $row_no++) {
		echo "<tr>";
	    $res->data_seek($row_no);
	    $row = $res->fetch_assoc();
		echo "<td>".$row['date']."</td>";
	    echo "<td>".$row['device_id']."</td>";
	    echo "<td>".$row['type']."</td>";
		echo "<td>".$row['value']."</td>";
	    echo "<td>".$row['unit_of_measure']."</td>";
		echo "</tr>";
	}
	echo "</table>";
	echo "</DIV>";
}

?>