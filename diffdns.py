from dns import zone
from iscpy.iscpy_dns.named_importer_lib import MakeNamedDict

import argparse
from lib.validate import diff_nameservers

import pdb
import os
import sys
import ConfigParser
from gettext import gettext as _, ngettext


# Add zones that should not be diffed here
black_list = (,)



def diff_zones(ns1, ns2, zone_file):
    config = ConfigParser.ConfigParser()
    config.read("diff.config")
    ZONE_PATH = config.get('zonefiles','dir_path')
    zones = MakeNamedDict(open(zone_file).read())
    for zone_name, zone_meta in zones['orphan_zones'].iteritems():
        if zone_name in black_list:
            continue
        handle_zone([ns1, ns2], zone_name, zone_meta, ZONE_PATH)

def diff_zone(ns1, ns2, zone_name, zone_file):
    config = ConfigParser.ConfigParser()
    config.read("diff.config")
    ZONE_PATH = config.get('zonefiles','dir_path')
    handle_zone([ns1, ns2], zone_name, {'file': zone_file}, ZONE_PATH)


def get_zone_data(zone_name, filepath, dirpath):
    cwd = os.getcwd()
    os.chdir(dirpath)
    mzone = zone.from_file(filepath, zone_name, relativize=False)
    os.chdir(cwd)
    return mzone


def handle_zone(nss, zone_name, zone_meta, ZONE_PATH):
    if not zone_meta['file']:
        print "No zone file for {0}".format(zone_name)
        return
    print "== Diffing {0}. ({1})".format(zone_name, zone_meta['file'])
    mzone = get_zone_data(zone_name, zone_meta['file'], ZONE_PATH)
    diff_nameservers(nss, zone_name, mzone)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Diff some nameservers')
    parser.add_argument('--ns1', required=True, help="The first nameserver to"
                        " diff", type=str)

    parser.add_argument('--ns2', required=True, help="The second nameserver "
                        " to diff")

    parser.add_argument('--file', dest="data_file", help="A single zone file."
                        " Use this option with the --zone option", type=str)

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument('--zones-file', help="A file containing bind zone "
                        "statements.")
    group.add_argument('--zone-name', help="A single zone's name. Use the "
                        "--file option to specify where to find it's zone "
                        "file.")

    nas = parser.parse_args(sys.argv[1:])
    print nas

    if nas.zone_name and not nas.data_file:
        print _("When using the --zone-name option you must specify the "
                "zone's file with --file")

    if nas.zones_file:
        diff_zones(nas.ns1, nas.ns2, nas.zones_file)
    elif nas.zone_name:
        diff_zone(nas.ns1, nas.ns2, nas.zone_name, nas.data_file)
