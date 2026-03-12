"use client";

import ReactMarkdown from "react-markdown";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function Recommendations({ markdown }: { markdown: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>권고사항</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <ReactMarkdown>{markdown}</ReactMarkdown>
        </div>
      </CardContent>
    </Card>
  );
}
