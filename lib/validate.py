import subprocess
import os
import itertools
from dns import zone


def resolve(name, ns, ns_port='53', proto='tcp', rdclass="all"):
    command = ["dig", "+" + ns.proto, "-p", ns.port, "@{0}".format(ns.name), name, rdclass, "+short"]
    proc = subprocess.Popen(
        command,
        stdout=subprocess.PIPE
    )
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


def check_rdtype(zone, ns1, ns2, rdtype):
    for (name, ttl, rdata) in zone.iterate_rdatas(rdtype):
        name = name.to_text()
        results = []
        for ns in [ns1, ns2]:
            res = resolve(name, ns, rdclass=rdtype)
            if res.strip('\n').find("unused") != -1:
                continue
            results.append(res.lower())
        if ns1.knows_more and results[0] and not results[1]:
            continue
        if len(set(results)) > 1:  # set() removes duplicates
            print "------------------------------------"
            print "Found differences for {0} {1}:".format(rdtype, name)

            for ns, result in itertools.izip([ns1, ns2], results):
                print "{0} returned:\n-->\n{1}\n<--".format(
                    ns, result.strip('\n')
                )


def diff_nameservers(ns1, ns2, zone_name, mzone):
    if zone_name.endswith('in-addr.arpa'):
        # Don't check for MX's
        rdtypes = ["A", "AAAA", "CNAME", "NS", "SRV", "TXT", "PTR"]
    else:
        rdtypes = ["A", "AAAA", "CNAME", "NS", "MX", "SRV", "TXT", "PTR"]
    for rdtype in rdtypes:
        check_rdtype(mzone, ns1, ns2, rdtype)
