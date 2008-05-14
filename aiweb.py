# coding: cp1251

from pony.main import *
from pony.thirdparty import sqlite
from datetime import *
from datetime import datetime
import sha
use_autoreload()

import core

users, messages = core.load_from_file()

def connect():
    return sqlite.connect('aiweb.db3')

class LoginForm(Form):
    def __init__(self):
        Form.__init__(self, method='POST')
        self.grid = Grid(columns=['', '', ''])
        self.grid.row_count = 2
        self.grid[0, 0] = StaticText(u'Логин')
        self.grid[0, 1] = Text(size=10, tabindex=1)
        self.grid[0, 2] = Submit(u'Вход', tabindex=3)
        self.grid[1, 0] = StaticText(u'Пароль')
        self.grid[1, 1] = Password(size=10, tabindex=2)
        self.grid[1, 2] = StaticText(link(u'Регистрация', register))
    def on_submit(self):
        con = connect()
        row = con.execute(u'select id, password from Users where login = ?', [ self.grid[0, 1].value ]).fetchone()
        if row is None:
            raise http.Redirect(url(login_error))
        id, password = row
        hash = sha.new(self.grid[1, 1].value).hexdigest()
        if hash != password:
            raise http.Redirect(url(login_error))
        http.user = id
        con.close()        

class RegForm(Form):
    def __init__(self):
        self.login=Text(u'Логин',required=True)
        self.email = Text(u'Почтовый адрес')
        self.password = Password(u'Пароль', required=True)
        self.password2 = Password(u'Повтор пароля', required=True)
    def validate(self):
        con = connect()
        try:
            if self.password.value!=self.password2.value:
                self.password.error_text = self.password2.error_text = u'Пароли не совпадают!'
            row = con.execute(u'select id from Users where login = ?', [ self.login.value ]).fetchone()
            if row is not None:
                self.login.error_text = u'Такой логин уже занят'
        finally: con.close()
    def on_submit(self):
        con = connect()
        hash = sha.new(self.password.value).hexdigest()
        cursor = con.execute(u"insert into Users(login, password, email, rating, disabled, reg_date) values(?, ?, ?, 1, 0, ?)", # datetime('now','localtime')
                             [ self.login.value, hash, self.email.value, datetime.now() ])
        http.user = cursor.lastrowid
        http.session['login'] = self.login.value
        con.commit()
        raise http.Redirect(url(main))

@printhtml
def registration_component():
    user_id = http.user
    if user_id is None:
        f = LoginForm()
        print f.header
        print f.grid.tag
        print '</form>'
        return
    con = connect()
    row = con.execute(u'select login from Users where id = ?', [ user_id ]).fetchone()
    if row:
        login = row[0]
        print u'<h3>Вы вошли как: %s</h3>' % link(login, home, login)
        print u'<p>%s</p>' % link(u'Выйти',logout)
        return
    print u"Внутренняя ошибка базы данных!"
    
@http('/')
@printhtml
def main():
    uranks = sorted(users.values(), key=lambda x: x.rank, reverse=True)
    mranks = sorted(messages.values(), key=lambda x: x.rank, reverse=True)
    return html()

@http('/register')
@printhtml
def register():
    f = RegForm()
    print u"Заполните необходимые регистрационные данные:"
    print f

@http('/logout')
@printhtml
def logout():
    user = http.user
    if user:
        con = connect()
        row = con.execute(u'select login from Users where id = ?', [ user ]).fetchone()
        if row:
            user = row[0]
            http.user = None
            print u'<meta http-equiv="Refresh" content="3; URL=%s">' % url(main)
            print u"<h2>До встречи, %s! Вы вышли</h2>" % user
            return
    http.user = None
    raise http.Redirect(url(main))

@http('/login')
@printhtml
def login_error():
    print u"Введенные Вами регистрационные данные неверны. Попробуйте еще раз."
    f = LoginForm()
    print f.header
    print f.grid.tag
    print '</form>'

@printhtml
def header():
    pass

@printhtml
def footer():
    pass
    
