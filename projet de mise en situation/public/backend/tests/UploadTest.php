<?php
declare(strict_types=1);

use DocuHelp\Repositories\ChunkRepository;
use DocuHelp\Repositories\DB;
use DocuHelp\Repositories\DocumentRepository;
use DocuHelp\Services\DocumentService;
use DocuHelp\Services\PdfExtractor;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use PHPUnit\Framework\TestCase;

final class UploadTest extends TestCase
{
    private string $tmpRoot;

    protected function setUp(): void
    {
        $this->tmpRoot = sys_get_temp_dir() . '/docuhelp_test_' . bin2hex(random_bytes(4));
        @mkdir($this->tmpRoot, 0777, true);
        $_ENV['STORAGE_PATH'] = $this->tmpRoot . '/storage';
        $_ENV['DB_PATH'] = $this->tmpRoot . '/database.sqlite';
        @mkdir($_ENV['STORAGE_PATH'] . '/logs', 0777, true);
    }

    protected function tearDown(): void
    {
        $this->rrmdir($this->tmpRoot);
    }

    public function testUploadTxtAndIndex(): void
    {
        $logger = new Logger('test');
        $logger->pushHandler(new StreamHandler($_ENV['STORAGE_PATH'] . '/logs/test.log'));

        $db = new DB($logger);
        $docs = new DocumentRepository($db);
        $chunks = new ChunkRepository($db);
        $service = new DocumentService($docs, $chunks, new PdfExtractor());

        $tmpFile = $this->tmpRoot . '/sample.txt';
        file_put_contents($tmpFile, "Bonjour DocuHelp. Ceci est un test d'indexation plein texte.");

        $result = $service->storeUpload($tmpFile, 'sample.txt', 'text/plain', filesize($tmpFile));
        $this->assertArrayHasKey('document_id', $result);
        $this->assertGreaterThan(0, $result['page_count']);
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

