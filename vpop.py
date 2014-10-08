from datetime import datetime
import requests

from settings import API_URL


class VPop():

    def __init__(self):
        self.latest_check = self._event_time_parser(
            self.get_events()[0]['time'][:-6])

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

    def get_market(self, country, industry, quality):
        url = "/feeds/market.json?country=%s&industry=%s&quality=%s"
        market_data = self._get_json(url % (country, industry, quality))
        return market_data

    def get_events(self):
        events = self._get_json("/feeds/events.json")
        return events[:10]

    def get_new_events(self):
        new_events = []
        events = self.get_events()

        for e in events:
            time = self._event_time_parser(e['time'][:-6])
            if time <= self.latest_check:
                break

            new_events.append(e['title'])
        self.latest_check = self._event_time_parser(events[0]['time'][:-6])
        return new_events

    def _event_time_parser(self, string):
        return datetime.strptime(string, "%a, %d %b %Y %H:%M:%S")

if __name__ == "__main__":
    i = VPop()
