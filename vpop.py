import requests
from bs4 import BeautifulSoup as bs


class VPop():

    def __init__(self, username="dontbanmepls",
                 password="asd1"):
        self.__login(username, password)

    def __login(self, username, password):
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

    def __get_page(self, page):
        page = "http://vpopulus.net%s" % page
        resp = requests.get(page, cookies=self.cookies)
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
        return {
            'strength': strength,
            'skill': highest,
            'skill_value': s[highest],
            'country': country,
            'place': place,
            'citizenship': citizenship,
            'name': name,
        }


if __name__ == "__main__":
    i = VPop(1, 2)
    print i.get_user_data(1773)
