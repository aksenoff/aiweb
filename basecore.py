# coding: cp1251

from pony.thirdparty import sqlite
from pony.main import *

#constants
dumping_factor = 0.85
karma_part = 0.1
del_coeff = -0.1

def connect():
    return sqlite.connect('aiweb.db3')

class Node(object):
    def __init__(self):
        self.rank = 0
        self.new_rank = 0
    def calc_targets(self):
        self.targets = {}

class User(Node):
    def __init__(self, login):
        con = connect()
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
        if not n_posts+n_comments: return
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
    def vote(self, message, sign):
        if self not in message.voters.keys():
            message.voters[self] = sign
            self.votes[message] = sign
            message.karma += sign
        else:
            if message.voters[self] ^ sign: ## if a user changed his mind, delete his vote
                del(message.voters[self])
            else: pass ## prevent double-voting

class Message(Node):
    def __init__(self, user, number, parent=None, deleted=False):
        Node.__init__(self)
        self.deleted = deleted
        self.karma = 0
        self.voters = {}
        self.user = user
        self.number = number
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
            self.parent.user.targets[self] = del_coeff

def from_base():
    users = {}
    messages = {}
    con = connect()
    u = con.execute(u'select login from Users')
    for user in u:
        user = user[0]
        users[user] = User(user) ## :)
    m = con.execute(u'select id from Messages')
    for id, user, parent, deleted in con.execute(u'select Messages.id, login, parent_id, deleted '
                                                 'from Messages, Users where Users.id = Messages.author_id'):
        user = users[user]
        if parent: parent = messages[parent]
        messages[id] = Message(user, id, parent, deleted)
    lm = con.execute(u'select * from LinksToMessages')
    for link in lm:
        message = messages.get(link[0])
        message2 = messages.get(link[1])
        message.links_to.add(message2)
        message2.links_from.add(message)
    return users, messages
        
nodes = []

def calc_rank():
    for node in nodes:
        node.new_rank = 0
    for node in nodes:
        rank = node.rank
#        print node
        for target, coeff in node.targets.items():
           target.new_rank += rank*coeff           
    for node in nodes:
        node.rank = 1. - dumping_factor + dumping_factor*node.new_rank

def recompute_base():
    users, messages = from_base()
    nodes.extend(users.itervalues())
    nodes.extend(messages.itervalues())
    for node in nodes:
        node.rank = 1.
        node.calc_targets() 
    for i in range(100): calc_rank()
    for login, user in users.iteritems(): print login, user.rank
    print sum(user.rank for user in users.values())
    con = connect()
    for user in users.itervalues():
        con.execute('update Users set rating = ? where login = ?', [ user.rank, user.login ])
    for message in messages.itervalues():
        con.execute('update Messages set rating = ? where id = ?', [ message.rank, message.number ])
    con.execute('')
    con.commit()

if __name__ == '__main__':
    recompute_base()