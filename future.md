# 🔮 GhostOS X — Future Engineering Roadmap & Architecture Analysis

This document outlines the architectural enhancements, performance optimizations, and future capabilities planned for **GhostOS X**, the zero-dependency proactive desktop orchestration engine.

---

## 🏛️ Current Architectural State & Technical Audit

### Core Strengths
- **Sub-Millisecond Overhead**: Uses deterministic SQLite activity logging and Markov transitional lookups without loading heavyweight PyTorch/TensorFlow runtimes into memory.
- **Fail-Safe Self-Healing**: Automated database recovery fallback, transparent backup rotators (`~/.local/share/ghostos/activity.db.bak`), and zero-crash exception insulation across desktop tracking loops.
- **Pure Local Privacy**: Complete offline execution boundary; no telemetry, telemetry daemons, or remote sync hooks.

### Known Bottlenecks & Architectural Debts
1. **X11 Coupling**: Relies predominantly on `xdotool` and `_NET_ACTIVE_WINDOW` polling via X11 atoms, limiting native support under pure Wayland environments (Sway, Hyprland, GNOME Wayland).
2. **Polling Frequency & CPU Wakeups**: Constant 5-second polling interval creates recurring CPU interrupts rather than utilizing event-driven IPC/D-Bus subscription mechanisms.
3. **Flat Window Semantics**: Window matching relies on static class strings rather than context-aware multi-monitor workspace coordinates, virtual desktop indices, or browser URL domain heuristics.

---

## 🗺️ Multi-Phase Roadmap

### Phase 1: Native Wayland & D-Bus Event-Driven Subsystems
- [ ] **Wayland Compositor Interop**: Implement native D-Bus listeners for GNOME Shell (`org.gnome.Mutter.DisplayConfig`), KDE KWin (`org.kde.KWin`), and Hyprland IPC sockets (`$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock`).
- [ ] **Zero-Polling Event Subscription**: Shift from 5s periodic polling loops to interrupt-driven active window change signals, reducing idle CPU footprint to `< 0.01%`.
- [ ] **Multi-Monitor Spatial Layout Staging**: Store monitor EDID, workspace IDs, and window geometry coordinates to automatically tile and snap spawned windows to their exact historical positions via `i3-msg`, `hyprctl dispatch`, or `wmctrl`.

### Phase 2: Higher-Order Probabilistic Modeling
- [ ] **Higher-Order Markov Chains**: Upgrade 1st-order state transitions to $N$-th order Markov models conditioned on temporal intervals (e.g., Morning Standup vs. Late Night Debugging).
- [ ] **Hidden Markov Models (HMM)**: Introduce latent state classification (e.g., "Full-Stack Web Dev", "Scientific Modeling", "Administrative Writing") inferred from rapid tool switching clusters.
- [ ] **Bayesian Confidence Filtering**: Establish dynamic confidence thresholds ($P(S_{t+1}|S_t) > 0.78$) with user-configured cooldown timers before proactive application dispatching.

### Phase 3: Project Context & Virtual Environment Auto-Staging
- [ ] **Git Working Directory Detection**: Extract working directory context from terminal window titles (via OSC 7 escape sequences or `/proc/$PID/cwd` traversal).
- [ ] **Integrated Environment Launchers**: Automatically activate matching Conda/Poetry/Python virtual environments and Docker compose services matching the detected project directory.
- [ ] **CLI Daemon IPC Protocol**: Expose a lightweight Unix domain socket (`/run/user/$UID/ghostos.sock`) for instant status inspection, manual autopilot overrides, and third-party panel integrations (Waybar, Polybar, GNOME Shell Extensions).

---

## 🔒 Security & Privacy Verification

- **Process Memory Hardening**: Strip sensitive command-line parameters and authentication tokens from tracked terminal command buffers before persisting to SQLite.
- **Strict User Sandbox**: Daemon enforces file permissions `0600` on `activity.db` and drops elevated privileges if mistakenly invoked via `sudo`.
