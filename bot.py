from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

from vpop import VPop
from settings import NICK, SERVER, PORT, CHANNEL


class VBot(irc.IRCClient):
    nickname = NICK

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.vpop = VPop()

    def connectionLost(self, reason):
        irc.IRCClient.connectionLOST(self, reason)

    def signedOn(self):
        self.join(self.factory.channel)

    def joined(self, channel):
        pass

    def kickedFrom(self, channel, kicker, message):
        self.join(channel)
        self.say(channel, ":(")

    def privmsg(self, user, channel, msg):
        nick, host = user.split("!")
        msgs = msg.split(" ")

        print msgs
        if msgs[0] == ".info":
            user = self.vpop.get_user_data(msgs[1])
            if user is None:
                self.say(channel, "Did not find any user matching that id")
                return

            for k, v in user.iteritems():
                user[k] = v.encode("utf-8")
            self.say(channel, ("\x02[\x0F %(name)s \x02]\x0F strength: "
                               "%(strength)s %(skill)s:"
                               " %(skill_value)s \x02-\x0F %(place)s/"
                               "%(country)s"
                               " \x02-\x0F %(citizenship)s"
                               "".encode("utf-8") % user))

    def action(self, user, channel, msg):
        print "action"


class VBotFactory(protocol.ClientFactory):

    def __init__(self, channel):
        self.channel = channel

    def buildProtocol(self, addr):
        p = VBot()
        p.factory = self
        return p

    def clientConnectionLost(self, connector, reason):
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        reactor.stop()

if __name__ == "__main__":
    f = VBotFactory(CHANNEL)
    reactor.connectTCP(SERVER, PORT, f)
    reactor.run()
