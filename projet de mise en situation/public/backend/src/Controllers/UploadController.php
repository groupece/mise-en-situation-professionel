<?php
declare(strict_types=1);

namespace DocuHelp\Controllers;

use DocuHelp\Repositories\DocumentRepository;
use DocuHelp\Services\Antivirus;
use DocuHelp\Services\DocumentService;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Log\LoggerInterface;
use Slim\Psr7\Response as SlimResponse;

final class UploadController
{
    public function __construct(
        private LoggerInterface $logger,
        private DocumentService $documents,
        private DocumentRepository $docRepo,
    ) {
    }

    public function upload(Request $request, Response $response): Response
    {
        $maxMb = (int)($_ENV['MAX_UPLOAD_MB'] ?? '20');
        $maxBytes = $maxMb * 1024 * 1024;
        $parsedBody = $request->getParsedBody();

        $files = $request->getUploadedFiles();
        if (!isset($files['file'])) {
            return $this->error($response, 400, 'Missing file field');
        }
        $file = $files['file'];
        if ($file->getError() !== UPLOAD_ERR_OK) {
            return $this->error($response, 400, 'Upload error');
        }
        if ($file->getSize() > $maxBytes) {
            return $this->error($response, 413, 'File too large');
        }

        $mime = $file->getClientMediaType();
        $allowed = ['application/pdf', 'text/plain'];
        if (!in_array($mime, $allowed, true)) {
            return $this->error($response, 415, 'Unsupported media type');
        }

        $tmpPath = $file->getStream()->getMetadata('uri');
        $antivirus = Antivirus::make($this->logger);
        if (!$antivirus->scan((string)$tmpPath)) {
            return $this->error($response, 400, 'Malware detected');
        }

        try {
            $result = $this->documents->storeUpload((string)$tmpPath, $file->getClientFilename() ?? 'file', $mime, (int)$file->getSize());
            $payload = json_encode($result);
            $response->getBody()->write($payload ?: '');
            return $response->withHeader('Content-Type', 'application/json');
        } catch (\Throwable $e) {
            $this->logger->error('Upload failed: ' . $e->getMessage());
            return $this->error($response, 500, 'Server error');
        }
    }

    public function listDocs(Request $request, Response $response): Response
    {
        $params = $request->getQueryParams();
        $page = max(1, (int)($params['page'] ?? 1));
        $limit = max(1, min(100, (int)($params['limit'] ?? 20)));
        $offset = ($page - 1) * $limit;
        $data = $this->docRepo->list($offset, $limit);
        $response->getBody()->write(json_encode($data) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function getDoc(Request $request, Response $response, array $args): Response
    {
        $doc = $this->docRepo->get($args['id']);
        if (!$doc) {
            return $this->error($response, 404, 'Not found');
        }
        $response->getBody()->write(json_encode($doc) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    public function deleteDoc(Request $request, Response $response, array $args): Response
    {
        $doc = $this->docRepo->get($args['id']);
        if (!$doc) {
            return $this->error($response, 404, 'Not found');
        }
        $storage = $_ENV['STORAGE_PATH'] ?? 'storage';
        $rawPath = $storage . '/raw/' . $doc['filename'];
        @unlink($rawPath);
        $this->docRepo->delete($args['id']);
        $response->getBody()->write(json_encode(['deleted' => true]) ?: '');
        return $response->withHeader('Content-Type', 'application/json');
    }

    private function error(Response $response, int $code, string $message): Response
    {
        $res = new SlimResponse($code);
        $res->getBody()->write(json_encode(['error' => $message]) ?: '');
        return $res->withHeader('Content-Type', 'application/json');
    }
}

