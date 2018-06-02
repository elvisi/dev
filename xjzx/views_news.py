from flask import Blueprint, render_template, session, jsonify, request
from models import NewsCategory, UserInfo, NewsInfo

new_blueprint = Blueprint('news', __name__)


@new_blueprint.route('/')
def index():
    # 查询分类，用于显示
    category_list = NewsCategory.query.all()

    # 判断用户是否登录
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

     # 获取分类排行前6条数据
    count_list=NewsInfo.query.filter_by(status=2).order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        'news/index.html',
        category_list=category_list,
        user=user,
        count_list=count_list
    )


@new_blueprint.route('/newslist')
def newslist():
    # 接收请求的页码值
    page = int(request.args.get('page', '1'))
    # 查询新闻信息
    pagination = NewsInfo.query.filter_by(status=2)
    # 接收分类的编号
    category_id = int(request.args.get('category_id', '0'))
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)

    # 排序分页
    pagination = pagination.order_by(NewsInfo.update_time.desc()).paginate(page, 4, False)
    # 获取当前页的数据
    news_list = pagination.items
    # 将python语言中的类型转换为json
    news_list2 = []
    for news in news_list:
        news_dict = {
            'id': news.id,
            'pic': news.pic_url,
            'title': news.title,
            'summary': news.summary,
            'user_avatar': news.user.avatar_url,
            'user_nick_name': news.user.nick_name,
            'update_time': news.update_time.strftime('%y-%m-%d'),
            'user_id': news.user.id,
            'category_id': news.category_id

        }
        news_list2.append(news_dict)
    return jsonify(news_list=news_list2)
