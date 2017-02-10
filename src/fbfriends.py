"""
 Created by waldo on 2/9/17
"""

import os
import subprocess

import sys

from socialtest import SocialMedium
import csv
import getpass

__author__ = "waldo"
__project__ = "SocialCrawler"


def main():
    os.system('cls' if os.name == 'nt' else 'clear')
    print "v0.1 - 2017"
    print "************************"
    print "*** Facebook Friends ***"
    print "************************\n"

    # email = raw_input("Enter your e-mail or username: ")
    # password = pa = getpass.getpass("Enter your password: ")
    # profile_name = raw_input("Enter the profile ID to search: ")

    email = "waldospek@gmail.com"
    password = "7Donders7"
    profile_name = "sylvia.garcia.marley"

    print "\nThis could take up to a few minutes..."

    facebook = SocialMedium(email, password)
    contacts = facebook.get_contact_list(profile_name)

    with open('../output/friends.csv', 'wb') as csvfile:
        file_path = os.path.dirname(os.path.realpath(csvfile.name))
        csvfile.write(u'\ufeff'.encode('utf8'))
        writer = csv.DictWriter(csvfile, ["name", "uri"])
        writer.writeheader()
        for contact in contacts:
            writer.writerow({k:v.encode('utf8') for k, v in contact.items()})

    print "\nTotal number of friends: {0}.".format(len(contacts))
    print "Location of CSV file: {0}".format(file_path)

    if sys.platform == 'linux2':
        os.system('xdg-open {0} 2>/dev/null'.format(file_path))
    else:
        os.startfile(file_path)

    facebook.logout()


if __name__ == '__main__':
    main()
