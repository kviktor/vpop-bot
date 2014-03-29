from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

from vpop import VPop
from modules import parse_msg
from settings import NICK, SERVER, PORT, CHANNELS


class VBot(irc.IRCClient):
    nickname = NICK

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.vpop = VPop()
        self.channels = self.factory.channels
        self.parse_msg = parse_msg
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

    def __load_modules(self):
        pass

    def action(self, user, channel, msg):
        print "action"

    def new_event(self):
        try:
            new_events = self.vpop.get_new_events()
            if new_events is not None:
                for c in self.channels:
                    self.say(c, (", ".join(new_events)).encode("utf-8"))
        except Exception as e:
            print e
        finally:
            reactor.callLater(600, self.new_event)


class VBotFactory(protocol.ClientFactory):

    def __init__(self, channels):
        self.channels = channels

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
