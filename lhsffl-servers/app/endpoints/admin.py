from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from app.decorators import admin_required
from app.models.articles import Articles
from app.models.users import Users
from app import db

admin = Blueprint('admin', __name__)


@admin.route('/admin/articles/unpublished', methods=['GET'])
@admin_required
def get_unpublished_articles():
    articles = (Articles.query
                .filter_by(published=False)
                .order_by(Articles.creation_date.desc())
                .all())
    return jsonify(success=True, articles=[a.serialize() for a in articles])


@admin.route('/admin/articles/<int:article_id>/publish', methods=['POST'])
@admin_required
def publish_article(article_id):
    article = db.session.get(Articles, article_id)

    if not article:
        return jsonify(success=False, error='Article not found'), 404

    if article.published:
        return jsonify(success=False, error='Article is already published'), 400

    article.published = True
    db.session.commit()

    return jsonify(success=True, article=article.serialize())


@admin.route('/admin/impersonate/<int:user_id>', methods=['POST'])
@admin_required
def impersonate(user_id):
    target = db.session.get(Users, user_id)

    if not target:
        return jsonify(success=False, error='User not found'), 404

    if not target.team_owner:
        return jsonify(success=False, error='User is not a team owner'), 400

    claims = {
        'admin': target.admin,
        'team_owner': target.team_owner,
        'impersonated_by': int(get_jwt_identity()),
    }
    token = create_access_token(identity=str(target.user_id), additional_claims=claims)

    return jsonify(success=True, access_token=token, user=target.serialize())
