from __future__ import absolute_import, unicode_literals
from celery import shared_task  # celery装饰器
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_register_active_email(to_email, username, token):
    """
    发送激活邮件
    :param to_email: 需要发送的邮箱地址
    :param username: 用户名
    :param token: 加密的地址签名
    """
    # 发送的邮件内容
    subject = '注册激活'
    message = ''  # 必选参数, 如果没有纯文本可留空
    from_email = settings.EMAIL_FROM
    recipient_list = [to_email]
    html_msg = '<h1>{}欢迎您成为本站的新会员</h1><p>您的激活地址为:</p><a href="http://127.0.0.1:8000/{}" target="_blank">http://127.0.0.1:8000/{}</a>'.format(
        username, token, token)
    # 发送邮件
    send_mail(subject, message, from_email,
              recipient_list, html_message=html_msg)
