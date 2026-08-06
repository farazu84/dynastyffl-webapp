import requests
import json
import os
import textwrap

from .. import db
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func
from app.models.schemas.articles import ArticlesJSONSchema
from app.models.article_teams import ArticleTeams
from app.models.teams import Teams
from app.models.league_state import LeagueState
from sqlalchemy.orm import relationship


class Articles(db.Model):
    __tablename__ = 'Articles'

    article_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    article_teams = relationship('ArticleTeams', back_populates='article')

    article_type = db.Column(db.Enum('power_ranking', 'franchise_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown', 'weekly_recap'), nullable=True)

    author = db.Column(db.String(64), nullable=True)

    title = db.Column(db.TEXT, nullable=False)

    content = db.Column(db.TEXT, nullable=False)

    thumbnail = db.Column(db.String(64), nullable=False)

    creation_date = db.Column(DATETIME, nullable=False, default=func.now())

    published = db.Column(db.Boolean, nullable=False, default=False)

    def serialize(self):
        return ArticlesJSONSchema().dump(self)

    @staticmethod
    def _provider():
        return os.environ.get("ARTICLE_LLM_PROVIDER", "anthropic")

    @staticmethod
    def _article_model_name():
        if Articles._provider() == "anthropic":
            return os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        return os.environ["OPENROUTER_MODEL"]

    @staticmethod
    def _chat_completion(system_prompt, user_prompt, *, online=True, temperature=0.4, top_p=0.9, max_tokens=4000, response_format=None, model_override=None):
        '''
        Call the configured LLM provider (ARTICLE_LLM_PROVIDER: anthropic | openrouter)
        and return the response content, or None on any failure.
        '''
        if Articles._provider() == "anthropic":
            return Articles._chat_completion_anthropic(
                system_prompt, user_prompt,
                online=online, temperature=temperature,
                max_tokens=max_tokens, response_format=response_format,
                model_override=model_override,
            )
        return Articles._chat_completion_openrouter(
            system_prompt, user_prompt,
            online=online, temperature=temperature, top_p=top_p,
            max_tokens=max_tokens, response_format=response_format,
            model_override=model_override,
        )

    @staticmethod
    def _chat_completion_anthropic(system_prompt, user_prompt, *, online, temperature, max_tokens, response_format=None, model_override=None):
        '''
        Call the Anthropic API directly. When online, the native web search tool
        lets the model run multiple searches and read the results itself.
        '''
        import anthropic

        model = model_override or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}] if online else []

        if response_format:
            system_prompt += "\nRespond with a single valid JSON object and nothing else."

        messages = [{"role": "user", "content": user_prompt}]
        try:
            client = anthropic.Anthropic()
            for _ in range(5):
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    # Claude 4+ rejects requests that set both temperature and top_p
                    temperature=temperature,
                    system=system_prompt,
                    messages=messages,
                    tools=tools,
                )
                if response.stop_reason != "pause_turn":
                    break
                # Server-side search loop paused; append the assistant turn and re-send to resume
                messages.append({"role": "assistant", "content": response.content})
        except anthropic.AnthropicError as e:
            print(f"Anthropic request failed: {e}")
            return None

        text = "".join(block.text for block in response.content if block.type == "text")
        return text or None

    @staticmethod
    def _chat_completion_openrouter(system_prompt, user_prompt, *, online, temperature, top_p, max_tokens, response_format=None, model_override=None):
        '''
        Call OpenRouter and return the response content, or None on any failure.
        '''
        model = (model_override or os.environ["OPENROUTER_MODEL"]) + (":online" if online else "")

        payload = {
            "model": model,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        if response_format:
            payload["response_format"] = response_format

        try:
            response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
        except requests.RequestException as e:
            print(f"OpenRouter request failed: {e}")
            return None

        if not response.ok:
            print(response.text)
            return None

        response_json = response.json()
        try:
            content = response_json['choices'][0]['message']['content']
        except (KeyError, IndexError, TypeError):
            print(f"Unexpected OpenRouter response: {response_json}")
            return None

        if not content:
            print(f"Empty content in OpenRouter response: {response_json}")
            return None

        return content

    @staticmethod
    def _parse_article_json(raw, fallback_title):
        '''
        Parse a {"title": ..., "content": ...} model response.
        Falls back to (fallback_title, raw) if the response is not valid JSON.
        '''
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[-1]
            cleaned = cleaned.rsplit('```', 1)[0]

        try:
            parsed = json.loads(cleaned)
            title = parsed.get('title')
            content = parsed.get('content')
            if title and content:
                return title.strip(), content
        except (json.JSONDecodeError, AttributeError):
            pass

        return fallback_title, raw

    @staticmethod
    def _create_article(article_type, title, content, team_ids):
        article = Articles(
            article_type=article_type,
            author=Articles._article_model_name(),
            title=title,
            content=content,
            thumbnail='',
        )
        db.session.add(article)
        db.session.flush()

        for team_id in team_ids:
            db.session.add(ArticleTeams(
                article_id=article.article_id,
                team_id=team_id,
            ))

        db.session.commit()
        return article

    @staticmethod
    def _season_stats_map(sleeper_ids):
        '''
        Bulk-load this season's weekly fantasy points for the given players.
        Returns {sleeper_id: {season_points, games_played, ppg}}.
        '''
        from app.models.player_weekly_stats import PlayerWeeklyStats
        from app.league_state_manager import get_current_year

        sleeper_ids = [sleeper_id for sleeper_id in sleeper_ids if sleeper_id]
        if not sleeper_ids:
            return {}

        rows = db.session.query(
            PlayerWeeklyStats.player_sleeper_id,
            PlayerWeeklyStats.points,
        ).filter(
            PlayerWeeklyStats.year == get_current_year(),
            PlayerWeeklyStats.player_sleeper_id.in_(sleeper_ids),
        ).all()

        weekly = {}
        for sleeper_id, points in rows:
            weekly.setdefault(sleeper_id, []).append(points)

        stats_map = {}
        for sleeper_id, games in weekly.items():
            season_points = round(sum(games), 1)
            stats_map[sleeper_id] = {
                'season_points': season_points,
                'games_played': len(games),
                'ppg': round(season_points / len(games), 1),
            }
        return stats_map

    @staticmethod
    def _team_context(team, include_bench=False, recent_results=0, stats_map=None):
        '''
        Build the JSON-serializable context for a team that gets fed to the model.
        '''
        stats_map = stats_map or {}

        def player_context(player):
            data = player.ai_serialize()
            data['fantasy_stats_this_season'] = stats_map.get(player.sleeper_id, 'no games recorded this season')
            return data

        context = {
            'starters': [player_context(player) for player in team.starters],
            'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners],
        }

        if include_bench:
            context['bench'] = [player_context(player) for player in team.players if not player.starter and not player.taxi]
            context['taxi_squad'] = [player_context(player) for player in team.players if player.taxi]

        record = team.current_team_record
        if record:
            games_played = record.wins + record.losses
            context['record'] = {
                'wins': record.wins,
                'losses': record.losses,
                'points_for': record.points_for,
                'points_against': record.points_against,
                'avg_points_per_week': round(record.points_for / max(games_played, 1), 1),
                'avg_points_against_per_week': round(record.points_against / max(games_played, 1), 1),
            }

        if recent_results:
            from app.models.matchups import Matchups
            from app.league_state_manager import get_current_year

            matchups = Matchups.query \
                .filter_by(sleeper_roster_id=team.sleeper_roster_id, year=get_current_year(), completed=True) \
                .order_by(Matchups.week.desc()) \
                .limit(recent_results) \
                .all()

            context['recent_results'] = [
                {
                    'week': m.week,
                    'opponent': m.opponent_team.team_name,
                    'score': f'{m.points_for}-{m.points_against}',
                    'result': 'W' if m.points_for > m.points_against else 'L',
                }
                for m in matchups
            ]

        return context

    @staticmethod
    def _data_fidelity_rules():
        from datetime import date
        return textwrap.dedent(f"""\
        ## Data Fidelity Rules (critical)
        - Today's date is {date.today().isoformat()}. Facts you remember from training may be outdated — the provided JSON is current.
        - The provided JSON is the single source of truth for: rosters, player ages, years of experience, current NFL team, injury status, league records, scores, and all fantasy point totals.
        - Fantasy scoring is provided per player as "fantasy_stats_this_season" (season points, games played, PPG). Cite these numbers directly; never compute, estimate, or invent fantasy point values.
        - Use web search only for real-NFL context (yardage, touchdowns, usage, news), and attribute searched stats to the current season explicitly.
        - If you cannot verify a real-NFL statistic via search, describe the player qualitatively without a number. Fewer numbers beats a wrong number.
        - Only mention an injury if it appears in the JSON injury_status or in a current-season search result. Never infer or recall injuries.""")

    @staticmethod
    def _fact_check(content, source_data):
        '''
        Cheap post-generation pass: list contradictions between the article and
        the data it was generated from. Never raises — returns None on failure
        or when disabled via ARTICLE_FACT_CHECK.
        '''
        if os.environ.get("ARTICLE_FACT_CHECK", "false").lower() != "true":
            return None

        if Articles._provider() == "anthropic":
            model = os.environ.get("ANTHROPIC_FACT_CHECK_MODEL", "claude-haiku-4-5")
        else:
            model = os.environ.get("OPENROUTER_FACT_CHECK_MODEL", "anthropic/claude-haiku-4.5")

        system_prompt = textwrap.dedent("""\
        ## Role
        You are a fact-checker for a fantasy football league site.

        ## Instructions
        - Compare the article against the source data it was generated from
        - List every factual contradiction: wrong records, wrong scores, wrong fantasy point totals, players attributed to the wrong team, or injuries that do not appear in the source data
        - Ignore real-NFL statistics (yardage, touchdowns) that are not in the source data — those come from web search and cannot be checked here
        - Return a short markdown bullet list of contradictions, or exactly "No contradictions found." if there are none
        """)

        try:
            return Articles._chat_completion(
                system_prompt,
                f"## Source Data\n{source_data}\n\n## Article\n{content}",
                online=False,
                temperature=0.0,
                max_tokens=1000,
                model_override=model,
            )
        except Exception as e:
            print(f"Fact check failed: {e}")
            return None

    @staticmethod
    def generate_pregame_report(matchup):
        '''
        Generate a pregame report for a matchup.
        '''
        from app.models.matchups import Matchups

        teams = [matchup.team, matchup.opponent_team]
        stats_map = Articles._season_stats_map([player.sleeper_id for team in teams for player in team.starters])
        team_dict = {team.team_name: Articles._team_context(team, recent_results=3, stats_map=stats_map) for team in teams}

        h2h = Matchups.query.filter(
            Matchups.sleeper_roster_id == matchup.sleeper_roster_id,
            Matchups.opponent_sleeper_roster_id == matchup.opponent_sleeper_roster_id,
            Matchups.completed == True,
            Matchups.matchup_id != matchup.matchup_id,
        ).order_by(Matchups.year.desc(), Matchups.week.desc()).all()

        if h2h:
            wins = sum(1 for m in h2h if m.points_for > m.points_against)
            losses = sum(1 for m in h2h if m.points_for < m.points_against)
            head_to_head = {
                'all_time_record': f"{wins}-{losses} from {matchup.team.team_name}'s perspective",
                'recent_meetings': [
                    {
                        'year': m.year,
                        'week': m.week,
                        'score': f'{m.points_for}-{m.points_against}',
                        'winner': matchup.team.team_name if m.points_for > m.points_against
                                  else matchup.opponent_team.team_name if m.points_for < m.points_against
                                  else 'tie',
                    }
                    for m in h2h[:5]
                ],
            }
        else:
            head_to_head = 'no previous meetings'

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a sports writer generating a matchup preview article for a fantasy football league (PPR scoring).

        ## Context
        Week {matchup.week} of the {matchup.year} NFL season. This is a 10-team dynasty league.
        Starting lineup: 1 QB, 2 RB, 3 WR, 1 TE, 1 Flex (RB/WR/TE), 1 K.

        ## Instructions
        - Analyze the two teams using the JSON provided (rosters, records, recent results, this-season fantasy stats)
        - Use web search to look up current season stats, recent performance, and matchup context for the players
        - Reference the head_to_head history provided when framing the storyline
        - Only cite statistics and facts that come from the provided data or your web search results
        - Do not fabricate any statistics, scores, or rankings

        {Articles._data_fidelity_rules()}

        ## Required Structure
        1. A headline storyline that frames the matchup
        2. A capsule for each team: record, recent form, and how the roster sets up this week (cite the provided PPG and season points)
        3. Key positional matchups (use the player positions provided)
        4. Injury watch: flag any players with an injury status and what it means for the lineup
        5. X-Factor: one player on each side who could swing the matchup
        6. Prediction: pick a winner with qualitative confidence (do not invent projected scores)

        ## Scoring Reference (do not include in article)
        PPR | 0.04 pts/passing yard | 0.1 pts/rushing+receiving yard | 6 pts/rushing+receiving TD | 4 pts/passing TD | -4/INT | -2/fumble lost

        ## Output Format
        Return the article in markdown. Be creative and write like a real sports journalist.
        Keep the tone professional and analytical.
        """)

        payload = {'teams': team_dict, 'head_to_head': head_to_head}
        user_prompt = f"Here are the teams for this week's matchup:\n{json.dumps(payload, indent=2)}"

        content = Articles._chat_completion(system_prompt, user_prompt, temperature=0.5, max_tokens=3500)
        if content is None:
            return None

        return Articles._create_article(
            article_type='matchup_breakdown',
            title=f'{matchup.team.team_name} vs {matchup.opponent_team.team_name} - Week {matchup.week}',
            content=content,
            team_ids=[matchup.team.team_id, matchup.opponent_team.team_id],
        )

    @staticmethod
    def generate_rumor(rumor, team_ids):
        '''
        Generate a rumor article.
        '''
        teams = db.session.query(Teams).filter(Teams.team_id.in_(team_ids)).all()
        all_player_ids = [p.sleeper_id for team in teams for p in team.players]
        stats_map = Articles._season_stats_map(all_player_ids)
        team_dict = {team.team_name: Articles._team_context(team, include_bench=True, stats_map=stats_map) for team in teams}

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a gossip-column fantasy football insider spreading a rumor about teams in a 10-team dynasty PPR league.
        Humor, snark, and playful jabs at the owners are encouraged — but the underlying analysis must stay grounded in the data.

        ## Instructions
        - Use the roster data, records, and the rumor to explain why the move would (or wouldn't) make sense for the teams involved
        - Use web search to find current player values, recent performance, and relevant context
        - Only cite statistics and facts from the provided data or your web search results
        - Do not propose any trade unless it is explicitly mentioned in the rumor
        - Do not fabricate any statistics, scores, or rankings

        {Articles._data_fidelity_rules()}

        ## Teams Involved
        {json.dumps(team_dict, indent=2)}

        ## Output Format
        Return a JSON object with exactly two keys:
        {{"title": "a short, punchy, plain-text headline", "content": "the full article in markdown"}}
        Write the content like a fantasy football insider column. Do not include the scoring rules in the article.
        """)

        raw = Articles._chat_completion(
            system_prompt,
            rumor,
            temperature=0.8,
            max_tokens=2500,
            response_format={"type": "json_object"},
        )
        if raw is None:
            return None

        fallback_title = f"League Rumor Mill: {', '.join(team.team_name for team in teams)}"
        title, content = Articles._parse_article_json(raw, fallback_title)

        return Articles._create_article(
            article_type='rumors',
            title=title,
            content=content,
            team_ids=team_ids,
        )

    @staticmethod
    def _generate_rankings(article_type, title, role, ranking_instructions, team_section_instructions):
        '''
        Shared core for ranking articles: gathers team context, references the
        previous published rankings of the same type for movement, and creates
        the article.
        '''
        teams = db.session.query(Teams).all()
        stats_map = Articles._season_stats_map([player.sleeper_id for team in teams for player in team.players])
        team_dict = {team.team_name: Articles._team_context(team, include_bench=True, recent_results=3, stats_map=stats_map) for team in teams}

        from app.league_state_manager import get_current_year, get_current_week

        previous_rankings = Articles.query \
            .filter_by(article_type=article_type, published=True) \
            .order_by(Articles.creation_date.desc()) \
            .first()

        movement_instructions = textwrap.dedent("""\
        - Previous rankings are provided; show each team's movement next to its name (▲n for risers, ▼n for fallers, — for no change)
        - End the article with a short "Biggest Riser / Biggest Faller" section explaining the largest moves
        """) if previous_rankings else \
        "- No previous rankings exist, so do not include movement indicators\n"

        system_prompt = textwrap.dedent(f"""\
        ## Role
        {role}

        ## Context
        Week {get_current_week()} of the {get_current_year()} NFL season. This is a 10-team dynasty league:
        rosters carry over year to year, and teams build through trades, an annual 4-round rookie draft, and blind-bid UDFA auctions.
        Draft picks are tradeable, so future picks are part of a team's asset base.
        Each team also has a taxi squad for stashing developmental players: only 1st and 2nd year players are eligible, and taxi players cannot be started.
        Starting lineup: 1 QB, 2 RB, 3 WR, 1 TE, 1 Flex (RB/WR/TE), 1 K.
        With only 1 QB starting in a 10-team league, QBs are generally less valuable than they are in real life.

        ## Instructions
        - Rank all 10 teams from 1 (best) to 10 (worst)
        {ranking_instructions}
        - Use web search to factor in recent player performance, relevant news, and recent injuries
        - Only cite statistics and facts from the provided data or your web search results
        - Do not fabricate any statistics, scores, or rankings
        {movement_instructions}
        {Articles._data_fidelity_rules()}

        ## Scoring Reference (do not include in article)
        PPR | 0.04 pts/passing yard | 0.1 pts/rushing+receiving yard | 6 pts/rushing+receiving TD | 4 pts/passing TD | -4/INT | -2/fumble lost

        ## Required Structure
        - A short intro paragraph framing the rankings
        {team_section_instructions}
        - Use dividers between teams to aid readability

        ## Output Format
        Return the article in markdown.
        Write like a confident analyst. Do not include the scoring rules in the article.
        """)

        user_prompt = f"Here are the league's teams:\n{json.dumps(team_dict, indent=2)}"
        if previous_rankings:
            user_prompt += f"\n\n## Previous Rankings ({previous_rankings.title})\n{previous_rankings.content}"

        content = Articles._chat_completion(system_prompt, user_prompt, temperature=0.4, top_p=0.9, max_tokens=6000)
        if content is None:
            return None

        return Articles._create_article(
            article_type=article_type,
            title=title,
            content=content,
            team_ids=[team.team_id for team in teams],
        )

    @staticmethod
    def generate_power_rankings():
        '''
        Generate weekly power rankings focused on current-season performance.
        '''
        from app.league_state_manager import get_current_year, get_current_week

        ranking_instructions = textwrap.dedent("""\
        - These rankings are about the current season: records, points for/against, and recent results are the primary signal
        - Weigh how each team is performing right now — hot and cold streaks, lineup health, and weekly scoring matter more than long-term roster value
        - Ground each team's analysis in its record, avg points per week, and its players' provided fantasy stats
        - Prospects and stashed players only matter here if they are contributing (or about to contribute) this season
        """)

        team_section_instructions = textwrap.dedent("""\
        - One section per team using this header format: `## {rank}. {Team Name} ({wins}-{losses})` plus the movement indicator when applicable
        - 2-3 sentences of analysis per team, then a one-line "**Outlook:**" verdict
        """)

        return Articles._generate_rankings(
            article_type='power_ranking',
            title=f'{get_current_year()} Week {get_current_week()} Power Rankings',
            role='You are a fantasy football analyst generating weekly power rankings for a PPR league, ranking teams by how they are performing this season.',
            ranking_instructions=ranking_instructions,
            team_section_instructions=team_section_instructions,
        )

    @staticmethod
    def generate_franchise_rankings():
        '''
        Generate franchise rankings focused on long-term dynasty value.
        '''
        from app.league_state_manager import get_current_year, get_current_week

        ranking_instructions = textwrap.dedent("""\
        - These rankings are about long-term franchise value: which teams have the best mix of elite young assets and win-now production
        - Evaluate the full roster — bench and taxi squad prospects can carry as much value as starters
        - Player ages and long-term outlook are the primary signal; current records and results are context, not the deciding factor
        - Classify each team's competitive window: contending, retooling, or rebuilding
        """)

        team_section_instructions = textwrap.dedent("""\
        - One section per team using this header format: `## {rank}. {Team Name}` plus the movement indicator when applicable
        - 2-3 sentences of analysis per team covering its core assets and age profile, then a one-line "**Window:**" verdict (contending / retooling / rebuilding)
        """)

        return Articles._generate_rankings(
            article_type='franchise_ranking',
            title=f'{get_current_year()} Franchise Rankings (Week {get_current_week()})',
            role='You are a fantasy football analyst generating franchise rankings for a dynasty PPR league, ranking teams by long-term value rather than current results.',
            ranking_instructions=ranking_instructions,
            team_section_instructions=team_section_instructions,
        )

    @staticmethod
    def generate_weekly_recap(week=None, year=None):
        '''
        Generate a recap of all completed matchups for a week.
        '''
        from app.models.matchups import Matchups
        from app.league_state_manager import get_current_year, get_current_week

        if year is None:
            year = get_current_year()
        if week is None:
            week = get_current_week()

        all_matchups = Matchups.query.filter_by(week=week, year=year, completed=True).all()
        unique_matchups = list({m.sleeper_matchup_id: m for m in all_matchups}.values())

        if not unique_matchups:
            return None

        all_player_ids = [
            p.sleeper_id
            for m in unique_matchups
            for team in [m.team, m.opponent_team]
            for p in team.starters
        ]
        stats_map = Articles._season_stats_map(all_player_ids)

        games = []
        team_ids = []
        for matchup in unique_matchups:
            games.append({
                matchup.team.team_name: {
                    'points': matchup.points_for,
                    **Articles._team_context(matchup.team, stats_map=stats_map),
                },
                matchup.opponent_team.team_name: {
                    'points': matchup.points_against,
                    **Articles._team_context(matchup.opponent_team, stats_map=stats_map),
                },
            })
            team_ids.extend([matchup.team.team_id, matchup.opponent_team.team_id])

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a sports writer recapping the week's results for a fantasy football league (PPR scoring).

        ## Context
        Week {week} of the {year} NFL season. This is a 10-team dynasty league.

        ## Instructions
        - Recap every game using the final scores provided — the team with more points won
        - Use web search to add context about how the key players actually performed this week
        - Only cite statistics and facts from the provided data or your web search results
        - Do not fabricate any player stat lines, scores, or rankings

        {Articles._data_fidelity_rules()}

        ## Required Structure
        - A short intro paragraph on the week as a whole
        - One section per game with the header format: `## {{Winner}} def. {{Loser}}, {{winning score}}-{{losing score}}`
        - 2-3 sentences telling the story of each game, then a one-line "**Game ball:**" for the standout player
        - A closing "## Week in Review" section: highest-scoring team, closest game, and what the results mean for the standings

        ## Output Format
        Return the article in markdown. Keep the tone professional and analytical.
        Do not include the scoring rules in the article.
        """)

        user_prompt = f"Here are this week's final results:\n{json.dumps(games, indent=2)}"

        content = Articles._chat_completion(system_prompt, user_prompt, temperature=0.4, max_tokens=5000)
        if content is None:
            return None

        return Articles._create_article(
            article_type='weekly_recap',
            title=f'{year} Week {week} Recap',
            content=content,
            team_ids=team_ids,
        )

    @staticmethod
    def generate_team_analysis(team_id):
        '''
        Generate a dynasty deep-dive article for a single team.
        '''
        team = db.session.get(Teams, team_id)
        if team is None:
            return None

        all_player_ids = [p.sleeper_id for p in team.players]
        stats_map = Articles._season_stats_map(all_player_ids)
        team_context = Articles._team_context(team, include_bench=True, recent_results=5, stats_map=stats_map)

        from app.league_state_manager import get_current_year, get_current_week

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a fantasy football analyst writing a dynasty deep-dive on a single team in a 10-team PPR league.

        ## Context
        Week {get_current_week()} of the {get_current_year()} NFL season.
        Starting lineup: 1 QB, 2 RB, 3 WR, 1 TE, 1 Flex (RB/WR/TE), 1 K — so QBs are less valuable than in real life.
        This is a dynasty league: player ages and long-term outlook matter as much as current production.

        ## Instructions
        - Analyze the full roster (starters, bench, taxi squad), the team's record, and recent results
        - Use web search for current season stats, player news, and injuries
        - Only cite statistics and facts from the provided data or your web search results
        - Do not fabricate any statistics, scores, or rankings

        {Articles._data_fidelity_rules()}

        ## Required Structure
        1. Opening verdict: is this team a contender, a fringe playoff team, or a rebuilder?
        2. Positional group grades (QB, RB, WR, TE, K) with brief justification
        3. Age curve: how the roster's age profile shapes its dynasty window
        4. Biggest strength and biggest weakness
        5. Three concrete recommendations (lineup, trade targets by archetype, or roster strategy)
        6. Outlook: rest of this season and the next two years

        ## Output Format
        Return a JSON object with exactly two keys:
        {{"title": "a short, plain-text headline about this team", "content": "the full article in markdown"}}
        Keep the tone professional and analytical. Do not include the scoring rules in the article.
        """)

        user_prompt = f"Here is the team to analyze:\n{json.dumps({team.team_name: team_context}, indent=2)}"

        raw = Articles._chat_completion(
            system_prompt,
            user_prompt,
            temperature=0.5,
            max_tokens=4000,
            response_format={"type": "json_object"},
        )
        if raw is None:
            return None

        title, content = Articles._parse_article_json(raw, f'State of the Franchise: {team.team_name}')

        return Articles._create_article(
            article_type='team_analysis',
            title=title,
            content=content,
            team_ids=[team.team_id],
        )
