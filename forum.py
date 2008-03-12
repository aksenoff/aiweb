import sys
from pony.main import http, printhtml, use_autoreload, Form, TextArea, webpage, Submit

use_autoreload()

http.start()

class MyForm(Form):
    def __init__(self):
        self.text = TextArea()
        self.button = Submit()

@webpage('/')
def indexfunc():
    print '<link jquery>'
    print '<script src="/static/forum.js"></script>'
    print '<h1>FORUM :)</h1>'
    print '<div id="messages"></div>'
    form = MyForm()
    print form

@webpage
def ajax_post():
    print>>sys.stderr, http.request.fields.getfirst('text', 'nothing')
    form = MyForm()
    print '<div id="message"><p>'
    print http.request.fields.getfirst('text', 'nothing')
    print '</div>'
