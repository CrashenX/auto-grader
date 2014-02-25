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

import argparse
import libvirt
import os
import paramiko
import socket
import sys
from collections import namedtuple

Environment = namedtuple('Environment', ['dom_name', 'ss_name'])

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

def ssh_connect( hostname="mininet"
               , port=22
               , username="mininet"
               , keyfile="~/.ssh/id_rsa"
               ):
    try:
        ssh = paramiko.SSHClient()
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect( hostname = hostname
                   , port = port
                   , username = username
                   , key_filename = os.path.expanduser(keyfile)
                   )
    except Exception, e:
        print "Connection to host '%s' failed (%s)" % (hostname, str(e))
        sys.exit(1)
    return ssh


def is_client_up( hostname="mininet"
                , port=22
                ):
    up = False
    ssh = ssh_connect(hostname=hostname, port=port)
    (stdin, stdout, stderr) = ssh.exec_command("mn --version")
    chan = stdout.channel
    if 0 == chan.recv_exit_status():
        up = True
    chan.close()
    ssh.close()
    return up

def setup_test_env(domain):
    xml = "<domainsnapshot><domain><name>%s</name></domain></domainsnapshot>"
    conn = libvirt.open(None)
    if conn == None:
        print "Failed to open connection to the hypervisor"
        sys.exit(1)
    try:
        dom = conn.lookupByName(domain)
    except:
        print "Failed to find domain '%s'" % domain
        sys.exit(1)
    if libvirt.VIR_DOMAIN_SHUTOFF == dom.state()[0]:
        print "Domain is shutdown; starting '%s'" % domain
        try:
            dom.create()
        except:
            print "Failed to start domain (%s)" % domain
            sys.exit(1)
    state = dom.state()[0]
    if libvirt.VIR_DOMAIN_RUNNING != state:
        print 'Domain (%s) in unsupported state (%s)' % (domain, state)
        sys.exit(1)
    if not is_client_up():
        print "Unable to reach client on host '%s'" % hostname
        sys.exit(1)
    try:
        ss = dom.snapshotCreateXML(xml % domain, 0)
    except:
        print "Failed to create snapshot of domain (%s)" % domain
        sys.exit(1)
    conn.close()
    return Environment(dom_name=domain, ss_name=ss.getName())

def teardown_test_env(env):
    conn = libvirt.open(None)
    if conn == None:
        print "Failed to open connection to the hypervisor"
        sys.exit(1)
    try:
        dom = conn.lookupByName(env.dom_name)
    except:
        print "Failed to find domain '%s'" % env.dom_name
        sys.exit(1)
    try:
        ss = dom.snapshotLookupByName(env.ss_name)
        ss.delete(0)
    except:
        print "Failed to cleanup snapshot of domain (%s)" % env.dom_name
        sys.exit(1)
    conn.close()

def main():
    args = parse_prog_input()
    env = setup_test_env(args.domain)
    # push code and test suite to VM
    # test code
    # display results
    teardown_test_env(env)

if __name__ == "__main__":
    main()
