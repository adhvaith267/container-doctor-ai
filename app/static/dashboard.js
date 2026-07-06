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

    const updateDockerStatus = (connected) => {
        const status = document.querySelector("[data-docker-status]");
        const label = document.querySelector("[data-docker-label]");
        if (!status || !label) {
            return;
        }

        status.classList.toggle("connected", connected);
        status.classList.toggle("unavailable", !connected);
        label.textContent = connected
            ? "Docker Connected"
            : "Docker Unavailable";
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
            updateDockerStatus(metrics.docker_connected);
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
