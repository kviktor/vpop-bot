import re
from datetime import datetime
import requests

from settings import API_URL


class VPop():

    def __init__(self):
        events = self.get_events()
        if events:
            self.latest_check = self._event_time_parser(
                events[0]['time'][:-6])

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

    def get_country_data(self, id):
        lookup_by = "id"
        if not id.isdigit():
            lookup_by = "name"
        url = "/feeds/country.json?%s=%s" % (lookup_by, id)
        country_data = self._get_json(url)

        return country_data

    def get_region_data(self, id):
        lookup_by = "id"
        if not id.isdigit():
            lookup_by = "name"
        url = "/feeds/region.json?%s=%s" % (lookup_by, id)
        return self._get_json(url)

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

            new_events.append({
                'title': e['title'],
                'link': e.get("link"),
                'country': self._get_country_id(e['link'])
            })
        self.latest_check = self._event_time_parser(events[0]['time'][:-6])
        return new_events

    def _event_time_parser(self, string):
        return datetime.strptime(string, "%a, %d %b %Y %H:%M:%S")

    def _get_country_id(self, link):
        if "region" in link:
            regex = ".*?([0-9]+)\/$"
            region_id = re.match(regex, link).group(1)
            region = self._get_region(region_id)
            return region['country']['country_id']
        else:
            regex = ".*country/([0-9]+)/.*"
            m = re.match(regex, link)
            return int(m.group(1))


if __name__ == "__main__":
    i = VPop()
