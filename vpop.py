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

    def get_productivity(self, name):
        user_data = self.get_user_data(name)

        company_id = user_data['company']['id']
        url = "/feeds/company.json?id=%d" % company_id
        company_data = self._get_json(url)

        region_id = company_data['location']['region']['id']
        url = "/feeds/region.json?id=%d" % region_id
        region_data = self._get_json(url)

        return {
            'user': user_data,
            'company': company_data,
            'region': region_data,
        }

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
