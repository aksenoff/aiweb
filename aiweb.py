from pony.main import *
use_autoreload()

from core import users, messages

@printhtml
def registration_component():
    print '''
    <div class="span-6 last">option 44</div>
    <div class="span-6 last">option 55</div>
    <div class="span-6 last">option 66</div>
    '''
    
@http('/')
@printhtml
def home():
    uranks = sorted(users.values(), key=lambda x: x.rank, reverse=True)
    mranks = sorted(messages.values(), key=lambda x: x.rank, reverse=True)
    return html()


http.start()    