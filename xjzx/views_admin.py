import time
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, session, g, current_app
from models import UserInfo

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
        # 登录成功后进行状态保存
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


# 使用app注册的钩子，整个项目所有的视图都会执行
# 使用蓝图注册的钩子，只会被这个蓝图中的视图所使用
@admin_blueprint.before_request
def login_validate():
    # 当大部分视图需要执行一段代码时，可以写到请求钩子里面
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
    user_month=UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time>=now_month).count()
    # 用户日新增数
    now_day=datetime(now.year,now.month,now.day)
    user_day=UserInfo.query.filter_by(isAdmin=False).filter(UserInfo.create_time>=now_day).count()

    # 获取分时登录数据
    now = datetime.now()
    login_key='login%d_%d_%d' %(now.year,now.month,now.day)
    time_list=current_app.redis_client.hkeys(login_key)
    # redis里面获取的都是bytes类型，下面将bytes转成str
    time_list=[time.decode() for time in time_list]
    # 获取时间段对应的数量
    count_list=current_app.redis_client.hvals(login_key)
    # redis里面获取的都是bytes类型，下面将bytes转成int
    count_list=[int(count) for count in count_list]

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


@admin_blueprint.route('/news_review')
def news_review():
    return render_template('admin/news_review.html')


@admin_blueprint.route('/news_edit')
def news_edit():
    return render_template('admin/news_edit.html')


@admin_blueprint.route('/news_type')
def news_type():
    return render_template('admin/news_type.html')
