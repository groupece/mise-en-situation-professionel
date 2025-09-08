<?php
declare(strict_types=1);

namespace DocuHelp\Controllers;

use DocuHelp\Repositories\DB;
use DocuHelp\Services\IndexService;
use DocuHelp\Services\SnippetService;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Ramsey\Uuid\Uuid;

final class ChatController
{
    public function __construct(
        private DB $db,
        private IndexService $index,
        private SnippetService $snippets,
    ) {}

    public function createSession(Request $request, Response $response): Response
    {
        $id = Uuid::uuid4()->toString();
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('INSERT INTO chat_sessions(id, created_at) VALUES(?, ?)');
        $stmt->execute([$id, (new \DateTimeImmutable())->format(DATE_ATOM)]);
        $response->getBody()->write(json_encode(['session_id' => $id]) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function getMessages(Request $request, Response $response, array $args): Response
    {
        $pdo = $this->db->getConnection();
        $stmt = $pdo->prepare('SELECT * FROM chat_messages WHERE session_id = ? ORDER BY created_at ASC');
        $stmt->execute([$args['id']]);
        $rows = $stmt->fetchAll();
        $response->getBody()->write(json_encode(['items' => $rows, 'total' => count($rows)]) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function postMessage(Request $request, Response $response): Response
    {
        $data = json_decode((string)$request->getBody(), true) ?: [];
        $sessionId = (string)($data['session_id'] ?? '');
        $content = trim((string)($data['content'] ?? ''));
        if ($sessionId === '' || $content === '') {
            $response->getBody()->write(json_encode(['error' => 'Invalid payload']) ?: '');
            return $response->withHeader('Content-Type', 'application/json')->withStatus(400);
        }
        $pdo = $this->db->getConnection();
        $now = (new \DateTimeImmutable())->format(DATE_ATOM);
        $stmt = $pdo->prepare('INSERT INTO chat_messages(id, session_id, role, content, created_at) VALUES(?,?,?,?,?)');
        $stmt->execute([Uuid::uuid4()->toString(), $sessionId, 'user', $content, $now]);

        $rows = $this->index->search($content, 5, null);
        $top = [];
        foreach ($rows as $row) {
            $top[] = [
                'document_id' => $row['document_id'],
                'page_number' => (int)$row['page_number'],
                'snippet' => $this->snippets->buildSnippet($row['content'], $content),
                'score' => (float)$row['score'],
            ];
        }
        $systemPayload = json_encode(['top_passages' => $top], JSON_UNESCAPED_UNICODE);
        $stmt = $pdo->prepare('INSERT INTO chat_messages(id, session_id, role, content, created_at) VALUES(?,?,?,?,?)');
        $stmt->execute([Uuid::uuid4()->toString(), $sessionId, 'system', (string)$systemPayload, $now]);

        $response->getBody()->write($systemPayload ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }
}

