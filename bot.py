from twisted.words.protocols import irc
from twisted.internet import reactor, protocol, defer

from vpop import VPop
import modules
from settings import NICK, SERVER, PORT, CHANNELS


class VBot(irc.IRCClient):
    nickname = NICK

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.vpop = VPop()
        self.channels = self.factory.channels
        self.parse_msg = modules.parse_msg
        self._namescallback = {}
        reactor.callLater(600, self.new_event)

    def connectionLost(self, reason):
        irc.IRCClient.connectionLOST(self, reason)

    def signedOn(self):
        for c in self.channels:
            self.join(c)

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

    def action(self, user, channel, msg):
        print "action"

    def new_event(self):
        try:
            new_events = self.vpop.get_new_events()
            if new_events:
                for c in ["#vpopulus"]:
                    self.say(c, (" | ".join(new_events)).encode("utf-8"))
        except Exception as e:
            print e
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

    def __init__(self, channels):
        self.channels = channels
        self._namescallback = {}

    def buildProtocol(self, addr):
        p = VBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()


if __name__ == "__main__":
    f = VBotFactory(CHANNELS)
    reactor.connectTCP(SERVER, PORT, f)
    reactor.run()
