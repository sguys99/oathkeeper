"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  FileText,
  GitBranch,
  PauseCircle,
  BarChart3,
  Users,
  ShieldAlert,
  Search,
  Scale,
  XCircle,
  CheckCircle,
  type LucideIcon,
} from "lucide-react";

// ── Prompt → node highlight mapping ─────────────────────────────────────

const PROMPT_NODE_MAP: Record<string, string[]> = {
  system: ["deal_structuring", "scoring"],
  deal_structuring: ["deal_structuring"],
  scoring: ["scoring"],
  resource_estimation: ["resource_estimation"],
  risk_analysis: ["risk_analysis"],
  similar_project: ["similar_project"],
  final_verdict: ["final_verdict"],
};

// ── Node configuration ──────────────────────────────────────────────────

interface NodeConfig {
  id: string;
  label: string;
  subtitle: string;
  Icon: LucideIcon;
  iconBg: string;
  iconText: string;
  highlightIconBg: string;
}

const NODES: Record<string, NodeConfig> = {
  deal_structuring: {
    id: "deal_structuring",
    label: "딜 구조화",
    subtitle: "Structuring",
    Icon: FileText,
    iconBg: "bg-blue-500/10",
    iconText: "text-blue-500",
    highlightIconBg: "bg-blue-500",
  },
  condition: {
    id: "condition",
    label: "필드 검증",
    subtitle: "Decision",
    Icon: GitBranch,
    iconBg: "bg-amber-500/10",
    iconText: "text-amber-500",
    highlightIconBg: "bg-amber-500",
  },
  hold_verdict: {
    id: "hold_verdict",
    label: "보류 판정",
    subtitle: "Hold Verdict",
    Icon: PauseCircle,
    iconBg: "bg-red-500/10",
    iconText: "text-red-500",
    highlightIconBg: "bg-red-500",
  },
  scoring: {
    id: "scoring",
    label: "스코어링",
    subtitle: "Scoring",
    Icon: BarChart3,
    iconBg: "bg-violet-500/10",
    iconText: "text-violet-500",
    highlightIconBg: "bg-violet-500",
  },
  resource_estimation: {
    id: "resource_estimation",
    label: "리소스 산정",
    subtitle: "Estimation",
    Icon: Users,
    iconBg: "bg-emerald-500/10",
    iconText: "text-emerald-500",
    highlightIconBg: "bg-emerald-500",
  },
  risk_analysis: {
    id: "risk_analysis",
    label: "리스크 분석",
    subtitle: "Risk Analysis",
    Icon: ShieldAlert,
    iconBg: "bg-orange-500/10",
    iconText: "text-orange-500",
    highlightIconBg: "bg-orange-500",
  },
  similar_project: {
    id: "similar_project",
    label: "유사 프로젝트",
    subtitle: "Similar Projects",
    Icon: Search,
    iconBg: "bg-cyan-500/10",
    iconText: "text-cyan-500",
    highlightIconBg: "bg-cyan-500",
  },
  final_verdict: {
    id: "final_verdict",
    label: "최종 판단",
    subtitle: "Final Verdict",
    Icon: Scale,
    iconBg: "bg-indigo-500/10",
    iconText: "text-indigo-500",
    highlightIconBg: "bg-indigo-500",
  },
};

// ── Sub-components ──────────────────────────────────────────────────────

function Terminal({ label, className }: { label: string; className?: string }) {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full bg-foreground px-3.5 py-1.5 text-xs font-semibold text-background",
        className,
      )}
    >
      {label}
    </div>
  );
}

