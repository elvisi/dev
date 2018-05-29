from flask import Blueprint,render_template

new_blueprint = Blueprint('news', __name__)


@new_blueprint.route('/')
def index():
    return render_template(
        'news/index.html',
    )