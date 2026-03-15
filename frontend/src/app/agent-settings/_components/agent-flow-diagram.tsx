"use client";

const PROMPT_NODE_MAP: Record<string, string[]> = {
  system: ["deal_structuring", "scoring"],
  deal_structuring: ["deal_structuring"],
  scoring: ["scoring"],
  resource_estimation: ["resource_estimation"],
  risk_analysis: ["risk_analysis"],
  similar_project: ["similar_project"],
  final_verdict: ["final_verdict"],
};

const NODE_LABELS: Record<string, string> = {
  deal_structuring: "딜 구조화",
  scoring: "스코어링",
  resource_estimation: "리소스 산정",
  risk_analysis: "리스크 분석",
  similar_project: "유사 프로젝트",
  final_verdict: "최종 판단",
  hold_verdict: "보류 판정",
};

interface AgentFlowDiagramProps {
  selectedPrompt: string;
}

function NodeBox({
  x,
  y,
  width,
  height,
  id,
  highlighted,
}: {
  x: number;
  y: number;
  width: number;
  height: number;
  id: string;
  highlighted: boolean;
}) {
  const label = NODE_LABELS[id] ?? id;
  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={height}
        rx={8}
        fill={highlighted ? "#3b82f6" : "#f4f4f5"}
        stroke={highlighted ? "#2563eb" : "#d4d4d8"}
        strokeWidth={highlighted ? 2 : 1}
      />
      <text
        x={x + width / 2}
        y={y + height / 2 + 1}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={10}
        fontWeight={highlighted ? 600 : 400}
        fill={highlighted ? "#ffffff" : "#3f3f46"}
      >
        {label}
      </text>
    </g>
  );
}

function Circle({
  cx,
  cy,
  label,
}: {
  cx: number;
  cy: number;
  label: string;
}) {
  return (
    <g>
      <circle cx={cx} cy={cy} r={14} fill="#18181b" />
      <text
        x={cx}
        y={cy + 1}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={9}
        fontWeight={600}
        fill="#ffffff"
      >
        {label}
      </text>
    </g>
  );
}

function Diamond({
  cx,
  cy,
  size,
  label,
}: {
  cx: number;
  cy: number;
  size: number;
  label: string;
}) {
  const points = `${cx},${cy - size} ${cx + size},${cy} ${cx},${cy + size} ${cx - size},${cy}`;
  return (
    <g>
      <polygon
        points={points}
        fill="#fef3c7"
        stroke="#f59e0b"
        strokeWidth={1.5}
      />
      <text
        x={cx}
        y={cy + 1}
        textAnchor="middle"
        dominantBaseline="central"
        fontSize={9}
        fontWeight={500}
        fill="#92400e"
      >
        {label}
      </text>
    </g>
  );
}

function Arrow({
  x1,
  y1,
  x2,
  y2,
}: {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}) {
  return (
    <line
      x1={x1}
      y1={y1}
      x2={x2}
      y2={y2}
      stroke="#a1a1aa"
      strokeWidth={1.5}
      markerEnd="url(#arrowhead)"
    />
  );
}

function ArrowPath({ d }: { d: string }) {
  return (
    <path
      d={d}
      fill="none"
      stroke="#a1a1aa"
      strokeWidth={1.5}
      markerEnd="url(#arrowhead)"
    />
  );
}

