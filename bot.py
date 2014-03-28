from twisted.words.protocols import irc
from twisted.internet import reactor, protocol

from vpop import VPop
from settings import NICK, SERVER, PORT, CHANNEL


class VBot(irc.IRCClient):
    nickname = NICK

    def connectionMade(self):
        irc.IRCClient.connectionMade(self)
        self.vpop = VPop()
        reactor.callLater(600, self.new_event)

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
        elif msgs[0] == ".battles" and len(msgs) > 1 and msgs[1] == "detailed":
            out = []
            type = 1 if msgs[-1] == "global" else 17
            battles = self.vpop.get_detailed_battles(type)

            for b in battles[:5]:
                out.append(("%s \x02%s\x0F \x02[\x0F %s vs %s \x02]\x0F %s"
                            "" % (b['region'], b['damage'], b['c1'], b['c2'],
                                  b['time'])
                            ).encode("utf-8"))
            self.say(channel, ", ".join(out))

        elif msgs[0] == ".battles":
            out = []
            type = 2 if msgs[-1] == "global" else 1
            battles = self.vpop.get_quick_battles(type)

            for b in battles[:5]:
                out.append(("%s \x02[\x0F %s vs %s \x02]\x0F" % (b[2],
                                                                 b[0], b[1])
                            ).encode("utf-8"))
            self.say(channel, ", ".join(out))

        elif msgs[0] == ".help":
            self.msg(channel, ("Commands: .info <citizen id>, "
                               ".battles [detailed] [global]"))

    def __load_modules(self):
        pass

    def action(self, user, channel, msg):
        print "action"

    def new_event(self):
        try:
            new_events = self.vpop.get_new_events()
            if new_events is not None:
                self.say(self.factory.channel, ", ".join(new_events))
        except Exception as e:
            print e
        finally:
            reactor.callLater(600, self.new_event)


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
