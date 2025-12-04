const updater = (id, value) => {
    const el = document.getElementById(id);
    if (!el) return;
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
};

async function liveFeed() {
try {
    const data = await fetch("/sensors").then(r => r.json());
    const readings = data.readings;
    const scores = data.scores;
    updater("tempValue", `${readings.temperature_f.toFixed(1)} °F`);
    updater("humValue", `${readings.humidity_pct.toFixed(1)} %`);
    updater("lightValue", `${readings.light_lux.toFixed(1)} lux`);
    updater("noiseValue", `${readings.noise_db.toFixed(1)} dB`);
    updater("tempScore", scores.temperature_score);
    updater("humScore", scores.humidity_score);
    updater("lightScore", scores.light_score);
    updater("noiseScore", scores.noise_score);
    updater("cciScore", scores.total_score);
    setCognitiveScore(scores.total_score);

} catch (err) {
    console.error("Failed to update sensors", err);
}
}
setInterval(liveFeed, 1000);

const button = document.getElementById("readButton");
const statusEl = document.getElementById("status");
const card = document.getElementById("readingCard");

const timeEl = document.getElementById("time");
const tempEl = document.getElementById("temp");
const humEl = document.getElementById("hum");
const lightEl = document.getElementById("light");
const noiseEl = document.getElementById("noise");

async function takeReading() {
    button.disabled = true;
    statusEl.textContent = "Taking reading on Pi...";
    card.style.display = "none";

    try {
    const res = await fetch("/sensors");
    if (!res.ok) {
        throw new Error("Pi returned status " + res.status);
    }
    const readings = await res.json();

    tempEl.textContent = readings.temperature_f.toFixed(1) + " °F";
    humEl.textContent = readings.humidity_pct.toFixed(1) + " %";
    lightEl.textContent = readings.light_lux.toFixed(1) + " lux";
    noiseEl.textContent = readings.noise_db.toFixed(1) + " dB";

    card.style.display = "block";
    statusEl.textContent = "Reading received.";
    } catch (err) {
    console.error(err);
    statusEl.textContent = "Error contacting Pi.";
    } finally {
    button.disabled = false;
    }
}

// Guard: page may not have the old manual reading button anymore.
if (button) {
    button.addEventListener("click", takeReading);
}

function setCognitiveScore(score) {
  const circle = document.getElementById("cog-ring");
  const textEl = document.getElementById("cog-score");

  if (!circle || !textEl) return;

  // clamp score 0–100
  const value = Math.max(0, Math.min(100, Number(score)));

  const radius = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * radius;

  circle.style.strokeDasharray = `${circumference} ${circumference}`;

  const offset = circumference * (1 - value / 100);
  circle.style.strokeDashoffset = offset;

  textEl.textContent = Math.round(value);
}

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
        if (!res.ok) {
            throw new Error(data?.message || `Request failed: ${res.status}`);
        }
        input.value = "";
        await refreshLeaderboard();
    } catch (err) {
        console.error("Failed to save study spot", err);
        alert(`Error: ${err.message}`);
    }
}

async function refreshLeaderboard() {
    try {
        const res = await fetch("/leaderboard");
        const list = await res.json();
        renderLeaderboard(list);
    } catch (err) {
        console.error("Failed to load leaderboard", err);
    }
}

function renderLeaderboard(items) {
    const tbody = document.getElementById("leaderboard-body");
    if (!tbody) return;
    tbody.innerHTML = "";
    if (!items || items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="col-empty">No study spots logged yet.</td></tr>`;
        return;
    }
    const rows = (items || []).map((item, idx) => {
        const dateStr = formatTimestamp(item.timestamp_utc);
        return `
            <tr>
                <td class="col-rank">${idx + 1}</td>
                <td class="col-name">${escapeHtml(item.location)}</td>
                <td class="col-time">${dateStr}</td>
                <td class="col-cci">${Math.round(item.total_score)}</td>
                <td class="col-temp">${Math.round(item.temperature_score)}</td>
                <td class="col-hum">${Math.round(item.humidity_score)}</td>
                <td class="col-light">${Math.round(item.light_score)}</td>
                <td class="col-noise">${Math.round(item.noise_score)}</td>
            </tr>
        `;
    });
    tbody.innerHTML = rows.join("");
}

function formatTimestamp(ts) {
    if (!ts) return "";
    try {
        const d = new Date(ts);
        return d.toLocaleString();
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

// initial load
document.addEventListener("DOMContentLoaded", async () => {
    await refreshLeaderboard();
});

// expose to global for inline HTML handlers
window.handleSaveStudySpot = handleSaveStudySpot;
window.refreshLeaderboard = refreshLeaderboard;

