<?php
declare(strict_types=1);

namespace DocuHelp;

use DocuHelp\Controllers\ChatController;
use DocuHelp\Controllers\HealthController;
use DocuHelp\Controllers\SearchController;
use DocuHelp\Controllers\UploadController;
use DocuHelp\Middlewares\ApiKeyMiddleware;
use DocuHelp\Middlewares\CorsMiddleware;
use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Slim\App;

final class Routes
{
    public static function register(App $app): void
    {
        $app->add(new CorsMiddleware());
        $app->add(new ApiKeyMiddleware());

        // Preflight CORS
        $app->options('/{routes:.+}', function (Request $request, Response $response) {
            return $response;
        });

        $app->get('/index.php/api/health', [HealthController::class, 'health']);
        $app->get('/index.php/api/version', [HealthController::class, 'version']);

        $app->post('/index.php/api/upload', [UploadController::class, 'upload']);
        $app->get('/index.php/api/docs', [UploadController::class, 'listDocs']);
        $app->get('/index.php/api/docs/{id}', [UploadController::class, 'getDoc']);
        $app->delete('/index.php/api/docs/{id}', [UploadController::class, 'deleteDoc']);

        $app->post('/index.php/api/search', [SearchController::class, 'search']);

        $app->post('/index.php/api/chat/session', [ChatController::class, 'createSession']);
        $app->get('/index.php/api/chat/session/{id}/messages', [ChatController::class, 'getMessages']);
        $app->post('/index.php/api/chat/message', [ChatController::class, 'postMessage']);
    }
}

