import sys
from pony.main import *

use_autoreload()

http.start()

class MyForm(Form):
    def __init__(self):
        self.text = Text()
        self.button = Submit()

@webpage('/')
def indexfunc():
    print '<link jquery>'
    print '<link rel="stylesheet" href="/static/ui.tabs.css" type="text/css" media="print, projection, screen">'
    print '<script src="/static/ui.tabs.js" type="text/javascript"></script>'
    print '<script src="/static/forum.js"></script>'
    print '<h1>FORUM :)!!!!</h1>'
    print '<div id="messages"></div>'
    form = MyForm()
    print form
    print """
    <div>
      <ul id="tabs">
      <li><a href="#aaa"><span>One</span></a>
      <li><a href="#bbb"><span>Two</span></a>
      <li><a href="#ccc"><span>Three</span></a>
      </ul>
      <div id="aaa">
        <h1>aaa</h1>
      </div>
      <div id="bbb">
        <h1>bbb</h1>
      </div>
      <div id="ccc">
        <h1>ccc</h1>
      </div>
    </div>
    """

@webpage
def ajax_post():
    print>>sys.stderr, http.request.fields.getfirst('text', 'nothing')
    form = MyForm()
    print '<div id="message"><p>'
    print http.request.fields.getfirst('text', 'nothing')
    print '</div>'
