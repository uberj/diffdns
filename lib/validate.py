import subprocess
import sys
import os
import pdb
import itertools
from dns import zone
from dns.zone import NoSOA


def resolve(name, ns, rdclass="all"):
    proc = subprocess.Popen(["dig", "@{0}".format(ns), name, rdclass,
        "+short"], stdout=subprocess.PIPE)
    x = proc.communicate()[0]
    x = x.split('\n')
    x = '\n'.join(sorted(x))
    return x


def collect_svn_zone(root_domain, zone_path, relative_zone_path):
    cwd = os.getcwd()
    os.chdir(relative_zone_path)
    rzone = zone.from_file(zone_path, root_domain, relativize=False)
    os.chdir(cwd)
    return rzone


def check_rdtype(zone, nss, rdtype):
    for (name, ttl, rdata) in zone.iterate_rdatas(rdtype):
        name = name.to_text()
        results = []
        for ns in nss:
            res = resolve(name, ns, rdclass=rdtype)
            if res.strip('\n').find("unused") != -1:
                continue
            results.append(res)
        if len(set(results)) > 1:  # set() removes duplicates
            print "------------------------------------"
            print "Found differences for {0} {1}:".format(rdtype, name)

            for ns, result in itertools.izip(nss, results):
                print "{0} returned:\n-->\n{1}\n<--".format(ns,
                        result.strip('\n'))


def diff_nameservers(nss, zone_name, mzone):
    if zone_name.endswith('in-addr.arpa'):
        # Don't check for MX's
        rdtypes = ["A", "AAAA", "CNAME", "NS", "SRV", "TXT", "PTR"]
    else:
        rdtypes = ["A", "AAAA", "CNAME", "NS", "MX", "SRV", "TXT", "PTR"]
    for rdtype in rdtypes:
        check_rdtype(mzone, nss, rdtype)
