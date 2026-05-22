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

    article_type = db.Column(db.Enum('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown'), nullable=True)

    author = db.Column(db.String(64), nullable=True)

    title = db.Column(db.TEXT, nullable=False)

    content = db.Column(db.TEXT, nullable=False)

    thumbnail = db.Column(db.String(64), nullable=False)

    creation_date = db.Column(DATETIME, nullable=False, default=func.now())

    published = db.Column(db.Boolean, nullable=False, default=False)

    def serialize(self):
        return ArticlesJSONSchema().dump(self)

    @staticmethod
    def generate_pregame_report(matchup):
        '''
        Generate a pregame report for a matchup.
        This costs roughly 3900 tokens.
        '''
        teams = [matchup.team, matchup.opponent_team]
        team_dict = {}
        for team in teams:
            team_info = {
                'starters': [player.ai_serialize() for player in team.starters],
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a sports writer generating a matchup preview article for a fantasy football league (PPR scoring).

        ## Context
        Week {matchup.week} of the {matchup.year} NFL season.

        ## Instructions
        - Analyze the two teams using the starters JSON provided
        - Consider positional advantages and any injury concerns
        - Use web search to look up current season stats, recent performance, and matchup context for the players
        - Only cite statistics and facts that come from the provided data or your web search results
        - Do not fabricate any statistics, scores, or rankings

        ## Scoring Reference (do not include in article)
        PPR | 0.04 pts/passing yard | 0.1 pts/rushing+receiving yard | 6 pts/rushing+receiving TD | 4 pts/passing TD | -4/INT | -2/fumble lost

        ## Output Format
        Return the article in markdown. Be creative and write like a real sports journalist.
        """)

        user_prompt = f"Here are the teams for this week's matchup:\n{json.dumps(team_dict, indent=2)}"

        response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                    "Content-Type": "application/json",
                },
                json={
                    "transforms": ["middle-out"],
                    "model": os.environ["OPENROUTER_MODEL"] + ":online",
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
            )
        if response.ok:
            response_json = response.json()
            print(response_json)
        else:
            print(response.text)
            return None

        article = Articles(
            article_type='matchup_breakdown',
            author=os.environ["OPENROUTER_MODEL"],
            title=f'{matchup.team.team_name} vs {matchup.opponent_team.team_name} - Week {matchup.week}',
            content=response_json['choices'][0]['message']['content'],
            thumbnail='',
        )

        db.session.add(article)
        db.session.flush()

        article_team1 = ArticleTeams(
            article_id=article.article_id,
            team_id=matchup.team.team_id,
        )

        article_team2 = ArticleTeams(
            article_id=article.article_id,
            team_id=matchup.opponent_team.team_id,
        )

        db.session.add(article_team1)
        db.session.add(article_team2)
        db.session.commit()

        return article

    @staticmethod
    def generate_rumor(rumor, team_ids):
        '''
        Generate a rumor article.
        '''

        teams = db.session.query(Teams).filter(Teams.team_id.in_(team_ids)).all()
        team_dict = {}
        for team in teams:
            team_info = {
                'starters': [player.ai_serialize() for player in team.starters],
                'bench': [player.ai_serialize() for player in team.players if not player.starter],
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a fantasy football insider spreading a rumor about teams in a PPR league.

        ## Instructions
        - Use the roster data and the rumor to explain why the move would make sense for the teams involved
        - Use web search to find current player values, recent performance, and relevant context
        - Only cite statistics and facts from the provided data or your web search results
        - Do not propose any trade unless it is explicitly mentioned in the rumor
        - Do not fabricate any statistics, scores, or rankings

        ## Teams Involved
        {json.dumps(team_dict, indent=2)}

        ## Output Format
        Return the article in markdown. Be creative and write like a fantasy football insider column.
        Do not include the scoring rules in the article.
        """)

        user_prompt = rumor

        response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                    "Content-Type": "application/json",
                },
                json={
                    "transforms": ["middle-out"],
                    "model": os.environ["OPENROUTER_MODEL"] + ":online",
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
            )

        if response.ok:
            response_json = response.json()
            print(response_json)
        else:
            print(response.text)
            return None

        print(response_json['choices'][0]['message']['content'])

        full_content = response_json['choices'][0]['message']['content']

        article_title = Articles.generate_article_title(full_content)

        article = Articles(
            article_type='rumors',
            author=os.environ["OPENROUTER_MODEL"],
            title=article_title,
            content=full_content,
            thumbnail='',
        )
        db.session.add(article)
        db.session.flush()

        for team_id in team_ids:
            article_team = ArticleTeams(
                article_id=article.article_id,
                team_id=team_id,
            )
            db.session.add(article_team)

        db.session.commit()

        return article

    @staticmethod
    def generate_power_rankings():
        '''
        Generate power rankings for all teams.
        '''

        teams = db.session.query(Teams).all()
        team_dict = {}
        for team in teams:
            team_info = {
                'players': [player.ai_serialize() for player in team.players],
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        from app.league_state_manager import get_current_year, get_current_week

        current_year = get_current_year()
        current_week = get_current_week()

        article_title = f'{current_year} Week {current_week} Power Rankings'

        system_prompt = textwrap.dedent(f"""\
        ## Role
        You are a fantasy football analyst generating weekly power rankings for a PPR league.

        ## Context
        Week {current_week} of the {current_year} NFL season.

        ## Instructions
        - Rank all 10 teams from 1 (best) to 10 (worst)
        - Remember the most valuable players may not always be the starters, so consider the value of all players on the roster
        - Remember this is a dynasty football league, so player ages and long term performance are important
        - The starting lineup consists of 1 QB, 2 RBs, 3 WRs, 1 TE, 1 Flex(RB,WR,TE), 1 K
        - So this means QBs are generally less valuable than they are in real life
        - Use web search to factor in recent player performance, relevant news, and recent injuries
        - Only cite statistics and facts from the provided data or your web search results
        - Do not fabricate any statistics, scores, or rankings
        - Provide reasoning and analysis for each team's ranking

        ## Output Format
        Return the article in markdown. Use headers and dividers between teams to aid readability.
        Write like a confident analyst. Do not include the scoring rules in the article.
        """)

        user_prompt = f"Here are the league's teams:\n{json.dumps(team_dict, indent=2)}"

        response = requests.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                    "Content-Type": "application/json",
                },
                json={
                    "transforms": ["middle-out"],
                    "model": os.environ["OPENROUTER_MODEL"] + ":online",
                    "temperature": 0.4,
                    "top_p": 0.9,
                    "max_tokens": 4000,
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
            )

        if response.ok:
            response_json = response.json()
            print(response_json)
        else:
            print(response.text)
            return None

        print(response_json['choices'][0]['message']['content'])

        full_content = response_json['choices'][0]['message']['content']

        article = Articles(
            article_type='power_ranking',
            author=os.environ["OPENROUTER_MODEL"],
            title=article_title,
            content=full_content,
            thumbnail='',
        )
        db.session.add(article)
        db.session.flush()

        for team in teams:
            article_team = ArticleTeams(
                article_id=article.article_id,
                team_id=team.team_id,
            )
            db.session.add(article_team)

        db.session.commit()

        return article


    def generate_article_title(article):
        '''
        Generate a title for an article.
        '''

        system_prompt = textwrap.dedent("""\
        Generate a short, plain text title for the fantasy football article provided.
        Return only the title — no quotes, no markdown, no explanation.
        """)

        user_prompt = article

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f'Bearer {os.environ["OPENROUTER_API_KEY"]}',
                "Content-Type": "application/json",
            },
            json={
                "transforms": ["middle-out"],
                "model": os.environ["OPENROUTER_MODEL"],
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
        )

        if response.ok:
            response_json = response.json()
            print(response_json)
        else:
            print(response.text)
            return None

        return response_json['choices'][0]['message']['content']
