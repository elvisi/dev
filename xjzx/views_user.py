from datetime import datetime

from flask import Blueprint, make_response, request, session, jsonify, current_app, render_template, redirect
from models import db, UserInfo, NewsInfo, NewsCategory

user_blueprint = Blueprint('user', __name__, url_prefix='/user')


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utills.captcha.captcha import captcha
    name, yzm, image = captcha.generate_captcha()
    # yzm表示随机生成的验证码字符串
    # 将数据进行保存，方便后面对比
    session['image_yzm'] = yzm
    # image表示图片的二进制数据
    response = make_response(image)
    # 默认浏览器将数据作为text/html解析
    # 需要告诉浏览器当前数据的类型为image/png
    response.mimetype = 'image/png'
    return response


@user_blueprint.route('/sms_yzm')
def sms_yzm():
    # 接收数据：手机号和图片验证码
    dict1 = request.args
    mobile = dict1.get('mobile')
    yzm = dict1.get('yzm')

    # 对比图片验证码
    if yzm != session['image_yzm']:
        return jsonify(result=1)

    # 随机生成一个四位的验证码
    import random
    yzm2 = random.randint(1000, 9999)

    # 将短信验证码进行保存，用于验证
    session['sms_yzm'] = yzm2

    # 发送短信
    # from utills.ytx_sdk.ytx_send import sendTemplateSMS
    # sendTemplateSMS(mobile, {yzm2, 5}, 1)
    print(yzm2)

    return jsonify(result=2)


@user_blueprint.route('/register', methods=['POST'])
def register():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    yzm_image = dict1.get('yzm_image')
    yzm_sms = dict1.get('yzm_sms')
    pwd = dict1.get('pwd')

    # 验证数据的有效性
    # 保证所有的数据都被填写,列表中只要有一个值为False,则结果为False
    if not all([mobile, yzm_image, yzm_sms, pwd]):
        return jsonify(result=1)
    # 对比图片验证码
    if yzm_image != session['image_yzm']:
        return jsonify(result=2)

    # 对比短信验证码
    if int(yzm_sms) != session['sms_yzm']:
        return jsonify(result=3)

    # 判断密码的长度
    import re
    if not re.match(r'[a-zA-Z0-9_]{6,20}', pwd):
        return jsonify(result=4)

    # 验证mobile是否存在
    mobile_count = UserInfo.query.filter_by(mobile=mobile).count()
    if mobile_count > 0:
        return jsonify(result=5)

    # 创建对象
    user = UserInfo()
    user.nick_name = mobile
    user.mobile = mobile
    user.password = pwd

    # 提交到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except:
        current_app.logger_xjzx.error('用户注册访问数据库失败')
        return jsonify(result=7)

    # 返回响应
    return jsonify(result=6)


@user_blueprint.route('/login', methods=['POST'])
def login():
    # 接收数据
    dict1 = request.form
    mobile = dict1.get('mobile')
    pwd = dict1.get('pwd')

    # 验证有效性
    if not all([mobile, pwd]):
        return jsonify(result=1)

    # 查询判断，响应
    user = UserInfo.query.filter_by(mobile=mobile).first()
    # 判断mobile是否正确
    if user:
        # 密码对比
        if user.check_pwd(pwd):
            # 状态保持
            session['user_id'] = user.id
            # 返回成功的结果,返回用户的头像，返回用户的名字
            return jsonify(result=4, avatar=user.avatar, nic_name=user.nick_name)
        else:
            # 密码错误
            return jsonify(result=3)
    else:
        # 如果查询不到数据返回None,表示mobile错误
        return jsonify(result=2)


@user_blueprint.route('/logout', methods=['POST'])
def logout():
    del session['user_id']
    return jsonify(result=1)


import functools


