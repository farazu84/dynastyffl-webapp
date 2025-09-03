import requests
import json 
import os

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
                'starters': json.dumps([player.serialize() for player in team.starters]),
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        system_prompt = f"""
        You are generating a matchup preview article for a fantasy football league. This is a PPR league.
        It is week {matchup.week} of the {matchup.year} season.
        I will pass you a serialized json object of the two teams playing each other.
        Use the starters to generate the matchup preview. You may also consider any injuries to the player.
        Consider the positional advantages.
        Here is the scoring rules for the league:
        - 1 point for each reception
        - .04 points for each throwing yard
        - .1 points for each recieving yard
        - .1 points for each rushing yard
        - 6 points for each passing touchdown
        - 6 points for each rushing touchdown
        - 4 points for a throwing touchdown
        - -4 point for each interception
        - -2 point for each fumble lost
        Do not write the league scoring rules in the article.
        Please return the matchup preview using markdown formatting. Only use markdown formatting and be creative.
        But make sure it still looks like an article.
        """

        user_prompt = f"""
        Here are the teams involved in this weeks matchup
        {json.dumps(team_dict, indent=4)}
        """

        print(system_prompt)
        print('--------------------------------')
        print(user_prompt)

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
                'starters': json.dumps([player.serialize() for player in team.starters]),
                'bench': json.dumps([player.serialize() for player in team.players if not player.starter]),
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        system_prompt = f"""
        You are spreading rumors about a fantasy football league. This is a PPR league.
        Please return the article using markdown formatting. Use proper markdown syntax
        I will pass you a serialized json object of the teams involved in the rumor.
        Use the players on the team and the rumor to consider why the rumor would make sense for the team involved in this rumor.
        Here is the scoring rules for the league:
        - 1 point for each reception
        - .04 points for each throwing yard
        - .1 points for each recieving yard
        - .1 points for each rushing yard
        - 6 points for each passing touchdown
        - 6 points for each rushing touchdown
        - 4 points for a throwing touchdown
        - -4 point for each interception
        - -2 point for each fumble lost
        Do not write the league scoring rules in the article.
        Do not propose any trade unless it is explicitly mentioned in the rumor.
        Please return the rumor using markdown formatting. Only use markdown formatting and be creative.
        But make sure it still looks like an article.
        Here are the teams involved:
        {json.dumps(team_dict, indent=4)}
        """

        user_prompt = rumor

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
                'starters': json.dumps([player.serialize() for player in team.starters]),
                'owner_names': [f"{owner.first_name} {owner.last_name}" for owner in team.owners]
            }
            team_dict[team.team_name] = team_info

        from app.league_state_manager import get_current_year, get_current_week
        
        # Get current state from global manager (no DB query!)
        current_year = get_current_year()
        current_week = get_current_week()
        
        article_title = f'{current_year} Week {current_week} Power Rankings'

        system_prompt = f"""
        You are generating power rankings for a fantasy football league. This is a PPR league.
        It is week {current_week} of the {current_year} season.
        I will pass you a serialized json object of all the teams in the league.
        Use the starters and bench players to generate the power rankings.
        The starters should be given a much higher weight than the bench players.
        The power rankings should be in order of the teams from 1 to 10.
        Give your reasoning for why you ranked the teams the way you did.
        Here is the scoring rules for the league:
        - 1 point for each reception
        - .04 points for each throwing yard
        - .1 points for each recieving yard
        - .1 points for each rushing yard
        - 6 points for each passing touchdown
        - 6 points for each rushing touchdown
        - 4 points for a throwing touchdown
        - -4 point for each interception
        - -2 point for each fumble lost
        Do not write the league scoring rules in the article.
        Please return the power rankings using markdown formatting. Only use markdown formatting and be creative.
        But make sure it still looks like an article.
        Break the teams up, please use multiple line and dividers to make the article more readable.
        """

        user_prompt = f"""
        Here are the teams, please generate me a power rankings article.
        {json.dumps(team_dict, indent=4)}
        """
        print(user_prompt)
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

        system_prompt = f"""
        You are generating a title for an article.
        I will pass you the content of the article that is in Markdown form.
        Generate a plain text title for the article.
        """

        user_prompt = f"""
        Here is the content of the article:
        {article}
        """

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
