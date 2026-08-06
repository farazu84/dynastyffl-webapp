"""
Tests for AI ranking article generation (power rankings & franchise rankings).

The OpenRouter call is mocked at Articles._chat_completion — the single choke
point for the LLM — so tests assert on two things:
  1. The article rows created (type, title, teams, published state)
  2. The prompts sent to the model (focus, league context, movement handling)

Scenarios:
  1. Power rankings create a correctly-typed article linked to every team
  2. Franchise rankings create their own article type with their own title
  3. The two prompts carry their distinct ranking focus + shared league context
  4. Movement only references previous rankings of the SAME type
  5. Model failure returns None and writes nothing
  6. Admin endpoints generate, reject non-admins, and surface failures
"""

import os
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

from flask_jwt_extended import create_access_token

from tests.conftest import make_user

os.environ.setdefault('OPENROUTER_MODEL', 'test-model')
# Pin the provider so the author column (and any unmocked dispatch) stays on the
# OpenRouter path, where OPENROUTER_MODEL='test-model' applies.
os.environ.setdefault('ARTICLE_LLM_PROVIDER', 'openrouter')

FAKE_ARTICLE = '## 1. Team 1\nGreat team.'


# ── helpers ───────────────────────────────────────────────────────────────────

def _generate(method_name, content=FAKE_ARTICLE, year=2024, week=5):
    """
    Run a ranking generator with the LLM call and league state mocked.
    Returns (article, llm_mock) so tests can inspect the prompts via
    llm_mock.call_args: positional args are (system_prompt, user_prompt).
    """
    from app.models.articles import Articles

    with patch.object(Articles, '_chat_completion', return_value=content) as llm, \
         patch('app.league_state_manager.get_current_year', return_value=year), \
         patch('app.league_state_manager.get_current_week', return_value=week):
        article = getattr(Articles, method_name)()
    return article, llm


def _prompts(llm_mock):
    system_prompt, user_prompt = llm_mock.call_args[0]
    return system_prompt, user_prompt


def _seed_published_article(db, article_type, content='PREVIOUS RANKINGS CONTENT',
                            title='Old Rankings', published=True):
    from app.models.articles import Articles
    article = Articles(
        article_type=article_type,
        title=title,
        content=content,
        thumbnail='',
        published=published,
    )
    db.session.add(article)
    db.session.commit()
    return article


def _bearer(token):
    return {'Authorization': f'Bearer {token}'}


def _admin_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': True, 'team_owner': False},
        )


def _user_token(app, user_id):
    with app.app_context():
        return create_access_token(
            identity=str(user_id),
            additional_claims={'admin': False, 'team_owner': True},
        )


# ── Scenario 1: Power rankings create a correctly-typed article ───────────────

class TestGeneratePowerRankings:

    def test_creates_article_linked_to_every_team(self, db, league):
        from app.models.articles import Articles
        from app.models.article_teams import ArticleTeams

        article, _ = _generate('generate_power_rankings')

        assert article is not None
        assert article.article_type == 'power_ranking'
        assert article.title == '2024 Week 5 Power Rankings'
        assert article.content == FAKE_ARTICLE
        assert article.published is False
        assert article.author == 'test-model'

        linked_team_ids = {at.team_id for at in ArticleTeams.query.filter_by(article_id=article.article_id)}
        assert linked_team_ids == {t.team_id for t in league.teams}

    def test_all_teams_appear_in_user_prompt(self, db, league):
        _, llm = _generate('generate_power_rankings')
        _, user_prompt = _prompts(llm)

        for team in league.teams:
            assert team.team_name in user_prompt


# ── Scenario 2: Franchise rankings are their own article type ─────────────────

class TestGenerateFranchiseRankings:

    def test_creates_franchise_ranking_article(self, db, league):
        article, _ = _generate('generate_franchise_rankings')

        assert article is not None
        assert article.article_type == 'franchise_ranking'
        assert article.title == '2024 Franchise Rankings (Week 5)'
        assert article.content == FAKE_ARTICLE
        assert article.published is False


# ── Scenario 3: The two prompts carry distinct focus + shared context ─────────

