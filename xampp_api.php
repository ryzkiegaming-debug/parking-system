<?php
/**
 * Simple REST-like endpoint for XAMPP / phpMyAdmin setup.
 *
 * Usage examples (POST requests recommended):
 *   action=signup    + student_number, password
 *   action=login     + student_number, password
 *   action=listSlots
 *   action=bookSlot  + student_number, slot_name, entry_date, entry_time, exit_date, exit_time
 *
 * Responses are JSON objects with fields: success (bool), message (string), data (optional)
 */

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, GET');

const DB_HOST = '127.0.0.1';
const DB_NAME = 'nwssu_parking_db';
const DB_USER = 'root';
const DB_PASS = '';

/**
 * @return PDO
 */
function db()
{
    static $pdo = null;
    if ($pdo === null) {
        try {
            $dsn = sprintf('mysql:host=%s;dbname=%s;charset=utf8mb4', DB_HOST, DB_NAME);
            $options = [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            ];
            $pdo = new PDO($dsn, DB_USER, DB_PASS, $options);
        } catch (PDOException $e) {
            respond(false, 'Database connection failed: ' . $e->getMessage() . 
                '. Make sure MySQL is running in XAMPP and the database exists.');
        }
    }
    return $pdo;
}

/**
 * Helper to send JSON responses and exit.
 */
function respond($success, $message, $data = null)
{
    echo json_encode([
        'success' => $success,
        'message' => $message,
        'data' => $data,
    ]);
    exit;
}

$action = $_POST['action'] ?? $_GET['action'] ?? null;
if (!$action) {
    respond(false, 'Missing action parameter.');
}

try {
    switch ($action) {
        case 'test':
            testConnection();
            break;
        case 'signup':
            signup();
            break;
        case 'login':
            login();
            break;
        case 'listSlots':
            listSlots();
            break;
        case 'bookSlot':
            bookSlot();
            break;
        default:
            respond(false, 'Unknown action.');
    }
} catch (Throwable $e) {
    respond(false, 'Server error: ' . $e->getMessage());
}

function testConnection()
{
    try {
        $pdo = db();
        $tables = ['users', 'parking_slots', 'bookings'];
        $missing = [];
        
        foreach ($tables as $table) {
            $stmt = $pdo->query("SHOW TABLES LIKE '$table'");
            if ($stmt->rowCount() === 0) {
                $missing[] = $table;
            }
        }
        
        if (!empty($missing)) {
            respond(false, 'Missing tables: ' . implode(', ', $missing) . 
                '. Please create them using the SQL file in templates/static/database/phpmyadmin.sql', [
                'missing_tables' => $missing,
                'connection' => 'OK'
            ]);
        }
        
        $userCount = $pdo->query('SELECT COUNT(*) as cnt FROM users')->fetch()['cnt'];
        $slotCount = $pdo->query('SELECT COUNT(*) as cnt FROM parking_slots')->fetch()['cnt'];
        
        respond(true, 'Database connection successful. All tables exist.', [
            'tables' => $tables,
            'user_count' => (int)$userCount,
            'slot_count' => (int)$slotCount
        ]);
    } catch (PDOException $e) {
        respond(false, 'Database error: ' . $e->getMessage());
    }
}

function signup()
{
    $studentNumber = trim($_POST['student_number'] ?? '');
    $password = $_POST['password'] ?? '';

    if ($studentNumber === '' || $password === '') {
        respond(false, 'Student number and password are required.');
    }

    $pdo = db();
    $stmt = $pdo->prepare('SELECT 1 FROM users WHERE student_number = ?');
    $stmt->execute([$studentNumber]);
    if ($stmt->fetch()) {
        respond(false, 'Student number already exists.');
    }

    $hash = password_hash($password, PASSWORD_DEFAULT);
    $insert = $pdo->prepare('INSERT INTO users (student_number, password_hash) VALUES (?, ?)');
    $insert->execute([$studentNumber, $hash]);

    respond(true, 'Account created. You can now log in.');
}

function login()
{
    $studentNumber = trim($_POST['student_number'] ?? '');
    $password = $_POST['password'] ?? '';

    if ($studentNumber === '' || $password === '') {
        respond(false, 'Student number and password are required.');
    }

    $pdo = db();
    $stmt = $pdo->prepare('SELECT user_id, password_hash FROM users WHERE student_number = ?');
    $stmt->execute([$studentNumber]);
    $user = $stmt->fetch();

    if (!$user || !password_verify($password, $user['password_hash'])) {
        respond(false, 'Invalid credentials.');
    }

    respond(true, 'Login successful.', ['user_id' => $user['user_id']]);
}

function listSlots()
{
    $pdo = db();
    try {
        $stmt = $pdo->query('SELECT slot_name, is_available FROM parking_slots ORDER BY slot_name');
        $slots = $stmt->fetchAll();
        if (empty($slots)) {
            respond(false, 'No parking slots found. Please run the SQL script to insert initial slots.');
        }
        respond(true, 'Slot list retrieved.', $slots);
    } catch (PDOException $e) {
        respond(false, 'Error retrieving slots: ' . $e->getMessage() . 
            '. Make sure the parking_slots table exists.');
    }
}

function bookSlot()
{
    $studentNumber = trim($_POST['student_number'] ?? '');
    $slotName = $_POST['slot_name'] ?? '';
    $entryDate = $_POST['entry_date'] ?? '';
    $entryTime = $_POST['entry_time'] ?? '';
    $exitDate = $_POST['exit_date'] ?? '';
    $exitTime = $_POST['exit_time'] ?? '';

    if (
        $studentNumber === '' || $slotName === '' ||
        $entryDate === '' || $entryTime === '' ||
        $exitDate === '' || $exitTime === ''
    ) {
        respond(false, 'All booking fields are required.');
    }

    $pdo = db();
    $pdo->beginTransaction();

    $userStmt = $pdo->prepare('SELECT user_id FROM users WHERE student_number = ? FOR UPDATE');
    $userStmt->execute([$studentNumber]);
    $user = $userStmt->fetch();
    if (!$user) {
        $pdo->rollBack();
        respond(false, 'Student not found. Please sign up.');
    }

    $slotStmt = $pdo->prepare('SELECT slot_id, is_available FROM parking_slots WHERE slot_name = ? FOR UPDATE');
    $slotStmt->execute([$slotName]);
    $slot = $slotStmt->fetch();
    if (!$slot) {
        $pdo->rollBack();
        respond(false, 'Slot does not exist.');
    }
    if ((int)$slot['is_available'] === 0) {
        $pdo->rollBack();
        respond(false, 'Slot already booked.');
    }

    $insert = $pdo->prepare(
        'INSERT INTO bookings (user_id, slot_id, entry_date, entry_time, exit_date, exit_time)
         VALUES (?, ?, ?, ?, ?, ?)'
    );
    $insert->execute([
        $user['user_id'],
        $slot['slot_id'],
        $entryDate,
        $entryTime,
        $exitDate,
        $exitTime,
    ]);

    $update = $pdo->prepare('UPDATE parking_slots SET is_available = 0 WHERE slot_id = ?');
    $update->execute([$slot['slot_id']]);

    $pdo->commit();
    respond(true, 'Booking confirmed.', [
        'slot_name' => $slotName,
        'entry_date' => $entryDate,
        'entry_time' => $entryTime,
        'exit_date' => $exitDate,
        'exit_time' => $exitTime,
    ]);
}

