from flask import Blueprint, make_response, request, session, jsonify, current_app, render_template, redirect
from models import db, UserInfo

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
        # 查询（展示时也需要查询，所以将代码在上面写一遍）
        # 为属性赋值
        user.signature = signature
        user.nick_name = nick_name
        user.gender = bool(gender)

        # 提交数据库
        db.session.commit()

        # 返回响应
        return jsonify(result=1)


@user_blueprint.route('/pic',methods=['GET','POST'])
@login_required
def pic():
    user_id=session['user_id']
    user=UserInfo.query.get(user_id)

    if request.method=='GET':
        return render_template('news/user_pic_info.html',user=user)
    elif request.method=='POST':
        # 接收文件
        avatar=request.files.get('avatar')
        # 上传到七牛云，并返回文件名
        from utills.qiniu_xjzx import upload_pic
        filename=upload_pic(avatar)

        # 修改用户的头像属性
        user.avatar=filename

        # 提交保存到数据库
        db.session.commit()

        # 返回响应
        return jsonify(result=1,avatar=user.avatar_url)

@user_blueprint.route('/follow')
@login_required
def follow():
    return render_template('news/user_follow.html')


@user_blueprint.route('/pwd')
@login_required
def pwd():
    return render_template('news/user_pass_info.html')


@user_blueprint.route('/collect')
@login_required
def collect():
    return render_template('news/user_collection.html')


@user_blueprint.route('/release')
def release():
    return render_template('news/user_news_release.html')


@user_blueprint.route('/news_list')
def news_list():
    return render_template('news/user_news_list.html')
