<?php
declare(strict_types=1);

namespace DocuHelp\Repositories;

use PDO;

final class ChunkRepository
{
    public function __construct(private DB $db) {}

    public function insert(string $id, string $documentId, int $pageNumber, string $content): void
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('INSERT INTO chunks(id, document_id, page_number, content) VALUES(?,?,?,?)');
        $stmt->execute([$id, $documentId, $pageNumber, $content]);
    }

    public function deleteByDocumentId(string $documentId): void
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('DELETE FROM chunks WHERE document_id = ?');
        $stmt->execute([$documentId]);
    }

    public function search(string $query, int $limit, ?string $documentId = null): array
    {
        $pdo = $this->db->getConnection();
        if ($documentId) {
            $stmt = $pdo->prepare('SELECT content, document_id, page_number, bm25(chunks_fts) AS score FROM chunks_fts WHERE chunks_fts MATCH :q AND document_id = :doc ORDER BY score LIMIT :lim');
            $stmt->bindValue(':doc', $documentId, PDO::PARAM_STR);
        } else {
            $stmt = $pdo->prepare('SELECT content, document_id, page_number, bm25(chunks_fts) AS score FROM chunks_fts WHERE chunks_fts MATCH :q ORDER BY score LIMIT :lim');
        }
        $stmt->bindValue(':q', $query, PDO::PARAM_STR);
        $stmt->bindValue(':lim', $limit, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }
}

