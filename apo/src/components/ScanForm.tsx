import { useState } from "react";
import { motion } from "framer-motion";
import { Search, ChevronDown, Wifi, WifiOff } from "lucide-react";
import type { ScanConfig } from "@/lib/api";

const jurisdictions = ["CCPA (California)", "GDPR (EU)", "LGPD (Brazil)", "PIPEDA (Canada)", "POPIA (South Africa)"];

interface ScanFormProps {
  onStartScan: (config: ScanConfig) => void;
  isScanning: boolean;
  backendAlive: boolean;
}

const ScanForm = ({ onStartScan, isScanning, backendAlive }: ScanFormProps) => {
  const [url, setUrl] = useState("https://www.cpchem.com");
  const [jurisdiction, setJurisdiction] = useState(jurisdictions[0]);
  const [crawlDepth, setCrawlDepth] = useState(3);
  const [showJurisdiction, setShowJurisdiction] = useState(false);

  const handleStart = () => {
    if (!url) return;
    onStartScan({
      url,
      framework: jurisdiction.split(" ")[0],
      crawl_depth: crawlDepth,
      use_llm: true,
    });
  };

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.4 }}
      className="max-w-4xl mx-auto px-4 mb-16"
    >
      <div className="glass-card p-6 md:p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <Search className="w-5 h-5 text-primary" />
            Configure Compliance Scan
          </h2>
          <div className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full border ${backendAlive
              ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
              : "text-yellow-400 border-yellow-400/30 bg-yellow-400/10"
            }`}>
            {backendAlive ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
            {backendAlive ? "Backend Connected" : "Demo Mode"}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {/* URL */}
          <div className="md:col-span-2">
            <label className="block text-sm text-muted-foreground mb-2">Target URL</label>
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full px-4 py-3 rounded-lg bg-muted/50 border border-border text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all font-mono text-sm"
            />
          </div>

          {/* Jurisdiction */}
          <div className="relative">
            <label className="block text-sm text-muted-foreground mb-2">Jurisdiction</label>
            <button
              onClick={() => setShowJurisdiction(!showJurisdiction)}
              className="w-full px-4 py-3 rounded-lg bg-muted/50 border border-border text-foreground text-left flex items-center justify-between text-sm"
            >
              {jurisdiction}
              <ChevronDown className="w-4 h-4 text-muted-foreground" />
            </button>
            {showJurisdiction && (
              <div className="absolute top-full left-0 right-0 mt-1 glass-card border border-border z-20 overflow-hidden">
                {jurisdictions.map((j) => (
                  <button
                    key={j}
                    onClick={() => { setJurisdiction(j); setShowJurisdiction(false); }}
                    className="w-full px-4 py-2.5 text-left text-sm text-foreground hover:bg-muted/50 transition-colors"
                  >
                    {j}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Crawl Depth */}
          <div>
            <label className="block text-sm text-muted-foreground mb-2">
              Crawl Depth: <span className="text-primary font-semibold">{crawlDepth}</span>
            </label>
            <input
              type="range" min={1} max={10} value={crawlDepth}
              onChange={(e) => setCrawlDepth(Number(e.target.value))}
              className="w-full accent-primary h-2 bg-muted rounded-full appearance-none cursor-pointer mt-2"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1"><span>1</span><span>10</span></div>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={isScanning || !url}
          className="btn-glow w-full mt-6 py-3.5 rounded-lg text-primary-foreground font-semibold text-sm tracking-wide uppercase flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isScanning ? (
            <>
              <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Scanning in Progress...
            </>
          ) : (
            "▶  Start Compliance Scan"
          )}
        </button>
      </div>
    </motion.section>
  );
};

export default ScanForm;
