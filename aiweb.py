# coding: cp1251

from pony.main import *
use_autoreload()

import core

users, messages = core.load_from_file()

class LoginForm(Form):
    def __init__(self):
        self.login = Text(u'Логин')
        self.password = Text(u'Пароль')
        self.button = Submit(u'Вход')

##    def __init__(self):
##        l1 = self.add_layout(True)
##        l2 = l1.add_layout(False)
##        l2.login = Text(u'Логин')
##        l2.password = Text(u'Пароль')
##        l1.button = Submit(u'Вход')

@printhtml
def registration_component():
    return LoginForm()
    
@http('/')
@printhtml
def main():
    uranks = sorted(users.values(), key=lambda x: x.rank, reverse=True)
    mranks = sorted(messages.values(), key=lambda x: x.rank, reverse=True)
    return html()

@http('/user/')

http.start()    