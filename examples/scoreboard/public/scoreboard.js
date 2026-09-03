/**
 * Browser UI for the live scoreboard.
 *
 * Flow:
 *  1. Poll /api/live-games every 30s to discover (and drop) in-progress events.
 *  2. For each game, open an EventSource to /api/games/:id/stream (push).
 *  3. If EventSource isn't available / errors repeatedly, fall back to polling
 *     /api/games/:id/score every 15s (matches Lumify's live score cache TTL).
 *
 * The Lumify API key never reaches this file — all calls go to our Express proxy.
 */

const POLL_DISCOVER_MS = 30_000;
const POLL_SCORE_MS = 15_000;
const MAX_SSE_RETRIES = 3;

const boardEl = document.getElementById("board");
const emptyBanner = document.getElementById("empty-banner");
const errorBanner = document.getElementById("error-banner");
const errorDetail = document.getElementById("error-detail");
const sportSelect = document.getElementById("sport-select");
const statusPill = document.getElementById("connection-status");

/** @type {Map<number, GameController>} */
const games = new Map();
let discoverTimer = null;

class GameController {
  constructor(event) {
    this.id = event.id;
    this.event = event;
    this.score = null;
    this.mode = "sse"; // 'sse' | 'poll'
    this.source = null;
    this.pollTimer = null;
    this.sseRetries = 0;
    this.el = null;
    this.finished = false;
  }

  start() {
    this.render();
    if (typeof EventSource === "undefined") {
      this.startPolling();
      return;
    }
    this.startStream();
  }

  startStream() {
    this.stop();
    this.mode = "sse";
    this.source = new EventSource(`/api/games/${this.id}/stream`);

    this.source.addEventListener("score", (e) => {
      this.sseRetries = 0;
      try {
        this.applyScore(JSON.parse(e.data));
      } catch {
        /* ignore malformed frame */
      }
    });

    this.source.addEventListener("reconnect", () => {
      // Informational — the proxy/SDK already reconnected to Lumify.
      // Briefly surface it in the card footer.
      if (this.el) {
        const mode = this.el.querySelector(".mode-tag");
        if (mode) mode.textContent = "sse · reconnect";
        setTimeout(() => {
          if (mode && this.mode === "sse") mode.textContent = "sse";
        }, 1500);
      }
    });

    this.source.addEventListener("done", () => {
      this.finished = true;
      if (this.score) {
        this.score = { ...this.score, status: "final", finished: true };
      } else if (this.event) {
        this.event = { ...this.event, status: "final" };
      }
      this.render();
      this.stop();
    });

    this.source.addEventListener("error", () => {
      // EventSource fires "error" on transient disconnects too.
      if (this.finished) return;
      this.sseRetries += 1;
      if (this.sseRetries >= MAX_SSE_RETRIES) {
        this.startPolling();
      }
    });
  }

  startPolling() {
    this.stop();
    this.mode = "poll";
    const tick = async () => {
      try {
        const res = await fetch(`/api/games/${this.id}/score`);
        if (res.status === 429) {
          const retry = Number(res.headers.get("Retry-After") || 30);
          setStatus("error", `Rate limited — retry in ${retry}s`);
          return;
        }
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        this.applyScore(data);
        if (data.finished || data.status === "final" || data.status === "walkover") {
          this.finished = true;
          this.stop();
        }
      } catch (err) {
        console.warn("score poll failed", this.id, err);
      }
    };
    tick();
    this.pollTimer = setInterval(tick, POLL_SCORE_MS);
    this.render();
  }

  applyScore(score) {
    const prev = this.score;
    this.score = score;
    this.render();
    if (prev && scoreChanged(prev, score) && this.el) {
      this.el.classList.add("is-flash");
      setTimeout(() => this.el?.classList.remove("is-flash"), 600);
    }
  }

  /** Merge fresh list-payload fields (name/sport/league) without tearing down the stream. */
  updateMeta(event) {
    this.event = { ...this.event, ...event };
    this.render();
  }

  render() {
    const data = this.score || summarizeFromEvent(this.event);
    const home = pickSide(data.scores, "home") || pickSide(data.scores, "player_1") || data.scores?.[0];
    const away = pickSide(data.scores, "away") || pickSide(data.scores, "player_2") || data.scores?.[1];
    const isFinal = data.finished || data.status === "final" || data.status === "walkover";
    const periodLabel = data.period_label || data.period || "—";
    const clock = data.clock || "";

    if (!this.el) {
      this.el = document.createElement("article");
      this.el.className = "card";
      this.el.dataset.eventId = String(this.id);
      boardEl.appendChild(this.el);
    }

    this.el.classList.toggle("is-final", Boolean(isFinal));
    this.el.innerHTML = `
      <div class="card-meta">
        <span>${escapeHtml(formatSportLeague(this.event))}</span>
        ${isFinal
          ? `<span class="final-badge">Final</span>`
          : `<span class="live-badge">Live</span>`}
      </div>
      <div class="period-clock">${escapeHtml(periodLabel)}${clock ? ` · ${escapeHtml(clock)}` : ""}</div>
      ${renderTeam(away)}
      ${renderTeam(home)}
      <div class="card-foot">
        <span>#${this.id}${this.event?.name ? ` · ${escapeHtml(this.event.name)}` : ""}</span>
        <span class="mode-tag">${this.mode}</span>
      </div>
    `;
  }