class TestRankingPrompts:

    def test_power_rankings_focus_on_current_season(self, db, league):
        _, llm = _generate('generate_power_rankings')
        system_prompt, _ = _prompts(llm)

        assert 'current season' in system_prompt
        assert '**Outlook:**' in system_prompt
        assert 'long-term franchise value' not in system_prompt

    def test_franchise_rankings_focus_on_long_term_value(self, db, league):
        _, llm = _generate('generate_franchise_rankings')
        system_prompt, _ = _prompts(llm)

        assert 'long-term franchise value' in system_prompt
        assert '**Window:**' in system_prompt
        assert 'taxi squad' in system_prompt

    def test_both_prompts_share_league_context_and_scoring(self, db, league):
        for method in ('generate_power_rankings', 'generate_franchise_rankings'):
            _, llm = _generate(method)
            system_prompt, _ = _prompts(llm)

            assert '10-team dynasty league' in system_prompt
            assert '4-round rookie draft' in system_prompt
            assert '1st and 2nd year players' in system_prompt
            assert 'PPR | 0.04 pts/passing yard' in system_prompt
            assert '1 QB, 2 RB, 3 WR, 1 TE, 1 Flex (RB/WR/TE), 1 K' in system_prompt


# ── Scenario 4: Movement only references rankings of the SAME type ────────────

class TestRankingMovement:

    def test_no_previous_rankings_means_no_movement(self, db, league):
        _, llm = _generate('generate_power_rankings')
        system_prompt, user_prompt = _prompts(llm)

        assert 'No previous rankings exist' in system_prompt
        assert 'Previous Rankings' not in user_prompt

    def test_previous_rankings_of_same_type_are_included(self, db, league):
        _seed_published_article(db, 'power_ranking')

        _, llm = _generate('generate_power_rankings')
        system_prompt, user_prompt = _prompts(llm)

        assert 'movement next to its name' in system_prompt
        assert 'PREVIOUS RANKINGS CONTENT' in user_prompt

    def test_power_and_franchise_rankings_do_not_cross_contaminate(self, db, league):
        _seed_published_article(db, 'power_ranking')

        _, llm = _generate('generate_franchise_rankings')
        system_prompt, user_prompt = _prompts(llm)

        assert 'No previous rankings exist' in system_prompt
        assert 'PREVIOUS RANKINGS CONTENT' not in user_prompt

    def test_unpublished_previous_rankings_are_ignored(self, db, league):
        _seed_published_article(db, 'power_ranking', published=False)

        _, llm = _generate('generate_power_rankings')
        system_prompt, user_prompt = _prompts(llm)

        assert 'No previous rankings exist' in system_prompt
        assert 'PREVIOUS RANKINGS CONTENT' not in user_prompt


# ── Scenario 5: Model failure returns None and writes nothing ─────────────────

class TestGenerationFailure:

    def test_returns_none_and_creates_no_article(self, db, league):
        from app.models.articles import Articles

        article, _ = _generate('generate_power_rankings', content=None)

        assert article is None
        assert Articles.query.count() == 0

    def test_franchise_failure_creates_no_article(self, db, league):
        from app.models.articles import Articles

        article, _ = _generate('generate_franchise_rankings', content=None)

        assert article is None
        assert Articles.query.count() == 0


# ── Scenario 6: Admin endpoints ───────────────────────────────────────────────

class TestGenerateRankingEndpoints:

    def _post_as_admin(self, app, client, db, article_type, content=FAKE_ARTICLE):
        from app.models.articles import Articles

        admin = make_user(db, user_name='admin', email='admin@example.com',
                          google_id='gid-admin', admin=True, team_owner=False)
        db.session.commit()
        token = _admin_token(app, admin.user_id)

        with patch.object(Articles, '_chat_completion', return_value=content), \
             patch('app.league_state_manager.get_current_year', return_value=2024), \
             patch('app.league_state_manager.get_current_week', return_value=5):
            return client.post(f'/v1/admin/articles/generate/{article_type}',
                               headers=_bearer(token))

    def test_power_ranking_endpoint_returns_article(self, app, client, db, league):
        res = self._post_as_admin(app, client, db, 'power_ranking')

        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert data['article']['article_type'] == 'power_ranking'

    def test_franchise_ranking_endpoint_returns_article(self, app, client, db, league):
        res = self._post_as_admin(app, client, db, 'franchise_ranking')

        assert res.status_code == 200
        data = res.get_json()
        assert data['success'] is True
        assert data['article']['article_type'] == 'franchise_ranking'

    def test_endpoint_returns_500_when_generation_fails(self, app, client, db, league):
        res = self._post_as_admin(app, client, db, 'franchise_ranking', content=None)

        assert res.status_code == 500
        assert res.get_json()['success'] is False

    def test_non_admin_cannot_generate(self, app, client, db, league):
        owner = make_user(db, user_name='owner', email='owner@example.com',
                          google_id='gid-owner', admin=False, team_owner=True)
        db.session.commit()
        token = _user_token(app, owner.user_id)

        res = client.post('/v1/admin/articles/generate/franchise_ranking',
                          headers=_bearer(token))

        assert res.status_code == 403

    def test_unauthenticated_cannot_generate(self, client, db):
        res = client.post('/v1/admin/articles/generate/franchise_ranking')
        assert res.status_code == 401


