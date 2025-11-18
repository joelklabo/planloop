# 🔬 Ultimate PTY Debugging Plan - Next-Level Production Debugging

**Mission**: Catch, diagnose, and prevent PTY corruption using every tool at our disposal

**Context**: We have Copilot CLI with custom agents, slash commands, web dashboard, local logs, crash reporting, and full system access. Let's use ALL of it creatively!

---

## 🎯 The Complete Debugging Arsenal

### Layer 1: Predictive Prevention (Stop Failures Before They Happen)

**Custom Agent: `@pty-guardian`**

A persistent agent that runs in the background monitoring bash session health in real-time.

**Implementation:**
```bash
# Custom agent defined in ~/.copilot/agents/pty-guardian.yaml
name: pty-guardian
description: Real-time PTY health monitoring agent
capabilities:
  - health_monitoring
  - auto_rotation
  - alert_generation
  
# Runs continuously, checking health every 10 commands
mode: persistent
check_interval: 10_commands
```

**Features:**
1. **Continuous Health Scoring**
   ```python
   class PTYGuardian:
       def __init__(self):
           self.monitor = BashHealthMonitor()
           self.tracker = PTYResourceTracker()
           self.pattern_analyzer = CommandPatternAnalyzer()
           
       async def watch_session(self, session_id):
           """Monitor session in real-time."""
           while True:
               # Check health
               health = self.monitor.check_health()
               
               # Take resource snapshot
               snapshot = self.tracker.take_snapshot()
               
               # Analyze trends
               if health["health_score"] < 70:
                   await self.alert("⚠️ Health degrading", health)
               
               if health["health_score"] < 50:
                   await self.emergency_rotate()
               
               await asyncio.sleep(10)  # Check every 10s
   ```

2. **Command Pattern Interception**
   - Hook into bash command execution
   - Analyze before execution
   - Suggest optimizations
   - Block dangerous patterns

   ```python
   @hook("before_bash_command")
   def intercept_command(command):
       """Analyze command before execution."""
       issues = pattern_analyzer.analyze_command(command)
       
       if issues:
           for issue in issues:
               if issue["severity"] == "critical":
                   return {
                       "block": True,
                       "message": f"⛔ Blocked: {issue['recommendation']}",
                       "alternative": optimize_command(command)
                   }
               else:
                   warn(f"⚠️ {issue['recommendation']}")
       
       return {"allow": True}
   ```

3. **Smart Auto-Rotation**
   ```python
   async def emergency_rotate(self):
       """Automatically rotate session when critical."""
       # 1. Save current context
       context = await self.save_context()
       
       # 2. Create new session
       new_session = f"auto_rotate_{int(time.time())}"
       
       # 3. Transfer state
       await self.transfer_state(context, new_session)
       
       # 4. Log rotation
       await self.log_rotation_event({
           "reason": "health_critical",
           "old_session": self.session_id,
           "new_session": new_session,
           "final_health_score": self.last_health_score
       })
       
       # 5. Notify agent
       return {
           "action": "rotate",
           "new_session": new_session,
           "message": "🔄 Session rotated automatically for health"
       }
   ```

---

### Layer 2: Real-Time Distributed Tracing (OpenTelemetry Integration)

**Track every bash command as a distributed trace span.**

**Implementation: Custom Slash Command `/trace-session`**

```bash
# In ~/.copilot/commands/trace-session.sh
#!/bin/bash
# Enable OpenTelemetry tracing for bash session

export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME="copilot-bash-session"
export OTEL_RESOURCE_ATTRIBUTES="session.id=${SESSION_ID},agent=copilot"

# Wrap bash to emit traces
function traced_bash() {
    local cmd="$1"
    local trace_id=$(uuidgen)
    
    # Start span
    otel-cli span start \
        --service "bash-session" \
        --name "$cmd" \
        --kind client \
        --trace-id "$trace_id"
    
    # Execute command
    bash -c "$cmd"
    local exit_code=$?
    
    # End span with metadata
    otel-cli span end \
        --trace-id "$trace_id" \
        --attribute "command=$cmd" \
        --attribute "exit_code=$exit_code" \
        --attribute "pty_count=$(lsof -p $$ | grep -E 'pts|tty' | wc -l)"
    
    return $exit_code
}
```

