import requests
from bs4 import BeautifulSoup as bs

from settings import API_URL


class VPop():

    def __init__(self):
        pass
        # self.events = self.get_quick_events()

    def _get_json(self, page):
        page = API_URL + page
        resp = requests.get(page, allow_redirects=False)
        return resp.json()

    def get_user_data(self, name):
        url = "/feeds/citizen.json?name=%s" % name

        user_data = self._get_json(url)

        if "message" not in user_data:
            highest = max(user_data['skills'], key=user_data['skills'].get)
            user_data['highest'] = {
                'name': highest,
                'value': user_data['skills'][highest]
            }

        return user_data

    def get_battles(self):
        battles = self._get_json("/feeds/active-battles.json")
        return battles

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
