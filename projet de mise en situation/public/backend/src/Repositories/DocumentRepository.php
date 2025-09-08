<?php
declare(strict_types=1);

namespace DocuHelp\Repositories;

use DateTimeImmutable;
use PDO;

final class DocumentRepository
{
    public function __construct(private DB $db) {}

    public function insert(string $id, string $filename, string $originalName, string $mime, int $sizeBytes, int $pageCount): void
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('INSERT INTO documents(id, filename, original_name, mime, size_bytes, page_count, created_at) VALUES(?,?,?,?,?,?,?)');
        $stmt->execute([$id, $filename, $originalName, $mime, $sizeBytes, $pageCount, (new DateTimeImmutable())->format(DATE_ATOM)]);
    }

    public function list(int $offset, int $limit): array
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('SELECT * FROM documents ORDER BY created_at DESC LIMIT :limit OFFSET :offset');
        $stmt->bindValue(':limit', $limit, PDO::PARAM_INT);
        $stmt->bindValue(':offset', $offset, PDO::PARAM_INT);
        $stmt->execute();
        $items = $stmt->fetchAll();
        $total = (int)$pdo->query('SELECT COUNT(*) FROM documents')->fetchColumn();
        return ['items' => $items, 'total' => $total];
    }

    public function get(string $id): ?array
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('SELECT * FROM documents WHERE id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public function delete(string $id): void
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('DELETE FROM documents WHERE id = ?');
        $stmt->execute([$id]);
    }
}

