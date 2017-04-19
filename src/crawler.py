"""
 Created by waldo on 2/10/17
"""

import csv
import os
import re
import mechanize
import logging
import time
from bs4 import BeautifulSoup
from enum import Enum

__author__ = "waldo"
__project__ = "prj_socialdata_backend"

logger = logging.getLogger(__name__)


class SocialMedia(Enum):
    ALL = 0
    FACEBOOK = 1
    LINKEDIN = 2


class FileFormat(Enum):
    ALL = 0
    CSV = 1
    EXCEL = 2


class Crawler(object):
    def __init__(self):
        self._current_session = None

    def open_session(self, social_media, user_name, password):
        if social_media is SocialMedia.FACEBOOK:
            self._current_session = SocialMedium(user_name, password)  # TODO: Change name SocialMedium man...

    def get_contacts_file(self, profile_id, file_format,
                          file_path='./contacts.csv'):  # TODO Return file handle instead of path
        contact_list = self._current_session.get_contact_list(profile_id)

        return self.list_to_file(contact_list, file_format, file_path)

    def close_session(self):
        self._current_session.logout()

    @staticmethod
    def list_to_file(contact_list, file_format, file_path):
        logger.debug("Converting contact list to file.")

        if file_format == FileFormat.CSV:
            with open(file_path, 'wb') as csvfile:
                file_path = os.path.realpath(csvfile.name)
                csvfile.write(u'\ufeff'.encode('utf8'))
                writer = csv.DictWriter(csvfile, ["name", "profile_id", "uri"])
                writer.writeheader()

                if not contact_list:
                    writer.writerow({"name": "No viewable contacts available.", "profile_id": "", "uri": ""})
                else:
                    for contact in contact_list:
                        writer.writerow({k: v.encode('utf8') for k, v in contact.items()})

                logger.debug("File created.")

            logger.debug("File may or may not be created. Check previous log messages.")

            return file_path


class SocialMedium(object):
    login_url = 'https://www.facebook.com/login.php'
    user_agent = 'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) ' \
                 'Chrome/7.0.517.41 Safari/534.7'

    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password
        self.browser = mechanize.Browser()
        after_login_page = self.login()
        self._extract_login_data(after_login_page)

    def login(self):
        self.browser.set_handle_robots(False)
        cookies = mechanize.CookieJar()
        self.browser.set_cookiejar(cookies)
        self.browser.addheaders = [('User-agent', self.user_agent)]
        self.browser.set_handle_refresh(False)
        self.browser.open(self.login_url).read()  # Login page
        self.browser.select_form(nr=0)  # This is login-password form -> nr = number = 0
        self.browser.form['email'] = self.user_name
        self.browser.form['pass'] = self.password
        response = self.browser.submit()

        return response.read()

    def logout(self):
        self.browser.close()

    def get_contact_list(self, profile_name):
        contact_list = []

        rolodex = Rolodex(self.browser, self.login_id, self.start_time,
                          profile_name)  # TODO: Write Singleton wrapper (Sessiion) for browser instead of passing around. You can put multiple fields in Session, so you don't have to pass them around either

        logger.debug("Building contact list.")

        for page_list in rolodex:
            contact_list.extend(page_list)

        logger.debug("Returning contact list.")

        return contact_list

    def _extract_login_data(self, html):
        pattern = re.compile("\"ACCOUNT_ID\":\"(\d+?)\"")
        match = pattern.search(html)
        if match:
            self.login_id = match.groups()[0]

        pattern = re.compile("\"startTime\":(\d+?),")
        match = pattern.search(html)
        if match:
            self.start_time = match.groups()[0]


