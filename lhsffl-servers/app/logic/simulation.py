import json
import os
import statistics
import textwrap
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

from app import db
from app.models.matchup_simulations import MatchupSimulations
from app.models.simulation_player_projections import SimulationPlayerProjections

PPR_SCORING_RULES = (
    "PPR scoring: 1 pt/reception | 0.1 pts/rushing+receiving yard | 0.04 pts/passing yard | "
    "6 pts/rushing|receiving TD | 4 pts/passing TD | -4 pts/INT | -2 pts/fumble lost"
)

LINEUP_NOTE = "Starting lineup: 1 QB, 2 RB, 3 WR, 1 TE, 1 Flex (RB/WR/TE), 1 K"

AGENT_PERSONAS = [
    {
        "name": "stat_analyst",
        "focus": (
            "You are a by-the-numbers fantasy football analyst. "
            "Search for season-long statistics — targets, carries, receptions, yards, TDs — "
            "and weight your projections on volume and efficiency trends over the full season."
        ),
    },
    {
        "name": "injury_scout",
        "focus": (
            "You are a fantasy football injury and availability specialist. "
            "Heavily weight each player's current injury status, practice participation, and recent "
            "health history. A player listed as Questionable or Doubtful should have their score "
            "significantly reduced. Search for the latest injury reports."
        ),
    },
    {
        "name": "matchup_specialist",
        "focus": (
            "You are a matchup-driven fantasy football analyst. "
            "Search for each NFL team's defensive rankings against each position (QB, RB, WR, TE, K). "
            "A player facing a weak defense should be projected higher; a tough defense lower. "
            "This is your primary signal."
        ),
    },
    {
        "name": "recent_form",
        "focus": (
            "You are a hot-hand / recent performance fantasy analyst. "
            "Search for each player's last 3 weeks of performance and weight recent games "
            "far more heavily than season averages. Trending up means project higher; trending down lower."
        ),
    },
    {
        "name": "contrarian",
        "focus": (
            "You are a contrarian fantasy football analyst who looks for mispriced players. "
            "Search for players who are being undervalued (under-targeted, facing a soft matchup) "
            "or overvalued (over-hyped, facing a tough defense). "
            "Your projections will often differ from consensus."
        ),
    },
    {
        "name": "weather_analyst",
        "focus": (
            "You are a weather and environment fantasy analyst. "
            "Search for game-time weather forecasts for each game. "
            "For outdoor stadiums: high wind (15+ mph) suppresses passing/kicking; "
            "heavy rain suppresses passing; cold (under 30°F) reduces scores slightly. "
            "Dome/indoor games get no weather adjustment."
        ),
    },
    {
        "name": "target_share",
        "focus": (
            "You are a usage and opportunity fantasy analyst. "
            "Search for each player's snap count %, target share, air yards, and carry share. "
            "Players with a high, consistent opportunity share are safer projections. "
            "Weight opportunity over box score results."
        ),
    },
    {
        "name": "consensus_ranker",
        "focus": (
            "You are an aggregator of expert fantasy football projections. "
            "Search for published weekly projections from FantasyPros, ESPN, and other major sites. "
            "Use the consensus expert projection as your primary estimate. "
            "Return the market consensus projection for each player."
        ),
    },
    {
        "name": "vegas_lines",
        "focus": (
            "You are a betting market analyst applying Vegas lines to fantasy football. "
            "Search for the current Vegas over/under, spread, and implied team totals for each game. "
            "A team with a high implied total should have boosted projections for skill players; "
            "a heavy favorite playing from ahead leans run-heavy (depresses pass catchers). "
            "The market has already aggregated enormous information — trust it heavily."
        ),
    },
    {
        "name": "game_script_modeler",
        "focus": (
            "You are a game script and situation analyst. "
            "Search for Vegas spreads and team win probabilities. "
            "Model the likely flow of each game: a team expected to win big will run more in the 2nd half "
            "(hurts their WRs/QB volume, helps their RBs); a team chasing a deficit will pass more "
            "(helps WRs/TE, hurts RB). Consider each player's role in their team's likely game script."
        ),
    },
    {
        "name": "rest_advantage",
        "focus": (
            "You are a rest, fatigue, and schedule analyst. "
            "Search for each team's recent schedule: short weeks (playing Thursday after Sunday), "
            "bye week returns (well-rested, but sometimes rusty), back-to-back road games, "
            "and travel fatigue for cross-country trips. "
            "Players on short rest face elevated injury risk and reduced performance. "
            "Bye week returners often exceed projections. Weight rest advantage heavily."
        ),
    },
    {
        "name": "snap_trend",
        "focus": (
            "You are a snap count and role trajectory analyst. "
            "Search for each player's snap count % and route participation over the last 3 weeks. "
            "A player whose snap share is rising is gaining role — project them higher than season average suggests. "
            "A player whose snaps are declining (injury, coach doghouse, emerging competition) project lower. "
            "Snap trend is a leading indicator that shows up in usage before it shows up in stats."
        ),
    },
]


