<?php
declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

// Load .env
if (file_exists(__DIR__ . '/../.env')) {
    Dotenv\Dotenv::createImmutable(__DIR__ . '/..')->safeLoad();
}

$storage = $_ENV['STORAGE_PATH'] ?? (__DIR__ . '/../storage');
@mkdir($storage . '/logs', 0777, true);
@mkdir($storage . '/raw', 0777, true);
@mkdir($storage . '/parsed', 0777, true);

$logger = new Monolog\Logger('migrate');
$logger->pushHandler(new Monolog\Handler\StreamHandler($storage . '/logs/app.log'));

$db = new DocuHelp\Repositories\DB($logger);
// Touch the connection/migration
$db->getConnection()->query('SELECT 1');
echo "Migration executed.\n";