**Visualization:**
- Use Jaeger or Grafana to see bash command flow
- Identify where PTY count spikes
- Correlate commands with health degradation
- Replay entire session visually

**Custom Agent: `@trace-analyzer`**
```python
class TraceAnalyzer:
    """Analyze OpenTelemetry traces for PTY patterns."""
    
    def analyze_trace(self, trace_id):
        """Analyze a session trace for PTY issues."""
        spans = self.fetch_spans(trace_id)
        
        analysis = {
            "total_commands": len(spans),
            "pty_growth": self.track_pty_growth(spans),
            "command_density": self.analyze_command_density(spans),
            "problematic_spans": self.find_problematic_spans(spans)
        }
        
        # Generate insights
        if analysis["pty_growth"] > 0.5:  # Growing 0.5 PTY per command
            return {
                "alert": "critical",
                "message": "Rapid PTY growth detected",
                "recommendation": "Rotate session immediately"
            }
        
        return analysis
```

---

### Layer 3: Kernel-Level Monitoring (eBPF/bpftrace)

**Custom Slash Command: `/ebpf-watch`**

Starts kernel-level monitoring of file descriptors and PTY operations.

```bash
#!/bin/bash
# ~/.copilot/commands/ebpf-watch.sh

PID=$$  # Current bash PID

# Start bpftrace monitoring
sudo bpftrace -e "
// Track open() calls
tracepoint:syscalls:sys_enter_openat
/pid == $PID/
{
    @opens[str(args->filename)] = count();
    printf(\"%s: OPEN %s\\n\", comm, str(args->filename));
}

// Track close() calls
tracepoint:syscalls:sys_enter_close
/pid == $PID/
{
    @closes[args->fd] = count();
    printf(\"%s: CLOSE fd=%d\\n\", comm, args->fd);
}

// Track PTY allocations
tracepoint:syscalls:sys_enter_openat
/pid == $PID && str(args->filename) =~ \"/dev/pts/\"/
{
    @pty_opens++;
    printf(\"⚠️ PTY ALLOCATED: %s\\n\", str(args->filename));
}

// Every 5 seconds, report FD leak status
interval:s:5
{
    printf(\"\\n=== FD LEAK CHECK ===\\n\");
    printf(\"PTYs allocated: %d\\n\", @pty_opens);
    printf(\"Total opens: %d\\n\", count(@opens));
    printf(\"Total closes: %d\\n\", count(@closes));
    
    // Calculate potential leaks
    \$leak_score = count(@opens) - count(@closes);
    if (\$leak_score > 10) {
        printf(\"🔴 LEAK DETECTED: %d unclosed FDs\\n\", \$leak_score);
    }
}

// On detach, show summary
END {
    print(@opens);
    print(@closes);
    printf(\"\\nFinal leak score: %d\\n\", count(@opens) - count(@closes));
}
" -o /tmp/ebpf-session-${SESSION_ID}.log &

echo "eBPF monitoring started (PID: $!)"
echo "Logs: /tmp/ebpf-session-${SESSION_ID}.log"
```

**Custom Agent: `@ebpf-analyzer`**
```python
class EBPFAnalyzer:
    """Parse eBPF logs to detect FD leaks."""
    
    def analyze_ebpf_log(self, log_path):
        """Analyze eBPF tracing logs."""
        with open(log_path) as f:
            logs = f.read()
        
        # Parse events
        opens = self.extract_opens(logs)
        closes = self.extract_closes(logs)
        pty_allocs = self.extract_pty_allocations(logs)
        
        # Calculate leaks
        leaked_fds = set(opens) - set(closes)
        
        return {
            "total_opens": len(opens),
            "total_closes": len(closes),
            "leaked_fds": list(leaked_fds),
            "pty_allocations": len(pty_allocs),
            "leak_score": len(leaked_fds),
            "verdict": "LEAK DETECTED" if len(leaked_fds) > 5 else "HEALTHY"
        }
```

