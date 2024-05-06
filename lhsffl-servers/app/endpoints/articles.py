from flask import Blueprint, jsonify
from app.models.articles import Articles

articles = Blueprint('articles', __name__)

@articles.route('/articles/<int:article_id>', methods=['GET', 'OPTIONS'])
def get_article(article_id):
    article = Articles.query.get(article_id)

    return jsonify(success=True, article=article.serialize())