@http('/$user_name?start=$offset')
@printhtml
def home(user_name, offset=0):
    print header()
    con = connect()
    row = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()
    if row:
        viewed_id = row[0]
        print html()
    else: print "There's no user called " + user_name + "!"
    print footer()

@http('/posts/$user_name')
def posts(user_name):
    con = connect()
    user_id = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()
    if user_id is None: raise http.NotFound
    user_id = user_id[0]
    if user_id==http.user: my = True
    else: my = False
    messages = con.execute(
        'select tags, created, last_modified, caption, summary, message_text '
        'from Messages where author_id = ? and parent_id = 0', [ user_id ])
    http.request.use_xslt = False
    return html()

@http('/comments/$user_name')
def comments(user_name):
    return html()

class PostForm(Form):
    def __init__(self, message_id=None):
        # message_id==None if message is posted for the first time :)
        self.message_id = message_id
        self.caption = Text(u'Заголовок', required=True)
        self.summary = TextArea(u'Краткой строкой')
        self.tag_string = Text(u'Теги')
        self.message = TextArea(u'Текст сообщения', required=True)
        if self.message_id:
            self.submit = Submit(u'Сохранить')
            con = connect()
            self.caption.value, self.summary.value, self.message.value, self.tag_string.value = \
                con.execute('select caption, summary, message_text, tags from Messages where id = ?', [ self.message_id ]).fetchone()
        else: self.submit = Submit(u'Запостить!')
    def on_submit(self):
        tag_string = self.tag_string.value.strip()
        tag_names = set(tag_string.split())
        summary = self.summary.value.strip()
        message = self.message.value
        if not summary and len(message) > 100:
            end = 100
            while message[end].isalnum(): end -= 1
            while not message[end].isalnum(): end -= 1
            summary = message[:end+1] + "..."
        user_id = http.user
        con = connect()
        now = datetime.now()
        if self.message_id:
            con.execute('update messages set last_modified = ?, caption = ?, message_text = ?, summary = ?, tags = ? where id = ?',
                        [ now, self.caption.value, message, summary, tag_string, self.message_id ])
            con.execute('delete from MessageTags where message_id = ?', [ self.message_id ])
        else:
            cur = con.execute('insert into Messages (rating, author_id, parent_id, deleted, created, last_modified, caption, message_text, summary, tags)\
                              values(0, ?, 0, 0, ?, ?, ?, ?, ?, ?)', [ user_id, now, now, self.caption.value, message, summary, tag_string ])
            self.message_id = cur.lastrowid
        for tag_name in tag_names:
            tag_id = con.execute('select id from Tags where name = ?', [ tag_name ]).fetchone()
            con.execute('insert into MessageTags values (?, ?)', [ self.message_id, tag_id ])
        con.commit()

class CommentForm(Form):
    def __init__(self, parent_id, parent_caption, message_id=None):
        # message_id==Null if comment is posted for the first time :)
        self.parent_id = parent_id
        self.parent_caption = parent_caption
        self.message_id = message_id
        self.caption = Text(u'Заголовок')
        self.message = TextArea(u'Текст комментария', required=True)
        if self.message_id:
            self.submit = Submit(u'Сохранить')
            con = connect()
            self.caption.value, self.message.value = con.execute('select caption, message_text from Messages where id = ?', [ self.message_id ]).fetchone()
        else: self.submit = Submit(u'Откомментить!')
    def on_submit(self):
        user_id = http.user
        if self.caption.value=="" and self.parent_caption[:3]!="Re:":
            self.caption.value = u'Re: ' + self.parent_caption
        con = connect()
        now = datetime.now()
        if self.message_id:
            con.execute('update Messages set last_modified = ?, caption = ?, message_text = ? where id = ?',
                        [ now, self.caption.value, self.message.value, self.message_id ])
            con.execute('delete from MessageTags where message_id = ?', [ self.message_id ])
        else:
            con.execute('insert into Messages (rating, author_id, parent_id, deleted, created, last_modified, caption, message_text)\
                        values(0, ?, ?, 0, ?, ?, ?, ?)', [ user_id, self.parent_id, now, now, self.caption.value, self.message.value ])
        con.commit()

http.start()