def _build_matchup_context(matchup, week):
    team_a = matchup.team
    team_b = matchup.opponent_team

    context = {
        "week": week,
        "year": matchup.year,
        "team_a": {
            "name": team_a.team_name,
            "starters": [p.simulation_serialize() for p in team_a.starters],
        },
        "team_b": {
            "name": team_b.team_name,
            "starters": [p.simulation_serialize() for p in team_b.starters],
        },
    }
    return context


def _run_agent(context, persona):
    """
    Run a single analyst agent. Returns a dict with team totals and per-player scores,
    or None on failure.
    """
    team_a_name = context["team_a"]["name"]
    team_b_name = context["team_b"]["name"]

    system_prompt = textwrap.dedent(f"""\
    ## Role
    {persona["focus"]}

    ## Task
    Predict the fantasy football score for every starter in this Week {context["week"]} of the {context["year"]} NFL season matchup.

    ## Scoring Rules
    {PPR_SCORING_RULES}
    {LINEUP_NOTE}

    ## Instructions
    - Use web search to find the information relevant to your analytical focus
    - Only cite statistics and facts you found via web search — do not fabricate numbers
    - Return ONLY a valid JSON object — no markdown fences, no explanation, just the JSON

    ## Output Format
    {{
      "{team_a_name}": {{
        "total": <float>,
        "players": {{
          "<player name>": {{"score": <float>, "reasoning": "<1-2 sentence explanation citing specific facts>"}},
          ...
        }}
      }},
      "{team_b_name}": {{
        "total": <float>,
        "players": {{
          "<player name>": {{"score": <float>, "reasoning": "<1-2 sentence explanation citing specific facts>"}},
          ...
        }}
      }}
    }}
    """)

    user_prompt = (
        f"Here is the matchup data for Week {context['week']}:\n"
        f"{json.dumps(context, indent=2)}"
    )

    simulation_model = os.environ.get("OPENROUTER_SIMULATION_MODEL", "google/gemini-flash-1.5")

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                "Content-Type": "application/json",
            },
            json={
                "model": simulation_model + ":online",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "response_format": {"type": "json_object"},
            },
            timeout=60,
        )
    except requests.exceptions.RequestException as e:
        print(f"[simulation] Agent {persona['name']} request failed: {e}")
        return None

    if not response.ok:
        print(f"[simulation] Agent {persona['name']} error: {response.text}")
        return None

    raw_content = response.json()["choices"][0]["message"]["content"]
    print(persona["name"])
    print(raw_content)
    try:
        result = json.loads(raw_content)
        result["_persona"] = persona["name"]
        return result
    except (json.JSONDecodeError, KeyError) as e:
        print(f"[simulation] Agent {persona['name']} parse error: {e}\nContent: {raw_content}")
        return None


