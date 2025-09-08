<?php
declare(strict_types=1);

namespace DocuHelp\Services;

use Smalot\PdfParser\Parser;

final class PdfExtractor
{
    public function __construct(private Parser $parser = new Parser())
    {
    }

    /**
     * @return array<int, string> pageNumber => text
     */
    public function extractByPage(string $filePath): array
    {
        $pdf = $this->parser->parseFile($filePath);
        $pages = $pdf->getPages();
        $results = [];
        foreach ($pages as $index => $page) {
            $text = trim($page->getText());
            $results[$index + 1] = $text;
        }
        return $results;
    }
}

