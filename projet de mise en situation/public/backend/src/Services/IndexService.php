<?php
declare(strict_types=1);

namespace DocuHelp\Services;

use DocuHelp\Repositories\ChunkRepository;

final class IndexService
{
    public function __construct(private ChunkRepository $chunks)
    {
    }

    public function search(string $query, int $limit, ?string $documentId = null): array
    {
        return $this->chunks->search($query, $limit, $documentId);
    }
}