def _aggregate_results(agent_results, team_a_name, team_b_name):
    """
    Aggregate raw agent predictions into summary statistics.
    Returns (team_a_stats, team_b_stats, player_projections).
    player_projections: {player_name: [{"persona": ..., "score": ...}, ...]}
    """
    team_a_totals = []
    team_b_totals = []
    player_scores = {}  # player_name -> list of (persona, score)

    for result in agent_results:
        persona = result.get("_persona", "unknown")

        team_a_data = result.get(team_a_name, {})
        team_b_data = result.get(team_b_name, {})

        if isinstance(team_a_data.get("total"), (int, float)):
            team_a_totals.append(float(team_a_data["total"]))
        if isinstance(team_b_data.get("total"), (int, float)):
            team_b_totals.append(float(team_b_data["total"]))

        all_players = {**team_a_data.get("players", {}), **team_b_data.get("players", {})}
        for name, value in all_players.items():
            # Support both new {"score": float, "reasoning": str} and plain float (fallback)
            if isinstance(value, dict):
                score = value.get("score")
                reasoning = value.get("reasoning", "")
            elif isinstance(value, (int, float)):
                score = value
                reasoning = ""
            else:
                continue
            if isinstance(score, (int, float)):
                player_scores.setdefault(name, []).append({
                    "persona": persona,
                    "score": float(score),
                    "reasoning": reasoning,
                })

    def _iqr(vals):
        if len(vals) < 2:
            return 0.0
        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        q1 = vals_sorted[n // 4]
        q3 = vals_sorted[(3 * n) // 4]
        return round(q3 - q1, 2)

    def _median(vals):
        return round(statistics.median(vals), 2) if vals else 0.0

    team_a_stats = {
        "median_score": _median(team_a_totals),
        "score_spread": _iqr(team_a_totals),
        "raw_totals": team_a_totals,
    }
    team_b_stats = {
        "median_score": _median(team_b_totals),
        "score_spread": _iqr(team_b_totals),
        "raw_totals": team_b_totals,
    }

    n = len(team_a_totals)
    if n == 0:
        win_prob = 0.5
    else:
        team_a_wins = sum(1 for a, b in zip(team_a_totals, team_b_totals) if a > b)
        win_prob = round(team_a_wins / n, 3)

    return team_a_stats, team_b_stats, win_prob, player_scores


def run_simulation(matchup, week, n_agents=None):
    """
    Run the AI agent ensemble simulation for a matchup.
    Persists results to MatchupSimulations + SimulationPlayerProjections.
    Returns the MatchupSimulations instance.
    """
    personas = AGENT_PERSONAS[:n_agents] if n_agents else AGENT_PERSONAS
    context = _build_matchup_context(matchup, week)
    team_a_name = context["team_a"]["name"]
    team_b_name = context["team_b"]["name"]

    agent_results = []
    with ThreadPoolExecutor(max_workers=len(personas)) as executor:
        futures = {
            executor.submit(_run_agent, context, persona): persona
            for persona in personas
        }
        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                agent_results.append(result)

    if not agent_results:
        raise RuntimeError("All simulation agents failed — check OpenRouter API key and model availability")

    team_a_stats, team_b_stats, win_prob, player_scores = _aggregate_results(
        agent_results, team_a_name, team_b_name
    )

    simulation = MatchupSimulations(
        matchup_id=matchup.matchup_id,
        week=week,
        year=matchup.year,
        team_a_win_probability=win_prob,
        team_a_median_score=team_a_stats["median_score"],
        team_b_median_score=team_b_stats["median_score"],
        team_a_score_spread=team_a_stats["score_spread"],
        team_b_score_spread=team_b_stats["score_spread"],
        agent_results=agent_results,
        n_agents=len(agent_results),
    )
    db.session.add(simulation)
    db.session.flush()

    # Build a name → player_id lookup for starters on both teams
    name_to_player = {}
    for player in matchup.team.starters + matchup.opponent_team.starters:
        name_to_player[f"{player.first_name} {player.last_name}"] = player.player_id

    for player_name, predictions in player_scores.items():
        player_id = name_to_player.get(player_name)
        if player_id is None:
            continue
        for pred in predictions:
            proj = SimulationPlayerProjections(
                simulation_id=simulation.simulation_id,
                player_id=player_id,
                persona=pred["persona"],
                projected_score=pred["score"],
                reasoning=pred.get("reasoning") or None,
            )
            db.session.add(proj)

    db.session.commit()

    # Build per-player projections: median score + per-persona reasoning
    def _build_player_projections(starters, player_scores):
        result = {}
        starter_names = {f"{p.first_name} {p.last_name}" for p in starters}
        for name, preds in player_scores.items():
            if name not in starter_names:
                continue
            result[name] = {
                "median_score": round(statistics.median(p["score"] for p in preds), 2),
                "reasoning": {
                    p["persona"]: p["reasoning"]
                    for p in preds
                    if p.get("reasoning")
                },
            }
        return result

    simulation._response_data = {
        "team_a": {
            "name": team_a_name,
            "win_probability": win_prob,
            "median_score": team_a_stats["median_score"],
            "uncertainty": team_a_stats["score_spread"],
            "player_projections": _build_player_projections(matchup.team.starters, player_scores),
        },
        "team_b": {
            "name": team_b_name,
            "win_probability": round(1 - win_prob, 3),
            "median_score": team_b_stats["median_score"],
            "uncertainty": team_b_stats["score_spread"],
            "player_projections": _build_player_projections(matchup.opponent_team.starters, player_scores),
        },
        "n_agents": len(agent_results),
        "simulation_id": simulation.simulation_id,
        "agent_results": agent_results,
    }

    return simulation
