<?php
declare(strict_types=1);

use DocuHelp\Repositories\ChunkRepository;
use DocuHelp\Repositories\DB;
use DocuHelp\Repositories\DocumentRepository;
use DocuHelp\Services\IndexService;
use DocuHelp\Services\PdfExtractor;
use DocuHelp\Services\SnippetService;
use DocuHelp\Services\DocumentService;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use PHPUnit\Framework\TestCase;

final class SearchTest extends TestCase
{
    private string $tmpRoot;

    protected function setUp(): void
    {
        $this->tmpRoot = sys_get_temp_dir() . '/docuhelp_search_' . bin2hex(random_bytes(4));
        @mkdir($this->tmpRoot, 0777, true);
        $_ENV['STORAGE_PATH'] = $this->tmpRoot . '/storage';
        $_ENV['DB_PATH'] = $this->tmpRoot . '/database.sqlite';
        @mkdir($_ENV['STORAGE_PATH'] . '/logs', 0777, true);
    }

    protected function tearDown(): void
    {
        $this->rrmdir($this->tmpRoot);
    }

    public function testSearchReturnsSnippet(): void
    {
        $logger = new Logger('test');
        $logger->pushHandler(new StreamHandler($_ENV['STORAGE_PATH'] . '/logs/test.log'));

        $db = new DB($logger);
        $docs = new DocumentRepository($db);
        $chunks = new ChunkRepository($db);
        $docService = new DocumentService($docs, $chunks, new PdfExtractor());
        $index = new IndexService($chunks);
        $snippets = new SnippetService();

        $tmpFile = $this->tmpRoot . '/sample.txt';
        file_put_contents($tmpFile, "La recherche plein texte devrait trouver ce passage spécifique.");
        $docService->storeUpload($tmpFile, 'sample.txt', 'text/plain', filesize($tmpFile));

        $rows = $index->search('passage spécifique', 5);
        $this->assertNotEmpty($rows);
        $snippet = $snippets->buildSnippet($rows[0]['content'], 'passage spécifique');
        $this->assertStringContainsString('<mark>', $snippet);
    }

    private function rrmdir(string $dir): void
    {
        if (!is_dir($dir)) return;
        $items = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS), RecursiveIteratorIterator::CHILD_FIRST);
        foreach ($items as $item) {
            $item->isDir() ? rmdir($item->getPathname()) : unlink($item->getPathname());
        }
        @rmdir($dir);
    }
}

