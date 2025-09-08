<?php
declare(strict_types=1);

namespace DocuHelp\Services;

use Psr\Log\LoggerInterface;

interface AntivirusInterface
{
    public function scan(string $path): bool;
}

final class NoOpAntivirus implements AntivirusInterface
{
    public function scan(string $path): bool
    {
        return true;
    }
}

final class ClamAvAntivirus implements AntivirusInterface
{
    public function __construct(private LoggerInterface $logger)
    {
    }

    public function scan(string $path): bool
    {
        // Simple socket-based clamd ping (optional, best-effort)
        $socket = $_ENV['CLAMAV_SOCKET'] ?? '/var/run/clamav/clamd.ctl';
        if (!function_exists('socket_create')) {
            $this->logger->warning('ClamAV scan skipped: sockets not available');
            return true;
        }
        try {
            $client = @stream_socket_client('unix://' . $socket, $errno, $errstr, 1);
            if (!$client) {
                $this->logger->warning('ClamAV not reachable: ' . $errstr);
                return true; // do not block in dev
            }
            fwrite($client, "SCAN {$path}\n");
            $resp = stream_get_contents($client);
            fclose($client);
            if ($resp !== false && str_contains($resp, 'OK')) {
                return true;
            }
            if ($resp !== false && str_contains($resp, 'FOUND')) {
                $this->logger->error('ClamAV found malware: ' . trim($resp));
                return false;
            }
        } catch (\Throwable $e) {
            $this->logger->warning('ClamAV error: ' . $e->getMessage());
            return true;
        }
        return true;
    }
}

final class Antivirus
{
    public static function make(LoggerInterface $logger): AntivirusInterface
    {
        $enabled = ($_ENV['ENABLE_CLAMAV'] ?? 'false') === 'true';
        if ($enabled) {
            return new ClamAvAntivirus($logger);
        }
        return new NoOpAntivirus();
    }
}