function FlowNode({
  config,
  highlighted,
  isCondition,
}: {
  config: NodeConfig;
  highlighted: boolean;
  isCondition?: boolean;
}) {
  const { label, subtitle, Icon, iconBg, iconText, highlightIconBg } = config;

  return (
    <div className="relative">
      {/* Top port */}
      <div className="absolute -top-[3px] left-1/2 z-20 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-border" />
      {/* Bottom port */}
      <div className="absolute -bottom-[3px] left-1/2 z-20 h-1.5 w-1.5 -translate-x-1/2 rounded-full bg-border" />

      <div
        className={cn(
          "flex items-center gap-2.5 rounded-xl bg-card px-3 py-2.5 text-card-foreground ring-1 transition-all duration-200",
          highlighted
            ? "shadow-md ring-2 ring-primary"
            : "shadow-sm ring-foreground/10",
          isCondition && !highlighted && "border-l-4 border-amber-400",
        )}
      >
        {/* Icon badge */}
        <div
          className={cn(
            "flex h-7 w-7 shrink-0 items-center justify-center rounded-lg transition-colors duration-200",
            highlighted
              ? `${highlightIconBg} text-white`
              : `${iconBg} ${iconText}`,
          )}
        >
          <Icon className="h-3.5 w-3.5" />
        </div>
        {/* Text */}
        <div className="min-w-0">
          <div className="text-sm font-medium leading-tight">{label}</div>
          <div className="text-[11px] leading-tight text-muted-foreground">
            {subtitle}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Connector SVG layer ─────────────────────────────────────────────────

interface PortPos {
  x: number;
  y: number;
}

interface Connection {
  from: PortPos;
  to: PortPos;
  dashed?: boolean;
  path?: string; // custom SVG path override
}

function connectorPath(from: PortPos, to: PortPos): string {
  const dx = Math.abs(to.x - from.x);
  const dy = Math.abs(to.y - from.y);

  // Mostly horizontal: use step-wise path with rounded corners
  if (dx > dy * 0.8) {
    const midX = from.x + (to.x - from.x) * 0.5;
    return `M ${from.x},${from.y} L ${midX},${from.y} Q ${midX + Math.sign(to.x - from.x) * 8},${from.y} ${midX + Math.sign(to.x - from.x) * 8},${from.y + Math.sign(to.y - from.y) * 8} L ${midX + Math.sign(to.x - from.x) * 8},${to.y} L ${to.x},${to.y}`;
  }
  // Vertical: smooth bezier
  const offset = Math.min(Math.abs(dy) * 0.4, 30);
  return `M ${from.x},${from.y} C ${from.x},${from.y + offset} ${to.x},${to.y - offset} ${to.x},${to.y}`;
}

function ConnectorLayer({ connections }: { connections: Connection[] }) {
  return (
    <svg className="pointer-events-none absolute inset-0 h-full w-full overflow-visible">
      <defs>
        <marker
          id="flow-arrow"
          markerWidth="6"
          markerHeight="5"
          refX="5"
          refY="2.5"
          orient="auto"
        >
          <polygon points="0 0, 6 2.5, 0 5" className="fill-muted-foreground" />
        </marker>
      </defs>
      {connections.map((c, i) => (
        <g key={i}>
          <path
            d={c.path ?? connectorPath(c.from, c.to)}
            fill="none"
            className="stroke-muted-foreground"
            strokeWidth={1.5}
            strokeDasharray={c.dashed ? "4 3" : undefined}
            markerEnd="url(#flow-arrow)"
          />
          {/* Port dots at connection ends */}
          <circle cx={c.from.x} cy={c.from.y} r={2.5} className="fill-muted-foreground" />
          <circle cx={c.to.x} cy={c.to.y} r={2.5} className="fill-muted-foreground" />
        </g>
      ))}
    </svg>
  );
}

// ── Main component ──────────────────────────────────────────────────────

interface AgentFlowDiagramProps {
  selectedPrompt: string;
}

export function AgentFlowDiagram({ selectedPrompt }: AgentFlowDiagramProps) {
  const highlightedNodes = new Set(PROMPT_NODE_MAP[selectedPrompt] ?? []);
  const containerRef = useRef<HTMLDivElement>(null);
  const nodeRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const [connections, setConnections] = useState<Connection[]>([]);

  const setNodeRef = useCallback(
    (id: string) => (el: HTMLDivElement | null) => {
      nodeRefs.current[id] = el;
    },
    [],
  );

  useEffect(() => {
    function computeConnections() {
      const container = containerRef.current;
      if (!container) return;

      const rect = container.getBoundingClientRect();
      const getPos = (
        id: string,
        port: "top" | "bottom" | "left" | "right",
      ): PortPos | null => {
        const el = nodeRefs.current[id];
        if (!el) return null;
        const r = el.getBoundingClientRect();
        switch (port) {
          case "top":
            return {
              x: r.left + r.width / 2 - rect.left,
              y: r.top - rect.top,
            };
          case "bottom":
            return {
              x: r.left + r.width / 2 - rect.left,
              y: r.bottom - rect.top,
            };
          case "left":
            return {
              x: r.left - rect.left,
              y: r.top + r.height / 2 - rect.top,
            };
          case "right":
            return {
              x: r.right - rect.left,
              y: r.top + r.height / 2 - rect.top,
            };
        }
      };

      const conns: Connection[] = [];

      // Helper
      const add = (
        fromId: string,
        fromPort: "top" | "bottom" | "left" | "right",
        toId: string,
        toPort: "top" | "bottom" | "left" | "right",
        opts?: { dashed?: boolean; path?: string },
      ) => {
        const from = getPos(fromId, fromPort);
        const to = getPos(toId, toPort);
        if (from && to) conns.push({ from, to, ...opts });
      };

      // START → deal_structuring
      add("start", "bottom", "deal_structuring", "top");

      // deal_structuring → condition
      add("deal_structuring", "bottom", "condition", "top");

      // condition → fork → hold_verdict & phase1_group
      const condBottom = getPos("condition", "bottom");
      const holdTop = getPos("hold_verdict", "top");
      const phase1Top = getPos("phase1_group", "top");

      if (condBottom && holdTop) {
        // Bezier curve from condition bottom to hold_verdict top-center
        const midY = (condBottom.y + holdTop.y) / 2;
        const path = `M ${condBottom.x},${condBottom.y} C ${condBottom.x},${midY} ${holdTop.x},${midY} ${holdTop.x},${holdTop.y}`;
        conns.push({ from: condBottom, to: holdTop, dashed: true, path });
      }

      // hold_verdict → end_hold
      add("hold_verdict", "bottom", "end_hold", "top");

      if (condBottom && phase1Top) {
        // Bezier curve from condition bottom to phase1_group top-center
        const midY = (condBottom.y + phase1Top.y) / 2;
        const path = `M ${condBottom.x},${condBottom.y} C ${condBottom.x},${midY} ${phase1Top.x},${midY} ${phase1Top.x},${phase1Top.y}`;
        conns.push({ from: condBottom, to: phase1Top, path });
      }

      // phase1_group → phase2_group
      add("phase1_group", "bottom", "phase2_group", "top");

      // phase2_group → final_verdict (smooth S-curve for horizontal offset)
      const p2Bottom = getPos("phase2_group", "bottom");
      const fvTop = getPos("final_verdict", "top");
      if (p2Bottom && fvTop) {
        const midY = (p2Bottom.y + fvTop.y) / 2;
        const path = `M ${p2Bottom.x},${p2Bottom.y} C ${p2Bottom.x},${midY} ${fvTop.x},${fvTop.y - 20} ${fvTop.x},${fvTop.y}`;
        conns.push({ from: p2Bottom, to: fvTop, path });
      }

      // final_verdict → end_main
      add("final_verdict", "bottom", "end_main", "top");

      setConnections(conns);
    }

    const timer = setTimeout(computeConnections, 60);
    window.addEventListener("resize", computeConnections);
    return () => {
      clearTimeout(timer);
      window.removeEventListener("resize", computeConnections);
    };
  }, [selectedPrompt]);

  return (
    <div className="rounded-xl border border-border bg-muted/30 px-5 py-10">
      <div
        ref={containerRef}
        className="relative flex flex-col items-center gap-8"
      >
        <ConnectorLayer connections={connections} />

        {/* START */}
        <div ref={setNodeRef("start")} className="z-10">
          <Terminal label="START" />
        </div>

        {/* Deal Structuring */}
        <div
          ref={setNodeRef("deal_structuring")}
          className="z-10 w-[200px]"
        >
          <FlowNode
            config={NODES.deal_structuring}
            highlighted={highlightedNodes.has("deal_structuring")}
          />
        </div>

        {/* Condition */}
        <div
          ref={setNodeRef("condition")}
          className="z-10 w-[200px]"
        >
          <FlowNode config={NODES.condition} highlighted={false} isCondition />
        </div>

        {/* Branch area: hold (left) | continue (right) */}
        <div className="z-10 mb-4 flex w-full items-start gap-4">
          {/* Hold branch */}
          <div className="flex w-[200px] shrink-0 flex-col items-center gap-4">
            <div className="flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-500">
              <XCircle className="h-3.5 w-3.5" />
              <span>≥3 누락</span>
            </div>
            <div ref={setNodeRef("hold_verdict")} className="w-[200px]">
              <FlowNode config={NODES.hold_verdict} highlighted={false} />
            </div>
            <div ref={setNodeRef("end_hold")} className="mt-1">
              <Terminal label="END" />
            </div>
          </div>

          {/* Continue branch */}
          <div className="flex flex-1 flex-col items-center gap-4">
            <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-600">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>계속</span>
            </div>

            {/* Phase 1 parallel group */}
            <div
              ref={setNodeRef("phase1_group")}
              className="relative w-[220px] rounded-lg border border-dashed border-border p-2.5 pt-5"
            >
              <span className="absolute -top-2.5 left-3 rounded bg-muted/80 px-1.5 text-[10px] font-medium text-muted-foreground">
                Phase 1 병렬
              </span>
              <div className="flex flex-col gap-2">
                {(["resource_estimation", "similar_project"] as const).map(
                  (id) => (
                    <FlowNode
                      key={id}
                      config={NODES[id]}
                      highlighted={highlightedNodes.has(id)}
                    />
                  ),
                )}
              </div>
            </div>

            {/* Phase 2 parallel group */}
            <div
              ref={setNodeRef("phase2_group")}
              className="relative w-[220px] rounded-lg border border-dashed border-border p-2.5 pt-5"
            >
              <span className="absolute -top-2.5 left-3 rounded bg-muted/80 px-1.5 text-[10px] font-medium text-muted-foreground">
                Phase 2 병렬
              </span>
              <div className="flex flex-col gap-2">
                {(["scoring", "risk_analysis"] as const).map((id) => (
                  <FlowNode
                    key={id}
                    config={NODES[id]}
                    highlighted={highlightedNodes.has(id)}
                  />
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Final Verdict */}
        <div
          ref={setNodeRef("final_verdict")}
          className="z-10 w-[200px]"
        >
          <FlowNode
            config={NODES.final_verdict}
            highlighted={highlightedNodes.has("final_verdict")}
          />
        </div>

        {/* END */}
        <div ref={setNodeRef("end_main")} className="z-10">
          <Terminal label="END" />
        </div>
      </div>
    </div>
  );
}
