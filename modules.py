from datetime import datetime
from string import maketrans


def parse_msg(bot, nick, host, channel, msg):
    msg = msg.split(" ")
    modules = {
        ',info': mod_info,
        ',battles': mod_battles,
        ',help': mod_help,
        ',damage': mod_damage,
        ',prod': mod_prod,
        ',productivity': mod_prod,
        ',all': mod_all,
        ',reload': mod_reload,
        ',time': mod_time,
        ',vpop-time': mod_time,
        ',vfootball': mod_vfootball,
    }

    func = modules.get(msg[0])
    if func is not None:
        func(bot, nick, host, channel, msg)


def mod_info(bot, nick, host, channel, msg):
    user = bot.vpop.get_user_data(name=" ".join(msg[1:]))
    if "message" in user:
        bot.say(channel, user["message"].encode("utf-8"))
        return

    bot.msg(channel, ("\x02[\x0F %(name)s \x02]\x0F strength: "
                      "%(strength)s rank: %(rank)s %(skill)s:"
                      " %(skill_value)s \x02-\x0F %(place)s/"
                      "%(country)s"
                      " \x02-\x0F %(citizenship)s"
                      "".encode("utf-8") % {
                          'name': user['name'],
                          'strength': user['military']['strength'],
                          'rank': user['military']['rank-level'],
                          'skill': user['highest']['name'],
                          'skill_value': user['highest']['value'],
                          'place': user['location']['region']['name'],
                          'country': user['location']['country']['name'],
                          'citizenship': user['citizenship'
                                              ]['country']['name'],
                      }).encode("utf-8"))


def mod_battles(bot, nick, host, channel, msg):
    battles = bot.vpop.get_battles()
    if "message" in battles:
        bot.say(channel, battles["message"].encode("utf-8"))
        return

    local = True if len(msg) > 1 and msg[1] == "local" else False

    out = []
    for b in battles['battles'][:5]:
        region = b['region']['name']
        attacker = b['attacker']['name']
        defender = b['defender']['name']
        points = float(b['defence-points'])
        wall = float(b['objectives']['secure'])

        if local and not (attacker == "Hungary" or defender == "Hungary"):
            continue

        if points > wall:
            color = 3  # green
        elif points < 0:
            color = 4  # red
        else:
            color = 7  # yellow

        out.append(
            "%s \x0300,0%d%s\x0F \x02[\x0F %s vs %s \x02]\x0F %s" % (
                region, color, points, attacker, defender, "-"))
    bot.msg(channel, (", ".join(out)).encode("utf-8"))


def mod_help(bot, nick, host, channel, msg):
    bot.msg(channel, ("Commands: ,info <citizen name> | "
                      ",battles [local] | "
                      ",damage <citizen name> | "
                      ",prod <skill> <wellness> <quality> [high|medium]"
                      ))


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
    wellness_factor = (float(wellness) / 100.0) + 1.0
    emp_factor = 2.0

    return (float(skill) * wellness_factor * region_factor *
            emp_factor) / float(quality)


def mod_prod(bot, nick, host, channel, msg):
    data = bot.vpop.get_productivity(name=" ".join(msg[1:]))
    if "message" in data['user']:
        bot.say(channel, data['user']['message'].encode("utf-8"))
        return

    user = data['user']['name']
    skill = data['user']['highest']['value']
    skill_type = data['user']['highest']['name']
    wellness = data['user']['wellness']
    quality = data['company']['quality']
    company_type = data['company']['type']['name']

    if company_type in ['iron', 'grain', 'fruit', 'wood']:
        region_resource = data['region']['resources'].get(company_type)
        is_high = True if region_resource == "high" else False
    else:
        is_high = False

    current_prod = productivity_formula(skill, wellness, quality, is_high)
    max_prod = productivity_formula(skill, 100, quality, is_high)

    out = ("\x02[\x0F %s's productivity \x02]\x0F: %lf, at 100: %lf | Q%d %s"
           " | %s: %s") % (user, current_prod, max_prod, quality,
                           company_type.title(), skill_type.title(), skill)
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


def mod_reload(bot, nick, host, channel, msg):
    if nick != "CatLand":
        return

    bot._reload_modules()


def mod_time(bot, nick, host, channel, msg):
    now = datetime.utcnow()
    days = (now - datetime(2014, 3, 8)).days
    hour = now.hour
    minute = now.minute
    bot.say(channel, "\x02Day %d\x0F - \x02%d:%d" % (days, hour, minute))


def calculate_vfootball(rank, best_prod, sum_other_prod):
    return float(rank) * 4.0 / 3.0 + float(best_prod) + sum_other_prod / 3.0


def mod_vfootball(bot, nick, host, channel, msg):
    if len(msg) < 2:
        bot.say(channel, "http://vfootball.vpop.pl/")
    else:
        user = bot.vpop.get_user_data(name=" ".join(msg[1:]))
        if "message" in user:
            bot.say(channel, user['message'].encode("utf-8"))
            return

        name = user['name']
        rank = user['military']['rank-level']
        highest_skill = user['highest']['value']
        highest_skill_type = user['highest']['name']

        remaining_sum = 0
        for s in set(["cons", "manu", "land"]) - set([highest_skill_type]):
            remaining_sum += float(user['skills'][s])

        vfootball = calculate_vfootball(rank, highest_skill, remaining_sum)
        bot.say(channel, ("%s's vFootball point: %.2lf" % (
            name, vfootball)).encode("utf-8"))
