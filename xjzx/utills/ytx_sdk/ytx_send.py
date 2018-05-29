# 编码说明：coding = utf - 8
# 或gbk
from .CCPRestSDK import REST
# import ConfigParser

# 主帐号
accountSid = '8a216da85f5c89b1015f994144201b06'

# 主帐号Token
accountToken = '6ce3f903e23c418e8ef7e7d03704f591'

# 应用Id
appId = '8a216da85f5c89b1015f994145a21b0d'
# 请使用管理控制台中已创建应用的APPID。

serverIP = 'app.cloopen.com'
# 说明：请求地址，生产环境配置成app.cloopen.com。

serverPort = '8883'
# 说明：请求端口 ，生产环境为8883.

softVersion = '2013-12-26'  # 说明：REST API版本号保持不变。


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例外：{'12'#代表验证码是什么，'34'#代表多长时间过期}
# @param $tempId 模板Id


def sendTemplateSMS(to, datas, tempId):
    # 初始化REST SDK
    rest = REST(serverIP, serverPort, softVersion)
    rest.setAccount(accountSid, accountToken)
    rest.setAppId(appId)

    result = rest.sendTemplateSMS(to, datas, tempId)
    return result.get('statusCode')
