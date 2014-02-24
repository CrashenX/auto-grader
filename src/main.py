#!/usr/bin/python
# Mininet Automatic Testing Tool (Prototype)
# Copyright (C) 2013 Jesse J. Cook

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import libvirt
import sys
import argparse
import os

def parse_prog_input():
    desc = "Mininet Testing Tool (Prototype)"
    contract = """program contract:
  Requires:
    - The test VM to be defined as a domain in libvirt (for now, mininet VM)
      SEE: https://plus.google.com/+JesseCooks/posts/a7GHgtS6bsT
    - The paths to following be provided and read access granted:
        the code that is to be tested
        the test suite that is to be run against the code
        the guest domain from which the tests will be run
    - The guest domain from which the tests will be run:
        to be reachable via the network from the host
        to have a client listening over the network (for now, ssh on port 22)
        to have sufficent free space on the disk (60%% of allocated suggested)
  Guarantees:
    - A snapshot of the guest will be created
    - The following will be installed on the snapshot of the guest:
        the code that is to be tested (for now, 1 python file)
        the test suite that is to be run (for now, 1 python file)
    - The test suite will be run against the code on the guest
    - The test results will be presented (for now, printed to stdout)
    - The snapshot will be deleted
  """
    frmt = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser( description=desc
                                    , epilog=contract
                                    , formatter_class=frmt
                                    )
    parser.add_argument( '--submission'
                       , dest='code'
                       , default='sample-submission.py'
                       , help='code submission to be tested'
                       )
    parser.add_argument( '--test-suite'
                       , dest='tests'
                       , default='sample-test-suite.py'
                       , help='test suite to test the code submission with'
                       )
    parser.add_argument( '--domain-name'
                       , dest='domain'
                       , default='mininet-test'
                       , help='libvirt domain to test the code submission on'
                       )
    return parser.parse_args()

def setup_test_environment(domain):
    xml = "<domainsnapshot><domain><name>%s</name></domain></domainsnapshot>"
    conn = libvirt.open(None)
    if conn == None:
        print 'Failed to open connection to the hypervisor'
        sys.exit(1)

    try:
        dom0 = conn.lookupByName(domain)
    except:
        print 'Failed to find the main domain'
        sys.exit(1)

    if 1 != dom0.state()[0]:
        dom0.create()
    # verify reachability; use ssh?

    ss = dom0.snapshotCreateXML(xml % domain, 0)
    print ss.getName()

def main():
    args = parse_prog_input()
    setup_test_environment(args.domain)


if __name__ == "__main__":
    main()