---

### Layer 4: Session Recording & Replay (asciinema Integration)

**Automatically record every agent session for post-mortem analysis.**

**Custom Slash Command: `/record-session`**

```bash
#!/bin/bash
# ~/.copilot/commands/record-session.sh

SESSION_ID="${1:-$(uuidgen)}"
RECORDING_DIR="$HOME/.copilot/recordings"
mkdir -p "$RECORDING_DIR"

# Start asciinema recording
asciinema rec \
    --title "Copilot Session $SESSION_ID" \
    --command bash \
    --input \
    --overwrite \
    "$RECORDING_DIR/session-$SESSION_ID.cast"

# On exit, analyze recording
trap "analyze_recording $SESSION_ID" EXIT

analyze_recording() {
    local session_id=$1
    local cast_file="$RECORDING_DIR/session-$session_id.cast"
    
    # Generate analysis
    python3 <<EOF
import json

# Load recording
with open("$cast_file") as f:
    events = [json.loads(line) for line in f if line.strip()]

# Analyze
commands = [e for e in events if e[0] == "o"]  # Output events
total_commands = len([c for c in commands if "\\$ " in c[1]])

print(f"Session Analysis:")
print(f"  Total commands: {total_commands}")
print(f"  Duration: {events[-1][0]:.1f}s")
print(f"  Recording: $cast_file")

# Check for errors
errors = [c for c in commands if "error" in c[1].lower() or "failed" in c[1].lower()]
if errors:
    print(f"  ⚠️ {len(errors)} errors detected")
EOF
}
```

**Integration with Web Dashboard:**

```javascript
// Add to planloop web dashboard
class SessionReplayViewer {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.castFile = `/recordings/session-${sessionId}.cast`;
    }
    
    async render() {
        // Embed asciinema player
        const player = AsciinemaPlayer.create(
            this.castFile,
            document.getElementById('player-container'),
            {
                speed: 1,
                theme: 'monokai',
                idleTimeLimit: 2,
                poster: 'npt:0:10'
            }
        );
        
        // Add annotations for PTY events
        await this.addAnnotations(player);
    }
    
    async addAnnotations(player) {
        // Fetch PTY events from health monitoring
        const events = await fetch(`/api/pty-events/${this.sessionId}`).then(r => r.json());
        
        // Add markers at timestamps where PTY count spiked
        events.forEach(event => {
            player.addMarker(event.timestamp, {
                label: `PTY: ${event.pty_count}`,
                color: event.pty_count > 6 ? 'red' : 'yellow'
            });
        });
    }
}
```

---

### Layer 5: Crash Reporting (Sentry Integration)

**Send PTY failure reports to Sentry for aggregation and alerting.**

**Custom Agent: `@crash-reporter`**

