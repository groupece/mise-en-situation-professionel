<?php
declare(strict_types=1);

namespace DocuHelp;

use DI\ContainerBuilder;
use Dotenv\Dotenv;
use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;
use Psr\Log\LoggerInterface;

final class Bootstrap
{
    public static function buildContainer(): \DI\Container
    {
        $rootPath = realpath(__DIR__ . '/..');

        // Load .env if present
        $envDir = dirname($rootPath);
        if (file_exists($envDir . '/.env')) {
            $dotenv = Dotenv::createImmutable($envDir);
            $dotenv->safeLoad();
        }

        $storagePath = $_ENV['STORAGE_PATH'] ?? 'storage';
        $logsPath = $storagePath . '/logs';
        if (!is_dir($logsPath)) {
            @mkdir($logsPath, 0777, true);
        }

        $containerBuilder = new ContainerBuilder();

        $containerBuilder->addDefinitions([
            LoggerInterface::class => function (): LoggerInterface {
                $logger = new Logger('docuhelp');
                $level = (($_ENV['APP_DEBUG'] ?? 'false') === 'true') ? Level::Debug : Level::Info;
                $logFile = ($_ENV['STORAGE_PATH'] ?? 'storage') . '/logs/app.log';
                $logger->pushHandler(new StreamHandler($logFile, $level));
                return $logger;
            },
        ]);

        return $containerBuilder->build();
    }
}

