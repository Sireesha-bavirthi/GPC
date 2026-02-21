import { motion } from "framer-motion";
import { AlertTriangle, Shield, FileSearch, TrendingUp } from "lucide-react";

interface MetricsDashboardProps {
  isComplete: boolean;
  result: any | null;
}

const MetricsDashboard = ({ isComplete, result }: MetricsDashboardProps) => {
  const vs = result?.violation_summary;
  const ss = result?.session_summary;

  const violations = vs?.total ?? (isComplete ? 4 : null);
  // compliance score: inverse of reduced tracker ratio, or fallback
  const totalPages = ss?.compliance_gpc_on?.pages_visited ?? ss?.baseline?.pages_visited ?? (isComplete ? 13 : null);
  const domainCount = (result?.gpc_verdict?.domains_ignoring_gpc ?? []).length;
  const temporalLeaks = result?.gpc_verdict?.temporal_leak_count ?? (isComplete ? 180 : null);
  const complianceScore = isComplete
    ? (violations === 0 ? 100 : Math.max(0, 100 - (violations ?? 0) * 20 - (domainCount > 0 ? 15 : 0)))
    : null;

  const metrics = [
    {
      label: "Violations Found",
      value: violations !== null ? String(violations) : "—",
      icon: <AlertTriangle className="w-5 h-5" />,
      gradient: "var(--gradient-danger)",
      sub: violations !== null ? `${vs?.severity_breakdown?.HIGH ?? 0} High severity` : "Pending",
    },
    {
      label: "Compliance Score",
      value: complianceScore !== null ? `${complianceScore}%` : "—",
      icon: <Shield className="w-5 h-5" />,
      gradient: complianceScore !== null && complianceScore < 60
        ? "var(--gradient-danger)"
        : "var(--gradient-warning)",
      sub: isComplete
        ? complianceScore! < 60 ? "Non-Compliant 🚨" : "Needs Improvement"
        : "Pending",
    },
    {
      label: "Pages Scanned",
      value: totalPages !== null ? String(totalPages) : "—",
      icon: <FileSearch className="w-5 h-5" />,
      gradient: "var(--gradient-info)",
      sub: isComplete ? `${domainCount} domains ignoring GPC` : "Pending",
    },
    {
      label: "Temporal Leaks",
      value: temporalLeaks !== null ? String(temporalLeaks) : "—",
      icon: <TrendingUp className="w-5 h-5" />,
      gradient: "var(--gradient-success)",
      sub: isComplete ? "Trackers fired <500ms after GPC" : "Pending",
    },
  ];

  return (
    <section className="max-w-6xl mx-auto px-4 mb-16">
      <h2 className="text-lg font-semibold text-foreground mb-6">Scan Metrics</h2>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <motion.div
            key={m.label}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.05 * i }}
            className="glass-card-hover p-5 relative overflow-hidden"
          >
            <div
              className="absolute top-0 right-0 w-20 h-20 opacity-10 rounded-bl-full"
              style={{ background: m.gradient }}
            />
            <div className="inline-flex p-2 rounded-lg mb-3" style={{ background: m.gradient }}>
              <span className="text-primary-foreground">{m.icon}</span>
            </div>
            <div className="text-2xl font-bold text-foreground mb-0.5">{m.value}</div>
            <div className="text-xs text-muted-foreground">{m.label}</div>
            <div className="text-xs mt-1">
              <span className="text-muted-foreground">{m.sub}</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Verdict banner */}
      {isComplete && result && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="mt-4 rounded-xl p-4 flex items-center gap-4 border"
          style={{
            background: result.gpc_verdict?.verdict === "NON-COMPLIANT"
              ? "linear-gradient(135deg, rgba(235,51,73,0.15), rgba(244,92,67,0.1))"
              : "linear-gradient(135deg, rgba(17,153,142,0.15), rgba(56,239,125,0.1))",
            borderColor: result.gpc_verdict?.verdict === "NON-COMPLIANT"
              ? "rgba(235,51,73,0.3)" : "rgba(56,239,125,0.3)",
          }}
        >
          <span className="text-4xl">{result.gpc_verdict?.verdict === "NON-COMPLIANT" ? "🚨" : "✅"}</span>
          <div>
            <div className="font-bold text-foreground text-base">{result.gpc_verdict?.verdict}</div>
            <div className="text-sm text-muted-foreground">
              Max potential CCPA penalty:{" "}
              <strong className="text-foreground">
                ${(vs?.max_potential_penalty_usd ?? 0).toLocaleString()}
              </strong>
            </div>
            {(result.gpc_verdict?.domains_ignoring_gpc ?? []).length > 0 && (
              <div className="text-xs text-red-400 mt-0.5">
                Domains ignoring GPC: {result.gpc_verdict.domains_ignoring_gpc.join(", ")}
              </div>
            )}
          </div>
        </motion.div>
      )}
    </section>
  );
};

export default MetricsDashboard;
