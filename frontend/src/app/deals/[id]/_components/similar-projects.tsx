import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { SimilarProject } from "@/lib/api/types";

export function SimilarProjects({
  projects,
}: {
  projects: SimilarProject[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>유사 프로젝트</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4 sm:grid-cols-3">
          {projects.map((p, idx) => (
            <div
              key={idx}
              className="rounded-md border p-4 space-y-2"
            >
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">{p.project_name}</span>
                <Badge variant="secondary" className="text-xs">
                  {Math.round(p.similarity_score * 100)}%
                </Badge>
              </div>
              {p.industry && (
                <p className="text-xs text-muted-foreground">
                  산업: {p.industry}
                </p>
              )}
              {p.duration_months !== null && (
                <p className="text-xs text-muted-foreground">
                  기간: {p.duration_months}개월
                </p>
              )}
              {p.result && (
                <p className="text-xs text-muted-foreground">
                  결과: {p.result}
                </p>
              )}
              {p.tech_stack && p.tech_stack.length > 0 && (
                <div className="flex flex-wrap gap-1">
                  {p.tech_stack.map((tech) => (
                    <Badge key={tech} variant="outline" className="text-xs">
                      {tech}
                    </Badge>
                  ))}
                </div>
              )}
              {p.lessons_learned && (
                <p className="text-xs text-muted-foreground">
                  {p.lessons_learned}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
