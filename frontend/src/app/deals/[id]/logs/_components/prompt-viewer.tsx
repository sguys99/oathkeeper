"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";

interface PromptViewerProps {
  label: string;
  content: string | null;
  isJson?: boolean;
}

export function PromptViewer({ label, content, isJson }: PromptViewerProps) {
  const [expanded, setExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!content) return null;

  const displayContent = isJson
    ? JSON.stringify(JSON.parse(content), null, 2)
    : content;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="border-t pt-3">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground"
      >
        {expanded ? (
          <ChevronDown className="h-4 w-4" />
        ) : (
          <ChevronRight className="h-4 w-4" />
        )}
        {label}
      </button>
      {expanded && (
        <div className="relative mt-2">
          <Button
            variant="ghost"
            size="sm"
            className="absolute right-2 top-2 h-7 w-7 p-0"
            onClick={handleCopy}
          >
            {copied ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
          <pre className="max-h-80 overflow-auto rounded-md bg-muted p-4 text-xs leading-relaxed">
            {displayContent}
          </pre>
        </div>
      )}
    </div>
  );
}
