

def parse_msg(bot, nick, host, channel, msg):
    msg = msg.split(" ")
    modules = {
        '.info': mod_info,
        '.battles': mod_battles,
        '.help': mod_help,
        '.damage': mod_damage,
    }

    func = modules.get(msg[0])
    if func is not None:
        func(bot, nick, host, channel, msg)


def mod_info(bot, nick, host, channel, msg):
    user = bot.vpop.get_user_data(msg[1])
    if user is None:
        bot.say(channel, "Did not find any user matching that id!")
        return

    for k, v in user.iteritems():
        user[k] = v.encode("utf-8")

    bot.msg(channel, ("\x02[\x0F %(name)s \x02]\x0F strength: "
                      "%(strength)s rank: %(rank)s %(skill)s:"
                      " %(skill_value)s \x02-\x0F %(place)s/"
                      "%(country)s"
                      " \x02-\x0F %(citizenship)s"
                      "".encode("utf-8") % user))


def mod_battles(bot, nick, host, channel, msg):
    if msg[0] == ".battles" and len(msg) > 1 and msg[1] == "detailed":
        out = []
        type = 1 if msg[-1] == "global" else 17
        battles = bot.vpop.get_detailed_battles(type)

        for b in battles[:5]:
            out.append(("%s \x02%s\x0F \x02[\x0F %s vs %s \x02]\x0F %s"
                        "" % (b['region'], b['damage'], b['c1'], b['c2'],
                              b['time'])
                        ).encode("utf-8"))
        bot.msg(channel, ", ".join(out))

    else:
        out = []
        type = 2 if msg[-1] == "global" else 1
        battles = bot.vpop.get_quick_battles(type)

        for b in battles[:5]:
            out.append(("%s \x02[\x0F %s vs %s \x02]\x0F" % (b[2],
                                                             b[0], b[1])
                        ).encode("utf-8"))
        bot.msg(channel, ", ".join(out))


def mod_help(bot, nick, host, channel, msg):
    bot.msg(channel, ("Commands: .info <citizen id>, "
                      ".battles [detailed] [global]"))


def damage_formula(weapon, rank, strength, wellness):
    if weapon == 0:
        weapon = 0.5
    else:
        weapon += 1

    return (weapon * (1 + (rank / float(5))) * strength *
            (1 + (wellness - 25) / float(100)) * 2)


def mod_damage(bot, nick, host, channel, msg):
    user = bot.vpop.get_user_data(msg[1])
    if user is None:
        bot.say(channel, "Did not find any user matching that id")
        return

    out = "\x02%s\x0f's damage:" % (user['name'])
    damages = []
    for i in range(0, 6):
        damages.append("Q%d: %.2lf" % (
            i,
            damage_formula(i, int(user['rank_id']),
                           float(user['strength']),
                           int(user['wellness']))))
    out = ("%s %s (S: %s W: %s R: %s)" % (
        out, " | ".join(damages),
        user['strength'], user['wellness'], user['rank'])).encode("utf-8")

    bot.msg(channel, out)
