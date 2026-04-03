"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import {
  FileText,
  PauseCircle,
  BarChart3,
  Users,
  ShieldAlert,
  Search,
  Scale,
  XCircle,
  CheckCircle,
  Brain,
  ScanEye,
  type LucideIcon,
} from "lucide-react";

// ── Prompt → node highlight mapping ─────────────────────────────────────

const PROMPT_NODE_MAP: Record<string, string[]> = {
  orchestrator: ["orchestrator", "reflection"],
  system: [
    "deal_structuring",
    "scoring",
    "resource_estimation",
    "risk_analysis",
    "similar_project",
    "final_verdict",
  ],
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
  orchestrator: {
    id: "orchestrator",
    label: "오케스트레이터",
    subtitle: "Orchestrator",
    Icon: Brain,
    iconBg: "bg-purple-500/10",
    iconText: "text-purple-500",
    highlightIconBg: "bg-purple-500",
  },
  deal_structuring: {
    id: "deal_structuring",
    label: "딜 구조화",
    subtitle: "Structuring",
    Icon: FileText,
    iconBg: "bg-blue-500/10",
    iconText: "text-blue-500",
    highlightIconBg: "bg-blue-500",
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
  reflection: {
    id: "reflection",
    label: "결과 검토",
    subtitle: "Reflection",
    Icon: ScanEye,
    iconBg: "bg-slate-500/10",
    iconText: "text-slate-500",
    highlightIconBg: "bg-slate-500",
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
}: {
  config: NodeConfig;
  highlighted: boolean;
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

      // START → orchestrator
      add("start", "bottom", "orchestrator", "top");

      // orchestrator → deal_structuring
      add("orchestrator", "bottom", "deal_structuring", "top");

      // deal_structuring → hold_verdict (dashed, curve to left branch)
      const dsBottom = getPos("deal_structuring", "bottom");
      const holdTop = getPos("hold_verdict", "top");
      if (dsBottom && holdTop) {
        const midY = (dsBottom.y + holdTop.y) / 2;
        const path = `M ${dsBottom.x},${dsBottom.y} C ${dsBottom.x},${midY} ${holdTop.x},${midY} ${holdTop.x},${holdTop.y}`;
        conns.push({ from: dsBottom, to: holdTop, dashed: true, path });
      }

      // hold_verdict → end_hold
      add("hold_verdict", "bottom", "end_hold", "top");

      // deal_structuring → parallel_group (continue, straight down)
      add("deal_structuring", "bottom", "parallel_group", "top");

      // parallel_group → reflection
      add("parallel_group", "bottom", "reflection", "top");

      // reflection → final_verdict
      add("reflection", "bottom", "final_verdict", "top");

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

        {/* Orchestrator */}
        <div ref={setNodeRef("orchestrator")} className="z-10 w-[200px]">
          <FlowNode
            config={NODES.orchestrator}
            highlighted={highlightedNodes.has("orchestrator")}
          />
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

        {/* Branch area: hold (left) | continue badge (right) */}
        <div className="z-10 flex w-full items-start">
          {/* Hold branch */}
          <div className="flex w-[140px] shrink-0 flex-col items-center gap-4">
            <div className="flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-1 text-xs font-medium text-red-500 dark:bg-red-500/10">
              <XCircle className="h-3.5 w-3.5" />
              <span>&#x2265;3 누락</span>
            </div>
            <div ref={setNodeRef("hold_verdict")} className="w-[140px]">
              <FlowNode config={NODES.hold_verdict} highlighted={false} />
            </div>
            <div ref={setNodeRef("end_hold")} className="mt-1">
              <Terminal label="END" />
            </div>
          </div>

          {/* Continue badge */}
          <div className="flex flex-1 items-start justify-center pt-0.5">
            <div className="flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-600 dark:bg-emerald-500/10">
              <CheckCircle className="h-3.5 w-3.5" />
              <span>계속</span>
            </div>
          </div>
        </div>

        {/* Parallel analysis group — full width, separate row */}
        <div
          ref={setNodeRef("parallel_group")}
          className="relative z-10 w-full rounded-lg border border-dashed border-border p-3 pt-6"
        >
          <span className="absolute -top-2.5 left-3 rounded bg-muted/80 px-1.5 text-[10px] font-medium text-muted-foreground">
            병렬 분석
          </span>
          <div className="grid grid-cols-2 gap-2.5">
            {(
              [
                "scoring",
                "resource_estimation",
                "risk_analysis",
                "similar_project",
              ] as const
            ).map((id) => (
              <FlowNode
                key={id}
                config={NODES[id]}
                highlighted={highlightedNodes.has(id)}
              />
            ))}
          </div>
        </div>

        {/* Reflection */}
        <div ref={setNodeRef("reflection")} className="z-10 w-[200px]">
          <FlowNode
            config={NODES.reflection}
            highlighted={highlightedNodes.has("reflection")}
          />
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