def login_required(view_fun):
    @functools.wraps(view_fun)  # 保持view_fun的函数名称不变，不会被FUN2的名称代替
    def fun2(*args, **kwargs):
        # 判断当前用户是否登录
        if 'user_id' not in session:
            return redirect('/')
        # 视图执行完，会返回response对象,此处需要将response对象继续return，最终交给浏览器执行
        return view_fun(*args, **kwargs)

    return fun2


@user_blueprint.route('/')
@login_required
def index():
    # 获取当前登录的用户对象
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 将对象传递到模板中，用于显示昵称，头像
    return render_template('news/user.html', user=user)


@user_blueprint.route('/base', methods=['GET', 'POST'])
@login_required
def base():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    if request.method == 'GET':
        return render_template('news/user_base_info.html', user=user)
    elif request.method == 'POST':
        # 接收
        dict1 = request.form
        signature = dict1.get('signature')
        nick_name = dict1.get('nick_name')
        gender = dict1.get('gender')
        if gender == 'True':
            gender = True
        else:
            gender = False
        # 查询（展示时也需要查询，所以将代码在上面写一遍）
        # 为属性赋值
        user.signature = signature
        user.nick_name = nick_name
        user.gender = gender

        # 提交数据库
        db.session.commit()

        # 返回响应
        return jsonify(result=1)


@user_blueprint.route('/pic', methods=['GET', 'POST'])
@login_required
def pic():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)

    if request.method == 'GET':
        return render_template('news/user_pic_info.html', user=user)
    elif request.method == 'POST':
        # 接收文件
        avatar = request.files.get('avatar')
        # 上传到七牛云，并返回文件名
        from utills.qiniu_xjzx import upload_pic
        filename = upload_pic(avatar)

        # 修改用户的头像属性
        user.avatar = filename

        # 提交保存到数据库
        db.session.commit()

        # 返回响应
        return jsonify(result=1, avatar=user.avatar_url)


@user_blueprint.route('/follow')
@login_required
def follow():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)

    # 获取当前页码值
    page = int(request.args.get('page', '1'))

    # 通过关联属性获取关注的用户对象
    # 对查询的数据进行分页
    pagination = user.follow_user.paginate(page, 4, False)
    # 获取当前页的数据
    user_list = pagination.items
    # 获取总页数
    total_page = pagination.pages

    return render_template(
        'news/user_follow.html',
        user_list=user_list,
        total_page=total_page,
        page=page

    )


@user_blueprint.route('/pwd', methods=['GET', 'POST'])
@login_required
def pwd():
    if request.method == 'GET':
        # 展示页面，供用户输入密码
        return render_template('news/user_pass_info.html')
    elif request.method == 'POST':
        # 接收用户输入，进行密码更改
        # 1.接收数据
        dict1 = request.form
        current_pwd = dict1.get('current_pwd')
        new_pwd = dict1.get('new_pwd')
        new_pwd2 = dict1.get('new_pwd2')
        # 2.验证
        # 2.1值不为空
        if not all([current_pwd, new_pwd, new_pwd2]):
            return render_template(
                'news/user_pass_info.html',
                msg='请将信息填写完成'
            )
        # 2.2密码长度
        import re
        if not re.match(r'[a-zA-Z0-9_]{6,20}', current_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='当前密码错误'
            )

        if not re.match(r'[a-zA-Z0-9_]{6,20}', new_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='新密码格式错误'
            )

        # 2.3两个新密码一致
        if new_pwd != new_pwd2:
            return render_template(
                'news/user_pass_info.html',
                msg='两次密码输入不一致'
            )
        # 2.4查询对象，当前密码正确
        user = UserInfo.query.get(session['user_id'])
        if not user.check_pwd(current_pwd):
            return render_template(
                'news/user_pass_info.html',
                msg='当前密码错误'
            )

        # 查询对象，修改属性
        user.password = new_pwd
        # 提交
        db.session.commit()
        # 响应
        return render_template(
            'news/user_pass_info.html',
            msg='密码修改成功'
        )