# ── Scenario 7: Data grounding — real stats and head-to-head in the prompts ───

def _assign_starter(db, league, sleeper_id, roster_id):
    player = league.player(sleeper_id)
    player.team_id = roster_id  # team_id == sleeper_roster_id in create_league
    player.starter = True
    db.session.commit()
    return player


def _seed_weekly_stats(db, player_sleeper_id, week_points, year=2024, roster_id=1):
    from app.models.player_weekly_stats import PlayerWeeklyStats
    for week, points in week_points.items():
        db.session.add(PlayerWeeklyStats(
            year=year, week=week,
            sleeper_roster_id=roster_id,
            player_sleeper_id=player_sleeper_id,
            points=points,
            is_starter=True,
        ))
    db.session.commit()


def _make_matchup(db, roster_id=1, opponent_roster_id=2, year=2024, week=5,
                  sleeper_matchup_id=1, points_for=0, points_against=0, completed=False):
    from app.models.matchups import Matchups
    m = Matchups(
        year=year, week=week,
        sleeper_matchup_id=sleeper_matchup_id,
        sleeper_roster_id=roster_id,
        opponent_sleeper_roster_id=opponent_roster_id,
        points_for=points_for,
        points_against=points_against,
        completed=completed,
    )
    db.session.add(m)
    db.session.commit()
    return m


def _generate_pregame(matchup, content=FAKE_ARTICLE, year=2024, week=5):
    from app.models.articles import Articles

    with patch.object(Articles, '_chat_completion', return_value=content) as llm, \
         patch('app.league_state_manager.get_current_year', return_value=year), \
         patch('app.league_state_manager.get_current_week', return_value=week):
        article = Articles.generate_pregame_report(matchup)
    return article, llm


class TestDataGrounding:

    def test_power_rankings_include_player_season_stats(self, db, league):
        _assign_starter(db, league, 101, 1)
        _seed_weekly_stats(db, 101, {3: 10.0, 4: 20.0, 5: 30.0})

        _, llm = _generate('generate_power_rankings')
        _, user_prompt = _prompts(llm)

        assert 'fantasy_stats_this_season' in user_prompt
        assert '"season_points": 60.0' in user_prompt
        assert '"ppg": 20.0' in user_prompt

    def test_players_without_stats_are_flagged(self, db, league):
        _assign_starter(db, league, 102, 2)

        _, llm = _generate('generate_power_rankings')
        _, user_prompt = _prompts(llm)

        assert 'no games recorded this season' in user_prompt

    def test_record_includes_weekly_scoring_averages(self, db, league):
        from app.models.team_records import TeamRecords
        db.session.add(TeamRecords(team_id=1, year=2024, wins=3, losses=2,
                                   points_for=500.0, points_against=450.0))
        db.session.commit()

        _, llm = _generate('generate_power_rankings')
        _, user_prompt = _prompts(llm)

        assert '"avg_points_per_week": 100.0' in user_prompt
        assert '"avg_points_against_per_week": 90.0' in user_prompt

    def test_fidelity_rules_in_both_ranking_prompts(self, db, league):
        for method in ('generate_power_rankings', 'generate_franchise_rankings'):
            _, llm = _generate(method)
            system_prompt, _ = _prompts(llm)

            assert 'Data Fidelity Rules' in system_prompt
            assert 'never compute, estimate, or invent fantasy point values' in system_prompt


# ── Scenario 8: Pregame report — stats, head-to-head, fidelity rules ──────────

