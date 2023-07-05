import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.utils import formataddr
import datetime



def send_email():
    # 发送方邮箱账号和密码（需要开启SMTP服务和POP3/IMAP服务）
    sender_email = "suxiuzhen@matrixtime.com"
    sender_password = "kYKvQQkBzxsHHjQf"

    # 接收方邮箱
    recipient_emails = ["xiongxinzhou@matrixtime.com", "zhouyilong@matrixtime.com", "caojin@matrixtime.com"]

    # 抄送方邮箱
    cc_emails = ["luochangzhi@matrixtime.com", "liangyunfei@matrixtime.com", "chenchen@matrixtime.com",
                 "sunyaozhuang@matrixtime.com", "tanyulong@matrixtime.com",
                 "xingtao@matrixtime.com"]

    time_today = (datetime.datetime.now() + datetime.timedelta(days=-1)).strftime('%Y-%m-%d')

    # 邮件内容
    mail_content =f"""
    <p>Hi all:</p>
    
    <p>&emsp;下图是{time_today}嘉兴隆基接线盒NG比例统计。请查收!</p>
    <p>
        &emsp;<img src="cid:image1">
    </p>
    """

    image_path = "ng_image/image.png"

    # 构造邮件
    msg = MIMEMultipart()
    msg['From'] = formataddr(["苏秀振", sender_email])
    msg['To'] = ", ".join(recipient_emails)
    msg['Cc'] = ", ".join(cc_emails)
    msg['Subject'] = f"【嘉兴隆基接线盒】算法每日NG比例统计-{time_today}"

    # 添加文本内容
    text = MIMEText(mail_content, _subtype='html', _charset='utf-8')
    msg.attach(text)

    # 添加图片
    with open(image_path, "rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID", "image1")
        msg.attach(img)

    # 将图片嵌入邮件内容
    # text.attach(MIMEText('<html><body><img src="cid:image1"></body></html>', 'html', 'utf-8'))

    # 连接到SMTP服务器
    smtp_server = "smtp.exmail.qq.com"
    smtp_port = 465
    server = smtplib.SMTP_SSL(smtp_server, smtp_port)

    # 登录到SMTP服务器
    print('login....')
    server.login(sender_email, sender_password)
    print('login success')
    # 发送邮件
    # 发送邮件
    to_emails = recipient_emails + cc_emails
    server.sendmail(sender_email, to_emails, msg.as_string())

    # 关闭连接
    server.quit()


if __name__ == '__main__':
    send_email()
