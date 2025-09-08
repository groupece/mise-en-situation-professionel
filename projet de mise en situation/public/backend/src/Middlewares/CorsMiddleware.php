<?php
declare(strict_types=1);

namespace DocuHelp\Middlewares;

use Psr\Http\Message\ResponseInterface as Response;
use Psr\Http\Message\ServerRequestInterface as Request;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface as Handler;

final class CorsMiddleware implements MiddlewareInterface
{
    public function process(Request $request, Handler $handler): Response
    {
        $response = $handler->handle($request);
        $env = $_ENV['APP_ENV'] ?? 'prod';
        if ($env !== 'dev') {
            return $response;
        }
        $origins = $_ENV['CORS_ALLOWED_ORIGINS'] ?? '';
        $origin = $request->getHeaderLine('Origin');
        $allow = 'null';
        if ($origin && self::originAllowed($origin, $origins)) {
            $allow = $origin;
        }
        return $response
            ->withHeader('Access-Control-Allow-Origin', $allow)
            ->withHeader('Access-Control-Allow-Methods', 'GET,POST,DELETE,OPTIONS')
            ->withHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-API-Key')
            ->withHeader('Access-Control-Allow-Credentials', 'true');
    }

    private static function originAllowed(string $origin, string $rules): bool
    {
        $list = array_filter(array_map('trim', explode(',', $rules)));
        foreach ($list as $rule) {
            $pattern = '/^' . str_replace(['*', '.'], ['.*', '\\.'], preg_quote($rule, '/')) . '$/i';
            if (preg_match($pattern, $origin)) {
                return true;
            }
        }
        return false;
    }
}