class TestPregameReport:

    def test_creates_matchup_breakdown_article(self, db, league):
        matchup = _make_matchup(db)

        article, _ = _generate_pregame(matchup)

        assert article is not None
        assert article.article_type == 'matchup_breakdown'
        assert article.title == 'Team 1 vs Team 2 - Week 5'

    def test_starter_stats_appear_in_prompt(self, db, league):
        _assign_starter(db, league, 101, 1)
        _seed_weekly_stats(db, 101, {4: 15.5, 5: 24.5})
        matchup = _make_matchup(db)

        _, llm = _generate_pregame(matchup)
        _, user_prompt = _prompts(llm)

        assert '"season_points": 40.0' in user_prompt
        assert '"ppg": 20.0' in user_prompt

    def test_head_to_head_history_in_prompt(self, db, league):
        _make_matchup(db, year=2023, week=4, sleeper_matchup_id=90,
                      points_for=120.0, points_against=100.0, completed=True)
        _make_matchup(db, year=2024, week=2, sleeper_matchup_id=91,
                      points_for=90.0, points_against=110.0, completed=True)
        matchup = _make_matchup(db)

        _, llm = _generate_pregame(matchup)
        _, user_prompt = _prompts(llm)

        assert "1-1 from Team 1's perspective" in user_prompt
        assert '"winner": "Team 2"' in user_prompt

    def test_no_previous_meetings(self, db, league):
        matchup = _make_matchup(db)

        _, llm = _generate_pregame(matchup)
        _, user_prompt = _prompts(llm)

        assert 'no previous meetings' in user_prompt

    def test_fidelity_rules_in_system_prompt(self, db, league):
        matchup = _make_matchup(db)

        _, llm = _generate_pregame(matchup)
        system_prompt, _ = _prompts(llm)

        assert 'Data Fidelity Rules' in system_prompt
        assert 'head_to_head history' in system_prompt


# ── Scenario 9: Provider dispatch ─────────────────────────────────────────────

class TestProviderDispatch:

    def test_routes_to_anthropic(self, db):
        from app.models.articles import Articles

        with patch.dict(os.environ, {'ARTICLE_LLM_PROVIDER': 'anthropic'}), \
             patch.object(Articles, '_chat_completion_anthropic', return_value='out') as impl:
            assert Articles._chat_completion('sys', 'user') == 'out'
        impl.assert_called_once()

    def test_routes_to_openrouter(self, db):
        from app.models.articles import Articles

        with patch.dict(os.environ, {'ARTICLE_LLM_PROVIDER': 'openrouter'}), \
             patch.object(Articles, '_chat_completion_openrouter', return_value='out') as impl:
            assert Articles._chat_completion('sys', 'user') == 'out'
        impl.assert_called_once()

    def test_author_uses_provider_model(self, db, league):
        # ARTICLE_LLM_PROVIDER is pinned to openrouter at module import, so the
        # author column records OPENROUTER_MODEL ('test-model')
        article, _ = _generate('generate_power_rankings')
        assert article.author == 'test-model'


# ── Scenario 10: Anthropic path — text extraction and pause_turn resume ───────

def _anthropic_response(stop_reason, blocks):
    return SimpleNamespace(stop_reason=stop_reason, content=blocks)


def _text_block(text):
    return SimpleNamespace(type='text', text=text)


class TestAnthropicPath:

    def _call(self, client_mock, **kwargs):
        from app.models.articles import Articles
        with patch('anthropic.Anthropic', return_value=client_mock):
            return Articles._chat_completion_anthropic(
                'sys', 'user', online=True, temperature=0.4, max_tokens=100, **kwargs)

    def test_extracts_only_text_blocks(self, db):
        client = MagicMock()
        client.messages.create.return_value = _anthropic_response('end_turn', [
            SimpleNamespace(type='server_tool_use'),
            SimpleNamespace(type='web_search_tool_result'),
            _text_block('Hello '),
            _text_block('world'),
        ])

        assert self._call(client) == 'Hello world'

        tools = client.messages.create.call_args.kwargs['tools']
        assert tools[0]['type'] == 'web_search_20260209'

    def test_pause_turn_resumes_with_assistant_content(self, db):
        paused = _anthropic_response('pause_turn', [SimpleNamespace(type='server_tool_use')])
        done = _anthropic_response('end_turn', [_text_block('done')])
        client = MagicMock()
        client.messages.create.side_effect = [paused, done]

        assert self._call(client) == 'done'

        assert client.messages.create.call_count == 2
        resumed_messages = client.messages.create.call_args.kwargs['messages']
        assert resumed_messages[0] == {'role': 'user', 'content': 'user'}
        assert resumed_messages[1] == {'role': 'assistant', 'content': paused.content}

    def test_api_error_returns_none(self, db):
        import anthropic
        client = MagicMock()
        client.messages.create.side_effect = anthropic.AnthropicError('boom')

        assert self._call(client) is None