  stop() {
    if (this.source) {
      this.source.close();
      this.source = null;
    }
    if (this.pollTimer) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
  }

  destroy() {
    this.stop();
    this.el?.remove();
    this.el = null;
  }
}

function renderTeam(side) {
  if (!side) {
    return `<div class="team-row"><span class="team-name">TBD</span><span class="team-score">—</span></div>`;
  }
  const abbr = side.abbreviation ? `<span class="team-abbr">${escapeHtml(side.abbreviation)}</span>` : "";
  const winner = side.is_winner ? " winner" : "";
  const gameScore = side.game_score
    ? `<div class="game-score">${escapeHtml(String(side.game_score))}</div>`
    : "";
  return `
    <div class="team-row">
      <span class="team-name">${escapeHtml(side.name || "TBD")}${abbr}</span>
      <div>
        <div class="team-score${winner}">${escapeHtml(side.score ?? "—")}</div>
        ${gameScore}
      </div>
    </div>
  `;
}

function summarizeFromEvent(event) {
  const participants = event.participants || [];
  return {
    event_id: event.id,
    status: event.status,
    finished: event.status === "final" || event.status === "walkover",
    period: event.period,
    period_label: event.period_label,
    clock: event.clock,
    scores: participants.map((p) => ({
      role: p.role,
      name: p.team?.name || p.player?.name || "TBD",
      abbreviation: p.team?.abbreviation || null,
      score: p.score,
      game_score: p.game_score,
      is_winner: p.is_winner,
    })),
  };
}

function pickSide(scores, role) {
  return (scores || []).find((s) => s.role === role);
}

function scoreChanged(a, b) {
  const as = (a.scores || []).map((s) => `${s.role}:${s.score}:${s.game_score}`).join("|");
  const bs = (b.scores || []).map((s) => `${s.role}:${s.score}:${s.game_score}`).join("|");
  return as !== bs || a.clock !== b.clock || a.period !== b.period || a.status !== b.status;
}

function formatSportLeague(event) {
  const sport = (event.sport || "").toUpperCase();
  const league = (event.league || "").toUpperCase();
  if (sport && league && sport !== league) return `${sport} · ${league}`;
  return sport || league || "LIVE";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setStatus(state, label) {
  statusPill.dataset.state = state;
  statusPill.querySelector(".label").textContent = label;
}

async function refreshLiveGames() {
  const sport = sportSelect.value;
  const qs = sport ? `?sport=${encodeURIComponent(sport)}` : "";
  try {
    const res = await fetch(`/api/live-games${qs}`);
    if (res.status === 429) {
      const retry = Number(res.headers.get("Retry-After") || 30);
      setStatus("error", `Rate limited — retry in ${retry}s`);
      errorBanner.hidden = false;
      errorDetail.textContent = `Lumify returned 429. Wait ${retry}s and the board will retry.`;
      return;
    }
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.error || `HTTP ${res.status}`);
    }
    const data = await res.json();
    const events = data.events || [];
    errorBanner.hidden = true;

    const liveIds = new Set(events.map((e) => e.id));

    // Add / update
    for (const event of events) {
      const existing = games.get(event.id);
      if (existing) {
        existing.updateMeta(event);
      } else {
        const ctrl = new GameController(event);
        games.set(event.id, ctrl);
        ctrl.start();
      }
    }

    // Remove games that left the inprogress set (and aren't still finishing on the board)
    for (const [id, ctrl] of games) {
      if (!liveIds.has(id) && !ctrl.finished) {
        ctrl.destroy();
        games.delete(id);
      }
    }

    // Also prune finished cards that are no longer in the live list after a while
    for (const [id, ctrl] of games) {
      if (ctrl.finished && !liveIds.has(id)) {
        ctrl.destroy();
        games.delete(id);
      }
    }

    emptyBanner.hidden = games.size > 0;
    const liveCount = [...games.values()].filter((g) => !g.finished).length;
    setStatus(
      liveCount > 0 ? "live" : "idle",
      liveCount > 0 ? `${liveCount} live` : "No live games"
    );
  } catch (err) {
    console.error(err);
    setStatus("error", "Error");
    errorBanner.hidden = false;
    errorDetail.textContent = err.message || String(err);
  }
}

function resetBoard() {
  for (const ctrl of games.values()) ctrl.destroy();
  games.clear();
  boardEl.innerHTML = "";
}

sportSelect.addEventListener("change", () => {
  resetBoard();
  refreshLiveGames();
});

refreshLiveGames();
discoverTimer = setInterval(refreshLiveGames, POLL_DISCOVER_MS);

window.addEventListener("beforeunload", () => {
  clearInterval(discoverTimer);
  for (const ctrl of games.values()) ctrl.destroy();
});
