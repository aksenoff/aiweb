# coding: cp1251

from pony.main import *
from pony.thirdparty import sqlite
from datetime import *
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
        self.grid[0, 0] = StaticText(u'�����')
        self.grid[0, 1] = Text(size=10)
        self.grid[0, 2] = Submit(u'����')
        self.grid[1, 0] = StaticText(u'������')
        self.grid[1, 1] = Password(size=10)
        self.grid[1, 2] = StaticText(link(u'�����������', register))


class RegForm(Form):
    def __init__(self):
        self.login=Text(u'�����',required=True)
        self.email = Text(u'�������� �����')
        self.password = Password(u'������', required=True)
        self.password2 = Password(u'������ ������', required=True)
        self.con = connect()
    def validate(self):        
        if self.password.value!=self.password2.value:
            self.password.error_text = self.password2.error_text = u'������ �� ���������!'
        row = self.con.execute(u'select id from Users where login = ?', [ self.login.value ]).fetchone()
        if row is not None:
            self.login.error_text = u'����� ����� ��� �����'
    def on_submit(self):
        hash = sha.new(self.password.value).hexdigest()
        cursor = self.con.execute(u'insert into Users(login, password, email, rating, disabled, reg_date) values(?, ?, ?, 1, 0, ?)',
                             [ self.login.value, hash, self.email.value, datetime() ])
        user_id = cursor.lastrowid
        set_user(user_id)
        get_session()['login'] = self.login.value
        self.con.commit()
        

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
    print u'<h3>�� ����� ���: %s</h3>' % (login)
    print u'<p>%s</p>' % link(u'�����',logout)
    
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
    print u"��������� ����������� ��������������� ������:"
    print f

@http('/logout')
@printhtml
def logout():
    user = get_session()['login']
    set_user(None)
    print html(u"""$if (user) { �� �������, $user!}
                <h2>�� �����</h2>""")

http.start()    