<?php
declare(strict_types=1);

namespace DocuHelp\Repositories;

use PDO;
use Psr\Log\LoggerInterface;

final class DB
{
    private PDO $pdo;

    public function __construct(private LoggerInterface $logger)
    {
        $dbPath = $_ENV['DB_PATH'] ?? 'database/database.sqlite';
        $dir = dirname($dbPath);
        if (!is_dir($dir)) {
            @mkdir($dir, 0777, true);
        }
        $this->pdo = new PDO('sqlite:' . $dbPath, options: [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);
        $this->pdo->exec('PRAGMA foreign_keys = ON;');
        $this->migrate();
    }

    public function getConnection(): PDO
    {
        return $this->pdo;
    }

    private function migrate(): void
    {
        $migrationFile = __DIR__ . '/../../database/migrations/001_init.sql';
        if (!file_exists($migrationFile)) {
            return;
        }
        $sql = file_get_contents($migrationFile);
        if ($sql === false) {
            return;
        }
        try {
            $this->pdo->exec($sql);
        } catch (\Throwable $e) {
            $this->logger->error('Migration error: ' . $e->getMessage());
            throw $e;
        }
    }
}