```python
import sentry_sdk
from sentry_sdk import capture_exception, capture_message, set_context

class PTYCrashReporter:
    """Report PTY failures to Sentry."""
    
    def __init__(self):
        sentry_sdk.init(
            dsn="YOUR_SENTRY_DSN",
            environment="production",
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
    
    def report_pty_failure(self, session_data):
        """Report PTY failure with full context."""
        
        # Set context
        set_context("session", {
            "session_id": session_data["session_id"],
            "health_score": session_data["health_score"],
            "command_count": session_data["command_count"],
            "pty_count": session_data["pty_count"],
            "fd_count": session_data["fd_count"]
        })
        
        set_context("system", {
            "os": platform.system(),
            "pty_limit": self.get_pty_limit(),
            "fd_limit": self.get_fd_limit()
        })
        
        set_context("command_history", {
            "last_5_commands": session_data["command_history"][-5:],
            "problematic_patterns": session_data["problematic_patterns"]
        })
        
        # Capture exception
        try:
            raise PTYExhaustionError(
                f"PTY exhaustion in session {session_data['session_id']}"
            )
        except PTYExhaustionError as e:
            capture_exception(e)
        
        # Add breadcrumbs for command history
        for cmd in session_data["command_history"]:
            sentry_sdk.add_breadcrumb(
                category='bash',
                message=cmd["command"],
                level='info',
                data={
                    'cmd_number': cmd["cmd_number"],
                    'timestamp': cmd["timestamp"],
                    'pty_count': cmd.get("pty_count")
                }
            )
```

**Sentry Dashboard Features:**
- **Issue Grouping**: All PTY failures grouped together
- **Frequency Tracking**: How often failures occur
- **User Impact**: Which agents/users are affected
- **Release Tracking**: Did new version introduce regressions?
- **Performance Monitoring**: Correlate with system load
- **Alerts**: Slack/PagerDuty when failures spike

---

### Layer 6: Automated Forensics (Custom Agents)

**When PTY error occurs, automatically run forensic analysis.**

**Custom Agent: `@forensics`**

```python
class ForensicsAgent:
    """Automated forensics on PTY failure."""
    
    async def investigate_failure(self, session_id):
        """Run complete forensic analysis."""
        
        # 1. Capture system state
        system_state = await self.capture_system_state()
        
        # 2. Analyze transcript
        transcript_analysis = await self.analyze_transcript(session_id)
        
        # 3. Parse eBPF logs
        ebpf_analysis = await self.parse_ebpf_logs(session_id)
        
        # 4. Review session recording
        recording_analysis = await self.analyze_recording(session_id)
        
        # 5. Check distributed traces
        trace_analysis = await self.analyze_traces(session_id)
        
        # 6. Generate comprehensive report
        report = self.generate_forensic_report({
            "system_state": system_state,
            "transcript": transcript_analysis,
            "ebpf": ebpf_analysis,
            "recording": recording_analysis,
            "traces": trace_analysis
        })
        
        # 7. Send to Sentry
        await self.send_to_sentry(report)
        
        # 8. Store locally
        await self.save_report(report, f"/tmp/forensics-{session_id}.json")
        
        # 9. Notify user
        return {
            "status": "complete",
            "report_path": f"/tmp/forensics-{session_id}.json",
            "sentry_url": report["sentry_url"],
            "recommendations": report["recommendations"]
        }
    
    def generate_forensic_report(self, data):
        """Generate comprehensive forensic report."""
        return {
            "incident_id": f"pty-{int(time.time())}",
            "timestamp": datetime.now().isoformat(),
            
            "executive_summary": self.generate_summary(data),
            
            "timeline": self.reconstruct_timeline(data),
            
            "root_cause": self.identify_root_cause(data),
            
            "contributing_factors": self.identify_factors(data),
            
            "evidence": {
                "system_state": data["system_state"],
                "command_history": data["transcript"]["commands"],
                "fd_leaks": data["ebpf"]["leaked_fds"],
                "pty_growth": data["transcript"]["pty_growth"],
                "trace_spans": data["traces"]["spans"]
            },
            
            "recommendations": self.generate_recommendations(data),
            
            "prevention_plan": self.create_prevention_plan(data)
        }
```

---

### Layer 7: Web Dashboard Integration

**Real-time PTY health dashboard at `http://localhost:8000/pty-health`**

