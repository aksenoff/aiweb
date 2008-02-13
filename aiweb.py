import re

re_line = re.compile(r"^( *)(-?)(\w+:\d+)(?: *->((?: *\b\w+:\d+\b)+))?\s*\Z")

class Node(object):
    def __init__(self):
        self.rank = 1
    def calc_targets(self):
        self.targets = {}

class User(Node):
    def __init__(self, login):
        Node.__init__(self)
        self.login = login
        self.posts = []
        self.comments = []
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.login)
    def calc_targets(self):
        tmp = len(self.posts)*2 + len(self.comments)
        post_weight = 2. / tmp
        comment_weight = 1. / tmp
        self.targets = {}
        for post in self.posts:
            self.targets[post] = post_weight
        for comment in self.coments:
            self.targets[comment] = comment_weight

class Message(Node):
    def __init__(self, user, number, parent=None, indent=0):
        Node.__init__(self)
        self.deleted = False
        self.user = user
        self.number = number
        self.indent = indent
        self.parent = parent
        self.links_to = []
        self.links_from = []
        if parent: user.comments.append(self)
        else: user.posts.append(self)
    def __repr__(self):
        return '<%s %s:%d>' % (self.__class__.__name__, self.user.login, self.number)

class SyntaxError(Exception):
    def __init__(self, line_number, msg, line_text):
        Exception.__init__(self)
        self.line_number = line_number
        self.msg = msg
        self.line_text = line_text

def do_parse(f):
    users = {}
    messages = {}
    links = {}
    parents = []
    for i, line in enumerate(f):
        if line.isspace(): continue
        match = re_line.match(line)
        if match is None: raise SyntaxError(i+1, 'incorrect syntax', line)
        indent, deleted, msg, links_to = match.groups()
        indent = len(indent)
        flag = False
        while parents and parents[-1].indent >= indent:
            if parents[-1].indent > indent: flag = True
            parents.pop()
        if flag and parents and parents[-1].indent < indent:
            raise SyntaxError(i+1, 'incorrect indent', line)
        parent = parents and parents[-1] or None
        login, number = msg.split(':')
        number = int(number)
        if number in messages: raise SyntaxError(i+1, 'duplicate message number: %d' % number, line)
        user = users.get(login)
        if user is None: user = users[login] = User(login)
        message = Message(user, number, parent, indent)
        if deleted: message.deleted = True
        parents.append(message)
        messages[number] = message
        links[message] = links_to or ''
    for message, links_to in links.items():
        links_to = links_to.split()
        for msg_name in links_to:
            login, number = msg_name.split(':')
            number = int(number)
            message2 = messages.get(number)
            if message2 is None:
                raise SyntaxError(-1, 'non-existent message number: %d' % number, '???')
            if message2.user.login != login:
                raise SyntaxError(-1, 'incorrect user %s in message %d' % (login, number))
            if message2 in message.links_to or message in message2.links_from:
                raise SyntaxError(-1, 'duplicate link between %d and %d' % (message.number, number))
            message.links_to.append(message2)
            message2.links_from.append(message)
    return users, messages

def parse(f):
    try:
        return do_parse(f)
    except SyntaxError, e:
        print 'Syntax error in line %d: %s' % (e.line_number, e.msg)
        print e.line_text

def calc_rank(users, messages):
    nodes = []
    nodes.extend(users.itervalues())
    nodes.extend(messages.itervalues())
    for node in nodes: node.calc_targets()
        
if __name__ == '__main__':
    users, messages = parse(file('test.txt'))
    # raw_input()
    