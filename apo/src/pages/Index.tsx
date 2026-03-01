import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import HeroSection from "@/components/HeroSection";
import ScanForm from "@/components/ScanForm";
import AgentCards from "@/components/AgentCards";
import MetricsDashboard from "@/components/MetricsDashboard";
import ViolationsTable from "@/components/ViolationsTable";
import ArchitectureFlowchart from "@/components/ArchitectureFlowchart";
import DownloadSection from "@/components/DownloadSection";
import TerminalLog from "@/components/TerminalLog";
import { startScan, streamLogs, getResults, healthCheck, type LogEvent, type ScanConfig } from "@/lib/api";

// ─── State shape ──────────────────────────────────────
interface AgentProgress {
  discovery: number;
  interaction: number;
  observability: number;
}

interface ScanState {
  isScanning: boolean;
  isComplete: boolean;
  scanId: string | null;
  agentProgress: AgentProgress;
  logs: LogEvent[];
  result: any | null;
  useBackend: boolean;   // false if backend unavailable → simulation
  isUnauthorized: boolean;
}

const INITIAL: ScanState = {
  isScanning: false,
  isComplete: false,
  scanId: null,
  agentProgress: { discovery: 0, interaction: 0, observability: 0 },
  logs: [],
  result: null,
  useBackend: false,
  isUnauthorized: false,
};

// ─── Simulated log feed (used when backend is offline) ─
const SIM_LOGS: LogEvent[] = [
  { timestamp: "", agent: "discovery", level: "INFO", msg: "Playwright browser launched" },
  { timestamp: "", agent: "discovery", level: "INFO", msg: "[01/13] Crawling https://www.cpchem.com — Claude analyzing..." },
  { timestamp: "", agent: "discovery", level: "SUCCESS", msg: "Risk 8/10 — PII forms + no DNS link detected" },
  { timestamp: "", agent: "interaction", level: "INFO", msg: "Claude planning session strategy across 13 pages" },
  { timestamp: "", agent: "interaction", level: "INFO", msg: "[BASELINE] GPC-OFF session started" },
  { timestamp: "", agent: "interaction", level: "WARNING", msg: "⚠ Temporal leak: 15 trackers fired <500ms on /becoming-supplier" },
  { timestamp: "", agent: "interaction", level: "SUCCESS", msg: "Both sessions complete | 1240 baseline / 1229 compliance requests" },
  { timestamp: "", agent: "observability", level: "INFO", msg: "Loading 11 CCPA rules from rules.sql" },
  { timestamp: "", agent: "observability", level: "ERROR", msg: "VIOLATION: GPC_NOT_HONORED — 6 domains ignored Sec-GPC:1" },
  { timestamp: "", agent: "observability", level: "ERROR", msg: "VIOLATION: TEMPORAL_LEAK — 180 leaks detected" },
  { timestamp: "", agent: "observability", level: "ERROR", msg: "VIOLATION: MISSING_DO_NOT_SELL_LINK — 0/13 pages" },
  { timestamp: "", agent: "observability", level: "WARNING", msg: "VIOLATION: PII_IN_TRACKING_REQUESTS — uid in 4 tracker URLs" },
  { timestamp: "", agent: "observability", level: "SUCCESS", msg: "Evidence report generated — 4 violations | max fine $30,000" },
];

function nowTime() {
  return new Date().toLocaleTimeString("en-US", { hour12: false });
}

