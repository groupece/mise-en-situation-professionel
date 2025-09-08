<?php
declare(strict_types=1);

namespace DocuHelp\Services;

use DocuHelp\Repositories\ChunkRepository;
use DocuHelp\Repositories\DocumentRepository;
use Ramsey\Uuid\Uuid;

final class DocumentService
{
    public function __construct(
        private DocumentRepository $documents,
        private ChunkRepository $chunks,
        private PdfExtractor $pdfExtractor,
    ) {
    }

    public function storeUpload(string $tmpPath, string $originalName, string $mime, int $sizeBytes): array
    {
        $storage = $_ENV['STORAGE_PATH'] ?? 'storage';
        $rawDir = $storage . '/raw';
        $parsedDir = $storage . '/parsed';
        @mkdir($rawDir, 0777, true);
        @mkdir($parsedDir, 0777, true);

        $id = Uuid::uuid4()->toString();
        $ext = $this->guessExtension($mime, $originalName);
        $filename = $id . '.' . $ext;
        $destPath = $rawDir . '/' . $filename;
        if (!@rename($tmpPath, $destPath)) {
            // fallback copy+unlink on Windows
            @copy($tmpPath, $destPath);
            @unlink($tmpPath);
        }

        $pages = [];
        if ($mime === 'application/pdf') {
            $pages = $this->pdfExtractor->extractByPage($destPath);
        } else {
            $text = file_get_contents($destPath) ?: '';
            $pages = $this->splitTextIntoPseudoPages($text, 1300);
        }

        $pageCount = count($pages);
        $this->documents->insert($id, $filename, $originalName, $mime, $sizeBytes, $pageCount);

        $i = 1;
        foreach ($pages as $pageNumber => $content) {
            $chunkId = Uuid::uuid4()->toString();
            $this->chunks->insert($chunkId, $id, $pageNumber, $content);
            $i++;
        }

        file_put_contents($parsedDir . '/' . $id . '.json', json_encode([
            'id' => $id,
            'filename' => $filename,
            'original_name' => $originalName,
            'mime' => $mime,
            'size_bytes' => $sizeBytes,
            'page_count' => $pageCount,
            'pages' => $pages,
        ], JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE));

        return [
            'document_id' => $id,
            'filename' => $filename,
            'page_count' => $pageCount,
        ];
    }

    private function splitTextIntoPseudoPages(string $text, int $chunkSize): array
    {
        $text = preg_replace('/\r\n?/', "\n", $text) ?? $text;
        $len = strlen($text);
        $pages = [];
        $page = 1;
        for ($i = 0; $i < $len; $i += $chunkSize) {
            $pages[$page] = substr($text, $i, $chunkSize);
            $page++;
        }
        if ($pages === []) {
            $pages[1] = '';
        }
        return $pages;
    }

    private function guessExtension(string $mime, string $original): string
    {
        return match ($mime) {
            'application/pdf' => 'pdf',
            'text/plain' => 'txt',
            default => pathinfo($original, PATHINFO_EXTENSION) ?: 'bin',
        };
    }
}

