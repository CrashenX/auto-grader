#!/usr/bin/env python

################################################################################
# The Pyretic Project                                                          #
# frenetic-lang.org/pyretic                                                    #
# author: Joshua Reich (jreich@cs.princeton.edu)                               #
# author: Jesse J. Cook (jesse.j.cook@gatech.edu                               #
################################################################################
# Licensed to the Pyretic Project by one or more contributors. See the         #
# NOTICES file distributed with this work for additional information           #
# regarding copyright and ownership. The Pyretic Project licenses this         #
# file to you under the following license.                                     #
#                                                                              #
# Redistribution and use in source and binary forms, with or without           #
# modification, are permitted provided the following conditions are met:       #
# - Redistributions of source code must retain the above copyright             #
#   notice, this list of conditions and the following disclaimer.              #
# - Redistributions in binary form must reproduce the above copyright          #
#   notice, this list of conditions and the following disclaimer in            #
#   the documentation or other materials provided with the distribution.       #
# - The names of the copyright holds and contributors may not be used to       #
#   endorse or promote products derived from this work without specific        #
#   prior written permission.                                                  #
#                                                                              #
# Unless required by applicable law or agreed to in writing, software          #
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT    #
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the     #
# LICENSE file distributed with this work for specific language governing      #
# permissions and limitations under the License.                               #
################################################################################

from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.lib.query import *
import logging

class Switch(DynamicPolicy):
    def __init__(self):
        super(Switch, self).__init__()
        self.forward = flood()
        self.query = packets(limit=1,group_by=['srcmac','switch'])
        self.policy = self.forward + self.query
        self.query.register_callback(self.learn_from_a_packet)

    def learn_from_a_packet(self, pkt):
        self.forward = if_( match(dstmac=pkt['srcmac'], switch=pkt['switch'])
                          , fwd(pkt['inport'])
                          , self.forward
                          )
        self.policy = self.forward + self.query

def main():
    """ Only allow packets to or from '00:00:00:00:00:01' """

    allowed = match(srcmac=EthAddr('00:00:00:00:00:01'))
    allowed = allowed | match(dstmac=EthAddr('00:00:00:00:00:01'))
    allowed = allowed | match(dstmac=EthAddr('ff:ff:ff:ff:ff:ff'))

    return allowed >> Switch()