export function AgentFlowDiagram({ selectedPrompt }: AgentFlowDiagramProps) {
  const highlightedNodes = new Set(PROMPT_NODE_MAP[selectedPrompt] ?? []);

  // Layout constants — vertical top-to-bottom flow
  const svgW = 300;
  const svgH = 420;
  const nodeW = 90;
  const nodeH = 26;
  const pNodeW = 85;
  const pNodeH = 22;
  const centerX = svgW / 2 + 20;

  // Y positions (top → bottom)
  const startY = 16;
  const dealY = 48;
  const condY = 104;
  const parallelTopY = 156;
  const parallelGap = 30;
  const endMainY = 380;

  // Hold branch (left side)
  const holdCenterX = 60;
  const holdY = 156;
  const endHoldY = 206;

  // final_verdict centered between parallel bottom and END
  const parallelBottomY = parallelTopY + parallelGap * 3 + pNodeH + 12;
  const endMainCenterY = endMainY + 14;
  const finalY = (parallelBottomY + endMainCenterY) / 2 - nodeH / 2;

  // Parallel nodes
  const parallelNodeX = centerX - pNodeW / 2;
  const pNodes = [
    { id: "scoring", y: parallelTopY },
    { id: "resource_estimation", y: parallelTopY + parallelGap },
    { id: "risk_analysis", y: parallelTopY + parallelGap * 2 },
    { id: "similar_project", y: parallelTopY + parallelGap * 3 },
  ];

  return (
    <div className="rounded-lg border border-border p-4">
      <svg
        viewBox={`0 0 ${svgW} ${svgH}`}
        className="w-full"
        role="img"
        aria-label="OathKeeper 에이전트 파이프라인 다이어그램"
      >
        <defs>
          <marker
            id="arrowhead"
            markerWidth="8"
            markerHeight="6"
            refX="7"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 8 3, 0 6" fill="#a1a1aa" />
          </marker>
        </defs>

        {/* START */}
        <Circle cx={centerX} cy={startY} label="START" />

        {/* START → deal_structuring */}
        <Arrow x1={centerX} y1={startY + 14} x2={centerX} y2={dealY} />

        {/* deal_structuring */}
        <NodeBox
          x={centerX - nodeW / 2}
          y={dealY}
          width={nodeW}
          height={nodeH}
          id="deal_structuring"
          highlighted={highlightedNodes.has("deal_structuring")}
        />

        {/* deal_structuring → condition */}
        <Arrow
          x1={centerX}
          y1={dealY + nodeH}
          x2={centerX}
          y2={condY - 18}
        />

        {/* Condition diamond */}
        <Diamond cx={centerX} cy={condY} size={18} label="조건" />

        {/* Condition → Hold (left branch) */}
        <ArrowPath
          d={`M ${centerX - 18} ${condY} L ${holdCenterX} ${condY} L ${holdCenterX} ${holdY}`}
        />
        <text x={holdCenterX + 4} y={condY - 6} fontSize={8} fill="#a1a1aa">
          ≥3 누락
        </text>

        {/* hold_verdict */}
        <NodeBox
          x={holdCenterX - nodeW / 2}
          y={holdY}
          width={nodeW}
          height={nodeH}
          id="hold_verdict"
          highlighted={false}
        />

        {/* hold → END */}
        <Arrow
          x1={holdCenterX}
          y1={holdY + nodeH}
          x2={holdCenterX}
          y2={endHoldY}
        />
        <Circle cx={holdCenterX} cy={endHoldY + 14} label="END" />

        {/* Condition → Parallel (down) */}
        <Arrow
          x1={centerX}
          y1={condY + 18}
          x2={centerX}
          y2={parallelTopY - 18}
        />
        <text x={centerX + 4} y={condY + 32} fontSize={8} fill="#a1a1aa">
          계속
        </text>

        {/* Parallel group dashed box */}
        <rect
          x={parallelNodeX - 12}
          y={parallelTopY - 12}
          width={pNodeW + 24}
          height={parallelGap * 3 + pNodeH + 24}
          rx={8}
          fill="none"
          stroke="#d4d4d8"
          strokeWidth={1}
          strokeDasharray="5 3"
        />
        <text
          x={parallelNodeX - 6}
          y={parallelTopY - 18}
          fontSize={9}
          fill="#a1a1aa"
        >
          병렬 실행
        </text>

        {/* Parallel nodes */}
        {pNodes.map((node) => (
          <NodeBox
            key={node.id}
            x={parallelNodeX}
            y={node.y}
            width={pNodeW}
            height={pNodeH}
            id={node.id}
            highlighted={highlightedNodes.has(node.id)}
          />
        ))}

        {/* Parallel → final_verdict */}
        <Arrow
          x1={centerX}
          y1={parallelBottomY}
          x2={centerX}
          y2={finalY}
        />

        {/* final_verdict */}
        <NodeBox
          x={centerX - nodeW / 2}
          y={finalY}
          width={nodeW}
          height={nodeH}
          id="final_verdict"
          highlighted={highlightedNodes.has("final_verdict")}
        />

        {/* final_verdict → END */}
        <Arrow
          x1={centerX}
          y1={finalY + nodeH}
          x2={centerX}
          y2={endMainY}
        />
        <Circle cx={centerX} cy={endMainY + 14} label="END" />
      </svg>
    </div>
  );
}
