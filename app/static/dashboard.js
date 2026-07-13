(() => {
    "use strict";

    const dashboard = document.querySelector("[data-dashboard-metrics]");
    if (!dashboard) {
        return;
    }

    const endpoint = dashboard.dataset.metricsUrl;
    const refreshIntervalMs = 7000;

    const updateText = (metric, value) => {
        document
            .querySelectorAll(`[data-metric="${metric}"]`)
            .forEach((element) => {
                element.textContent = value;
            });
    };

    const updateRuntimeState = (connected) => {
        const card = document.querySelector("[data-runtime-card]");
        if (!card) {
            return;
        }

        card.classList.toggle("is-online", connected);
        card.classList.toggle("is-offline", !connected);
        updateText("docker-runtime-status", connected ? "Connected" : "Unavailable");
        updateText(
            "docker-runtime-detail",
            connected
                ? "Container engine is responding"
                : "Docker daemon cannot be reached",
        );
    };

    const updateAiState = (online) => {
        const card = document.querySelector("[data-ai-card]");
        if (card) {
            card.classList.toggle("is-online", online);
            card.classList.toggle("is-offline", !online);
        }
    };

    const updateLatestDecision = (decision) => {
        if (!decision) {
            return;
        }

        updateText("latest-ai-container", decision.container);
        updateText("latest-ai-root-cause", decision.root_cause);
        updateText("latest-ai-action", `${decision.action}`);
        updateText("latest-ai-confidence", `${Math.round(decision.confidence * 100)}%`);
        updateText("latest-ai-model", decision.model);

        document
            .querySelectorAll('[data-metric="latest-ai-severity"]')
            .forEach((element) => {
                element.className = `badge severity-${decision.severity}`;
                element.textContent = decision.severity;
            });
    };

    const escapeHtml = (value) => String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

    const renderRecentIncidents = (incidents) => {
        const container = document.querySelector("[data-incident-feed-container]");
        if (!container || !Array.isArray(incidents)) {
            return;
        }

        if (incidents.length === 0) {
            container.innerHTML = `
                <div class="empty-state quiet-state">
                    <span class="empty-icon" aria-hidden="true">✓</span>
                    <h3>No incidents recorded</h3>
                    <p>No recovery work is needed right now. New incidents will appear here automatically.</p>
                </div>`;
            return;
        }

        const rows = incidents.map((incident) => {
            const success = incident.success === true;
            const state = success ? "recovered" : "failed";
            const result = success ? "Recovered" : "Needs attention";
            return `
                <a class="incident-row" href="/history/${encodeURIComponent(incident.id)}">
                    <span class="incident-state ${state}" aria-hidden="true"></span>
                    <div class="incident-main">
                        <div><strong>${escapeHtml(incident.container)}</strong><span class="badge severity-${escapeHtml(incident.severity)}">${escapeHtml(incident.severity)}</span></div>
                        <p>${escapeHtml(incident.root_cause)}</p>
                    </div>
                    <div class="incident-action"><span>${escapeHtml(incident.action)}</span><small>${result}</small></div>
                    <time>${escapeHtml(incident.display_timestamp)}</time>
                    <span class="incident-arrow" aria-hidden="true">→</span>
                </a>`;
        }).join("");
        container.innerHTML = `<div class="incident-feed" data-incident-feed>${rows}</div>`;
    };

    const refreshMetrics = async () => {
        if (document.hidden) {
            return;
        }

        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 5000);

        try {
            const response = await fetch(endpoint, {
                cache: "no-store",
                headers: { Accept: "application/json" },
                signal: controller.signal,
            });
            if (!response.ok) {
                return;
            }

            const metrics = await response.json();
            updateText(
                "ai-engine-status",
                metrics.ai_engine_status === "online"
                    ? "Online"
                    : "Offline",
            );
            updateAiState(metrics.ai_engine_status === "online");
            updateText("ai-engine-model", metrics.ai_engine_model);
            updateText("active-containers", metrics.active_containers);
            updateText("total-incidents", metrics.total_incidents);
            updateText(
                "recovery-success",
                `${metrics.recovery_success_rate}%`,
            );
            updateText(
                "recovery-detail",
                `${metrics.successful_restarts} of ${metrics.restart_attempts} restarts`,
            );
            updateText(
                "problematic-container",
                metrics.most_problematic_container,
            );
            updateLatestDecision(metrics.latest_ai_decision);
            renderRecentIncidents(metrics.recent_incidents);
            updateRuntimeState(metrics.docker_connected);
        } catch (error) {
            if (error.name !== "AbortError") {
                console.warn("Dashboard refresh failed.");
            }
        } finally {
            window.clearTimeout(timeout);
        }
    };

    window.setInterval(refreshMetrics, refreshIntervalMs);
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            refreshMetrics();
        }
    });
})();
