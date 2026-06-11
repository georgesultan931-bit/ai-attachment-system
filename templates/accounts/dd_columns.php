<?php
// Change these to match your database settings
$host = "localhost";
$username = "root";      // Default XAMPP/WAMP username
$password = "";          // Default XAMPP/WAMP has no password
$database = "your_database_name";  // CHANGE THIS to your actual database name

// Connect to database
$conn = new mysqli($host, $username, $password, $database);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

echo "Connected successfully!<br><br>";

// Run the SQL to add columns
$sql = "ALTER TABLE users 
        ADD COLUMN reset_token VARCHAR(255) DEFAULT NULL,
        ADD COLUMN reset_expires DATETIME DEFAULT NULL";

if ($conn->query($sql) === TRUE) {
    echo "✅ SUCCESS: 'reset_token' and 'reset_expires' columns added to 'users' table!<br>";
    echo "<strong style='color:red;'>⚠️ DELETE THIS FILE NOW FOR SECURITY!</strong>";
} else {
    echo "Error: " . $conn->error . "<br><br>";
    
    // If error says column already exists, that's fine
    if(strpos($conn->error, "Duplicate column") !== false) {
        echo "✅ Columns already exist. Nothing to do.";
    }
}

$conn->close();
?>