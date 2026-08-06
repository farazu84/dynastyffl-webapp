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


@articles.route('/articles/generate_rumor', methods=['POST'])
def generate_rumor():
    data = request.get_json() or {}
    rumor = data.get('rumor')
    team_ids = data.get('team_ids')

    if not rumor or not team_ids:
        return jsonify(success=False, error='rumor and team_ids are required'), 400

    article = Articles.generate_rumor(rumor, team_ids)

    if not article:
        return jsonify(success=False, error='Failed to generate rumor. Check server logs for details.'), 500

    return jsonify(success=True, article=article.serialize())


@articles.route('/articles/get_news', methods=['GET', 'OPTIONS'])
def get_news():
    articles = Articles.query.filter(Articles.published == True).order_by(Articles.creation_date.desc()).all()
    return jsonify(success=True, articles=[ article.serialize() for article in articles ])