from flask import Blueprint, jsonify, request
from app.models.articles import Articles

articles = Blueprint('articles', __name__)

@articles.route('/articles/<int:article_id>', methods=['GET', 'OPTIONS'])
def get_article(article_id):
    article = Articles.query.get(article_id)

    return jsonify(success=True, article=article.serialize())


@articles.route('/articles/get_latest_articles', methods=['GET', 'OPTIONS'])
def get_latest_articles():
    articles = Articles.query.filter(Articles.published == True).order_by(Articles.creation_date.desc()).limit(5).all()
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])


@articles.route('/articles/generate_rumor', methods=['POST', 'OPTIONS'])
def generate_rumor():
    rumor = request.get_json()['rumor']
    team_ids = request.get_json()['team_ids']

    article = Articles.generate_rumor(rumor, team_ids)

    return jsonify(success=True, article=article.serialize())


@articles.route('/articles/generate_power_ranking', methods=['GET', 'OPTIONS'])
def generate_power_ranking():
    article = Articles.generate_power_rankings()

    return jsonify(success=True, article=article.serialize())


@articles.route('/articles/get_news', methods=['GET', 'OPTIONS'])
def get_news():
    articles = Articles.query.filter(Articles.published == True).order_by(Articles.creation_date.desc()).all()
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])