from string import maketrans


def parse_msg(bot, nick, host, channel, msg):
    msg = msg.split(" ")
    modules = {
        # '.info': mod_info,
        # '.battles': mod_battles,
        '.help': mod_help,
        '.damage': mod_damage,
        '.prod': mod_prod,
        '.productivity': mod_prod,
        '.all': mod_all,
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
                      ".battles [detailed] [global], "
                      ".damage <citizen id>"))


def damage_formula(weapon, rank, strength, wellness):
    if weapon == 0:
        weapon = 0.5
    else:
        weapon = 1 + (int(weapon) / 5.0)

    return (weapon * (1 + (int(rank) / float(5))) * float(strength) *
            (1 + (int(wellness) - 25) / float(100)) * 2.0)


def mod_damage(bot, nick, host, channel, msg):
    user = bot.vpop.get_user_data(name=" ".join(msg[1:]))
    if "message" in user:
        bot.say(channel, user["message"].encode("utf-8"))
        return

    strength = user['military']['strength']
    rank_level = user['military']['rank-level']
    wellness = user['wellness']

    out = "\x02%s\x0f's damage:" % (user['name'])
    damages = []
    for i in range(0, 6):
        damages.append("Q%d: %.2lf" % (i, damage_formula(
            i, rank_level, strength, wellness)))

    out = ("%s %s (S: %s W: %s R: %s)" % (
        out, " | ".join(damages),
        strength, wellness, rank_level)).encode("utf-8")

    bot.msg(channel, out)


def productivity_formula(skill, wellness, quality, is_high=False):
    region_factor = 2.0 if is_high else 1.0
    wellness_factor = (float(wellness) / 100.0) + 1
    emp_factor = 2.0
    return (float(skill) * wellness_factor * region_factor *
            emp_factor) / float(quality)


def mod_prod(bot, nick, host, channel, msg):
    try:
        skill = msg[1]
        wellness = msg[2]
        quality = msg[3]

        if len(msg) > 4:
            if msg[4] == "high":
                is_high = True
            elif msg[4] == "medium":
                is_high = False
            else:
                bot.say(channel, "lol, low")
                return
        else:
            is_high = False

        prod = productivity_formula(skill, wellness, quality, is_high)
    except:
        bot.say(channel,
                "Usage: .prod <skill> <wellness> <quality> [high|medium]")
        return
    out = "\x02[\x0F Productivity \x02]\x0F: %lf" % prod
    bot.say(channel, out.encode("utf-8"))


def mod_all(bot, nick, host, channel, msg):
    bot.names(channel, (bot, nick, host, channel, msg)).addCallback(print_all)


def print_all(params):
    nicklist_with_modes = params[0]
    nick = params[1][1]
    bot = params[1][0]
    channel = params[1][3]
    msg = params[1][4]

    trans = maketrans("+%@&", "    ")
    nicklist = [n.translate(trans).lstrip() for n in nicklist_with_modes]

    if nicklist_with_modes[nicklist.index(nick)][0] not in "%@&":
        return

    bot.msg(channel, ", ".join(nicklist))
    if len(msg) > 1:
        bot.msg(channel, "\x02%s" % msg[1].encode("utf-8"))