@user_blueprint.route('/collect')
@login_required
def collect():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 获取当前的页码值
    page = int(request.args.get('page', '1'))
    # 当前用户收藏的新闻列表
    pagination = user.news_collect.order_by(NewsInfo.update_time.desc()).paginate(page, 6, False)
    # 获取当前页的数据
    news_list = pagination.items
    # 获取总页码值
    total_page = pagination.pages

    return render_template(
        'news/user_collection.html',
        news_list=news_list,
        total_page=total_page,
        page=page
    )


@user_blueprint.route('/release', methods=['GET', 'POST'])
@login_required
def release():
    # 查询所有分类
    category_list = NewsCategory.query.all()
    if request.method == 'GET':

        return render_template(
            'news/user_news_release.html',
            category_list=category_list
        )
    elif request.method == 'POST':
        # 接收用户填写的数据，创建新闻对象，保存到数据库中
        # 1.接收用户输入的数据
        dict1 = request.form
        title = dict1.get('title')
        category_id = int(dict1.get('category'))
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 1.2接收文件
        news_pic = request.files.get('news_pic')

        # 2.验证
        # 2.1数据不为空
        if not all([title, category_id, summary, content, news_pic]):
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                msg='数据不能为空'
            )

        # 将文件上传到七牛云，并返回文件名
        from utills.qiniu_xjzx import upload_pic
        filename = upload_pic(news_pic)

        # 3.创建对象并赋值
        news = NewsInfo()
        news.category_id = category_id
        news.pic = filename
        news.title = title
        news.summary = summary
        news.content = content
        news.user_id = session['user_id']

        # 4.提交数据到数据库
        db.session.add(news)
        db.session.commit()
        # 4.响应：转到列表页面
        return redirect("/user/news_list")


@user_blueprint.route('/news_list')
@login_required
def news_list():
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    # 接收page
    page = int(request.args.get("page", "1"))
    # 使用关联属性访问发布的对象
    pagination = user.news.order_by(NewsInfo.update_time.desc()).paginate(page, 6, False)
    # 获取当前页的数据
    news_list = pagination.items
    # 总页码
    total_page = pagination.pages

    return render_template(
        'news/user_news_list.html',
        news_list=news_list,
        page=page,
        total_page=total_page

    )


@user_blueprint.route('/release_update/<int:news_id>', methods=['GET', 'POST'])
@login_required
def release_update(news_id):
    news = NewsInfo.query.get(news_id)
    category_list = NewsCategory.query.all()
    if request.method == 'GET':
        return render_template(
            'news/user_news_update.html',
            news=news,
            category_list=category_list
        )
    elif request.method == 'POST':
        # 接收用户填写的数据，修改新闻对象，保存到数据库中
        # 1.接收用户输入的数据
        dict1 = request.form
        title = dict1.get('title')
        category_id = int(dict1.get('category'))
        summary = dict1.get('summary')
        content = dict1.get('content')
        # 1.2接收文件
        news_pic = request.files.get('news_pic')

        # 2.验证
        # 2.1数据不为空，不需要验证图片，因为用户可以不用修改图片，则不上传文件
        if not all([title, category_id, summary, content]):
            return render_template(
                'news/user_news_release.html',
                category_list=category_list,
                msg='数据不能为空'
            )

        # 将文件上传到七牛云，并返回文件名
        if news_pic:
            from utills.qiniu_xjzx import upload_pic
            filename = upload_pic(news_pic)

        # 3.将查询到的对象属性赋值
        news.category_id = category_id
        if news_pic:
            news.pic = filename
        news.title = title
        news.summary = summary
        news.content = content
        news.user_id = session['user_id']
        # 修改时，更新为最新的时间
        news.update_time = datetime.now()
        # 修改时，将状态设置成'待审核'
        news.status = 1

        # 4.提交数据到数据库
        db.session.commit()
        # 4.响应：转到列表页面
        return redirect("/user/news_list")
