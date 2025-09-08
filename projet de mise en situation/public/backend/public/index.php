<?php
declare(strict_types=1);

use DI\Bridge\Slim\Bridge as SlimBridge;
use DocuHelp\Bootstrap;
use DocuHelp\Routes;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Log\LoggerInterface;

require __DIR__ . '/../../vendor/autoload.php';

// Create app via Bootstrap
$containerBuilder = Bootstrap::buildContainer();
$app = SlimBridge::create($containerBuilder);

// Register routes and middlewares
Routes::register($app);

// Run app
$app->run();

