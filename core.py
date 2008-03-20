import re

re_line = re.compile(r"^( *)(-?)(\w+:\d+)(?: *-> *\(((?: *\b\w+:\d+\b)+)\))?((?: *[+-]\w+)+)?\s*\Z")

#constants
dumping_factor = 0.85
karma_part = 0.1
del_coeff = -0.1

class Node(object):
    def __init__(self):
        self.rank = 0
        self.new_rank = 0
    def calc_targets(self):
        self.targets = {}

class User(Node):
    def __init__(self, login):
        Node.__init__(self)
        self.login = login
        self.posts = []
        self.comments = []
        self.votes = {}
    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, self.login)
    def calc_targets(self):
        self.targets = {}
        n_posts = len(self.posts)
        n_comments = len(self.comments)
        tmp = n_posts*2 + n_comments
        post_weight = 2. / tmp
        comment_weight = 1. / tmp
        self.targets = {}
        for post in self.posts:
            self.targets[post] = post_weight
        for comment in self.comments:
            self.targets[comment] = comment_weight
        for message, sign in self.votes.items():
            self.targets[message] = sign * karma_part / len(self.votes)
    def del_message(self, message):
        message.deleted = True
    def vote(self, message, sign):
        # True for "+" and False for "-"
        if self not in message.voters.keys():
            message.voters[self] = sign
            self.votes[message] = sign
            message.karma += sign
        else: pass

class Message(Node):
    def __init__(self, user, number, parent=None, indent=0):
        Node.__init__(self)
        self.deleted = False
        self.karma = 0
        self.voters = {}
        self.user = user
        self.number = number
        self.indent = indent
        self.parent = parent
        self.links_to = set()
        self.links_from = set()
        if parent: user.comments.append(self)
        else: user.posts.append(self)
    def __repr__(self):
        return '<%s %s:%d>' % (self.__class__.__name__, self.user.login, self.number)
    def calc_targets(self):
        self.targets = {}
        parent, targets = self.parent, self.targets
        if parent: tmp = 2 + len(self.links_to)
        else: tmp = 1 + len(self.links_to)
        user_weight = parent_weight = link_weight = 1. / tmp
        if parent: targets[parent] = parent_weight
        targets[self.user] = user_weight
        for link in self.links_to: targets[link] = link_weight
        if self.deleted:
            self.parent.user.targets[self.user] = del_coeff
    # def delete(self, deleter):
    #    self.deleted

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
        indent, deleted, msg, links_to, voters = match.groups()
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
        if voters is None: continue
        for voter in voters.split():
            sign, login = voter[0], voter[1:]
            user = users.get(login)
            if user is None: user = users[login] = User(login)
            user.vote(message, sign == '+' and 1 or -1)
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
            message.links_to.add(message2)
            message2.links_from.add(message)
    return users, messages

def parse(f):
    try:
        return do_parse(f)
    except SyntaxError, e:
        print 'Syntax error in line %d: %s' % (e.line_number, e.msg)
        print e.line_text

nodes = []

def calc_rank():
    for node in nodes: node.new_rank = 0
    for node in nodes:
        rank = node.rank
        for target, coeff in node.targets.items():
           target.new_rank += rank*coeff
           # print node, rank, target, coeff, rank*coeff, target.new_rank
    for node in nodes:
        # print node, node.new_rank
        node.rank = 1. - dumping_factor + dumping_factor*node.new_rank

if __name__ == '__main__':
    users, messages = parse(file('test.txt'))
    nodes.extend(users.itervalues())
    nodes.extend(messages.itervalues())
    for node in nodes:
        node.rank = 1.
        node.calc_targets() 
    for i in range(1000): calc_rank()
    for login, user in users.iteritems(): print login, user.rank
    