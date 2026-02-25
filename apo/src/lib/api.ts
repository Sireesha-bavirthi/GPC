/**
 * APO v2 — API Client
 * Connects the React frontend to the FastAPI backend at http://localhost:8000
 */

const BASE = "http://localhost:8000";
const TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc3MjQ1ODMxMX0.4R6BiFuxZvDbzZNEwr55C6FZ04pwIF920XvYkLCN3Qo";

const _authHeaders = {
    "Authorization": `Bearer ${TOKEN}`
};

export interface ScanConfig {
    url: string;
    framework: string;
    crawl_depth: number;
    use_llm: boolean;
    claude_key?: string;
    openai_key?: string;
}

export interface LogEvent {
    timestamp: string;
    agent: "discovery" | "interaction" | "observability" | "system";
    level: "INFO" | "WARNING" | "ERROR" | "SUCCESS" | "DONE";
    msg: string;
}

export interface ScanStatus {
    scan_id: string;
    status: "pending" | "running" | "complete" | "error";
    phase: string;
    progress: { discovery: number; interaction: number; observability: number };
    event_count: number;
    error?: string;
}

/** Start a new scan and return the scan_id */
export async function startScan(config: ScanConfig): Promise<string> {
    const res = await fetch(`${BASE}/api/scan`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            ..._authHeaders
        },
        body: JSON.stringify(config),
    });
    if (!res.ok) throw new Error(`Start scan failed: ${res.status}`);
    const data = await res.json();
    return data.scan_id as string;
}

/** Poll scan status (fallback when SSE isn't used) */
export async function getScanStatus(scanId: string): Promise<ScanStatus> {
    const res = await fetch(`${BASE}/api/status/${scanId}`, { headers: _authHeaders });
    if (!res.ok) throw new Error("Status check failed");
    return res.json();
}

/** Fetch final evidence report */
export async function getResults(scanId: string): Promise<any> {
    const res = await fetch(`${BASE}/api/results/${scanId}`, { headers: _authHeaders });
    if (!res.ok) throw new Error("Results not ready");
    return res.json();
}

/**
 * Subscribe to SSE log stream.
 * Calls onEvent for every LogEvent, onDone when pipeline finishes.
 * Returns a cleanup function to close the stream.
 */
export function streamLogs(
    scanId: string,
    onEvent: (ev: LogEvent) => void,
    onDone: (status: "complete" | "error") => void
): () => void {
    const src = new EventSource(`${BASE}/api/stream/${scanId}?token=${TOKEN}`);

    src.onmessage = (e) => {
        try {
            const ev: LogEvent = JSON.parse(e.data);
            if (ev.level === "DONE") {
                onDone(ev.msg as "complete" | "error");
                src.close();
            } else {
                onEvent(ev);
            }
        } catch (_) {
            // ignore malformed events
        }
    };

    src.onerror = () => {
        onDone("error");
        src.close();
    };

    return () => src.close();
}

/** Download URL for output files */
export function downloadUrl(filename: string): string {
    return `${BASE}/api/download/${filename}?token=${TOKEN}`;
}

/** Check if backend is reachable */
export async function healthCheck(): Promise<"ok" | "unauthorized" | "offline"> {
    try {
        const res = await fetch(`${BASE}/health`, {
            headers: _authHeaders,
            signal: AbortSignal.timeout(3000)
        });
        if (res.status === 401) return "unauthorized";
        return res.ok ? "ok" : "offline";
    } catch {
        return "offline";
    }
}
