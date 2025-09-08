<?php
declare(strict_types=1);

namespace DocuHelp\Middlewares;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface as Handler;
use Slim\Psr7\Response as SlimResponse;

final class ApiKeyMiddleware implements MiddlewareInterface
{
    public function process(Request $request, Handler $handler): Response
    {
        $disabled = ($_ENV['API_KEY_DISABLED'] ?? 'false') === 'true';
        if ($disabled) {
            return $handler->handle($request);
        }

        $provided = $request->getHeaderLine('X-API-Key') ?: ($request->getQueryParams()['api_key'] ?? '');
        $expected = $_ENV['API_KEY'] ?? '';

        if ($expected === '' || hash_equals($expected, (string)$provided)) {
            return $handler->handle($request);
        }

        $response = new SlimResponse(401);
        $response->getBody()->write(json_encode(['error' => 'Unauthorized']));
        return $response->withHeader('Content-Type', 'application/json');
    }
}

