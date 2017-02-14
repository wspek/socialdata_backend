"""
 Created by waldo on 2/9/17
"""

import os
import sys
import argparse
import crawler

__author__ = "waldo"
__project__ = "SocialCrawler"


class CommandLineTool(object):
    # overload in the actual subclass
    #
    AP_PROGRAM = sys.argv[0]
    AP_DESCRIPTION = u"Generic Command Line Tool"
    AP_ARGUMENTS = [
        # required args
        # {"name": "foo", "nargs": 1, "type": str, "default": "baz", "help": "Foo help"},
        #
        # optional args
        # {"name": "--bar", "nargs": "?", "type": str,, "default": "foofoofoo", "help": "Bar help"},
        # {"name": "--quiet", "action": "store_true", "help": "Do not output to stdout"},
    ]

    # noinspection PyArgumentList,PyTypeChecker,PyTypeChecker
    def __init__(self):
        self.parser = argparse.ArgumentParser(
            prog=self.AP_PROGRAM,
            description=self.AP_DESCRIPTION,
            formatter_class=lambda prog: argparse.HelpFormatter(prog, width=110, max_help_position=64)
        )
        self.vargs = None

        # Create a dictionary of mutually exclusive groups
        groups = dict()
        for arg in self.AP_ARGUMENTS:
            # Return the mutually exclusive group or 'None' if not present.
            group = arg.pop("group", None)
            if group is not None:
                # If the group name has not been added to the groups dict() yet, add it as a key, with an empty list
                # as value. Otherwise, append the arguments to the already existing groups entry.
                groups.setdefault(group, []).append(arg)
            else:
                self.parser.add_argument(arg.pop("name"), **arg)

        # If there are mutually exclusive groups to be made, we go into this loop
        for group_name, arguments in groups.iteritems():
            group = self.parser.add_mutually_exclusive_group()
            for arg in arguments:
                name = arg.pop("name")
                group.add_argument(name, **arg)

    def run(self):
        self.vargs = vars(self.parser.parse_args())
        self.actual_command()

    # overload this in your actual subclass
    def actual_command(self):
        self.print_stdout(u"This script does nothing. Invoke another .py")


class CrawlerTool(CommandLineTool):
    socialcrawler = crawler.Crawler()

    AP_PROGRAM = u"Friend List"
    AP_DESCRIPTION = u"Retrieves all contacts from a social network"
    AP_ARGUMENTS = [
        {
            "name": "-u",
            "required": True,
            "type": str,
            "default": None,
            "help": "username of the account used to retrieve.",
            "metavar": "USERNAME"
        },
        {
            "name": "-p",
            "required": True,
            "type": str,
            "default": None,
            "help": "password of the account used to retrieve.",
            "metavar": "PASSWORD"
        },
        {
            "name": "-n",
            "required": True,
            "type": str,
            "default": None,
            "help": "social media network.",
            "choices": ["facebook", "linkedin"]
        },
        {
            "name": "--profile",
            "required": True,
            "type": str,
            "default": None,
            "help": "profile ID to retrieve contacts from.",
            "metavar": "PROFILE"
        },
        # {
        #     "name": "--format",
        #     "type": str,
        #     "default": None,
        #     "help": "Output format after conversion",
        #     "choices": ["csv", "xls"]
        # },
    ]

    def actual_command(self):
        print "\nThis could take up to a few minutes..."

        network = None
        if self.vargs['n'] == "facebook":
            network = crawler.SocialMedia.FACEBOOK
        elif self.vargs['n'] == "linkedin":
            network = crawler.SocialMedia.LINKEDIN

        # TODO: Data validation? Or does argparse take care of it already?

        self.socialcrawler.open_session(network, self.vargs["u"], self.vargs["p"])
        contacts_file = self.socialcrawler.get_contacts_file(self.vargs["profile"], crawler.FileFormat.CSV)

        if contacts_file is not None:
            print "Contacts file available at '{0}'.".format(contacts_file)

            if sys.platform == 'linux2':
                os.system('xdg-open {0} 2>/dev/null'.format(os.path.dirname(contacts_file)))
            else:
                os.startfile(os.path.dirname(contacts_file))
        else:
            print "Contacts file could not be created."

        self.socialcrawler.close_session()


def main():
    CrawlerTool().run()


if __name__ == '__main__':
    main()
