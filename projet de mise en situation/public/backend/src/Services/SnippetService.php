<?php
declare(strict_types=1);

namespace DocuHelp\Services;

final class SnippetService
{
    public function buildSnippet(string $content, string $query, int $radius = 120): string
    {
        $terms = $this->extractTerms($query);
        $contentNorm = ' ' . preg_replace('/\s+/', ' ', $content) . ' ';
        $bestPos = null;
        foreach ($terms as $term) {
            $pos = stripos($contentNorm, $term);
            if ($pos !== false) {
                $bestPos = $bestPos === null ? $pos : min($bestPos, $pos);
            }
        }
        if ($bestPos === null) {
            $snippet = substr($contentNorm, 0, 2 * $radius);
        } else {
            $start = max(0, $bestPos - $radius);
            $snippet = substr($contentNorm, $start, 2 * $radius);
        }
        $snippet = htmlspecialchars($snippet ?? '', ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
        foreach ($terms as $term) {
            if ($term === '') continue;
            $snippet = preg_replace('/(' . preg_quote($term, '/') . ')/i', '<mark>$1</mark>', $snippet) ?? $snippet;
        }
        return '…' . trim($snippet) . '…';
    }

    private function extractTerms(string $query): array
    {
        preg_match_all('/"([^"]+)"|(\w[\w\-*]+)/u', $query, $m);
        $terms = [];
        foreach ($m[0] as $raw) {
            $t = trim($raw, '"');
            if ($t !== '') $terms[] = $t;
        }
        return array_values(array_unique($terms));
    }
}

