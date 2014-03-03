#!/usr/bin/env python
# Mininet Sample Automatic Testing Test Suite (Prototype)
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

from mininet.topo import Topo
from mininet.node import CPULimitedHost
from mininet.link import TCLink
from mininet.net import Mininet
from mininet.util import dumpNodeConnections
from mininet.node import RemoteController
import os
import subprocess
import signal
import sys
import time
import pwd

from collections import namedtuple
MACPair = namedtuple('MACPair', ['src', 'dst'])
USER='mininet'
HOME='/home/%s' % USER
PYTHONPATH='%s/pyretic:%s/mininet:%s/pox' % (HOME,HOME,HOME)
CMD=[ '%s/pyretic/pyretic.py' % HOME
    , 'pyretic.examples.pyretic_firewall'
    ]

# Topology to be instantiated in Mininet
class QTopo(Topo):
    "Quiet topology: You can only talk to gateway (h1)"

    def __init__(self, n=5, cpu=10, bw=100, delay="5ms", loss=0, maxq=100):
        super(QTopo, self).__init__()
        self.n = n
        self.cpu = cpu
        self.bw = bw
        self.delay = delay
        self.loss = loss
        self.maxq = maxq
        self.create_topology()

    def create_topology(self):
        host_conf = {'cpu': self.cpu}
        link_conf = { 'bw': self.bw
                    , 'delay': self.delay
                    , 'loss': self.loss
                    , 'max_queue_size': self.maxq
                    }

        s1 = self.addSwitch('s1')
        for x in range (1,self.n+1):
            self.addHost("h%d" % x, **host_conf)
        for x in range (1,self.n+1):
            self.addLink("h%d" % x, s1, **link_conf)

def l2_reachable_pairs(hosts):
    pairs = []
    first_arp = True
    for s in hosts:
        for t in hosts:
            if s == t:
                continue
            if first_arp:
                c = 3
                first_arp = False
            else:
                c = 1
            rc = int(s.cmd("arping -c %s %s &>/dev/null; echo $?" % (c,t.IP())))
            pair = MACPair(src=s.MAC(),dst=t.MAC())
            if 0 == rc:
                pairs.append(pair)
                print "%s reachable from %s" % (pair.dst, pair.src)
            else:
                print "%s not reachable from %s" % (pair.dst, pair.src)
    return pairs

def start_controller():
    cpid = os.fork()
    if 0 != cpid:
        time.sleep(1)
        return cpid
    pw = pwd.getpwnam("mininet")
    sys.stdout.flush()
    sys.stderr.flush()
    os.setgid(pw.pw_gid)
    os.setuid(pw.pw_uid)
    env = os.environ.copy()
    env['HOME'] = HOME
    env['LOGNAME'] = USER
    env['PWD'] = HOME
    env['USER'] = USER
    env['PYTHONPATH'] = PYTHONPATH
    os.execve(CMD[0], CMD, env)

def main():
    "Create network and run Buffer Sizing experiment"
    expected = [ MACPair(src='00:00:00:00:00:01', dst='00:00:00:00:00:02')
               , MACPair(src='00:00:00:00:00:02', dst='00:00:00:00:00:01')
               , MACPair(src='00:00:00:00:00:01', dst='00:00:00:00:00:03')
               , MACPair(src='00:00:00:00:00:03', dst='00:00:00:00:00:01')
               , MACPair(src='00:00:00:00:00:01', dst='00:00:00:00:00:04')
               , MACPair(src='00:00:00:00:00:04', dst='00:00:00:00:00:01')
               , MACPair(src='00:00:00:00:00:01', dst='00:00:00:00:00:05')
               , MACPair(src='00:00:00:00:00:05', dst='00:00:00:00:00:01')
               ]
    cpid = start_controller()
    topo = QTopo()
    net = Mininet( topo=topo
                 , controller=RemoteController
                 , host=CPULimitedHost
                 , link=TCLink
                 , autoPinCpus=True
                 , autoSetMacs=True
                 )
    net.start()
    dumpNodeConnections(net.hosts)
    actual = l2_reachable_pairs(net.hosts)
    net.stop()
    os.kill(cpid, signal.SIGINT)
    should_not = list(set(actual) - set(expected))
    should = list(set(expected) - set(actual))
    if 0 != len(should):
        print "\n".join(map( lambda x: "-1: %s should be reachable from %s" %
                             (x.dst, x.src)
                           , should
                           ))
    if 0 != len(should_not):
        print "\n".join(map( lambda x: "-1: %s should not be reachable from %s" %
                             (x.dst, x.src)
                           , should_not
                           ))
    num_hosts = len(net.hosts)
    permutations = num_hosts * (num_hosts - 1)
    correct = permutations - len(should) - len(should_not)
    grade = round(float(correct) / float(permutations) * 100)
    return grade

if __name__ == '__main__':
    sys.exit(int(main()))