```python
# Add to planloop web server
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/pty-health")
async def pty_health_dashboard():
    """Live PTY health dashboard."""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>PTY Health Monitor</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/asciinema-player@3.0.1/dist/bundle/asciinema-player.min.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/asciinema-player@3.0.1/dist/bundle/asciinema-player.css">
</head>
<body>
    <h1>PTY Health Monitor</h1>
    
    <!-- Real-time health score -->
    <div id="health-score" class="metric">
        <h2>Health Score: <span id="score">100</span>/100</h2>
        <div id="score-bar"></div>
    </div>
    
    <!-- Live metrics -->
    <div class="metrics-grid">
        <div class="metric">
            <h3>Commands</h3>
            <span id="command-count">0</span>
        </div>
        <div class="metric">
            <h3>PTYs</h3>
            <span id="pty-count">0</span>
        </div>
        <div class="metric">
            <h3>FDs</h3>
            <span id="fd-count">0</span>
        </div>
    </div>
    
    <!-- PTY growth chart -->
    <canvas id="pty-chart"></canvas>
    
    <!-- Session recording -->
    <div id="player-container"></div>
    
    <!-- Alert feed -->
    <div id="alerts"></div>
    
    <script>
        // WebSocket connection for live updates
        const ws = new WebSocket('ws://localhost:8000/ws/pty-health');
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            // Update UI
            document.getElementById('score').textContent = data.health_score;
            document.getElementById('command-count').textContent = data.command_count;
            document.getElementById('pty-count').textContent = data.pty_count;
            document.getElementById('fd-count').textContent = data.fd_count;
            
            // Update chart
            updateChart(data);
            
            // Show alerts
            if (data.health_score < 60) {
                showAlert(data);
            }
        };
        
        function showAlert(data) {
            const alertDiv = document.getElementById('alerts');
            const alert = document.createElement('div');
            alert.className = 'alert alert-warning';
            alert.textContent = `⚠️ Health degrading: ${data.health_score}/100`;
            alertDiv.prepend(alert);
        }
    </script>
</body>
</html>
    """)

@app.websocket("/ws/pty-health")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live health updates."""
    await websocket.accept()
    
    monitor = BashHealthMonitor()
    
    while True:
        # Check health
        health = monitor.check_health()
        
        # Send to dashboard
        await websocket.send_json(health)
        
        await asyncio.sleep(2)  # Update every 2 seconds
```

---

### Layer 8: ML-Based Anomaly Detection

**Train a model to predict PTY failures before they happen.**

**Custom Agent: `@ml-predictor`**

```python
from sklearn.ensemble import RandomForestClassifier
import numpy as np

class PTYFailurePredictor:
    """ML model to predict PTY failures."""
    
    def __init__(self):
        self.model = RandomForestClassifier(n_estimators=100)
        self.trained = False
    
    def train(self, historical_sessions):
        """Train on historical session data."""
        X = []
        y = []
        
        for session in historical_sessions:
            # Extract features
            features = self.extract_features(session)
            X.append(features)
            
            # Label: 1 if failed, 0 if successful
            y.append(1 if session["failed"] else 0)
        
        # Train model
        self.model.fit(np.array(X), np.array(y))
        self.trained = True
    
    def extract_features(self, session):
        """Extract features from session."""
        return [
            session["command_count"],
            session["pty_count"],
            session["fd_count"],
            session["age_minutes"],
            session["avg_command_interval"],
            session["command_rate"],
            session["pty_growth_rate"],
            session["has_complex_chains"],
            session["has_subprocess_spawning"]
        ]
    
    def predict_failure_probability(self, current_session):
        """Predict likelihood of failure."""
        if not self.trained:
            return 0.5  # Unknown
        
        features = self.extract_features(current_session)
        probability = self.model.predict_proba([features])[0][1]
        
        return probability
    
    def should_rotate(self, current_session, threshold=0.7):
        """Recommend rotation based on ML prediction."""
        probability = self.predict_failure_probability(current_session)
        
        if probability > threshold:
            return {
                "rotate": True,
                "reason": "ml_prediction",
                "failure_probability": probability,
                "confidence": "high" if probability > 0.85 else "medium"
            }
        
        return {"rotate": False, "failure_probability": probability}
```

