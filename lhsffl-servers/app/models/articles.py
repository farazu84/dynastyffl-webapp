import requests
import json 
import os

from .. import db
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.sql import func
from app.models.schemas.articles import ArticlesJSONSchema


class Articles(db.Model):
    __tablename__ = 'Articles'

    article_id = db.Column(db.Integer(), nullable=False, primary_key=True)

    article_type = db.Column(db.Enum('power_ranking', 'team_analysis', 'rumors', 'trade_analysis', 'injury', 'matchup_analysis', 'matchup_breakdown'), nullable=True)

    author = db.Column(db.String(64), nullable=True)

    title = db.Column(db.TEXT, nullable=False)

    content = db.Column(db.TEXT, nullable=False)

    thumbnail = db.Column(db.String(64), nullable=False)

    team_id = db.Column(db.Integer(), nullable=True)

    creation_date = db.Column(DATETIME, nullable=False, default=func.now())

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

        team1_starters_str = ", ".join([f"{player.first_name} {player.last_name} ({player.nfl_team})" for player in team1_starters])
        team2_starters_str = ", ".join([f"{player.first_name} {player.last_name} ({player.nfl_team})" for player in team2_starters])

        system_prompt = f"""
        You are creating a pregame matchup article for a fantasy football league.
        This is a PPR league, you will recieve starter from each team. This is for week {matchup.week} of the {matchup.year} season.
        Use previous seasons Fantasy and Real NFL data to reason about the matchups.
        Also consider how players could be coming off of injuries, and that they could be on a new team this year.
        Maybe talk about teams player positional advantages if they exist at certain positions.
        Please return the article using markdown formatting. Use proper markdown syntax:
        - Use ## for main sections and ### for subsections
        - Use **bold** for emphasis and *italics* for highlights
        - Only use bullet points (- ) when creating actual lists, not for regular sentences
        - Write regular paragraphs as normal text without leading dashes
        - You can be creative, but don't use leading dashes.
        """

        user_prompt = f"""
        Team 1: {team1_name}
        Starters: {team1_starters_str}
        Team 2: {team2_name}
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
                    "model": "openai/gpt-oss-20b:free",
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
            author='openai/gpt-oss-20b',
            title=f'{team1_name} vs {team2_name} - Week {matchup.week}',
            content=response_json['choices'][0]['message']['content'],
            thumbnail='',
        )

        db.session.add(article)
        db.session.commit()

        return article