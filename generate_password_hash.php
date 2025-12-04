<?php
/**
 * Quick script to generate a password hash for inserting into the database
 * 
 * Usage: Run this file in your browser or via command line:
 *   php generate_password_hash.php
 * 
 * Or visit: http://localhost/Parking_app/generate_password_hash.php
 */

$password = 'admin123'; // Change this to your desired password
$hash = password_hash($password, PASSWORD_DEFAULT);

echo "Password: " . $password . "\n";
echo "Hash: " . $hash . "\n\n";
echo "SQL INSERT statement:\n";
echo "INSERT IGNORE INTO `users` (`student_number`, `password_hash`) VALUES\n";
echo "('12345', '" . $hash . "');\n";

