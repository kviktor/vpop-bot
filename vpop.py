from datetime import datetime

import requests
from bs4 import BeautifulSoup as bs


class VPop():

    def __init__(self, username="dontbanmepls",
                 password="asd1"):
        self.__login(username, password)
        self.events = self.get_quick_events()

    def __login(self, username="dontbanmepls", password="asd1"):
        self.last_login = datetime.utcnow()
        self.cookies = None
        return None
        login_url = "http://vpopulus.net/auth/login"
        payload = {
            'name': username,
            'password': password,
        }

        headers = {
            'User-Agent': 'fajerfox',
        }

        resp = requests.post(login_url, headers=headers, data=payload,
                             allow_redirects=False)
        self.cookies = resp.cookies
        print "login happened"
        self.last_login = datetime.utcnow()

    def __get_page(self, page):
        if (datetime.utcnow() - self.last_login).seconds > 300:
            self.__login()

        page = "http://vpopulus.net%s" % page
        resp = requests.get(page, cookies=self.cookies,
                            allow_redirects=False)
        return resp.content

    def get_user_data(self, id):
        content = self.__get_page("/citizen/--%s" % id)
        soup = bs(content)
        container = soup.find("div", id="citizen_content_right")

        if container is None:
            return None

        name = container.find("div", class_="entity_headerBig").text
        strength = container.find("div", id="citizenPage_strength_value").text
        economic = container.find_all("div",
                                      class_="citizenPage_economy_value")
        s = {}
        s['manu'], s['land'], s['const'] = [e.text for e in economic]
        highest = max(s, key=s.get)

        location = container.find("div", id="citizenPage_location_txt")
        country, place = [l.text for l in location.find_all("a")]
        citizenship = container.find("div", id="citizenPage_citizenship_txt"
                                     ).text
        rank = container.find("div", id="citizenPage_rank_value").text
        rank_id = container.find("div", id="citizenPage_rank_img").find("img")
        rank_id = rank_id['src'].split("/")[-1].replace(".png", "")

        wellness = container.find("div", id="citizenPage_wellness_txt").text
        wellness = wellness.replace("%", "")

        return {
            'strength': strength,
            'skill': highest,
            'skill_value': s[highest],
            'country': country,
            'place': place,
            'citizenship': citizenship,
            'name': name,
            'rank': rank,
            'rank_id': rank_id,
            'wellness': wellness,
        }

    def get_quick_battles(self, type_id=1):
        content = self.__get_page("/battle/getList?typeID=%d&_=2" % type_id)
        soup = bs(content)
        battles = soup.find_all("div", class_="active_battle")
        countries = []
        for b in battles:
            region = b.find(class_="active_battle_region").find("a").text
            b = b.find_all("img")
            c1 = b[0]['src'].split("/")[-1].replace(".png", "").title()
            c2 = b[1]['src'].split("/")[-1].replace(".png", "").title()
            countries.append((c1, c2, region))
        return countries

    def get_detailed_battles(self, country):
        content = self.__get_page("/battle/all?countryID=%s" % country)
        soup = bs(content)
        battles = soup.find_all("div",
                                class_="activewarPage_battleList_holder")
        countries = []
        for b in battles:
            damage = b.find("div", class_="activewarPage_battleList_DP").text
            time = b.find("div", class_="activewarPage_battleList_time").text
            region = b.find("div",
                            class_="activewarPage_battleList_region").text
            cs = b.find_all("img")
            c1 = cs[0]['src'].split("/")[-1].replace(".png", "").title()
            c2 = cs[1]['src'].split("/")[-1].replace(".png", "").title()
            countries.append({
                'region': region,
                'time': time,
                'damage': damage,
                'c1': c1,
                'c2': c2,
            })
        return countries

    def get_quick_events(self, type_id=1):
        content = self.__get_page("/events/getEvents?tabID=%s&_=1" % type_id)
        soup = bs(content)
        events = soup.find_all("div", class_="latest_event")

        return [e.find("a", class_="link1").text for e in events]

    def get_new_events(self, type_id=1):
        new_events = self.get_quick_events(type_id)

        if self.events == new_events:
            return None
        else:
            # TODO fix this
            result = [e for e in new_events if e not in self.events]
            self.events = new_events
            return result

if __name__ == "__main__":
    i = VPop()
#    a = i.get_quick_events(1)
#    b = i.get_quick_events(1)
#    print a == b
#    print i.get_new_events()
    print i.get_user_data(1773)
