import { motion } from "framer-motion";
import { Bot, Eye, BarChart3, CheckCircle2, Loader2 } from "lucide-react";

interface Agent {
  name: string;
  icon: React.ReactNode;
  status: "idle" | "running" | "complete";
  progress: number;
  description: string;
  tasks: string[];
}

interface AgentCardsProps {
  isScanning: boolean;
  scanProgress: number;
  agentProgress?: { discovery: number; interaction: number; observability: number };
}

const AgentCards = ({ isScanning, scanProgress, agentProgress }: AgentCardsProps) => {
  const agents: Agent[] = [
    {
      name: "Discovery Agent",
      icon: <Bot className="w-5 h-5" />,
      status: isScanning
        ? ((agentProgress?.discovery ?? scanProgress * 3) >= 100 ? "complete" : "running")
        : "idle",
      progress: agentProgress?.discovery ?? (isScanning ? Math.min(scanProgress * 3, 100) : 0),
      description: "Crawls target URL and maps data flows",
      tasks: ["Page enumeration", "Cookie detection", "Third-party tracker scan", "Consent banner check"],
    },
    {
      name: "Interaction Agent",
      icon: <Eye className="w-5 h-5" />,
      status: isScanning
        ? ((agentProgress?.interaction ?? 0) >= 100 ? "complete" : (agentProgress?.discovery ?? scanProgress) >= 100 ? "running" : "idle")
        : "idle",
      progress: agentProgress?.interaction ?? (isScanning ? Math.max(0, Math.min((scanProgress - 30) * 3, 100)) : 0),
      description: "Tests user-facing privacy controls",
      tasks: ["Consent flow testing", "Opt-out verification", "Data request forms", "Privacy policy analysis"],
    },
    {
      name: "Observability Agent",
      icon: <BarChart3 className="w-5 h-5" />,
      status: isScanning
        ? ((agentProgress?.observability ?? 0) >= 100 ? "complete" : (agentProgress?.interaction ?? 0) >= 100 ? "running" : "idle")
        : "idle",
      progress: agentProgress?.observability ?? (isScanning ? Math.max(0, Math.min((scanProgress - 60) * 3, 100)) : 0),
      description: "Correlates findings and generates compliance score",
      tasks: ["Violation classification", "Risk scoring", "Report generation", "Remediation mapping"],
    },
  ];

  return (
    <section className="max-w-6xl mx-auto px-4 mb-16">
      <h2 className="text-lg font-semibold text-foreground mb-6">Agent Execution Pipeline</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {agents.map((agent, i) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 * i }}
            className="glass-card-hover p-5"
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg gradient-bg text-primary-foreground">
                  {agent.icon}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-foreground">{agent.name}</h3>
                  <p className="text-xs text-muted-foreground">{agent.description}</p>
                </div>
              </div>
              {agent.status === "running" && <Loader2 className="w-4 h-4 text-primary animate-spin" />}
              {agent.status === "complete" && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
            </div>

            {/* Progress bar */}
            <div className="h-1.5 rounded-full bg-muted mb-4 overflow-hidden">
              <motion.div
                className="h-full rounded-full progress-bar-animated"
                initial={{ width: 0 }}
                animate={{ width: `${agent.progress}%` }}
                transition={{ duration: 0.5 }}
              />
            </div>

            {/* Task list */}
            <div className="space-y-1.5">
              {agent.tasks.map((task, j) => {
                const taskProgress = agent.progress / 25;
                const isDone = taskProgress > j + 1;
                const isActive = taskProgress > j && taskProgress <= j + 1;
                return (
                  <div
                    key={task}
                    className={`flex items-center gap-2 text-xs py-1 px-2 rounded transition-colors ${isDone ? "text-emerald-400" : isActive ? "text-primary" : "text-muted-foreground"
                      }`}
                  >
                    {isDone ? (
                      <CheckCircle2 className="w-3 h-3 flex-shrink-0" />
                    ) : isActive ? (
                      <Loader2 className="w-3 h-3 flex-shrink-0 animate-spin" />
                    ) : (
                      <div className="w-3 h-3 rounded-full border border-muted-foreground/30 flex-shrink-0" />
                    )}
                    {task}
                  </div>
                );
              })}
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
};

export default AgentCards;
