# POX openflow

## Thành viên

| MSSV    | Họ Tên          | Phân công                              |
| ------- | --------------- | -------------------------------------- |
| 1612340 | Nguyễn Văn Linh | tìm hiểu, viết code                    |
| 1612311 | Đoàn Khuê       | tìm hiểu,test, demo, code              |
|         | Võ Ngọc Lâm     | tìm hiểu, test,thiết kế custom mininet |

## Topology

```python
"""Custom topology example

Adding the 'topos' dict with a key/value pair to generate our newly defined
topology enables one to pass in '--topo=mytopo' from the command line.
"""

from mininet.topo import Topo


class MyTopo(Topo):
    "Simple topology example."

    def __init__(self):
        "Create custom topo."

        # Initialize topology
        Topo.__init__(self)

        # Add hosts
        h1 = self.addHost('h1')
        h2 = self.addHost('h2')
        h3 = self.addHost('h3')
        h4 = self.addHost('h4')
        h5 = self.addHost('h5')

        # Add switchs
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')
        s4 = self.addSwitch('s4')
        s5 = self.addSwitch('s5')

        # Add links switch to host
        self.addLink(s1, h1)
        self.addLink(s2, h2)
        self.addLink(s3, h3)
        self.addLink(s4, h4)
        self.addLink(s5, h5)

        # Add links switch to switch
        self.addLink(s1, s2)
        self.addLink(s1, s3)
        self.addLink(s1, s4)
        self.addLink(s2, s4)
        self.addLink(s2, s5)
        self.addLink(s3, s4)
        self.addLink(s4, s5)


topos = {'mytopo': (lambda: MyTopo())}

```

![topology](https://raw.githubusercontent.com/nobabykill/python-project/master/POX%20openflow/images/topology.png)

## Source code

```python
# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A super simple OpenFlow learning switch that installs rules for
each pair of L2 addresses.
"""

# These next two imports are common POX convention
from pox.core import core
import pox.openflow.libopenflow_01 as of


# Even a simple usage of the logger is much nicer than print!
log = core.getLogger()


# This table maps (switch,MAC-addr) pairs to the port on 'switch' at
# which we last saw a packet *from* 'MAC-addr'.
# (In this case, we use a Connection object for the switch.)
table = {}

# broadcasted list
broadcasted_packet = []


# To send out all ports, we can use either of the special ports
# OFPP_FLOOD or OFPP_ALL.  We'd like to just use OFPP_FLOOD,
# but it's not clear if all switches support this, so we make
# it selectable.
all_ports = of.OFPP_FLOOD


# Handle messages the switch has sent us because it has no
# matching rule.
def _handle_PacketIn(event):
    packet = event.parsed
    pl = packet.payload

    # Learn the source
    if (event.connection, packet.src) not in table:
        table[(event.connection, packet.src)] = event.port

    dst_port = table.get((event.connection, packet.dst))

    if dst_port is None:
        # store package info
        # (switchinfo, src MAC, dst MAC, src ip, dst ip, packet type)
        pkt_info = (event.connection, packet.src, packet.dst,
                    pl.protosrc, pl.protodst, packet.type)

        # check if packet already broadcasted or not
        if pkt_info in broadcasted_packet:  # broadcasted packet, drop packet
            msg = of.ofp_packet_out(data=event.ofp)
            msg.actions.append(of.ofp_action_output(port=of.OFPP_NONE))
            event.connection.send(msg)
            return

        # We don't know where the destination is yet.  So, we'll just
        # send the packet out all ports (except the one it came in on!)
        # and hope the destination is out there somewhere. :)
        msg = of.ofp_packet_out(data=event.ofp)
        msg.actions.append(of.ofp_action_output(port=all_ports))
        event.connection.send(msg)
        # add info broadcasted packet to list
        broadcasted_packet.append(pkt_info)
    else:
        # Since we know the switch ports for both the source and dest
        # MACs, we can install rules for both directions.
        msg = of.ofp_flow_mod()
        msg.match.dl_dst = packet.src
        msg.match.dl_src = packet.dst
        msg.actions.append(of.ofp_action_output(port=event.port))
        event.connection.send(msg)

        # This is the packet that just came in -- we want to
        # install the rule and also resend the packet.
        msg = of.ofp_flow_mod()
        msg.data = event.ofp  # Forward the incoming packet
        msg.match.dl_src = packet.src
        msg.match.dl_dst = packet.dst
        msg.actions.append(of.ofp_action_output(port=dst_port))
        event.connection.send(msg)

        log.debug("Installing flow entry for %s %s <-> %s" %
                  (event.connection, packet.src, packet.dst))


def launch(disable_flood=False):
    global all_ports
    if disable_flood:
        all_ports = of.OFPP_ALL

    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)

    log.info("Pair-Learning switch running.")
```

- Dictionary **table** lưu thông tin key-value map (switch, MAC):port của switch, để biết máy nào đang kết nối với port nào của switch
- List **Broadcasted_packet** lưu thông tin các gói tin đã broadcast, nếu packet đã tồn tại trong list, drop packet

## Kết quả thực hiện

## Câu lệnh

- Start openflow controller

```sh
sudo ~/pox/pox.py forwarding.prevent_flood info.packet_dump samples.pretty_log log.level --DEBUG
```

- Start mininet topology

```sh
 sudo mn --custom custom_topology.py --topo mytopo --mac --controller remote --switch ovsh
```

## Tham khảo

- <https://en.wikipedia.org/wiki/OpenFlow>
- <https://www.sdxcentral.com/networking/sdn/definitions/what-is-openflow/>
- <https://openflow.stanford.edu/display/ONL/POX+Wiki.html>
- <https://noxrepo.github.io/pox-doc/html/>
- <http://mininet.org/walkthrough/>
- <https://www.youtube.com/watch?v=H0UPYZg9I6A>
- <https://github.com/mininet/openflow-tutorial/wiki>
