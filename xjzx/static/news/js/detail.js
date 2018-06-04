function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    vue_list_con = new Vue({
        el:'.comment_list_con',
        delimiters:['[[',']]'],
        data:{
            comment_list:[]
        }
    });
    get_comment_list();

    // 收藏
    $(".collection").click(function () {
        $.post('/collect', {
            'news_id': $('#news_id').val(),
            'csrf_token': $('#csrf_token').val()
        }, function (data) {
            if (data.result == 1) {
                // 显示登录窗口
                $('.login_btn').click();
            } else if (data.result == 5) {
                // 隐藏'收藏按钮',显示已收藏按钮
                $('.collection').hide();
                $('.collected').show();
            }
        });

    });

    // 取消收藏
    $(".collected").click(function () {
        $.post('/collect', {
            'news_id': $('#news_id').val(),
            'csrf_token': $('#csrf_token').val(),
            'action': 2
        }, function (data) {
            if (data.result == 5) {
                // 显示收藏按钮',隐藏已收藏按钮
                $('.collection').show();
                $('.collected').hide();
            }
        });


    });

    // 评论提交
    $(".comment_form").submit(function (e) {
        e.preventDefault();
        var msg=$('#msg').val();
        if (msg.length<=0){
            alert('评论内容不能为空')
            return;
        }
        $.post('/comment/add',{
            'news_id':$('#news_id').val(),
            'msg':msg,
            'csrf_token':$('#csrf_token').val()
        },function (data) {
            if(data.result==1){
                // 评论成功
                $('#msg').val('');
                get_comment_list();
                // 更新页面中的评论数量
                $('.comment').text(data.comment_count);
                $('.comment_count>span').text(data.comment_count);
            }
        });
    });

    $('.comment_list_con').delegate('a,input', 'click', function () {

        var sHandler = $(this).prop('class');

        if (sHandler.indexOf('comment_reply') >= 0) {
            $(this).next().toggle();
        }

        if (sHandler.indexOf('reply_cancel') >= 0) {
            $(this).parent().toggle();
        }

        if (sHandler.indexOf('comment_up') >= 0) {
            var $this = $(this);
            if (sHandler.indexOf('has_comment_up') >= 0) {
                // 如果当前该评论已经是点赞状态，再次点击会进行到此代码块内，代表要取消点赞
                $this.removeClass('has_comment_up')
            } else {
                $this.addClass('has_comment_up')
            }
        }

        if (sHandler.indexOf('reply_sub') >= 0) {
            alert('回复评论')
        }
    })

    // 关注当前新闻作者
    $(".focus").click(function () {

    })

    // 取消关注当前新闻作者
    $(".focused").click(function () {

    })
});

function get_comment_list() {
    $.get('/comment/list/'+$('#news_id').val(),function (data) {
        vue_list_con.comment_list=data.comment_list;
    });
}