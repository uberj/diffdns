# Since this tool doesn't chroot and named does, we must be smart about file
# paths. The tuple 'swap_paths' contains tuples that will have the left side
# swaped with the right side.
# I.E:
# If swap_paths contained ('/foo/bar/', '/baz/bar'), any path encounered by the
# script would have any occurences of '/foo/bar/' swapped with '/baz/bar/'
swap_paths = (
    ('/var/run/named/', ''),
    ('/var/named/', ''),
)
