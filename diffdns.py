import os
import sys
import re

from dns import zone
from iscpy.iscpy_dns.named_importer_lib import MakeNamedDict

import argparse
from lib.validate import diff_nameservers
from lib.paths import swap_paths


# Add zones that should not be diffed here
black_list = [
]


def diff_zones(ns1, ns2, zone_file, named_path):
    zones = MakeNamedDict(open(zone_file).read())
    for zone_name, zone_meta in zones['orphan_zones'].iteritems():
        if zone_meta['type'] != 'master':
            continue
        if zone_name in black_list:
            continue
        handle_zone(ns1, ns2, zone_name, zone_meta, named_path)


def diff_zone(ns1, ns2, zone_name, zone_file, named_path):
    handle_zone(ns1, ns2, zone_name, {'file': zone_file}, named_path)


def diff_view(ns1, ns2, view_file1, named_path1, named_path2=None,
              view_file2=None):
    if view_file2 and named_path2:
        if diff_view_contents(named_path1, named_path2, view_file1,
                              view_file2):
            print "-- Found differences, not continuing"
            return
    zones = parse_view_config_data(named_path1, view_file1)
    print "Using files under {0} as the datasource.".format(named_path1)
    for zone_name, zone_meta in zones.iteritems():
        if zone_meta['type'] != 'master':
            continue
        if zone_name in black_list:
            continue
        handle_zone(ns1, ns2, zone_name, zone_meta, named_path1)


def diff_view_contents(named_path1, named_path2, view_file1, view_file2):
    zones1 = set(parse_view_config_data(named_path1, view_file1))
    zones2 = set(parse_view_config_data(named_path2, view_file2))

    ldiff = zones1 - zones2
    rdiff = zones2 - zones1

    difference = False

    if ldiff:
        difference = True
        msg = "zones statments that were in {0} but not in {1}:".format(
            view_file1, view_file2
        )
        print '=' * len(msg)
        print msg
        print '=' * len(msg)
        for lz in ldiff:
            print lz

    if rdiff:
        difference = True
        msg = "zones statments that were in {0} but not in {1}:".format(
            view_file2, view_file1
        )
        print '=' * len(msg)
        print msg
        print '=' * len(msg)
        for rz in rdiff:
            print rz

    return difference


def parse_view_config_data(named_path, view_file):
    include_m = re.compile("\s+include\s+['\"](\S+)['\"]")
    includes = []
    with open(view_file) as fd:
        for line in fd:
            m = include_m.match(line)
            if m:
                path = m.groups()[0]
                includes.append(swap_fpaths(path))

    zones = {}
    for conf_file in includes:
        parsed = parse_config_data(named_path, conf_file)
        zones.update(parsed)
    return zones


def swap_fpaths(path):
    for s in swap_paths:
        path = path.replace(*s)
    return path


def parse_config_data(named_path, filepath):
    cwd = os.getcwd()
    os.chdir(named_path)
    zones = MakeNamedDict(open(filepath).read())
    os.chdir(cwd)
    return zones['orphan_zones']


def get_zone_data(zone_name, filepath, dirpath):
    cwd = os.getcwd()
    os.chdir(dirpath)
    mzone = zone.from_file(filepath, zone_name, relativize=False)
    os.chdir(cwd)
    return mzone


def handle_zone(ns1, ns2, zone_name, zone_meta, ZONE_PATH):
    if not zone_meta['file']:
        print "No zone file for {0}".format(zone_name)
        return
    print "== Diffing {0}. ({1})".format(zone_name, zone_meta['file'])
    mzone = get_zone_data(zone_name, zone_meta['file'], ZONE_PATH)
    diff_nameservers(ns1, ns2, zone_name, mzone)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Diff some nameservers')
    parser.add_argument('--ns1', required=True, help="The first nameserver to"
                        " diff", type=str)

    parser.add_argument(
        '--ns1-knows-more', dest='ns1_knows_more', required=False, default=False,
        help="If ns1 is allowed to know more than ns2 add this flag. It will "
        "ignore differences when ns1 sees records that ns2 does not",
        action='store_true'
    )

    parser.add_argument(
        '--ns1-port', dest='ns1_port', required=False, default='53',
        help="The first nameservers DNS port", type=str
    )

    parser.add_argument(
        '--ns1-tcp', dest='ns1_tcp', required=False,
        help="Use tcp for queries to ns1", action='store_true',
        default=False
    )

    parser.add_argument('--ns2', required=True, help="The second nameserver "
                        " to diff")

    parser.add_argument(
        '--ns2-port', dest='ns2_port', required=False, default='53',
        help="The second nameservers DNS port", type=str
    )
    parser.add_argument(
        '--ns2-tcp', dest='ns2_tcp', required=False,
        help="Use tcp for queries to ns2", action='store_true',
        default=False
    )

    parser.add_argument('--file', dest="data_file", help="A single zone file."
                        " Use this option with the --zone option", type=str)

    parser.add_argument(
        '--named-path', dest='named_path1', type=str, required=True,
        help="A full path to where named would be running."
    )

    parser.add_argument(
        '--second-named-path', dest='named_path2', type=str, default=None,
        help="Used to help resolve file paths when --second-view-file is used."
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        '--zones-file', help="A file containing bind zone statements."
    )

    group.add_argument(
        '--zone-name', help="A single zone's name. Use the "
        "--file option to specify where to find it's zone "
        "file."
    )
    group.add_argument(
        '--view-file', dest='view_file1', type=str,
        default=None, help="A full file path to a view file"
    )

    parser.add_argument(
        '--second-view-file', dest='view_file2', type=str,
        default=None, help="An optional file. If both view-file and "
        "second-view-file are provided, their contents will be compared "
        "statically"
    )

    nas = parser.parse_args(sys.argv[1:])

    if nas.zone_name and not nas.data_file:
        print ("When using the --zone-name option you must specify the "
               "zone's file with --file")
        sys.exit(1)

    if nas.view_file2 and not nas.view_file1:
        print "Speciefy view-file when using second-view-file"
        sys.exit(1)

    if nas.view_file2 and not nas.named_path2:
        print "Speciefy second-named-path when using second-view-file"
        sys.exit(1)

    class Nameserver(object):
        def __str__(self):
            return "{0}://{1}:{2}".format(self.proto, self.name, self.port)
        def __repr__(self):
            return str(self)

    def configure_ns(nas, nsname):
        ns = Nameserver()
        setattr(ns, 'name', getattr(nas, nsname))
        setattr(ns, 'port', getattr(nas, nsname + '_port', '53'))
        setattr(ns, 'proto',
            'tcp' if getattr(nas, nsname + '_tcp', False) else 'notcp'
        )
        return ns

    ns1 = configure_ns(nas, 'ns1')
    ns2 = configure_ns(nas, 'ns2')

    if nas.ns1_knows_more:
        ns1.knows_more = True

    if nas.view_file1:
        diff_view(
            ns1, ns2, nas.view_file1, nas.named_path1,
            named_path2=nas.named_path2, view_file2=nas.view_file2
        )
    elif nas.zones_file:
        diff_zones(
            ns1, ns2, nas.zones_file, nas.named_path1,
        )
    elif nas.zone_name:
        diff_zone(
            ns1, ns2, nas.zone_name, nas.data_file, nas.named_path1
        )
    print "Done diffing!"
