import requests
import json 
import os

from .. import db
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func
from app.models.schemas.articles import ArticlesJSONSchema
from app.models.article_teams import ArticleTeams
from app.models.teams import Teams

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

        team1 = matchup.team
        team2 = matchup.opponent_team

        team1_starters = team1.starters
        team2_starters = team2.starters

        team1_name = team1.team_name
        team2_name = team2.team_name

        team1_starters_str = ", ".join([f"{player.position}: {player.first_name} {player.last_name} ({player.nfl_team})" for player in team1_starters])
        team2_starters_str = ", ".join([f"{player.position}: {player.first_name} {player.last_name} ({player.nfl_team})" for player in team2_starters])

        team1_owner = ", ".join([f"{owner.first_name} {owner.last_name}" for owner in team1.owners])
        team2_owner = ", ".join([f"{owner.first_name} {owner.last_name}" for owner in team2.owners])

        system_prompt = f"""
        You are creating a pregame matchup article for a fantasy football league.
        In a fantasy football league, the owner is the also the General Manager of the team.
        This is a PPR league, you will recieve starter from each team. This is for week {matchup.week} of the {matchup.year} season.
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
        Maybe talk about teams player positional advantages if they exist at certain positions.
        Please return the article using markdown formatting, do not use any html, MARKDOWN ONLY. Make sure things are formatted in a nice way to read as an article.
        """

        user_prompt = f"""
        Here are the teams involved in this weeks matchup
        Team 1:
            Name: {team1_name}
            Owner: {team1_owner}
            Starters: {team1_starters_str}
        Team 2:
            Name: {team2_name}
            Owner: {team2_owner}
            Starters: {team2_starters_str}
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
            title=f'{team1_name} vs {team2_name} - Week {matchup.week}',
            content=response_json['choices'][0]['message']['content'],
            thumbnail='',
        )

        db.session.add(article)
        db.session.flush()

        article_team1 = ArticleTeams(
            article_id=article.article_id,
            team_id=team1.team_id,
        )

        article_team2 = ArticleTeams(
            article_id=article.article_id,
            team_id=team2.team_id,
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
            team_starters_str = ", ".join([f"{player.position}: {player.first_name} {player.last_name} ({player.nfl_team})" for player in team.starters])
            team_bench_str = ", ".join([f"{player.position}: {player.first_name} {player.last_name} ({player.nfl_team})" for player in team.players if not player.starter])

            team_dict[team.team_name] = {
                'starters': team_starters_str,
                'bench': team_bench_str
            }

        system_prompt = f"""
        You are spreading rumors about a fantasy football league. This is a PPR league.
        Please return the article using markdown formatting. Use proper markdown syntax
        I will pass you a stringified json object, where the key is the team name
        and the value is an object of starters and bench players, the players are
        in the format of position: first_name last_name (nfl_team).
        The year is 2025, make sure all information that you use is up to date.
        Use this information to determine possibly why the rumor would make sense
        for each team involved.
        Consider the age of the player involved, and possibly there stats from last year.
        Search the internet for any recent information about the player and include it if it is relevant.
        For the players mentioned in the rumor make sure to reference stringified json object I will pass is in
        so that you don't hallucinate about the player position or nfl_team.
        Give this article a title at the start of the article and have it surrounded by /* <TITLE> */ so I can parse it out.
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
            article_type='rumors',
            author=os.environ["OPENROUTER_MODEL"],
            title='Rumor: ' + rumor,
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