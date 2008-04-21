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
    def validate(self):
        con = connect()
        row = con.execute(u'select id from Users where login = ?', [ self.grid[0, 1].value ]).fetchone()
        if row is None:
            raise http.Redirect(url(login_error))
        hash = sha.new(self.grid[1, 1].value).hexdigest()
        hash2 = con.execute('select password fron Users where id = ?', [ http.user ])
        if hash!=hash2:
            raise http.Redirect(url(login_error))
        con.close()        
    def on_submit(self):
        pass
        

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
            row = self.con.execute(u'select id from Users where login = ?', [ self.login.value ]).fetchone()
            if row is not None:
                self.login.error_text = u'Такой логин уже занят'
        finally: con.close()
    def on_submit(self):
        hash = sha.new(self.password.value).hexdigest()
        cursor = self.con.execute(u"insert into Users(login, password, email, rating, disabled, reg_date) values(?, ?, ?, 1, 0, ?)", # datetime('now','localtime')
                             [ self.login.value, hash, self.email.value, datetime.now() ])
        http.user = cursor.lastrowid
        http.session['login'] = self.login.value
        con.commit()
        raise http.Redirect(url(main))

@printhtml
def registration_component():
    user_id = get_user()
    if user_id is None:
        f = LoginForm()
        print f.header
        print f.grid.tag
        print '</form>'
        return
    con=connect()
    login = con.execute(u'select login from Users where id=?',[user_id]).fetchone()
    print u'<h3>Вы вошли как: %s</h3>' % (login)
    print u'<p>%s</p>' % link(u'Выйти',logout)
    
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
    user = get_session()['login']
    set_user(None)
    print html(u"""$if (user) { До встречи, $user!}
                <h2>Вы вышли</h2>""")

@http('/login')
@printhtml
def login_error():
    print u"Введенные Вами регистрационные данные неверны. Попробуйте еще раз."
    f = LoginForm()
    print f.header
    print f.grid.tag
    print '</form>'

@printhtml
def get_quote(id):
    con = connect()
    rating, parent_id, caption, deleted, message_text, created, last_modified = \
       con.execute(u'select rating, parent_id, caption, deleted, message_text, created, last_modified from Messages where id = ?', [id]).fetchone()

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
        print html()
    else: print "There's no user called " + user_name + "!"
    print footer()

class PostForm(Form):
    def __init__(self, message_id=None):
        # message_id==Null if message is posted for the first time :)
        self.message_id = message_id
        self.caption = Text(u'Заголовок:', required=True)
        self.summary = TextArea(u'Краткой строкой:') # TODO: Summary(?)
        self.tags = Text(u'Теги:')       # TODO: Tags
        self.message = TextArea(u'Текст сообщения:', required=True)
        if self.message_id:
            self.submit = Submit(u'Сохранить')
            con = connect()
            self.caption.value, #self.summary.value,
            self.message.value = con.execute('select caption, message_text from Messages where id = ?', [ self.message_id ]).fetchone()
            self.tags.value = u'' # !!!!!!!!!!!!!!!!!!!!!
        else: self.submit = Submit(u'Запостить!')
    def validate(self):
        con = connect()
        try:
            self.tag_names = [] # !!!!!!!!!!!!!!!!!!!!!
            for tag_name in self.tag_names:
                if tag_name not in con.execute('select name from Tags'):
                    self.tags.error_text = u'Неправильный(е) теги(и)!'
        finally: con.close()
    def on_submit(self):
        user_id = get_user()
        con = connect()
        if self.message_id:
            con.execute('update messages set last_modified = ?, caption = ?, message_text = ? where id = ?',
                        [ datetime.now(), self.caption.value, self.message.value, self.message_id ])
            con.execute('delete from MessageTags where message_id = ?', [ self.message_id ])
        else:
            con.execute('insert into Messages (rating, author_id, parent_id, deleted, created, last_modified, caption, message_text)\
                        values(0, ?, 0, 0, ?, ?, ?, ?)', [ user_id, datetime.now(), datetime.now(), self.caption.value, self.message.value ])
            self.message_id = con.execute('select id from Messages where message_text = ?', [ self.message.value ]).fetchone() # ха-ха-ха!
        for tag_name in self.tag_names:
            tag_id = con.execute('select id from Tags where name = ?', [ tag_name ]).fetchone()
            con.execute('insert into MessageTags values (?, ?)', [ self.message_id, tag_id ]) 

class CommentForm(Form):
    def __init__(self, parent_id, parent_caption, message_id=None):
        # message_id==Null if comment is posted for the first time :)
        self.parent_id = parent_id
        self.parent_caption = parent_caption
        self.message_id = message_id
        self.caption = Text(u'Заголовок:')
        self.message = TextArea(u'Текст комментария:', required=True)
        if self.message_id:
            self.submit = Submit(u'Сохранить')
            con = connect()
            self.caption.value, self.message.value = con.execute('select caption, message_text from Messages where id = ?', [ self.message_id ]).fetchone()
        else: self.submit = Submit(u'Откомментить!')
    def validate(self):
        pass
    def on_submit(self):
        user_id = get_user()
        if self.caption.value=="":
            self.caption.value = u'Re: ' + self.parent_caption
        con = connect()
        if self.message_id:
            con.execute('update Messages set last_modified = ?, caption = ?, message_text = ? where id = ?',
                        [ datetime.now(), self.caption.value, self.message.value, self.message_id ])
            con.execute('delete from MessageTags where message_id = ?', [ self.message_id ])
        else:
            con.execute('insert into Messages (rating, author_id, parent_id, deleted, created, last_modified, caption, message_text)\
                        values(0, ?, ?, 0, ?, ?, ?, ?)', [ user_id, self.parent_id, datetime.now(), datetime.now(), self.caption.value, self.message.value ])    

http.start()
