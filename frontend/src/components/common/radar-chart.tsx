"use client";

import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
} from "recharts";
import type { ScoreDetail } from "@/lib/api/types";

const SHORT_LABELS: Record<string, string> = {
  "기술 적합성": "기술",
  "수익성": "수익",
  "리소스 가용성": "리소스",
  "일정 리스크": "일정",
  "고객 리스크": "고객",
  "요구사항 명확성": "요구사항",
  "전략적 가치": "전략",
};

function shortenLabel(criterion: string): string {
  return SHORT_LABELS[criterion] ?? criterion;
}

export function RadarChart({ scores }: { scores: ScoreDetail[] }) {
  const data = scores.map((s) => ({
    criterion: shortenLabel(s.criterion),
    score: s.score,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RechartsRadarChart data={data}>
        <PolarGrid />
        <PolarAngleAxis dataKey="criterion" tick={{ fontSize: 12 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
        <Radar
          dataKey="score"
          stroke="hsl(220, 70%, 50%)"
          fill="hsl(220, 70%, 50%)"
          fillOpacity={0.3}
        />
      </RechartsRadarChart>
    </ResponsiveContainer>
  );
}