class Rolodex(object):
    def __init__(self, browser, login_id, start_time, profile_name):
        logger.debug("Creating rolodex.")

        self.browser = browser
        self.login_id = login_id
        self.start_time = start_time
        self.contact_url = 'https://www.facebook.com/{0}/friends'.format(profile_name)
        self._page_number = 1

        logger.debug("Rolodex created.")

    def __iter__(self):
        return self

    def next(self):
        if self._page_number == 1:
            logger.debug("Getting first page.")

            page = self.browser.open(self.contact_url).read()

            logger.debug("First page retrieved.")

            self.contact_url = self.compose_url_from_html(page)

            logger.debug("Attempt to construct contact URL finished.")

            contacts = self.extract_contacts_from_html(page)

            logger.debug("Attempt to extract contacts. Moving on.")
        else:
            logger.debug("Getting next page.")

            page = self.browser.open(self.contact_url).read().decode('unicode_escape')
            self.contact_url = self.compose_url_from_script(page)
            contacts = self.extract_contacts_from_script(page)

            logger.debug("Next page retrieved.")

        if self.contact_url is None:
            raise StopIteration

        self._page_number += 1
        return contacts

    def compose_url_from_html(self, html):
        soup = BeautifulSoup(html, "lxml")
        selection = soup.find_all('script')
        for script in selection:
            if len(script.contents) > 0:
                pattern = re.compile(
                    "TimelineAppCollection\",\"enableContentLoader\",.*\"pagelet_timeline_app_collection_(.*?)\".*?\},\"(.*?)\"")
                match = pattern.search(script.contents[0])
                if match:
                    profile_id, research_id, number = match.groups()[0].split(':')
                    cursor = match.groups()[1]
                    break
        else:
            logger.info("This profile has no viewable friends.")
            return None

        composed_url = \
            'https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet?' \
            'dpr=1&data=%7B%22collection_token%22%3A%22' \
            '{0}' \
            '%3A' \
            '{1}' \
            '%3A' \
            '{2}' \
            '%22%2C%22cursor%22%3A%22' \
            '{3}' \
            '%3D%22%2C%22tab_key%22%3A%22friends%22%2C%22profile_id%22%3A' \
            '{4}' \
            '%2C%22overview%22%3Afalse%2C%22lst%22%3A%22' \
            '{5}' \
            '%3A' \
            '{6}' \
            '%3A' \
            '{7}' \
            '%22%2C%22ftid%22%3Anull%2C%22order%22%3Anull%2C%22sk%22%3A%22' \
            'friends%22%2C%22importer_state%22%3Anull%7D&' \
            '__user={8}' \
            '&__a=&__dyn=&__af=i0&__req=&__be=-1&__pc=PHASED%3ADEFAULT&__rev=' \
                .format(profile_id, research_id, number, cursor, profile_id, self.login_id, profile_id, self.start_time,
                        self.login_id)

        return composed_url

    def compose_url_from_script(self, script):  # DRY !
        pattern = re.compile(
            "TimelineAppCollection\",\"enableContentLoader\",.*\"pagelet_timeline_app_collection_(.*?)\".*?\},\"(.*?)\"")
        match = pattern.search(script)
        if match:
            profile_id, research_id, number = match.groups()[0].split(':')
            cursor = match.groups()[1]
        else:
            return None

        composed_url = \
            'https://www.facebook.com/ajax/pagelet/generic.php/AllFriendsAppCollectionPagelet?' \
            'dpr=1&data=%7B%22collection_token%22%3A%22' \
            '{0}' \
            '%3A' \
            '{1}' \
            '%3A' \
            '{2}' \
            '%22%2C%22cursor%22%3A%22' \
            '{3}' \
            '%3D%22%2C%22tab_key%22%3A%22friends%22%2C%22profile_id%22%3A' \
            '{4}' \
            '%2C%22overview%22%3Afalse%2C%22lst%22%3A%22' \
            '{5}' \
            '%3A' \
            '{6}' \
            '%3A' \
            '{7}' \
            '%22%2C%22ftid%22%3Anull%2C%22order%22%3Anull%2C%22sk%22%3A%22' \
            'friends%22%2C%22importer_state%22%3Anull%7D&' \
            '__user={8}' \
            '&__a=&__dyn=&__af=i0&__req=&__be=-1&__pc=PHASED%3ADEFAULT&__rev=' \
                .format(profile_id, research_id, number, cursor, profile_id, self.login_id, profile_id, self.start_time,
                        self.login_id)

        return composed_url

    def extract_contacts_from_html(self, html):
        # Debug code for timeout bug TODO
        logger.debug("Attempting to extract contacts from HTML.")
        file_path = '/var/tmp/' + time.strftime("%Y%m%d-%H%M%S") + '.txt'
        logger.debug("File path: '{0}'.".format(file_path))

        with open(file_path, 'w') as html_file:
            html_file.write(html)
            logger.debug("Wrote HTML to file '{0}'.".format(file_path))

        contacts = []
        soup = BeautifulSoup(html, "lxml")
        selection = soup.find_all('code')
        for item in selection:
            if len(item.contents) > 0:
                comment = item.contents[0]
                results = BeautifulSoup(comment, "lxml").find_all('a', {"data-hovercard-prefer-more-content-show": "1",
                                                                        "data-gt": re.compile('.*')}, )
                for elem in results:
                    link = elem.attrs['href'].replace("\\", "")
                    try:  # First try to see if the id is hidden in the url, like https://www.facebook.com/profile.php?id=100005592845863
                        profile_id = re.search(r'profile\.php\?id=(.*?)&', link).group(1)
                    except AttributeError as e:  # Else the id is not a number but a string
                        profile_id = re.search(r'\.facebook\.com/(.*)\?', link).group(1)
                    contacts.append({"name": elem.contents[0], "uri": link, "profile_id": profile_id})

        return contacts

    def extract_contacts_from_script(self, script):
        contacts = []
        pattern = re.compile("payload\":\"(.*)\",\"jsmods\"")
        html = re.findall(pattern, script)
        if len(html) > 0:
            results = BeautifulSoup(html[0], "lxml").find_all('a', {"data-hovercard-prefer-more-content-show": "1",
                                                                    "data-gt": re.compile('.*')})
            for elem in results:
                link = elem.attrs['href'].replace("\\", "")
                try:  # First try to see if the id is hidden in the url, like https://www.facebook.com/profile.php?id=100005592845863
                    profile_id = re.search(r'profile\.php\?id=(.*?)&', link).group(1)
                except AttributeError as e:  # Else the id is not a number but a string
                    profile_id = re.search(r'\.facebook\.com/(.*)\?', link).group(1)
                contacts.append({"name": elem.contents[0], "uri": link, "profile_id": profile_id})

        return contacts
