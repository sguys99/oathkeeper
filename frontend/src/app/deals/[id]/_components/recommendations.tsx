"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

function stripOuterCodeFence(text: string): string {
  const trimmed = text.trim();
  const match = trimmed.match(/^```(?:markdown)?\s*\n([\s\S]*?)\n```\s*$/);
  return match ? match[1] : trimmed;
}

export function Recommendations({ markdown }: { markdown: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>권고사항</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {stripOuterCodeFence(markdown)}
          </ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
