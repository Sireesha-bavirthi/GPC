import { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { Terminal } from "lucide-react";
import type { LogEvent } from "@/lib/api";

interface TerminalLogProps {
  isScanning: boolean;
  scanProgress: number;
  logs: LogEvent[];
}

const levelColor = (level: string) => {
  if (level === "ERROR") return "text-red-400";
  if (level === "WARNING") return "text-yellow-400";
  if (level === "SUCCESS") return "text-emerald-400";
  return "text-teal-400";
};

const agentColor = (agent: string) => {
  if (agent === "discovery") return "text-cyan-400";
  if (agent === "interaction") return "text-teal-300";
  if (agent === "observability") return "text-sky-300";
  return "text-muted-foreground";
};

const TerminalLog = ({ isScanning, scanProgress, logs }: TerminalLogProps) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <section className="max-w-6xl mx-auto px-4 mb-16">
      <h2 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
        <Terminal className="w-5 h-5 text-primary" />
        Live Scan Output
      </h2>
      <div className="terminal-bg rounded-xl border border-border overflow-hidden">
        {/* Mac-style top bar */}
        <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border/50">
          <div className="w-3 h-3 rounded-full bg-red-500/70" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/70" />
          <div className="w-3 h-3 rounded-full bg-emerald-500/70" />
          <span className="ml-2 text-xs text-muted-foreground font-mono">apo-framework — scan output</span>
          {isScanning && (
            <span className="ml-auto flex items-center gap-1.5 text-xs text-teal-400">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-pulse" />
              LIVE
            </span>
          )}
        </div>
        <div
          ref={scrollRef}
          className="p-4 h-64 overflow-y-auto font-mono text-xs leading-relaxed"
        >
          {logs.length === 0 && (
            <div className="text-muted-foreground">
              Waiting for scan to start...
              <span className="animate-pulse">▊</span>
            </div>
          )}
          {logs.map((log, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -5 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.15 }}
              className="flex gap-2 mb-0.5"
            >
              <span className="text-muted-foreground/50 shrink-0">[{log.timestamp || "00:00:00"}]</span>
              <span className={`shrink-0 font-semibold ${agentColor(log.agent)}`}>[{log.agent.toUpperCase().slice(0, 5)}]</span>
              <span className={`shrink-0 font-semibold ${levelColor(log.level)}`}>{log.level}</span>
              <span className="text-foreground/80">{log.msg}</span>
            </motion.div>
          ))}
          {isScanning && scanProgress < 100 && logs.length > 0 && (
            <span className="text-primary animate-pulse">▊</span>
          )}
        </div>
      </div>
    </section>
  );
};

export default TerminalLog;
