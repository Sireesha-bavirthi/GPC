import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";

interface ViolationsTableProps {
  isComplete: boolean;
  result: any | null;
}

// Fallback demo violations (when no backend result)
const DEMO_VIOLATIONS = [
  { violation_type: "GPC_NOT_HONORED", rule_id: "CCPA-1798.135b-01", section: "§1798.135(b)(1)", severity: "HIGH", evidence: { domains_ignoring_gpc: ["connect.facebook.net", "googletagmanager.com"] }, recommendation: "Stop tracker beacons when Sec-GPC: 1 is received" },
  { violation_type: "TEMPORAL_LEAK", rule_id: "CCPA-1798.135b-01", section: "§1798.135(b)(1)", severity: "HIGH", evidence: { leak_count: 180, leaked_domains: ["bat.bing.com", "px.ads.linkedin.com"] }, recommendation: "Pre-block trackers before page load when GPC is detected" },
  { violation_type: "MISSING_DO_NOT_SELL_LINK", rule_id: "CCPA-1798.135a-01", section: "§1798.135(a)", severity: "HIGH", evidence: { pages_missing_link: 13 }, recommendation: "Add 'Do Not Sell or Share My Personal Info' link to all pages" },
  { violation_type: "PII_IN_TRACKING_REQUESTS", rule_id: "CCPA-1798.100-01", section: "§1798.100", severity: "MEDIUM", evidence: { total_pii_hits: 4 }, recommendation: "Remove or anonymize PII from outbound tracker URLs" },
];

const severityClass: Record<string, string> = {
  HIGH: "severity-critical", MEDIUM: "severity-high", LOW: "severity-low", CRITICAL: "severity-critical",
};

const ViolationsTable = ({ isComplete, result }: ViolationsTableProps) => {
  if (!isComplete) return null;

  const violations = result?.violations?.length ? result.violations : DEMO_VIOLATIONS;

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="max-w-6xl mx-auto px-4 mb-16"
    >
      <h2 className="text-lg font-semibold text-foreground mb-6">
        Violations Report
        <span className="ml-2 text-sm font-normal text-muted-foreground">({violations.length} issues)</span>
      </h2>
      <div className="glass-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-muted-foreground font-medium text-xs uppercase tracking-wider">Severity</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium text-xs uppercase tracking-wider">Rule</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium text-xs uppercase tracking-wider">Violation Type</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium text-xs uppercase tracking-wider hidden lg:table-cell">Evidence</th>
                <th className="text-left py-3 px-4 text-muted-foreground font-medium text-xs uppercase tracking-wider hidden md:table-cell">Regulation</th>
              </tr>
            </thead>
            <tbody>
              {violations.map((v: any, i: number) => (
                <motion.tr
                  key={i}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="border-b border-border/50 hover:bg-muted/30 transition-colors"
                >
                  <td className="py-3 px-4">
                    <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-semibold text-primary-foreground ${severityClass[v.severity] ?? "severity-low"}`}>
                      {v.severity}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-mono text-muted-foreground text-xs">{v.rule_id}</td>
                  <td className="py-3 px-4">
                    <div className="text-foreground font-medium">{v.violation_type?.replace(/_/g, " ")}</div>
                    {v.recommendation && (
                      <div className="text-xs text-muted-foreground mt-0.5 max-w-xs truncate">{v.recommendation}</div>
                    )}
                  </td>
                  <td className="py-3 px-4 hidden lg:table-cell">
                    <div className="text-xs text-muted-foreground font-mono max-w-xs">
                      {typeof v.evidence === "object"
                        ? Object.entries(v.evidence).slice(0, 2).map(([k, val]) => (
                          <div key={k}><span className="text-primary/70">{k}:</span> {String(val).slice(0, 40)}</div>
                        ))
                        : String(v.evidence).slice(0, 80)}
                    </div>
                  </td>
                  <td className="py-3 px-4 hidden md:table-cell">
                    <span className="flex items-center gap-1 text-xs text-primary cursor-pointer hover:underline">
                      {v.section} <ExternalLink className="w-3 h-3" />
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </motion.section>
  );
};

export default ViolationsTable;
