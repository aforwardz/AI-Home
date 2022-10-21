import requests
from bs4 import BeautifulSoup
import re
import time
import sqlite3
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formataddr
import smtplib
from private_settings import EMAIL_HOST_USER, EMAIL_HOST_PASSWORD, MOVIE_MAIL_LIST, ADMIN_MAIL


MOVIE_RESOURCE_URL = "https://www.evernote.com/shard/s744/sh/63ebf76a-4f70-cdd2-f726-3ebe20b95aeb/529c07bafe11d66dcdfdb397adb97678?json=1&rdata=0"

MOVIE_RATING_URL = "https://api.wmdb.tv/api/v1/movie/search?q=%s"

RATING_BASELINE = 7.5


conn = sqlite3.connect('./movie.db')
print('movie数据库打开成功')
cursor = conn.cursor()


def find_good_movie():
    data = requests.get(MOVIE_RESOURCE_URL).json()

    new_good_movies = []
    if data and data.get('content'):
        # print(data)
        data = data.get('content')
        new_good_movies = parse_movie(data)

    return new_good_movies


def parse_movie(content, limit=50):
    bs = BeautifulSoup(content, 'html.parser')
    items = bs.find('en-note').find_all('div')
    # print(items)

    movies, current, status, count = [], [], False, 0
    for item in items:
        if 'color:#722ED1' in str(item):
            status = True
        if status:
            if '<br/>' in str(item):
                current.append(item)
                movie_name, year = parse_movie_item(current[0])
                if movie_name is None or not check_new(movie_name, year):
                    current = []
                    continue

                rating = query_movie(movie_name, year)
                movie_html = ''

                if rating >= RATING_BASELINE:
                    rating_div = """<div><b><span style="color:#722ED1;">豆瓣评分：%s</span>""" % rating
                    movie_html = rating_div + ''.join([str(i) for i in current])
                    movies.append(movie_html)

                insert_movie(movie_name, year, rating, movie_html)

                current = []
                count += 1
                if count >= limit:
                    break
                time.sleep(30)
            else:
                current.append(item)

    time.sleep(30)
    if current:
        movie_name, year = parse_movie_item(current[0])
        if movie_name is not None and check_new(movie_name, year):
            rating = query_movie(movie_name, year)
            movie_html = ''

            if rating >= RATING_BASELINE:
                rating_div = """<div><b><span style="color:#722ED1;">豆瓣评分：%s</span>""" % rating
                movie_html = rating_div + ''.join([str(i) for i in current])
                movies.append(movie_html)

            insert_movie(movie_name, year, rating, movie_html)

    return movies


def parse_movie_item(item):
    movie_name = item.text
    if '链接' in movie_name or '提取码' in movie_name:
        return None, None

    year = re.findall(r'(?:\()\d{4}(?:\))', item.text)
    if not year:
        year = re.findall(r'(?:\（)\d{4}(?:\）)', item.text)
    year = year[0].strip("()（）") if year else 0
    movie_name = movie_name.split(' ')[0].split('（')[0].split('【')[0].split('(')[0].split('.')[0].strip()
    print(movie_name, year)

    return movie_name, year


def check_new(name, year=0):
    sql = "SELECT * FROM movies WHERE name='{name}' and year={year}"
    res = cursor.execute(sql.format(name=name, year=year))

    return res.fetchone() is None


def query_movie(name, year=0):
    query_url = MOVIE_RATING_URL % name
    if year:
        query_url += '&year=%s' % year

    rating = 0.0
    info = requests.get(query_url).json()
    if info:
        info = info[0]
        rating = info.get('doubanRating', '')
        rating = round(float(rating), 1) if rating else 0.0
    print("query res: %s %s %s" % (name, year, rating))

    return rating


def insert_movie(name, year, rating, html):
    cursor.execute("INSERT INTO movies VALUES ('{name}', {year}, {rating}, {html})".format(
        name=name, year=year, rating=rating, html=html))
    conn.commit()


def send_email(movies_content, mail_to, sub_type='plain'):
    # 用户信息
    smtp_server = 'smtp.exmail.qq.com'  # 腾讯服务器地址

    # 内容初始化，定义内容格式（普通文本，html）
    msg = MIMEText(movies_content, sub_type, 'utf-8')

    # 发件人收件人信息格式化 ，可防空
    # 固定用法不必纠结，我使用lambda表达式进行简单封装方便调用
    lam_format_addr = lambda name, addr: formataddr((Header(name, 'utf-8').encode(), addr))
    # 传入昵称和邮件地址
    msg['From'] = EMAIL_HOST_USER
    msg['To'] = Header(','.join(mail_to))

    # 邮件标题
    msg['Subject'] = Header('今日高分电影', 'utf-8').encode()  # 腾讯邮箱略过会导致邮件被屏蔽

    # 腾讯邮箱支持SSL(不强制)， 不支持TLS。
    server = smtplib.SMTP_SSL(smtp_server, 465)  # 按需开启

    # 登陆服务器
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

    # 发送邮件及退出
    server.sendmail(EMAIL_HOST_USER, mail_to, msg.as_string())  # 发送地址需与登陆的邮箱一致
    server.quit()


if __name__ == '__main__':
    cursor.execute("CREATE TABLE IF NOT EXISTS movies(name TEXT, year INT, rating REAL, html TEXT)")
    try:
        today_movies = find_good_movie()
        if today_movies:
            send_email(''.join(today_movies), MOVIE_MAIL_LIST, sub_type='html')
    except Exception as e:
        print(e)
        send_email(str(e), ADMIN_MAIL)

