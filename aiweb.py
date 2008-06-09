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

@printhtml
def pages(type, pn=1, user_id=0, parent_id=0):
    # type == 1 : Pages for Posts tab on user homepage
    # type == 2 : Pages for Comments tab on user homepage
    # type == 3 : Pages for comments on message thread
    con = connect()
    if type == 1: nmessages = con.execute('select count(*) from Messages '
                                          'where author_id = ? and parent_id is null', [ user_id ]).fetchone()[0]
    if type == 2: nmessages = con.execute('select count(*) from Messages '
                                          'where author_id = ? and parent_id is not null', [ user_id ]).fetchone()[0]
    if type == 3: nmessages = con.execute('select count(*) from Messages '
                                          'where parent_id = ?', [ parent_id ]).fetchone()[0]
    user_name = con.execute('select login from Users where id = ?', [ user_id ]).fetchone()[0]
    if nmessages < 11: return
    npages = (nmessages / 10) + 1
    print '<div class="pages">'
    for i in range(1, npages+1):
        if i == pn: print '<strong>[%d]</strong>' % i
        else:
            if type == 1: print '[%s] ' % link(str(i), posts, user_name, (i-1)*10+1)
            if type == 2: print '[%s] ' % link(str(i), comments, user_name, (i-1)*10+1)
            if type == 3: print '[%s] ' % link(str(i), message_thread, user_name, parent_id, (i-1)*10+1)
    print '</div>'
    print '<hr>'
    
@http('/$user_name?start=$start')
@printhtml
def home(user_name, start=1):
    print header()
    con = connect()
    user_id = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()
    if user_id is None: raise http.NotFound
    user_id = user_id[0]
    my = user_id==http.user
    print html()

@http('/posts/$user_name?start=$start')
def posts(user_name, start=1):
    con = connect()
    user_id = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()
    if user_id is None: raise http.NotFound
    user_id = user_id[0]
    my = user_id==http.user
    messages = con.execute('select id, tags, created, last_modified, caption, summary, message_text '
                           'from Messages where author_id = ? and parent_id is null and offset >= ?'
                           'order by offset limit 10', [ user_id, start-1 ]).fetchall()
    http.request.use_xslt = False
    return html()

@http('/comments/$user_name?start=$start')
def comments(user_name, start=1):
    con = connect()
    user_id = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()
    if user_id is None: raise http.NotFound
    user_id = user_id[0]
    my = user_id==http.user    
    messages = con.execute('select id, created, parent_id, deleted, last_modified, caption, message_text '
                           'from Messages where author_id = ? and parent_id is not null and offset >= ?'
                           'order by offset limit 10', [ user_id, start-1 ]).fetchall()
    http.request.use_xslt = False
    return html()

@http('/$m_user_name/$message_id?start=$start')
def message_thread(m_user_name, message_id, start=1):
    con = connect()
    m_user_id = con.execute('select id from Users where login = ?', [ m_user_name ]).fetchone()
    if m_user_id is None: raise http.NotFound
    m_user_id = m_user_id[0]
    my = m_user_id==http.user
    main_message = con.execute('select id, tags, author_id, parent_id, deleted, created, last_modified, caption, summary, message_text '
                               'from Messages where id = ? and author_id = ?', [ message_id, m_user_id ]).fetchone()
    if main_message is None: raise http.NotFound
    m_id, m_tags, m_author_id, m_parent_id, m_deleted, m_created, m_last_modified, m_caption, m_summary, m_message_text = main_message
    post = not m_parent_id
    if not post:
        m_parent_author_name = con.execute('select login from Users'
                                           ' where id = (select author_id from Messages where id = ?)', [ m_parent_id ]).fetchone()[0]
    comments_list = con.execute('select Messages.id, author_id, login, deleted, created, last_modified, caption, message_text '
                                'from Messages, Users where parent_id = ? and offset >= ? and author_id = Users.id '
                                'order by offset limit 10', [ message_id, (start-1) ]).fetchall()
    return html()

@http('/$user_name/edit?message_id=$message_id')
def edit(user_name, message_id):
    con = connect()
    user_id = con.execute('select id from Users where login = ?', [ user_name ]).fetchone()[0]
    if user_id is None: raise http.NotFound
    if user_id != http.user: raise http.NotFound
    parent_id = con.execute('select parent_id from Messages where id = ?', [ message_id ]).fetchone()[0]
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
            cur = con.execute(
                'insert into Messages (offset, author_id, created, last_modified, caption, message_text, summary, tags)'
                ' values((select coalesce(max(offset)+1, 0) from Messages where author_id=? and parent_id is null), ?, ?, ?, ?, ?, ?, ?)',
                [ user_id, user_id, now, now, self.caption.value, message, summary, tag_string ])
            self.message_id = cur.lastrowid
        for tag_name in tag_names:
            tag_id = con.execute('select id from Tags where name = ?', [ tag_name ]).fetchone()
            con.execute('insert into MessageTags values (?, ?)', [ self.message_id, tag_id ])
        con.commit()

class CommentForm(Form):
    def __init__(self, parent_id, parent_caption=None, message_id=None):
        # message_id==Null if comment is posted for the first time :)
        self.parent_id = parent_id
        self.parent_caption = parent_caption
        self.message_id = message_id
        self.caption = Text(u'Заголовок')
        self.message = TextArea(u'Текст комментария', required=True)
        if self.message_id:
            self.submit = Submit(u'Сохранить')
            con = connect()
            self.caption.value, self.message.value = con.execute(
                'select caption, message_text from Messages where id = ?', [ self.message_id ]).fetchone()
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
            con.execute('insert into Messages (offset, author_id, parent_id, created, last_modified, caption, message_text) '
                        'values((select coalesce(max(offset)+1, 0) from Messages where parent_id = ?), ?, ?, ?, ?, ?, ?)',
                        [ self.parent_id, user_id, self.parent_id, now, now, self.caption.value, self.message.value ])
        con.commit()

http.start()
