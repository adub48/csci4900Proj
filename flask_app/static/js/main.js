const updater = (id, value) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = value;
    el.classList.remove("good", "medium", "bad");
    if (el.classList.contains("score")) {
        if (value >= 66) el.classList.add("good");
        else if (value >= 33) el.classList.add("medium");
        else el.classList.add("bad");
    }
};

function getQualityInfo(score) {
    if (score >= 80) return { label: "Excellent",  cls: "excellent", desc: "Optimal conditions for deep focus." };
    if (score >= 66) return { label: "Good",       cls: "good",      desc: "Well-suited for studying and concentration." };
    if (score >= 50) return { label: "Fair",       cls: "fair",      desc: "Some factors may cause mild distraction." };
    if (score >= 33) return { label: "Poor",       cls: "poor",      desc: "Conditions may hinder focus and productivity." };
    return                  { label: "Very Poor",  cls: "very-poor", desc: "Environment is not conducive to cognitive work." };
}

function setCognitiveScore(score) {
    const circle = document.getElementById("cog-ring");
    const textEl = document.getElementById("cog-score");
    if (!circle || !textEl) return;

    const value = Math.max(0, Math.min(100, Number(score)));
    const circumference = 2 * Math.PI * circle.r.baseVal.value;

    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference * (1 - value / 100);
    textEl.textContent = Math.round(value);

    const { label, cls, desc } = getQualityInfo(value);
    const labelEl = document.getElementById("cci-label");
    const descEl  = document.getElementById("cci-desc");
    if (labelEl) { labelEl.textContent = label; labelEl.className = `cci-label ${cls}`; }
    if (descEl)  { descEl.textContent = desc; }
}

function setFeedError(hasError) {
    const banner = document.getElementById("feed-error");
    if (banner) banner.hidden = !hasError;
}

async function liveFeed() {
    try {
        const data = await fetch("/sensors").then(r => r.json());
        const { readings, scores } = data;
        updater("tempValue", `${readings.temperature_f.toFixed(1)} °F`);
        updater("humValue", `${readings.humidity_pct.toFixed(1)} %`);
        updater("lightValue", `${readings.light_lux.toFixed(1)} lux`);
        updater("noiseValue", `${readings.noise_db.toFixed(1)} dB`);
        updater("tempScore", scores.temperature_score);
        updater("humScore", scores.humidity_score);
        updater("lightScore", scores.light_score);
        updater("noiseScore", scores.noise_score);
        setCognitiveScore(scores.total_score);
        setFeedError(false);
    } catch (err) {
        console.error("Live feed error:", err);
        setFeedError(true);
    }
}

setInterval(liveFeed, 1000);

function showToast(message, type) {
    const toast = document.getElementById("form-toast");
    if (!toast) return;
    toast.textContent = message;
    toast.className = `form-toast ${type}`;
    toast.hidden = false;
    setTimeout(() => { toast.hidden = true; }, 4000);
}

async function handleSaveStudySpot(event) {
    event.preventDefault();
    const input = document.getElementById("studySpotName");
    const name = (input?.value || "").trim();
    if (!name) return;

    const btn = event.target.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;

    try {
        const res = await fetch("/api/log", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data?.message || `Request failed: ${res.status}`);
        input.value = "";
        showToast("Study spot saved!", "success");
        await refreshLeaderboard();
    } catch (err) {
        console.error("Failed to save study spot:", err);
        showToast(`Error: ${err.message}`, "error");
    } finally {
        if (btn) btn.disabled = false;
    }
}

async function refreshLeaderboard() {
    try {
        const res = await fetch("/leaderboard");
        const list = await res.json();
        renderLeaderboard(list);
    } catch (err) {
        console.error("Failed to load leaderboard:", err);
    }
}

function renderLeaderboard(items) {
    const tbody = document.getElementById("leaderboard-body");
    if (!tbody) return;
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

function formatTimestamp(ts) {
    if (!ts) return "";
    try {
        return new Date(ts).toLocaleString();
    } catch {
        return ts;
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

document.addEventListener("DOMContentLoaded", async () => {
    document.getElementById("studyspot-form")
        ?.addEventListener("submit", handleSaveStudySpot);
    await refreshLeaderboard();
    await liveFeed();
});
