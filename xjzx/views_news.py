from flask import Blueprint, render_template, session, jsonify, request, abort, current_app
from models import NewsCategory, UserInfo, NewsInfo, db, NewsComment

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
    count_list = NewsInfo.query.filter_by(status=2).order_by(NewsInfo.click_count.desc())[0:6]

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


@new_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    # 判断是否存在这个新闻对象，如果不存在则抛出404
    if news is None:
        abort(404)

    # 查询当前登录的用户，用于在模板中显示登录状态
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

    # 将点击量增加
    news.click_count += 1
    db.session.commit()

    # 点击排行前六条数据
    count_list = NewsInfo.query.filter_by(status=2).order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        'news/detail.html',
        news=news,
        title='文章详情页',
        user=user,
        count_list=count_list
    )


@new_blueprint.route('/collect', methods=['POST'])
def collect():
    # 数据的添加操作：让用户user收藏新闻news
    # 接收处理的标记，是收藏还是取消收藏,1表示收藏，非1表示取消收藏
    action = request.form.get('action', '1')

    # 获取新闻编号
    news_id = request.form.get('news_id')
    if not all([news_id]):
        return jsonify(result=2)
    # 根据编号查询新闻对象
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=3)
    # 判断用户是否登录。如果未登录则提示登录
    if 'user_id' not in session:
        return jsonify(result=1)
    # 当前登录的用户
    user = UserInfo.query.get(session['user_id'])
    if action == '1':
        # 如果当前新闻已经被收藏，则直接返回
        if news in user.news_collect:
            return jsonify(result=4)
        # 进行收藏添加操作
        user.news_collect.append(news)
        # 取消收藏
    else:
        if news not in user.news_collect:
            return jsonify(result=4)

        user.news_collect.remove(news)
    # 提交到数据库
    db.session.commit()

    return jsonify(result=5)


@new_blueprint.route('/comment/add', methods=['POST'])
def commentadd():
    # 添加评论数据

    # 接收数据,news_id,msg,关于user_id是从session中获取的，所以不需要传递
    dict1 = request.form
    news_id = dict1.get('news_id')
    msg = dict1.get('msg')

    # 验证
    if not all([news_id, msg]):
        return jsonify(result=2)
    # 判断news_id是一个合法值
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=3)
    # 获取用户编号
    if 'user_id' not in session:
        return jsonify(result=4)
    user_id = session['user_id']

    # 创建对象，并为属性赋值
    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = user_id
    comment.msg = msg
    # 将新闻对象的评论量+1
    news.comment_count += 1

    # 提交数据
    db.session.add(comment)
    db.session.commit()

    # 响应
    return jsonify(result=1, comment_count=news.comment_count)


@new_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    # 根据news_id查询评论数据
    # comment_id = None表示这是一个评论不是一个回复
    comment_list = NewsComment.query. \
        filter_by(news_id=news_id, comment_id=None). \
        order_by(NewsComment.id.desc())
    # 将comment对象构造成json数据
    comment_list2 = []

    # 查询用户对哪些评论点过赞
    if 'user_id' in session:
        user_id = session['user_id']
        commentid_list = current_app.redis_client.lrange('comment%d' % user_id, 0, -1)
        commentid_list = [int(cid) for cid in commentid_list]
    else:
        commentid_list = []

    for comment in comment_list:
        # 判断当前用户是否为此点赞
        is_like = 0
        if comment.id in commentid_list:
            is_like = 1

        comment_dict = {
            'avatar': comment.user.avatar_url,
            'nick_name': comment.user.nick_name,
            'msg': comment.msg,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'like_count': comment.like_count,
            'id': comment.id,
            'is_like': is_like
        }
        # 已知评论对象comment，获取回复对象
        cback_list = []
        cback_list2 = comment.comments.order_by(NewsComment.id.desc())
        for cback in cback_list2:
            cback_dict = {
                'nick_name': cback.user.nick_name,
                'msg': cback.msg
            }
            cback_list.append(cback_dict)
        comment_dict['cback_list'] = cback_list

        comment_list2.append(comment_dict)
    return jsonify(comment_list=comment_list2)


@new_blueprint.route('/comment/up/<int:comment_id>', methods=['POST'])
def commentup(comment_id):
    # 点赞需要user_id,comment_id

    # 进行处理的标记，1表示点赞，2表示取消点赞
    action = int(request.form.get('action', '1'))
    # 获取用户编号

    if 'user_id' not in session:
        return jsonify(result=1)
    user_id = session['user_id']
    # #读取Redis的配置
    # host=current_app.config.get('REDIS_HOST')
    # port = current_app.config.get('REDIS_PORT')
    # redis_db = current_app.config.get('REDIS_DB')
    # import redis
    # redis_client=redis.StrictRedis(host=host,port=port,db=redis_db)
    # 将数据写入到Redis中

    comment = NewsComment.query.get(comment_id)
    # 点赞
    if action == 1:
        current_app.redis_client.rpush('comment%d' % user_id, comment_id)
        # 将评论的点赞数据+1
        comment.like_count += 1
    # 取消点赞
    else:
        current_app.redis_client.lrem('comment%d' % user_id, 0, comment_id)
        comment.like_count -= 1
    db.session.commit()

    return jsonify(result=2, like_count=comment.like_count)


@new_blueprint.route('/comment/back', methods=['POST'])
def commentback():
    # 评论回复：用户user_id 对comment_id进行回复，回复内容为msg
    # 创建一条新的评论对象：new_id,user_id,comment_id,msg
    # 接收
    new_id = request.form.get('news_id')
    msg = request.form.get('msg')
    comment_id = request.form.get('comment_id')
    # 验证
    if not all([new_id, msg, comment_id]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 处理
    # 创建对象
    comment = NewsComment()
    comment.news_id = int(new_id)
    comment.user_id = user_id
    comment.comment_id = comment_id
    comment.msg = msg
    # 提交到数据库
    db.session.add(comment)
    db.session.commit()
    # 响应
    return jsonify(result=3)


@new_blueprint.route('/follow', methods=['POST'])
def follow():
    # 关注：用户user_id关注用户follow_user_id
    action = request.form.get('action', '1')
    follow_user_id = request.form.get('follow_user_id')
    if not all([follow_user_id, action]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    # 查询用户对象
    user = UserInfo.query.get(user_id)
    follow_user = UserInfo.query.get(follow_user_id)
    # 判断是否关注
    if action == '1':
        # 关注
        user.follow_user.append(follow_user)
        follow_user.follow_count += 1
        # 取消关注
    else:
        user.follow_user.remove(follow_user)
        follow_user.follow_count -= 1
    db.session.commit()
    return jsonify(result=3, follow_count=follow_user.follow_count)
