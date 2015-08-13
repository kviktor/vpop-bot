from twisted.words.protocols import irc
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, protocol, defer
import dataset

from vpop import VPop
import modules
from settings import NICK, SERVER, PORT

db = dataset.connect("sqlite:///channels.db")
Channel = db['channel']


class VBot(irc.IRCClient):
    nickname = NICK

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.factory.clients.append(self)
        self.vpop = VPop()
        self.parse_msg = modules.parse_msg
        self._namescallback = {}
        reactor.callLater(300, self.new_event)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLOST(self, reason)
        self.factory.clients.remove(self)

    def signedOn(self):
        for c in Channel.all():
            self.join(str(c['name']))

    def joined(self, channel):
        pass

    def kickedFrom(self, channel, kicker, message):
        self.join(channel)
        self.say(channel, ":(")

    def privmsg(self, user, channel, msg):
        nick, host = user.split("!")
        if channel == self.nickname:
            channel = nick

        self.parse_msg(self, nick, host, channel, msg)

    def _reload_modules(self):
        reload(modules)
        self.parse_msg = modules.parse_msg
        self.vpop = VPop()

    def action(self, user, channel, msg):
        print("action")

    def new_event(self):
        try:
            new_events = self.vpop.get_new_events()
            for e in new_events:
                for c in Channel.all():
                    if (c['country'] and e['country'] and
                            c['country'] == e['country']):
                        self.say(str(c), (e['title']).encode("utf-8"))
                self.say("#vpopulus", (e['title']).encode("utf-8"))
        except Exception as e:
            print(e)
        finally:
            reactor.callLater(60, self.new_event)

    def names(self, channel, params):
        channel = channel.lower()
        d = defer.Deferred()
        if channel not in self._namescallback:
            self._namescallback[channel] = ([], [], params)

        self._namescallback[channel][0].append(d)
        self.sendLine("NAMES %s" % channel)
        return d

    def irc_RPL_NAMREPLY(self, prefix, params):
        channel = params[2].lower()
        nicklist = params[3].split(' ')

        if channel not in self._namescallback:
            return

        n = self._namescallback[channel][1]
        n += nicklist

    def irc_RPL_ENDOFNAMES(self, prefix, params):
        channel = params[1].lower()
        if channel not in self._namescallback:
            return

        callbacks, namelist, params_ = self._namescallback[channel]

        for cb in callbacks:
            cb.callback((namelist, params_))

        del self._namescallback[channel]


class VBotFactory(protocol.ClientFactory):

    def __init__(self):
        self.clients = []
        self._namescallback = {}

    def buildProtocol(self, addr):
        p = VBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.callLater(45, connector.connect)


class Web(Resource):
    isLeaf = True

    def __init__(self, irc_factory):
        Resource.__init__(self)
        self.irc_factory = irc_factory

    def render_POST(self, request):
        try:
            return self._add_channel(request)
        except Exception as e:
            print(e)
            return "NOTOK"

    def _add_channel(self, request):
        irc_bot = self.irc_factory.clients[0]
        ip = request.getClientIP()
        channel = "#" + request.args['channel'][0].lstrip("#")
        country = request.args.get("country")
        try:
            country = int(country[0])
        except:
            country = None

        print(channel, country)
        c = Channel.find_one(name=channel)
        if not c:
            Channel.insert({
                'name': channel,
                'country': country,
                'ip': ip,
            })
            irc_bot.join(channel)
            return "OK"
        else:
            return "Already added"


if __name__ == "__main__":
    irc_factory = VBotFactory()
    web = Site(Web(irc_factory))

    reactor.connectTCP(SERVER, PORT, irc_factory)
    reactor.listenTCP(8081, web)
    reactor.run()
