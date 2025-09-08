<?php
declare(strict_types=1);

namespace DocuHelp\Controllers;

use DocuHelp\Repositories\DB;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class HealthController
{
    public function __construct(private DB $db) {}

    public function health(Request $request, Response $response): Response
    {
        $okDb = true;
        $okFts = true;
        try {
            $pdo = $this->db->getConnection();
            $pdo->query('SELECT 1');
            $pdo->query('SELECT 1 FROM chunks_fts LIMIT 1');
        } catch (\Throwable $e) {
            $okDb = false;
            $okFts = false;
        }
        $payload = json_encode(['status' => 'ok', 'db' => $okDb, 'fts' => $okFts]);
        $response->getBody()->write($payload ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function version(Request $request, Response $response): Response
    {
        $composer = __DIR__ . '/../../composer.json';
        $version = 'dev';
        if (file_exists($composer)) {
            $data = json_decode((string)file_get_contents($composer), true);
            $version = $data['version'] ?? 'dev';
        }
        $response->getBody()->write(json_encode(['version' => $version]) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }
}