// ─── Component ────────────────────────────────────────
const Index = () => {
  const [state, setState] = useState<ScanState>(INITIAL);
  const cleanupRef = useRef<(() => void) | null>(null);

  // Check if backend is alive on mount
  useEffect(() => {
    healthCheck().then((status) => {
      if (status === "unauthorized") {
        setState((s) => ({ ...s, isUnauthorized: true }));
      } else if (status === "ok") {
        setState((s) => ({ ...s, useBackend: true }));
      }
    });
  }, []);

  // Derive legacy props from state
  const scanProgress =
    (state.agentProgress.discovery + state.agentProgress.interaction + state.agentProgress.observability) / 3;

  const handleStartScan = useCallback(async (config: ScanConfig) => {
    // Cleanup previous stream if any
    if (cleanupRef.current) { cleanupRef.current(); cleanupRef.current = null; }

    setState({
      ...INITIAL,
      useBackend: state.useBackend,
      isScanning: true,
    });

    // ── Backend path ───────────────────────────────────
    if (state.useBackend) {
      try {
        const scanId = await startScan(config);
        setState((s) => ({ ...s, scanId }));
        toast("Scan started", { description: `Scan ID: ${scanId} — streaming live from backend` });

        const cleanup = streamLogs(
          scanId,
          (ev) => {
            const ts = { ...ev, timestamp: ev.timestamp || nowTime() };
            setState((s) => {
              const prog = { ...s.agentProgress };
              // Infer rough progress from log count per agent
              const agentLogs = [...s.logs, ts].filter((l) => l.agent === ev.agent);
              if (ev.agent !== "system") prog[ev.agent as keyof AgentProgress] = Math.min(agentLogs.length * 8, 95);
              if (ev.level === "SUCCESS" && ev.agent !== "system") prog[ev.agent as keyof AgentProgress] = 100;
              return { ...s, logs: [...s.logs, ts], agentProgress: prog };
            });
          },
          async (status) => {
            if (status === "complete") {
              try {
                const result = await getResults(scanId);
                setState((s) => ({ ...s, isScanning: false, isComplete: true, result, agentProgress: { discovery: 100, interaction: 100, observability: 100 } }));
                toast.success("Scan complete!", { description: `${result?.violation_summary?.total ?? 0} violations found — report ready` });
              } catch {
                setState((s) => ({ ...s, isScanning: false }));
              }
            } else {
              setState((s) => ({ ...s, isScanning: false }));
              toast.error("Scan encountered an error");
            }
          }
        );
        cleanupRef.current = cleanup;
      } catch (err) {
        toast.error("Backend unavailable — switching to simulation");
        setState((s) => ({ ...s, useBackend: false }));
        runSimulation();
      }
      return;
    }

    // ── Simulation path (no backend) ───────────────────
    runSimulation();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [state.useBackend]);

  const runSimulation = () => {
    toast("Demo mode — backend offline", { description: "Connect backend for real scans" });
    let i = 0;
    const agentOrder = ["discovery", "interaction", "observability"] as const;
    let agentIdx = 0;

    const interval = setInterval(() => {
      if (i >= SIM_LOGS.length) {
        clearInterval(interval);
        setState((s) => ({
          ...s, isScanning: false, isComplete: true,
          agentProgress: { discovery: 100, interaction: 100, observability: 100 },
        }));
        toast.success("Scan complete", { description: "4 violations found — report ready" });
        return;
      }
      const ev = { ...SIM_LOGS[i], timestamp: nowTime() };
      i++;

      setState((s) => {
        const prog = { ...s.agentProgress };
        // Advance whichever agent is in ev
        if (ev.agent !== "system" && ev.agent in prog) {
          prog[ev.agent as keyof AgentProgress] = Math.min(s.agentProgress[ev.agent as keyof AgentProgress] + 9, ev.level === "SUCCESS" ? 100 : 90);
        }
        return { ...s, logs: [...s.logs, ev], agentProgress: prog };
      });

      if (i === 3) toast("Discovery Agent complete", { description: "Interaction Agent activated" });
      if (i === 7) toast("Interaction Agent complete", { description: "Observability Agent activated" });
    }, 900);
  };

  if (state.isUnauthorized) {
    return (
      <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
        <div className="max-w-md w-full glass-card p-8 text-center space-y-4 border border-red-500/30">
          <div className="w-16 h-16 bg-red-500/10 text-red-500 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" /></svg>
          </div>
          <h1 className="text-2xl font-bold text-foreground">Access Denied</h1>
          <p className="text-muted-foreground text-sm">
            You do not have permission to view this application. The security token provided is invalid or missing.
          </p>
          <div className="text-xs bg-muted p-2 rounded text-muted-foreground font-mono mt-4">
            HTTP 401 Unauthorized
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <HeroSection />
      <ScanForm onStartScan={handleStartScan} isScanning={state.isScanning} backendAlive={state.useBackend} />
      <AgentCards isScanning={state.isScanning} scanProgress={scanProgress} agentProgress={state.agentProgress} />
      <TerminalLog isScanning={state.isScanning} scanProgress={scanProgress} logs={state.logs} />
      {state.isComplete && (
        <>
          <MetricsDashboard isComplete={state.isComplete} result={state.result} />
          <ViolationsTable isComplete={state.isComplete} result={state.result} />
          <ArchitectureFlowchart />
          <DownloadSection isComplete={state.isComplete} scanId={state.scanId} />
        </>
      )}

      <footer className="text-center py-8 text-xs text-muted-foreground border-t border-border">
        APO Framework v2 — Autonomous Privacy Observability
        {state.useBackend ? (
          <span className="ml-3 text-green-400">● Backend Connected</span>
        ) : (
          <span className="ml-3 text-yellow-500">● Backend Offline (Demo Mode)</span>
        )}
      </footer>
    </div>
  );
};

export default Index;
