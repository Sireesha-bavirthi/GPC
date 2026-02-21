import { motion } from "framer-motion";

const ArchitectureFlowchart = () => {
  return (
    <section className="max-w-6xl mx-auto px-4 mb-16">
      <h2 className="text-lg font-semibold text-foreground mb-6">System Architecture</h2>
      <div className="glass-card p-6 md:p-8 overflow-x-auto">
        <svg viewBox="0 0 900 320" className="w-full min-w-[600px]" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#667eea" />
              <stop offset="100%" stopColor="#764ba2" />
            </linearGradient>
            <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#11998e" />
              <stop offset="100%" stopColor="#38ef7d" />
            </linearGradient>
            <linearGradient id="grad3" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#f2994a" />
              <stop offset="100%" stopColor="#f2c94c" />
            </linearGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Tier Labels */}
          <text x="150" y="30" textAnchor="middle" fill="#667eea" fontSize="12" fontWeight="600" fontFamily="Inter">TIER 1 — DISCOVERY</text>
          <text x="450" y="30" textAnchor="middle" fill="#38ef7d" fontSize="12" fontWeight="600" fontFamily="Inter">TIER 2 — INTERACTION</text>
          <text x="750" y="30" textAnchor="middle" fill="#f2c94c" fontSize="12" fontWeight="600" fontFamily="Inter">TIER 3 — OBSERVABILITY</text>

          {/* Tier 1 boxes */}
          <rect x="50" y="50" width="200" height="50" rx="8" fill="url(#grad1)" opacity="0.15" stroke="#667eea" strokeWidth="1" />
          <text x="150" y="80" textAnchor="middle" fill="#c4d0ff" fontSize="13" fontFamily="Inter" fontWeight="500">Web Crawler</text>

          <rect x="50" y="120" width="200" height="50" rx="8" fill="url(#grad1)" opacity="0.15" stroke="#667eea" strokeWidth="1" />
          <text x="150" y="150" textAnchor="middle" fill="#c4d0ff" fontSize="13" fontFamily="Inter" fontWeight="500">Cookie Scanner</text>

          <rect x="50" y="190" width="200" height="50" rx="8" fill="url(#grad1)" opacity="0.15" stroke="#667eea" strokeWidth="1" />
          <text x="150" y="220" textAnchor="middle" fill="#c4d0ff" fontSize="13" fontFamily="Inter" fontWeight="500">Tracker Detector</text>

          {/* Tier 2 boxes */}
          <rect x="350" y="50" width="200" height="50" rx="8" fill="url(#grad2)" opacity="0.15" stroke="#38ef7d" strokeWidth="1" />
          <text x="450" y="80" textAnchor="middle" fill="#a5f3d0" fontSize="13" fontFamily="Inter" fontWeight="500">Consent Tester</text>

          <rect x="350" y="120" width="200" height="50" rx="8" fill="url(#grad2)" opacity="0.15" stroke="#38ef7d" strokeWidth="1" />
          <text x="450" y="150" textAnchor="middle" fill="#a5f3d0" fontSize="13" fontFamily="Inter" fontWeight="500">Form Analyzer</text>

          <rect x="350" y="190" width="200" height="50" rx="8" fill="url(#grad2)" opacity="0.15" stroke="#38ef7d" strokeWidth="1" />
          <text x="450" y="220" textAnchor="middle" fill="#a5f3d0" fontSize="13" fontFamily="Inter" fontWeight="500">Policy Parser</text>

          {/* Tier 3 boxes */}
          <rect x="650" y="50" width="200" height="50" rx="8" fill="url(#grad3)" opacity="0.15" stroke="#f2c94c" strokeWidth="1" />
          <text x="750" y="80" textAnchor="middle" fill="#fde68a" fontSize="13" fontFamily="Inter" fontWeight="500">Risk Scorer</text>

          <rect x="650" y="120" width="200" height="50" rx="8" fill="url(#grad3)" opacity="0.15" stroke="#f2c94c" strokeWidth="1" />
          <text x="750" y="150" textAnchor="middle" fill="#fde68a" fontSize="13" fontFamily="Inter" fontWeight="500">Report Generator</text>

          <rect x="650" y="190" width="200" height="50" rx="8" fill="url(#grad3)" opacity="0.15" stroke="#f2c94c" strokeWidth="1" />
          <text x="750" y="220" textAnchor="middle" fill="#fde68a" fontSize="13" fontFamily="Inter" fontWeight="500">Remediation Engine</text>

          {/* Arrows */}
          <line x1="250" y1="75" x2="350" y2="75" stroke="#667eea" strokeWidth="1.5" opacity="0.5" markerEnd="url(#arrow)" filter="url(#glow)" />
          <line x1="250" y1="145" x2="350" y2="145" stroke="#667eea" strokeWidth="1.5" opacity="0.5" filter="url(#glow)" />
          <line x1="250" y1="215" x2="350" y2="215" stroke="#667eea" strokeWidth="1.5" opacity="0.5" filter="url(#glow)" />

          <line x1="550" y1="75" x2="650" y2="75" stroke="#38ef7d" strokeWidth="1.5" opacity="0.5" filter="url(#glow)" />
          <line x1="550" y1="145" x2="650" y2="145" stroke="#38ef7d" strokeWidth="1.5" opacity="0.5" filter="url(#glow)" />
          <line x1="550" y1="215" x2="650" y2="215" stroke="#38ef7d" strokeWidth="1.5" opacity="0.5" filter="url(#glow)" />

          {/* Data Store */}
          <rect x="325" y="270" width="250" height="40" rx="8" fill="url(#grad1)" opacity="0.2" stroke="#667eea" strokeWidth="1" strokeDasharray="4 2" />
          <text x="450" y="295" textAnchor="middle" fill="#c4d0ff" fontSize="12" fontFamily="Inter" fontWeight="500">Compliance Data Store</text>

          {/* Vertical lines to data store */}
          <line x1="150" y1="240" x2="150" y2="290" stroke="#667eea" strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />
          <line x1="150" y1="290" x2="325" y2="290" stroke="#667eea" strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />

          <line x1="750" y1="240" x2="750" y2="290" stroke="#f2c94c" strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />
          <line x1="750" y1="290" x2="575" y2="290" stroke="#f2c94c" strokeWidth="1" opacity="0.3" strokeDasharray="3 3" />
        </svg>
      </div>
    </section>
  );
};

export default ArchitectureFlowchart;
