(function () {
  "use strict";

  // ── Helpers ─────────────────────────────────────────────────────────────

  function updater(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    el.classList.remove("skeleton");
    el.textContent = value;
    el.classList.remove("good", "medium", "bad");
    if (el.classList.contains("score")) {
      if (value >= 66) {
        el.classList.add("good");
      } else if (value >= 33) {
        el.classList.add("medium");
      } else {
        el.classList.add("bad");
      }
    }
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatTimestamp(ts) {
    if (!ts) return "";
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  }

  // ── SVG progress ring ────────────────────────────────────────────────────

  function setCognitiveScore(score) {
    const circle = document.getElementById("cog-ring");
    const textEl = document.getElementById("cog-score");
    if (!circle || !textEl) return;

    const value = Math.max(0, Math.min(100, Number(score)));
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference * (1 - value / 100);
    textEl.textContent = Math.round(value);
  }

  // ── Live sensor feed with exponential backoff ────────────────────────────

  let pollInterval = 1_000;
  let consecutiveErrors = 0;
  let firstLoad = true;
  const MAX_POLL_INTERVAL = 16_000;

  function applySkeletons() {
    const ids = [
      "tempScore", "humScore", "lightScore", "noiseScore", "cciScore",
      "tempValue", "humValue", "lightValue", "noiseValue",
    ];
    ids.forEach(id => document.getElementById(id)?.classList.add("skeleton"));
  }

  async function liveFeed() {
    try {
      const res = await fetch("/sensors");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const { readings, scores } = data;

      updater("tempValue",  `${readings.temperature_f.toFixed(1)} °F`);
      updater("humValue",   `${readings.humidity_pct.toFixed(1)} %`);
      updater("lightValue", `${readings.light_lux.toFixed(1)} lux`);
      updater("noiseValue", `${readings.noise_db.toFixed(1)} dB`);
      updater("tempScore",  scores.temperature_score);
      updater("humScore",   scores.humidity_score);
      updater("lightScore", scores.light_score);
      updater("noiseScore", scores.noise_score);
      updater("cciScore",   scores.total_score);
      setCognitiveScore(scores.total_score);

      if (consecutiveErrors > 0) {
        document.getElementById("sensor-error")?.classList.remove("visible");
        consecutiveErrors = 0;
        pollInterval = 1_000;
      }
      firstLoad = false;
    } catch (err) {
      consecutiveErrors++;
      pollInterval = Math.min(pollInterval * 2, MAX_POLL_INTERVAL);
      document.getElementById("sensor-error")?.classList.add("visible");
      console.error("Sensor poll failed:", err);
    }

    setTimeout(liveFeed, pollInterval);
  }

  // ── Leaderboard ──────────────────────────────────────────────────────────

  function renderLeaderboard(items) {
    const tbody = document.getElementById("leaderboard-body");
    if (!tbody) return;
    tbody.innerHTML = "";

    if (!items || items.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="col-empty">No study spots logged yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map((item, idx) => `
      <tr>
        <td class="col-rank">${idx + 1}</td>
        <td class="col-name">${escapeHtml(item.location)}</td>
        <td class="col-time">${formatTimestamp(item.timestamp_utc)}</td>
        <td class="col-cci">${Math.round(item.total_score)}</td>
        <td class="col-temp">${Math.round(item.temperature_score)}</td>
        <td class="col-hum">${Math.round(item.humidity_score)}</td>
        <td class="col-light">${Math.round(item.light_score)}</td>
        <td class="col-noise">${Math.round(item.noise_score)}</td>
      </tr>
    `).join("");
  }

  async function refreshLeaderboard() {
    try {
      const res = await fetch("/leaderboard");
      renderLeaderboard(await res.json());
    } catch (err) {
      console.error("Failed to load leaderboard:", err);
    }
  }

  // ── Study spot form ──────────────────────────────────────────────────────

  async function handleSaveStudySpot(event) {
    event.preventDefault();
    const input = document.getElementById("studySpotName");
    const name = (input?.value || "").trim();
    if (!name) {
      alert("Please enter a study spot name.");
      return;
    }

    try {
      const res = await fetch("/api/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.message || `Request failed: ${res.status}`);
      input.value = "";
      await refreshLeaderboard();
    } catch (err) {
      console.error("Failed to save study spot:", err);
      alert(`Error: ${err.message}`);
    }
  }

  // ── Init ─────────────────────────────────────────────────────────────────

  document.addEventListener("DOMContentLoaded", async () => {
    applySkeletons();
    liveFeed();
    await refreshLeaderboard();
  });

  // Expose only the handlers needed by inline HTML form attributes.
  window.handleSaveStudySpot = handleSaveStudySpot;
  window.refreshLeaderboard = refreshLeaderboard;
})();
