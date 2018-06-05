from flask import Blueprint, jsonify
from flask import current_app
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from datetime import datetime
from utills.qiniu_xjzx import upload_pic
from models import UserInfo, NewsInfo, db, NewsCategory

admin_blueprint = Blueprint('admin', __name__, url_prefix='/admin')


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('admin/login.html')
    elif request.method == 'POST':
        # 接收
        dict1 = request.form
        mobile = dict1.get('username')
        pwd = dict1.get('password')
        # 验证
        if not all([mobile, pwd]):
            return render_template(
                'admin/login.html',
                msg='请填写用户名、密码'
            )
        # 处理
        user = UserInfo.query.filter_by(isAdmin=True, mobile=mobile).first()
        if user is None:
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='用户名错误'
            )
        if not user.check_pwd(pwd):
            return render_template(
                'admin/login.html',
                mobile=mobile,
                pwd=pwd,
                msg='密码错误'
            )
        # 登录成功后，进行状态保持
        session['admin_user_id'] = user.id
        # 响应
        return redirect('/admin/')


@admin_blueprint.route('/logout')
def logout():
    del session['admin_user_id']
    return redirect('/admin/login')


@admin_blueprint.route('/')
def index():
    return render_template('admin/index.html')


# 使用app注册勾子表示：项目中的所有视图都会执行这个勾子函数
# 使用蓝图注册勾子表示：只有这个蓝图中的视图会执行这个勾子函数
@admin_blueprint.before_request
def login_validate():
    # 当大部分视图需要执行一段代码时，可以写到请求勾子中
    # 对于不执行这段代码的视图，可以进行排除
    except_path_list = ['/admin/login']
    if request.path not in except_path_list:
        if 'admin_user_id' not in session:
            return redirect('/admin/login')
        g.user = UserInfo.query.get(session['admin_user_id'])


@admin_blueprint.route('/user_count')
def user_count():
    # 用户总数
    user_total = UserInfo.query.filter_by(isAdmin=False).count()
    # 获取当前月份
    now = datetime.now()
    now_month = datetime(now.year, now.month, 1)
    # 用户月新增数
    user_month = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time >= now_month).count()
    # 用户日新增数
    now_day = datetime(now.year, now.month, now.day)
    user_day = UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time >= now_day).count()

    # 获取分时登录数据
    now = datetime.now()
    login_key = 'login%d_%d_%d' % (now.year, now.month, now.day)
    time_list = current_app.redis_client.hkeys(login_key)
    # 将bytes==>str
    time_list = [time.decode() for time in time_list]
    # 获取时间段对应的数量
    count_list = current_app.redis_client.hvals(login_key)
    # 将bytes==>int
    count_list = [int(count) for count in count_list]

    return render_template(
        'admin/user_count.html',
        user_total=user_total,
        user_month=user_month,
        user_day=user_day,
        time_list=time_list,
        count_list=count_list
    )


@admin_blueprint.route('/user_list')
def user_list():
    return render_template('admin/user_list.html')


@admin_blueprint.route('/user_list_json')
def user_list_json():
    page = int(request.args.get('page', '1'))
    pagination = UserInfo.query.filter_by(isAdmin=False).order_by(UserInfo.id.desc()).paginate(page, 9, False)
    user_list1 = pagination.items
    total_page = pagination.pages
    user_list2 = []
    for user in user_list1:
        user_dict = {
            'nick_name': user.nick_name,
            'mobile': user.mobile,
            'create_time': user.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': user.update_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        user_list2.append(user_dict)

    return jsonify(user_list=user_list2, total_page=total_page)


@admin_blueprint.route('/news_review')
def news_review():
    return render_template('admin/news_review.html')


@admin_blueprint.route('/news_review_json')
def news_review_json():
    page = int(request.args.get('page', '1'))
    input_txt = request.args.get('input_txt')
    # .filter_by(status=1)
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()). \
        paginate(page, 10, False)
    news_list1 = pagination.items
    total_page = pagination.pages
    news_list2 = []
    for news in news_list1:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'create_time': news.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        news_list2.append(news_dict)

    return jsonify(news_list=news_list2, total_page=total_page)


@admin_blueprint.route('/news_review_detail/<int:news_id>', methods=['GET', 'POST'])
def news_review_detail(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == 'GET':
        return render_template('admin/news_review_detail.html', news=news)
    elif request.method == 'POST':
        # 接收
        action = request.form.get('action')
        if action == 'accept':
            news.status = 2
        elif action == 'reject':
            news.status = 3
            news.reason = request.form.get('reason')
        # 提交
        db.session.commit()
        # 响应
        return redirect('/admin/news_review')


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template('admin/news_edit.html')


@admin_blueprint.route('/news_edit_json')
def news_edit_json():
    page = int(request.args.get('page', '1'))
    input_txt = request.args.get('input_txt')
    # .filter_by(status=2)
    pagination = NewsInfo.query
    if input_txt:
        pagination = pagination.filter(NewsInfo.title.contains(input_txt))
    pagination = pagination.order_by(NewsInfo.id.desc()).paginate(page, 10, False)
    news_list1 = pagination.items
    total_page = pagination.pages
    news_list2 = []
    for news in news_list1:
        news_dict = {
            'id': news.id,
            'title': news.title,
            'create_time': news.create_time.strftime('%Y-%m-%d %H:%M:%S'),
        }
        news_list2.append(news_dict)

    return jsonify(news_list=news_list2, total_page=total_page)


@admin_blueprint.route('/news_edit_detail/<int:news_id>', methods=['GET', 'POST'])
def news_edit_detail(news_id):
    news = NewsInfo.query.get(news_id)
    if request.method == 'GET':
        category_list = NewsCategory.query.all()
        return render_template(
            'admin/news_edit_detail.html',
            news=news,
            category_list=category_list
        )
    elif request.method == 'POST':
        # 接收
        dict1 = request.form
        title = dict1.get('title')
        category_id = dict1.get('category_id')
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 接收文件
        pic = request.files.get('pic')
        if pic:
            pic_name = upload_pic(pic)
            news.pic = pic_name
        # 修改
        news.title = title
        news.category_id = int(category_id)
        news.summary = summary
        news.content = content
        # 提交
        db.session.commit()
        # 响应
        return redirect('/admin/news_edit')


@admin_blueprint.route('/news_type')
def news_type():
    return render_template('admin/news_type.html')


@admin_blueprint.route('/news_type_list')
def news_type_list():
    category_list1 = NewsCategory.query.all()
    category_list2 = []
    for category in category_list1:
        category_dict = {
            'id': category.id,
            'name': category.name
        }
        category_list2.append(category_dict)
    return jsonify(category_list=category_list2)


@admin_blueprint.route('/news_type_add', methods=['POST'])
def news_type_add():
    name = request.form.get('name')
    # 验证
    name_exists = NewsCategory.query.filter_by(name=name).count()
    if name_exists > 0:
        return jsonify(result=1)
    # 添加
    category = NewsCategory()
    category.name = name
    db.session.add(category)
    db.session.commit()
    # 响应
    return jsonify(result=2)


@admin_blueprint.route('/news_type_edit', methods=['POST'])
def news_type_edit():
    cid = request.form.get('cid')
    name = request.form.get('name')
    # 判断是否存在
    name_exists = NewsCategory.query.filter_by(name=name).count()
    if name_exists > 0:
        return jsonify(result=1)
    # 修改
    category = NewsCategory.query.get(cid)
    category.name = name
    db.session.commit()
    # 响应
    return jsonify(result=2)
