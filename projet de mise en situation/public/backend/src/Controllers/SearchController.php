<?php
declare(strict_types=1);

namespace DocuHelp\Controllers;

use DocuHelp\Repositories\DocumentRepository;
use DocuHelp\Services\IndexService;
use DocuHelp\Services\SnippetService;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;

final class SearchController
{
    public function __construct(
        private IndexService $index,
        private SnippetService $snippets,
        private DocumentRepository $docs,
    ) {}

    public function search(Request $request, Response $response): Response
    {
        $data = json_decode((string)$request->getBody(), true) ?: [];
        $query = trim((string)($data['query'] ?? ''));
        if ($query === '') {
            $response->getBody()->write(json_encode(['results' => []]) ?: '');
            return $response->withHeader('Content-Type', 'application/json');
        }
        $limit = (int)($data['limit'] ?? 5);
        $limit = max(1, min(20, $limit));
        $documentId = isset($data['document_id']) ? (string)$data['document_id'] : null;

        $rows = $this->index->search($query, $limit, $documentId);
        $results = [];
        foreach ($rows as $row) {
            $doc = $this->docs->get($row['document_id']);
            $snippet = $this->snippets->buildSnippet($row['content'], $query);
            $results[] = [
                'document_id' => $row['document_id'],
                'page_number' => (int)$row['page_number'],
                'snippet' => $snippet,
                'score' => (float)$row['score'],
                'source' => [
                    'filename' => $doc['original_name'] ?? ($doc['filename'] ?? ''),
                    'page' => (int)$row['page_number'],
                ],
            ];
        }
        $response->getBody()->write(json_encode(['results' => $results]) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }
}

