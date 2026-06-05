import { useEffect, useMemo, useState } from "react";
import "./Radar.css";

const DEFAULT_API = process.env.REACT_APP_RADAR_API_BASE || "http://127.0.0.1:8000";
const LS_KEY = "dynasty_radar_league_players";
const LS_KEY_ID = "dynasty_radar_league_id";
const TABS = ["overview", "league", "valuations", "lineup", "trade", "fa", "model"];

async function postJson(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const text = await res.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  if (!res.ok) {
    throw new Error(typeof body === "string" ? body : JSON.stringify(body));
  }
  return body;
}

async function getJson(url) {
  const res = await fetch(url);
  const text = await res.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  if (!res.ok) {
    throw new Error(typeof body === "string" ? body : JSON.stringify(body));
  }
  return body;
}

function StatCard({ label, value }) {
  return (
    <div className="stat-card">
      <p className="stat-label">{label}</p>
      <p className="stat-value">{value}</p>
    </div>
  );
}

function SortableTable({ title, rows, defaultSortKey, limit = 60 }) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState(defaultSortKey || "");
  const [sortDir, setSortDir] = useState("desc");

  const keys = useMemo(() => (rows && rows.length > 0 ? Object.keys(rows[0]) : []), [rows]);

  useEffect(() => {
    if (!sortKey && keys.length > 0) {
      setSortKey(keys[0]);
    }
  }, [keys, sortKey]);

  const filtered = useMemo(() => {
    if (!rows || rows.length === 0) {
      return [];
    }
    if (!query.trim()) {
      return rows;
    }
    const q = query.trim().toLowerCase();
    return rows.filter((row) =>
      Object.values(row).some((v) => String(v ?? "").toLowerCase().includes(q))
    );
  }, [rows, query]);

  const sorted = useMemo(() => {
    const out = [...filtered];
    if (!sortKey) {
      return out;
    }
    out.sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      const an = Number(av);
      const bn = Number(bv);
      const bothNum = Number.isFinite(an) && Number.isFinite(bn);

      let cmp = 0;
      if (bothNum) {
        cmp = an - bn;
      } else {
        cmp = String(av ?? "").localeCompare(String(bv ?? ""));
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
    return out;
  }, [filtered, sortKey, sortDir]);

  if (!rows || rows.length === 0) {
    return (
      <section className="stack panel">
        <div className="row between">
          <h3>{title}</h3>
        </div>
        <p className="muted">No data yet.</p>
      </section>
    );
  }

  const shown = sorted.slice(0, limit);

  function onHeaderClick(k) {
    if (sortKey === k) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(k);
    setSortDir("desc");
  }

  return (
    <section className="stack panel">
      <div className="row between">
        <h3>{title}</h3>
        <input
          className="input"
          style={{ maxWidth: 260 }}
          placeholder="Filter rows..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>
      <div style={{ overflowX: "auto", maxHeight: 520 }}>
        <table className="table">
          <thead>
            <tr>
              {keys.map((k) => (
                <th key={k} onClick={() => onHeaderClick(k)} style={{ cursor: "pointer" }}>
                  {k}
                  {sortKey === k ? (sortDir === "asc" ? " ▲" : " ▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {shown.map((r, idx) => (
              <tr key={idx}>
                {keys.map((k) => (
                  <td key={`${idx}-${k}`}>{String(r[k] ?? "")}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted">Showing {shown.length} of {sorted.length} rows.</p>
    </section>
  );
}

export default function LeagueWorkspace() {
  const [apiBase, setApiBase] = useState(DEFAULT_API);
  const [backendReady, setBackendReady] = useState(null);
  const [leagueId, setLeagueId] = useState("");
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("idle");
  const [tab, setTab] = useState("overview");

  const [leaguePlayers, setLeaguePlayers] = useState([]);
  const [valuations, setValuations] = useState([]);
  const [lineup, setLineup] = useState(null);
  const [trade, setTrade] = useState(null);
  const [tradeEval, setTradeEval] = useState(null);
  const [fa, setFa] = useState(null);
  const [modelQa, setModelQa] = useState(null);
  const [market, setMarket] = useState([]);

  const [selectedSend, setSelectedSend] = useState([]);
  const [selectedReceive, setSelectedReceive] = useState([]);

  const [myTeam, setMyTeam] = useState("");
  const [partner, setPartner] = useState("");
  const [superflex, setSuperflex] = useState(true);
  const [qaSeasonFrom, setQaSeasonFrom] = useState(2021);
  const [qaSeasonTo, setQaSeasonTo] = useState(2025);
  const [qaMinGames, setQaMinGames] = useState(4);
  const [qaEwmaAlpha, setQaEwmaAlpha] = useState(0.6);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(LS_KEY);
      const rawId = localStorage.getItem(LS_KEY_ID);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (Array.isArray(parsed)) {
          setLeaguePlayers(parsed);
        }
      }
      if (rawId) {
        setLeagueId(rawId);
      }
    } catch {
      // ignore malformed local storage
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function pingBackend() {
      try {
        setBackendReady(false);
        await getJson(`${apiBase}/health`);
        if (active) {
          setBackendReady(true);
        }
      } catch {
        if (active) {
          setBackendReady(false);
        }
      }
    }
    pingBackend();
    return () => {
      active = false;
    };
  }, [apiBase]);

  const teams = useMemo(() => {
    const uniq = new Set();
    for (const p of leaguePlayers) {
      if (p.display_name) {
        uniq.add(p.display_name);
      }
    }
    return [...uniq].sort((a, b) => a.localeCompare(b));
  }, [leaguePlayers]);

  const myTeamRoster = useMemo(
    () => leaguePlayers.filter((p) => p.display_name === myTeam),
    [leaguePlayers, myTeam]
  );

  const myTeamValuations = useMemo(
    () => valuations.filter((p) => p.display_name === myTeam),
    [valuations, myTeam]
  );

  useEffect(() => {
    if (!myTeam && teams.length > 0) {
      setMyTeam(teams[0]);
    }
    if (!partner && teams.length > 1) {
      const fallback = teams[0] === myTeam ? teams[1] : teams[0];
      setPartner(fallback || "");
    }
  }, [teams, myTeam, partner]);

  const candidateGive = (trade?.give_candidates && trade.give_candidates.length > 0)
    ? trade.give_candidates
    : (trade?.my_team_pool || []);
  const candidateReceive = (trade?.receive_candidates && trade.receive_candidates.length > 0)
    ? trade.receive_candidates
    : (trade?.partner_pool || []);

  function tabLabel(t) {
    const map = {
      overview: "Overview",
      league: "League",
      valuations: "Valuations",
      lineup: "Lineup",
      trade: "Trade Lab",
      fa: "FA Upgrades",
      model: "Model QA",
    };
    return map[t] || t;
  }

  async function loadLeague() {
    if (!leagueId.trim()) {
      setStatus("Enter a Sleeper league ID first.");
      return;
    }
    setBusy(true);
    setStatus("Loading league...");
    try {
      const out = await postJson(`${apiBase}/v1/league/load`, { league_id: leagueId.trim() });
      const players = out.players || [];
      setLeaguePlayers(players);
      setValuations([]);
      setLineup(null);
      setTrade(null);
      setTradeEval(null);
      setFa(null);
      setSelectedSend([]);
      setSelectedReceive([]);
      localStorage.setItem(LS_KEY, JSON.stringify(players));
      localStorage.setItem(LS_KEY_ID, leagueId.trim());
      setStatus(`Loaded ${players.length} players across ${new Set(players.map((p) => p.display_name)).size} teams.`);
      setTab("league");
    } catch (err) {
      setStatus(`Load failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function runValuations() {
    if (leaguePlayers.length === 0) {
      setStatus("Load a league first.");
      return;
    }
    setBusy(true);
    setStatus("Running valuations...");
    try {
      let mkt = market;
      if (mkt.length === 0) {
        const outMkt = await getJson(`${apiBase}/v1/market/default`);
        mkt = outMkt.players || [];
        setMarket(mkt);
      }
      const out = await postJson(`${apiBase}/v1/valuations`, {
        roster: leaguePlayers,
        market: mkt,
        superflex,
        ppr: true,
      });
      setValuations(out.players || []);
      setStatus(`Valuations complete (${out.players?.length || 0} players).`);
      setTab("valuations");
    } catch (err) {
      setStatus(`Valuation failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function runLineup() {
    if (!myTeam || myTeamRoster.length === 0) {
      setStatus("Select a team with rostered players first.");
      return;
    }

    setBusy(true);
    setStatus(`Running lineup for ${myTeam}...`);
    try {
      let mkt = market;
      if (mkt.length === 0) {
        const outMkt = await getJson(`${apiBase}/v1/market/default`);
        mkt = outMkt.players || [];
        setMarket(mkt);
      }
      const key = (name, pos) => `${String(name || "").toLowerCase().replace(/[^a-z0-9 ]/g, "").trim()}::${String(pos || "").toUpperCase()}`;
      const marketMap = new Map(mkt.map((p) => [key(p.name, p.pos), Number(p.market_value || 0)]));
      const valMap = new Map(
        valuations
          .filter((v) => v.display_name === myTeam)
          .map((v) => [key(v.name, v.pos), Number(v.market_value || 0)])
      );
      const out = await postJson(`${apiBase}/v1/lineup/recommend`, {
        roster: myTeamRoster.map((p) => {
          const k = key(p.name, p.pos);
          return {
            name: p.name,
            pos: p.pos,
            team: p.team,
            market_value: valMap.get(k) || marketMap.get(k) || 0,
          };
        }),
        superflex,
      });
      setLineup(out);
      setStatus("Lineup complete.");
      setTab("lineup");
    } catch (err) {
      setStatus(`Lineup failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function runTradeTargets() {
    if (!myTeam || !partner) {
      setStatus("Select both your team and a trade partner.");
      return;
    }
    if (valuations.length === 0) {
      setStatus("Run valuations first.");
      return;
    }

    setBusy(true);
    setStatus(`Running trade analysis for ${myTeam} vs ${partner}...`);
    try {
      const out = await postJson(`${apiBase}/v1/trade/targets`, {
        my_team: myTeam,
        partner,
        players: valuations.map((v) => ({
          name: v.name,
          pos: v.pos,
          display_name: v.display_name,
          true_value: v.true_value,
          risk_adjusted_value: v.risk_adjusted_value,
          floor_value: v.floor_value,
          ceiling_value: v.ceiling_value,
          confidence: v.confidence,
          risk_index: v.risk_index,
          market_value: v.market_value,
          edge: v.edge,
          edge_z_adj: v.edge_z_adj,
          WinNowScore: v.WinNowScore,
        })),
      });
      setTrade(out);
      setTradeEval(null);
      setSelectedSend([]);
      setSelectedReceive([]);
      setStatus("Trade candidates generated. Step 2: pick package players below.");
      setTab("trade");
    } catch (err) {
      setStatus(`Trade failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  function togglePick(setter, current, name) {
    if (current.includes(name)) {
      setter(current.filter((n) => n !== name));
      return;
    }
    setter([...current, name]);
  }

  async function evaluateTradePackage() {
    if (!trade || !partner) {
      setStatus("Run trade analysis first.");
      return;
    }
    if (selectedSend.length === 0 || selectedReceive.length === 0) {
      setStatus("Pick at least one send and one receive player.");
      return;
    }

    setBusy(true);
    setStatus("Evaluating selected package...");
    try {
      const out = await postJson(`${apiBase}/v1/trade/evaluate`, {
        my_team: myTeam,
        partner,
        send_names: selectedSend,
        receive_names: selectedReceive,
        players: valuations.map((v) => ({
          name: v.name,
          pos: v.pos,
          display_name: v.display_name,
          true_value: v.true_value,
          risk_adjusted_value: v.risk_adjusted_value,
          floor_value: v.floor_value,
          ceiling_value: v.ceiling_value,
          confidence: v.confidence,
          risk_index: v.risk_index,
          market_value: v.market_value,
          edge: v.edge,
          edge_z_adj: v.edge_z_adj,
          WinNowScore: v.WinNowScore,
        })),
      });
      setTradeEval(out);
      setStatus("Trade package evaluated.");
    } catch (err) {
      setStatus(`Trade package failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function runFaUpgrades() {
    if (!myTeam || myTeamRoster.length === 0) {
      setStatus("Select your team first.");
      return;
    }

    setBusy(true);
    setStatus("Running FA upgrades...");
    try {
      let mkt = market;
      if (mkt.length === 0) {
        const outMkt = await getJson(`${apiBase}/v1/market/default`);
        mkt = outMkt.players || [];
        setMarket(mkt);
      }
      const out = await postJson(`${apiBase}/v1/fa/upgrades`, {
        roster: myTeamRoster.map((p) => ({ name: p.name, pos: p.pos, team: p.team })),
        league_roster: leaguePlayers.map((p) => ({
          name: p.name,
          pos: p.pos,
          display_name: p.display_name,
          team: p.team,
        })),
        dp_market: mkt,
        superflex,
      });
      setFa(out);
      setStatus("FA upgrades complete.");
      setTab("fa");
    } catch (err) {
      setStatus(`FA upgrades failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  async function runModelQa() {
    setBusy(true);
    setStatus("Running historical model backtest...");
    try {
      const out = await postJson(`${apiBase}/v1/model/backtest/auto`, {
        season_from: Number(qaSeasonFrom),
        season_to: Number(qaSeasonTo),
        min_history_games: Number(qaMinGames),
        ewma_alpha: Number(qaEwmaAlpha),
      });
      setModelQa(out);
      setStatus("Model QA backtest complete.");
      setTab("model");
    } catch (err) {
      setStatus(`Model QA failed: ${err.message}`);
    } finally {
      setBusy(false);
    }
  }

  function renderTabBody() {
    if (tab === "overview") {
      return (
        <section className="stack">
          <div className="stat-grid">
            <StatCard label="League Players" value={leaguePlayers.length} />
            <StatCard label="Teams" value={teams.length} />
            <StatCard label="Valued Players" value={valuations.length} />
            <StatCard label="My Team" value={myTeam || "-"} />
          </div>
          <div className="panel stack">
            <h3>Quick Start</h3>
            <p className="muted">1) Load league, 2) Run valuations, 3) Open Trade Lab to build and evaluate a package.</p>
            <div className="row">
              <button className="button" disabled={busy} onClick={loadLeague} type="button">Load League</button>
              <button className="button" disabled={busy || leaguePlayers.length === 0} onClick={runValuations} type="button">Run Valuations</button>
              <button className="button" disabled={busy || valuations.length === 0} onClick={() => setTab("trade")} type="button">Go To Trade Lab</button>
            </div>
          </div>
        </section>
      );
    }

    if (tab === "league") {
      return (
        <section className="stack">
          <SortableTable title="League Players" rows={leaguePlayers} defaultSortKey="display_name" />
          <SortableTable title="My Team Roster" rows={myTeamRoster} defaultSortKey="pos" />
        </section>
      );
    }

    if (tab === "valuations") {
      return (
        <section className="stack">
          <SortableTable title="My Team Valuations" rows={myTeamValuations} defaultSortKey="risk_adjusted_value" />
          <SortableTable title="League Valuations" rows={valuations} defaultSortKey="risk_adjusted_value" />
        </section>
      );
    }

    if (tab === "lineup") {
      return (
        <section className="stack">
          {!lineup ? (
            <div className="panel stack">
              <p className="muted">Run lineup to view starters and bench.</p>
              <button className="button" disabled={busy || myTeamRoster.length === 0} onClick={runLineup} type="button">Run Lineup</button>
            </div>
          ) : (
            <>
              <div className="panel"><p><strong>Total Projected:</strong> {lineup.total_projected_points}</p></div>
              <SortableTable title="Starters" rows={lineup.starters || []} defaultSortKey="proj_week" />
              <SortableTable title="Bench" rows={lineup.bench || []} defaultSortKey="proj_week" />
            </>
          )}
        </section>
      );
    }

    if (tab === "trade") {
      return (
        <section className="stack">
          <div className="panel stack">
            <h3>Trade Lab</h3>
            <p className="muted">Step 1: Generate candidates. Step 2: Select send/receive players. Step 3: Evaluate package.</p>
            <div className="row">
              <button className="button" disabled={busy || valuations.length === 0 || !myTeam || !partner} onClick={runTradeTargets} type="button">1. Generate Candidates</button>
              <button className="button" disabled={busy || !trade} onClick={evaluateTradePackage} type="button">3. Evaluate Package</button>
            </div>
            <p className="muted">If the strict candidates are empty, full team pools are shown automatically for picking.</p>
          </div>

          {!trade ? (
            <div className="panel"><p className="muted">No trade candidates yet. Click “Generate Candidates”.</p></div>
          ) : (
            <>
              <div className="panel">
                <p><strong>Needs:</strong> {(trade.needs || []).join(", ") || "none"}</p>
                <p><strong>Surplus:</strong> {(trade.surplus || []).join(", ") || "none"}</p>
                {(trade.give_candidates || []).length === 0 || (trade.receive_candidates || []).length === 0 ? (
                  <p className="muted" style={{ marginTop: "0.35rem" }}>
                    Strict candidates were empty, so selector is using full team pools.
                  </p>
                ) : null}
              </div>

              <section className="panel stack">
                <h4>2. Build Package</h4>
                <div className="row">
                  <div className="pick-col">
                    <p><strong>You Send ({myTeam})</strong></p>
                    {candidateGive.slice(0, 30).map((p) => (
                      <label key={`send-${p.name}`} className="pick-item">
                        <input type="checkbox" checked={selectedSend.includes(p.name)} onChange={() => togglePick(setSelectedSend, selectedSend, p.name)} />
                        <span>{p.name} ({p.pos})</span>
                      </label>
                    ))}
                  </div>
                  <div className="pick-col">
                    <p><strong>You Receive ({partner || "Partner"})</strong></p>
                    {candidateReceive.slice(0, 30).map((p) => (
                      <label key={`recv-${p.name}`} className="pick-item">
                        <input type="checkbox" checked={selectedReceive.includes(p.name)} onChange={() => togglePick(setSelectedReceive, selectedReceive, p.name)} />
                        <span>{p.name} ({p.pos})</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div className="row">
                  <p className="muted"><strong>Selected Send:</strong> {selectedSend.join(", ") || "none"}</p>
                  <p className="muted"><strong>Selected Receive:</strong> {selectedReceive.join(", ") || "none"}</p>
                </div>
              </section>

              {tradeEval ? (
                <div className="panel stack">
                  <h4>Package Evaluation</h4>
                  <p><strong>Market:</strong> send {tradeEval.send_total_market.toFixed(1)} | receive {tradeEval.receive_total_market.toFixed(1)} | diff {tradeEval.market_diff.toFixed(1)}</p>
                  <p><strong>True Value:</strong> send {tradeEval.send_total_true_value.toFixed(1)} | receive {tradeEval.receive_total_true_value.toFixed(1)} | diff {tradeEval.true_value_diff.toFixed(1)}</p>
                  <p><strong>Risk-Adjusted:</strong> send {Number(tradeEval.send_total_risk_adjusted_value || 0).toFixed(1)} | receive {Number(tradeEval.receive_total_risk_adjusted_value || 0).toFixed(1)} | diff {Number(tradeEval.risk_adjusted_value_diff || 0).toFixed(1)}</p>
                  <p><strong>Package Quality:</strong> send {Number(tradeEval.send_package_quality || 0).toFixed(1)} | receive {Number(tradeEval.receive_package_quality || 0).toFixed(1)} | diff {Number(tradeEval.package_quality_diff || 0).toFixed(1)}</p>
                  <p><strong>Deal Score:</strong> {Number(tradeEval.deal_score || 0).toFixed(1)} | <strong>Verdict:</strong> {String(tradeEval.deal_verdict || "neutral")}</p>
                  <p><strong>Partner Acceptance:</strong> {String(tradeEval.partner_acceptance || "medium")} ({Number(tradeEval.acceptance_likelihood_pct || 0).toFixed(0)}%)</p>
                  {(tradeEval.warnings || []).length > 0 ? (
                    <p className="muted"><strong>Warnings:</strong> {(tradeEval.warnings || []).join(" | ")}</p>
                  ) : null}
                  <p><strong>Fairness:</strong> {tradeEval.fairness_score.toFixed(3)} (closer to 1.0 is more balanced)</p>
                </div>
              ) : null}

              <SortableTable title="Targets" rows={trade.targets || []} defaultSortKey="edge_z_adj" />
              <SortableTable title="Give Candidates" rows={candidateGive} defaultSortKey="risk_adjusted_value" />
              <SortableTable title="Receive Candidates" rows={candidateReceive} defaultSortKey="risk_adjusted_value" />
            </>
          )}
        </section>
      );
    }

    if (tab === "fa") {
      return (
        <section className="stack">
          {!fa ? (
            <div className="panel stack">
              <p className="muted">Run FA upgrade scan to view suggestions.</p>
              <button className="button" disabled={busy || myTeamRoster.length === 0} onClick={runFaUpgrades} type="button">Run FA Upgrades</button>
            </div>
          ) : (
            <>
              <div className="panel"><p><strong>Total Projected:</strong> {fa.total_projected_points}</p></div>
              <SortableTable title="Upgrades" rows={fa.upgrades || []} defaultSortKey="delta_pts" />
              <SortableTable title="FA Pool" rows={fa.fa_pool || []} defaultSortKey="proj_week" />
            </>
          )}
        </section>
      );
    }

    if (tab === "model") {
      return (
        <section className="stack">
          <div className="panel stack">
            <h3>Model QA</h3>
            <p className="muted">Runs walk-forward backtest on nflverse historical weekly player points.</p>
            <div className="row">
              <label className="label">
                Season From
                <input className="input" type="number" value={qaSeasonFrom} onChange={(e) => setQaSeasonFrom(e.target.value)} />
              </label>
              <label className="label">
                Season To
                <input className="input" type="number" value={qaSeasonTo} onChange={(e) => setQaSeasonTo(e.target.value)} />
              </label>
              <label className="label">
                Min History Games
                <input className="input" type="number" min="1" value={qaMinGames} onChange={(e) => setQaMinGames(e.target.value)} />
              </label>
              <label className="label">
                EWMA Alpha
                <input className="input" type="number" step="0.05" min="0.05" max="0.95" value={qaEwmaAlpha} onChange={(e) => setQaEwmaAlpha(e.target.value)} />
              </label>
            </div>
            <div className="row">
              <button className="button" disabled={busy} onClick={runModelQa} type="button">Run Backtest</button>
            </div>
          </div>

          {modelQa ? (
            <div className="stat-grid">
              <StatCard label="Observations" value={modelQa.observations} />
              <StatCard label="Model MAE" value={Number(modelQa.model_mae).toFixed(3)} />
              <StatCard label="Baseline MAE" value={Number(modelQa.baseline_mae).toFixed(3)} />
              <StatCard label="Model RMSE" value={Number(modelQa.model_rmse).toFixed(3)} />
              <StatCard label="Baseline RMSE" value={Number(modelQa.baseline_rmse).toFixed(3)} />
              <StatCard label="MAE Improvement %" value={Number(modelQa.mae_improvement_pct).toFixed(2)} />
              <StatCard label="Model Spearman" value={Number(modelQa.model_spearman).toFixed(3)} />
              <StatCard label="Baseline Spearman" value={Number(modelQa.baseline_spearman).toFixed(3)} />
            </div>
          ) : (
            <div className="panel"><p className="muted">No backtest result yet.</p></div>
          )}
        </section>
      );
    }

    return null;
  }

  return (
    <div className="radar-page">
      <main className="shell dark-shell">
      <div className="topbar panel">
        <div>
          <h1>Dynasty Radar</h1>
          <p className="muted">v2.0</p>
        </div>
        <div className="status-chip">
          {busy ? "Working..." : backendReady === false ? "Waking API..." : "Ready"}
        </div>
      </div>

      <section className="panel stack">
        <div className="row">
          <label className="label grow">
            Sleeper League ID
            <input className="input" value={leagueId} onChange={(e) => setLeagueId(e.target.value)} placeholder="1195252934627844096" />
          </label>
        </div>
        <div className="row">
          <button className="button" type="button" onClick={() => setShowAdvanced((v) => !v)}>
            {showAdvanced ? "Hide Advanced" : "Show Advanced"}
          </button>
        </div>
        {showAdvanced ? (
          <div className="row">
            <label className="label grow">
              API Base URL
              <input className="input" value={apiBase} onChange={(e) => setApiBase(e.target.value)} />
            </label>
          </div>
        ) : null}

        <div className="row">
          <label className="label grow">
            My Team
            <select className="input" value={myTeam} onChange={(e) => setMyTeam(e.target.value)}>
              <option value="">Select team...</option>
              {teams.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="label grow">
            Trade Partner
            <select className="input" value={partner} onChange={(e) => setPartner(e.target.value)}>
              <option value="">Select partner...</option>
              {teams.filter((t) => t !== myTeam).map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
          <label className="label">
            Superflex
            <select className="input" value={String(superflex)} onChange={(e) => setSuperflex(e.target.value === "true")}>
              <option value="true">true</option>
              <option value="false">false</option>
            </select>
          </label>
        </div>

        <div className="row">
          <button className="button" disabled={busy} onClick={loadLeague} type="button">Load League</button>
          <button className="button" disabled={busy || leaguePlayers.length === 0} onClick={runValuations} type="button">Run Valuations</button>
          <button className="button" disabled={busy || myTeamRoster.length === 0} onClick={runLineup} type="button">Run Lineup</button>
          <button className="button" disabled={busy || valuations.length === 0 || !partner} onClick={runTradeTargets} type="button">Run Trade</button>
          <button className="button" disabled={busy || myTeamRoster.length === 0} onClick={runFaUpgrades} type="button">Run FA</button>
        </div>

        <pre className="pre">{status}</pre>
      </section>

      <nav className="tabbar">
        {TABS.map((t) => (
          <button
            key={t}
            className={`tab ${tab === t ? "active" : ""}`}
            type="button"
            onClick={() => setTab(t)}
          >
            {tabLabel(t)}
          </button>
        ))}
      </nav>

        {renderTabBody()}
      </main>
    </div>
  );
}