---

## 🚀 The Ultimate Workflow

**When starting a new agent session:**

```bash
# 1. Enable all monitoring
/trace-session
/ebpf-watch
/record-session

# 2. Start PTY guardian
@pty-guardian watch

# 3. Initialize ML predictor
@ml-predictor init

# 4. Open web dashboard
open http://localhost:8000/pty-health
```

**During the session:**

- Guardian monitors in background
- eBPF tracks kernel events
- OpenTelemetry traces commands
- asciinema records everything
- ML model predicts failures
- Web dashboard shows live status

**When health degrades:**

1. Guardian alerts
2. ML model suggests rotation
3. Web dashboard shows red
4. eBPF reports FD leaks
5. Traces show problematic commands
6. Agent automatically rotates if critical

**When failure occurs (despite prevention):**

1. `@forensics` agent automatically investigates
2. Captures all data sources
3. Generates comprehensive report
4. Sends to Sentry
5. Saves locally
6. Notifies user with actionable recommendations

**After session:**

```bash
# Analyze everything
@trace-analyzer analyze <session-id>
@ebpf-analyzer parse /tmp/ebpf-session-<id>.log
planloop monitor analyze-transcript <session-id>

# Review recording
asciinema play ~/.copilot/recordings/session-<id>.cast

# Check Sentry for patterns
open https://sentry.io/issues/?query=tag:pty_failure

# Train ML model on new data
@ml-predictor retrain
```

---

## 📊 Data Collection Schema

**Store every session with complete metadata:**

```json
{
  "session_id": "copilot-2025-11-18-235900",
  "agent": "claude",
  "start_time": "2025-11-18T23:59:00Z",
  "end_time": "2025-11-19T00:45:00Z",
  "duration_minutes": 46,
  
  "final_status": "success",
  "failure_detected": false,
  
  "metrics": {
    "total_commands": 47,
    "pty_peak": 8,
    "fd_peak": 203,
    "health_score_min": 55,
    "health_score_final": 72
  },
  
  "recordings": {
    "asciinema": "~/.copilot/recordings/session-xxx.cast",
    "ebpf_log": "/tmp/ebpf-session-xxx.log",
    "transcript": "~/.planloop/sessions/xxx/logs/agent-transcript.jsonl",
    "trace_id": "otel-trace-xxx"
  },
  
  "alerts": [
    {
      "timestamp": "2025-11-19T00:20:00Z",
      "type": "health_degraded",
      "health_score": 55,
      "message": "PTY count elevated (8, threshold: 6)"
    }
  ],
  
  "actions_taken": [
    {
      "timestamp": "2025-11-19T00:20:10Z",
      "action": "optimization_suggested",
      "command": "cd /path && source .venv && python",
      "recommendation": "Use .venv/bin/python directly"
    }
  ],
  
  "ml_predictions": [
    {
      "timestamp": "2025-11-19T00:30:00Z",
      "failure_probability": 0.75,
      "recommended_action": "rotate"
    }
  ]
}
```

---

## 🎯 Success Metrics

**You'll know the debugging plan is working when:**

1. **Zero Unexpected Failures**
   - All PTY failures caught proactively
   - Automatic rotation before corruption

2. **Sub-Minute Diagnosis**
   - From failure to root cause < 60 seconds
   - Complete forensic report generated automatically

3. **Continuous Learning**
   - ML model accuracy improves over time
   - Fewer false positives/negatives

4. **Full Observability**
   - Every command traced
   - Every FD tracked
   - Every session recorded
   - Complete audit trail

5. **Actionable Insights**
   - Clear recommendations
   - Specific code examples
   - Prevention strategies

---

## 🔧 Implementation Checklist

