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
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from tests.conftest import make_user

os.environ.setdefault('OPENROUTER_MODEL', 'test-model')

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
