import { motion } from "framer-motion";
import { Download, FileJson, Database, GitBranch, FileText, CheckCircle2, Clock } from "lucide-react";

const BACKEND = "https://d2rh3h60ye9e31.cloudfront.net";
const TOKEN = "fake-token-for-testing-123";

interface DownloadFile {
  label: string;
  filename: string;
  icon: React.ReactNode;
  description: string;
  size: string;
  tag: string;
  tagColor: string;
}

const FILES: DownloadFile[] = [
  {
    label: "Evidence Report",
    filename: "evidence_report.json",
    icon: <FileJson className="w-5 h-5" />,
    description: "Full CCPA compliance audit — violations, rules, penalties & LLM analysis",
    size: "9.0 KB",
    tag: "PRIMARY",
    tagColor: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
  },
  {
    label: "Traffic Baseline",
    filename: "traffic_baseline.json",
    icon: <Database className="w-5 h-5" />,
    description: "All network requests captured during the GPC-OFF baseline browsing session",
    size: "459 KB",
    tag: "GPC-OFF",
    tagColor: "bg-red-500/20 text-red-400 border-red-500/30",
  },
  {
    label: "Traffic Compliance",
    filename: "traffic_compliance.json",
    icon: <Database className="w-5 h-5" />,
    description: "Network requests captured during the GPC-ON compliance session (Sec-GPC: 1)",
    size: "455 KB",
    tag: "GPC-ON",
    tagColor: "bg-teal-500/20 text-teal-400 border-teal-500/30",
  },
  {
    label: "Interaction Graph",
    filename: "interaction_graph.json",
    icon: <GitBranch className="w-5 h-5" />,
    description: "Page dependency graph built by Discovery Agent — nodes, edges, risk scores",
    size: "34 KB",
    tag: "GRAPH",
    tagColor: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  },
  {
    label: "Proxy Traffic Log",
    filename: "raw_traffic_proxy.jsonl",
    icon: <FileText className="w-5 h-5" />,
    description: "Raw mitmproxy JSONL capture with full request/response headers per request",
    size: "Live",
    tag: "PROXY",
    tagColor: "bg-purple-500/20 text-purple-400 border-purple-500/30",
  },
];

// Scan summary stats — shown at top of section (from last run)
const SCAN_SUMMARY = {
  target: "www.cpchem.com",
  verdict: "NON-COMPLIANT",
  violations: 4,
  pagesScanned: 13,
  maxPenalty: "$30,000",
  generatedAt: "Feb 20, 2026 · 17:11 IST",
};

interface DownloadSectionProps {
  isComplete: boolean;
  scanId: string | null;
}

const DownloadSection = ({ isComplete, scanId }: DownloadSectionProps) => {
  const handleDownload = async (filename: string) => {
    try {
      const res = await fetch(`${BACKEND}/api/download/${filename}`, {
        headers: { "Authorization": `Bearer ${TOKEN}` }
      });
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
        return;
      }
    } catch {
      // backend not available
    }
    // Fallback: tell user to start backend
    alert(`Backend not reachable. Start the backend with:\ncd apo_v2 && python backend.py`);
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="max-w-6xl mx-auto px-4 mb-20"
    >
      <h2 className="text-lg font-semibold text-foreground mb-6 flex items-center gap-2">
        <Download className="w-5 h-5 text-primary" />
        Report Downloads
      </h2>

      {/* Scan summary card */}
      <div
        className="glass-card p-5 mb-6 flex flex-wrap items-center gap-6 border"
        style={{ borderColor: SCAN_SUMMARY.verdict === "NON-COMPLIANT" ? "rgba(239,68,68,0.25)" : "rgba(52,211,153,0.25)" }}
      >
        <div className="text-3xl">{SCAN_SUMMARY.verdict === "NON-COMPLIANT" ? "🚨" : "✅"}</div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`text-xs font-bold px-2.5 py-0.5 rounded-full ${SCAN_SUMMARY.verdict === "NON-COMPLIANT"
                ? "bg-red-500/20 text-red-400"
                : "bg-emerald-500/20 text-emerald-400"
                }`}
            >
              {SCAN_SUMMARY.verdict}
            </span>
            {(isComplete || scanId) && (
              <span className="text-xs text-emerald-400 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Latest scan complete
              </span>
            )}
          </div>
          <div className="font-semibold text-foreground">{SCAN_SUMMARY.target}</div>
          <div className="text-xs text-muted-foreground flex items-center gap-1 mt-0.5">
            <Clock className="w-3 h-3" /> {SCAN_SUMMARY.generatedAt}
          </div>
        </div>
        <div className="flex gap-6 text-center shrink-0">
          <div>
            <div className="text-2xl font-black text-red-400">{SCAN_SUMMARY.violations}</div>
            <div className="text-xs text-muted-foreground">Violations</div>
          </div>
          <div>
            <div className="text-2xl font-black text-primary">{SCAN_SUMMARY.pagesScanned}</div>
            <div className="text-xs text-muted-foreground">Pages</div>
          </div>
          <div>
            <div className="text-2xl font-black text-yellow-400">{SCAN_SUMMARY.maxPenalty}</div>
            <div className="text-xs text-muted-foreground">Max Fine</div>
          </div>
        </div>
      </div>

      {/* File grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {FILES.map((f, i) => (
          <motion.button
            key={f.filename}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.07 }}
            onClick={() => handleDownload(f.filename)}
            className="glass-card-hover p-4 text-left flex flex-col gap-3 w-full group"
          >
            {/* Top row */}
            <div className="flex items-start justify-between">
              <div className="p-2 rounded-lg gradient-bg text-primary-foreground shrink-0">
                {f.icon}
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${f.tagColor}`}>
                  {f.tag}
                </span>
                <Download className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
            </div>

            {/* Label + desc */}
            <div>
              <div className="font-semibold text-foreground text-sm">{f.label}</div>
              <div className="text-xs text-muted-foreground mt-1 leading-relaxed">{f.description}</div>
            </div>

            {/* Size + filename */}
            <div className="flex items-center justify-between mt-auto">
              <span className="font-mono text-[11px] text-muted-foreground/70">{f.filename}</span>
              <span className="text-xs text-muted-foreground bg-muted/50 px-2 py-0.5 rounded">{f.size}</span>
            </div>
          </motion.button>
        ))}
      </div>
    </motion.section>
  );
};

export default DownloadSection;