**Phase 1: Core Monitoring (Week 1)**
- [ ] Implement `@pty-guardian` agent
- [ ] Add `/trace-session` command
- [ ] Integrate `planloop monitor bash-health`
- [ ] Set up basic web dashboard

**Phase 2: Deep Diagnostics (Week 2)**
- [ ] Add `/ebpf-watch` command
- [ ] Integrate asciinema recording
- [ ] Implement `@ebpf-analyzer` agent
- [ ] Create forensics automation

**Phase 3: Production Integration (Week 3)**
- [ ] Set up Sentry integration
- [ ] Implement `@crash-reporter` agent
- [ ] Build web dashboard UI
- [ ] Add WebSocket live updates

**Phase 4: Intelligence (Week 4)**
- [ ] Train ML prediction model
- [ ] Implement `@ml-predictor` agent
- [ ] Add automatic rotation logic
- [ ] Create feedback loops

**Phase 5: Polish (Week 5)**
- [ ] Add session replay to dashboard
- [ ] Implement pattern detection
- [ ] Create alerting rules
- [ ] Write documentation

---

## 💡 Creative Bonus Ideas

### 1. **PTY Health Badge**
Add to GitHub Copilot CLI prompt:
```
[🟢 PTY: 95/100]  # Shows current health inline
```

### 2. **Slack Integration**
```python
# Send alerts to Slack
@app.route("/webhook/pty-alert")
def slack_alert(health_data):
    slack_client.chat_postMessage(
        channel="#copilot-alerts",
        text=f"⚠️ PTY health degrading: {health_data['health_score']}/100",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Session*: {health_data['session_id']}\n*Score*: {health_data['health_score']}/100"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Rotate Now"},
                        "action_id": "rotate_session"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Dashboard"},
                        "url": "http://localhost:8000/pty-health"
                    }
                ]
            }
        ]
    )
```

### 3. **GitHub Issue Auto-Creation**
When pattern detected 3+ times:
```python
def create_github_issue(pattern):
    """Auto-create GitHub issue for recurring pattern."""
    gh_client.create_issue(
        repo="planloop",
        title=f"PTY Issue: {pattern['name']} detected {pattern['count']} times",
        body=f"""
## Problem
{pattern['description']}

## Occurrences
- First seen: {pattern['first_seen']}
- Last seen: {pattern['last_seen']}
- Count: {pattern['count']}

## Evidence
- Sessions affected: {', '.join(pattern['sessions'])}
- Common commands: {pattern['common_commands']}

## Recommendation
{pattern['recommendation']}

## Auto-generated by @forensics agent
        """,
        labels=["pty", "automated", "bug"]
    )
```

### 4. **Time-Travel Debugging**
```bash
# Replay session from any point
/replay-from <timestamp>

# Step through commands one-by-one
/step-through <session-id>

# Show "what-if" with different command
/simulate-alternative <command>
```

### 5. **Predictive Rotation Schedule**
```python
# Based on ML model, suggest optimal rotation times
def suggest_rotation_schedule(user_patterns):
    """Suggest when to rotate based on user patterns."""
    return {
        "optimal_command_count": 35,  # ML-determined
        "optimal_duration": "40 minutes",
        "best_rotation_triggers": [
            "After test suite runs",
            "Before long-running builds",
            "Every 30 minutes during peak hours"
        ]
    }
```

---

## 🎬 Conclusion

**This is not just debugging—it's a complete observability platform for PTY health.**

With this plan, you'll have:
- ✅ Real-time monitoring
- ✅ Automatic prevention
- ✅ Kernel-level visibility
- ✅ Complete audit trail
- ✅ ML-powered predictions
- ✅ Instant forensics
- ✅ Production-ready alerting
- ✅ Beautiful dashboards

**The next PTY failure won't stand a chance.** 🎯

You'll catch it before it happens, and if it somehow still occurs, you'll have a complete forensic report in under 60 seconds with actionable recommendations.

**Let's catch that bug!** 🐛🔬
