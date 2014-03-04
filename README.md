auto-grader
===========

Problem
-------

The turnaround time on student feedback for coursework is
not yet fast enough to support the scale that Udacity and Georgia
Tech aim to achieve.

If you haven't already, check out my post about this on Google+:
https://plus.google.com/+JesseCooks/posts/8fXD9dHPFxA

Solution
--------

1. Create a sandbox for testing (See: 'Setup the Environment')
2. Develop requirements (the assignment)
3. Develop black box tests for the requirements
4. Give students the requirements (possibly including a deadline)
5. Provide a portal for students to test and submit solutions (e.g. Udacity)

Description
-----------

Prototype automatic grading framework with sample submission
and test-suite for mininet programming problem.

This prototype requires that you have a specific sandbox environment
configured. See the 'Setup the Environment' section for steps to set
up the sandbox. Once you have the environment setup, you can simply
run the following to test:

     cd src/
     ./auto-grader.py

For program usage and code contract run:

     auto-grader.py -h

How It Works
------------

1. Start the VM
2. Create a snapshot
3. Copy the code and test suite onto the guest
4. Run the test suite
5. Capture the output
6. Report the results
7. Revert the VM
8. Delete the snapshot

Q&A
---

Why is prototype focused around Mininet?

1. I needed a use case to test against
2. CS-6250 in the OMS CS program is focused around Mininet
3. It's not a contrived problem (must stand-up Mininet and test network)
4. I can use it to test my homework

Why Python?

1. It seems to be the lingua franca of Udacity and education.
2. It has bindings for the libvirt API
3. I just started using Python for the first time for the OMS CS program and
   wanted to get some experience with it.

Why Libvirt?

1. It's an open-source virtualization API
2. It supports KVM (+ most/all of the other contenders)
3. I have a lot of experience with it

Why KVM?

1. Open-source
2. Supports full and paravirtualization (guest OS can be different than host OS)
3. Fast
4. I have a lot of experience with it

Why Qcow2?

1. Open-source
2. Copy-on-write
3. Internal and external snapshots
4. I have a lot of experience with it

Why not Cucumber or Lettuce?

1. I didn't know Cucumber could be used with Python until I was done
2. I didn't know about Lettuce until I was done
3. A minimal Python script met my requirements for prototyping

Known Issues
------------

1. The auto grader code starts the domain if it isn't running. Occasionally,
   the ssh connection fails if the domain isn't already running.
 * Workaround: Just run `./auto-grader` again
2. The sample-test-suite's scoring lacks sophistication

Setup the Environment
---------------------

1. Get the mininet image:

        mkdir in
        pushd in
        wget https://bitbucket.org/mininet/mininet-vm-images/downloads/mininet-2.1.0-130919-ubuntu-13.04-server-amd64-ovf.zip
        popd

2. Convert the image to a qcow2:

        pushd in
        unzip mininet-2.1.0-130919-ubuntu-13.04-server-amd64-ovf.zip
        popd
        mkdir -p ~/vm/pool/baseline
        virt-convert -D qcow2 in ~/vm/pool/baseline
        chmod 444 ~/vm/pool/baseline/


3. Create an external snapshot:

        mkdir -p ~/vm/pool/snapshots
        pushd ~/vm/pool/snapshots
        qemu-img create -f qcow2 -b ../baseline/mininet-vm-x86_64.qcow2 mininet.qcow2
        popd

4. Define the domain:

        PATH_TO_SS="$HOME/vm/pool/snapshots/mininet.qcow2"
        cat res/mininet-domain.xml | grep 'source file' # view placeholder path
        sed -i -e "s^/path/to/mininet.qcow2^$PATH_TO_SS^" res/mininet-domain.xml
        cat res/mininet-domain.xml | grep 'source file' # verify path is correct
        virsh define res/mininet-domain.xml

5. Configure mininet:

        virsh start mininet
        ip addr show # Review host network settings
        vncviewer :1 # the first boot will take a little time
        ############# Guest Commands #############
        # Login to the guest (login: mininet password: mininet)
        sudo -i # become root
        NET=/etc/network/interfaces
        IP=192.168.10.3 # Set to available ip on your host network
        NETMASK=255.255.255.0 # Set to your networks netmask
        GATEWAY=192.168.10.1 # Set to your networks gateway
        NS=192.168.10.1 # Set to your local recursive nameserver
        echo auto lo > $NET
        echo iface lo inet loopback >> $NET
        echo auto eth0 >> $NET
        echo iface eth0 inet static >> $NET
        echo "    address $IP" >> $NET
        echo "    netmask $NETMASK" >> $NET
        echo "    gateway $GATEWAY" >> $NET
        echo "    dns-nameservers $NS" >> $NET
        cat $NET # Verify file looks correct
        service networking restart
        ssh-keygen -lf /etc/ssh/ssh_host_ecdsa_key.pub
        exit
        exit
        # Close window
        ############# Host  Commands #############
        # Setup networking over wireless "bridge" for guest
        su -c 'src/vm-bridge mininet 192.168.10.3' # Set to guests IP
        su -c 'echo "192.168.10.3   mininet" >> /etc/hosts'
        ssh mininet@mininet # fingerprint should match above if ECDSA
        mkdir ~/.ssh/
        # Couple optional config items:
        #echo 'set editing-mode vi' > ~/.inputrc
        #echo 'set -o vi'|cat - ~/.bashrc > /tmp/out && mv /tmp/out ~/.bashrc
        exit
        scp /home/jesse/.ssh/id_rsa.pub mininet@mininet:~/.ssh/authorized_keys
        ssh mininet@mininet
        sudo apt-get install acpid acpi-support # virsh shutdown support
        sudo apt-get install arping bwm-ng python-matplotlib python-argparse\
        vnc4server libnss3-dev # stuff you will likely need
        exit
        virsh shutdown mininet && watch -n 1 'virsh list --all'
        # ctrl+c after state goes to shut off

6. Create an internal snapshot:

        virsh snapshot-create-as mininet base-config "Mostly networking config"

7. Configure pyretic:

        virsh start mininet
        ssh mininet@mininet
        # Follow pyretic instructions (skip any Virtual Box / VM export steps):
        #  https://github.com/frenetic-lang/pyretic/wiki/Building-the-Pyretic-VM
        #  N.B., make sure your path changes are persistent
        exit
        virsh shutdown mininet && watch -n 1 'virsh list --all'
        # ctrl+c after state goes to shut off

8. Create an internal snapshot:

        virsh snapshot-create-as mininet pyretic "Pyretic config"

9. Verify everything works:

        pushd src
        auto-grade.py # Should run and score 100%; if not see Known Issues
        popd

10. Cleanup downloaded and intermediate files:

        rm -iv mininet-2.1.0-130919-ubuntu-13.04-server-amd64-ovf.zip
        rm -riv in

