import { motion } from "framer-motion";

const HeroSection = () => {
  return (
    <section className="relative overflow-hidden py-20 px-4">
      {/* Animated gradient background */}
      <div className="absolute inset-0 opacity-30">
        <div
          className="absolute inset-0 animate-float"
          style={{
            background:
              "radial-gradient(ellipse at 20% 50%, hsla(234, 85%, 65%, 0.4) 0%, transparent 50%), radial-gradient(ellipse at 80% 50%, hsla(270, 50%, 55%, 0.4) 0%, transparent 50%), radial-gradient(ellipse at 50% 80%, hsla(300, 70%, 70%, 0.2) 0%, transparent 50%)",
          }}
        />
      </div>
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI0MCIgaGVpZ2h0PSI0MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAwIDEwIEwgNDAgMTAgTSAxMCAwIEwgMTAgNDAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-50" />

      <div className="relative z-10 max-w-5xl mx-auto text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-6 glass-card text-sm text-muted-foreground border border-primary/20 bg-primary/5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
            Next-Generation Privacy Compliance
          </div>
          <h1 className="text-5xl md:text-7xl font-black tracking-tight mb-4">
            <span className="gradient-text">APO</span>{" "}
            <span className="text-foreground">FRAMEWORK</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
            Autonomous Privacy Observability — Secure, AI-driven compliance scanning to safeguard your platform against GDPR, CCPA, and global privacy regulations.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
          className="flex items-center justify-center gap-6 mt-8 text-sm text-muted-foreground"
        >
          {["3-Tier Architecture", "Real-Time Monitoring", "Multi-Jurisdiction"].map(
            (label) => (
              <div key={label} className="flex items-center gap-2">
                <div className="w-1 h-1 rounded-full gradient-bg" />
                {label}
              </div>
            )
          )}
        </motion.div>
      </div>
    </section>
  );
};

export default HeroSection;
