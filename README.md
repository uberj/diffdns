Diffdns
=======

Given two nameservers and some zone files, do the nameservers respond with the same information when asked about the data in the zone files? This tools does the asking and the comparing.

Requirements:
```
A patched version of iscpy  (see rpm/iscpy-1.0.3-1.noarch.rpm)
A patched version of dnspython (see rpm/dnspython-1.10.0-1.noarch.rpm)
```

Configuring
-----------
There is one option you need to configure in ``diff.config``: the ``dir_path`` parameter. This is the relative path bind uses to resolve ``$INCLUDE`` statements.

Examples:
---------
If you have a file containing BIND ``zone`` statements, you can use this form.
```
python diffdns.py --ns1 dev1.foo.com --ns2 ns1.foo.com --zones-file /path/to/zones/zones.private
```

If you just want to test one zone use this form.
```
python diffdns.py --ns1 dev1.foo.com --ns2 ns1.foo.com --zone-name dc1.foo.com --file ~/path/to/zone/file
```

```
python diffdns.py --ns1 ns1.mozilla.com --ns2 ns2.mozilla.com --named-path ~/var/named/ --view-file ~/var/named/config/view.public --second-named-path ~/testing/var/named/ --second-view-file ~/testing/var/named/config/view.public
```

Tunneling:
----------
Due to views, you will sometimes you need to pretend you are somewhere else when querying a production nameserver. You can do something like:

    ssh -v juber@remote-host.mozilla.com -L 5353:localhost:53

Then use:

    ... --ns2 localhost --ns2-port 5353 --ns2-tcp ...

This changes the port from the default `53` to `5253` and use TCP instead of UDP (TCP is needed because SSH only forwards TCP).
