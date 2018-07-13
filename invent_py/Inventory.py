#!/usr/bin/python

import subprocess
import os
import re

IS_DIG_DEC = re.compile(r'\d+\.?\d*')  # Is an integer or decimal


def sudocheck():
    """
    Checks to see if user has sudo privileges
    :return: void
    """

    access = os.getuid()
    if access != 0:
        print('You must run this script as root or under sudo')
        exit(code=1)


def prereqcheck():
    """
    Checks for and installs prerequisites if necessary
    :return:
    """
    prerequisites = ['dmidecode', 'util-linux', 'ethtool', 'usbutils', 'gptfdisk', 'bc']
    for i in range(len(prerequisites)):
        rpm = subprocess.Popen(('rpm', '-qa', '--last'), stdout=subprocess.PIPE)
        try:
            output = subprocess.check_output(('grep', '-iw', prerequisites[i]), stdin=rpm.stdout)
        except Exception as e:
            output = None
        rpm.wait()
        if output is None:
            print('Installing dependency: ' + prerequisites[i])
            # subprocess.run(['zypper', '-n', 'install', prerequisites[i]])
            os.system('zypper -n install ' + prerequisites[i])
        else:
            print('Dependency ' + prerequisites[i] + ' is already satisfied')


def asset():
    return 'ASSET'


def hostname():
    """
    Determines the hostname of the machine via three methods
    :return: Hostname of current machine
    """
    host_a = str(subprocess.check_output(('hostname', '-s'))).rstrip()
    host_b1 = subprocess.Popen(('uname', '-n'), stdout=subprocess.PIPE)
    host_b2 = subprocess.check_output(('sed', 's/[.].*$//'), stdin=host_b1.stdout)
    host_b = str(host_b2).rstrip()
    host_c1 = open('/etc/hostname')
    host_c = host_c1.readline().rstrip()

    if host_a is not None:
        return host_a
    elif host_b is not None:
        return host_b
    elif host_c is not None:
        return host_c
    else:
        return "---"


def pcode():
    return 'PCODE'


def mm():
    return 'MM'


def sdp():
    return 'SDP'


def serialnumber():
    """
    Uses dmidecode to find system serial number
    :return: System serial number
    """
    serial = str(subprocess.check_output(('dmidecode', '-s', 'system-serial-number'))).rstrip()

    if serial is not None:
        if any(c.isalpha() for c in serial):
            return serial
    else:
        return "---"


def makemodel():
    """
    Determines the CPU architecture-type
    :return: Returns the make and model of the CPU
    """
    compinfo = subprocess.Popen(('cat', '/proc/cpuinfo'), stdout=subprocess.PIPE)
    comparch = subprocess.Popen(('grep', '-m', '1', '-i', 'model name'), stdin=compinfo.stdout, stdout=subprocess.PIPE)
    compinfo.stdout.close()
    compmodel = subprocess.check_output(('sed', 's/.*: //'), stdin=comparch.stdout)
    comparch.stdout.close()
    make = str(compmodel).rstrip()

    if make is not None:
        return make
    else:
        return "---"


def vendor():
    """
    Determines the brand of CPU used
    :return: CPU type
    """
    vendorlscpu = subprocess.Popen(('lscpu'), stdout=subprocess.PIPE)
    vendorgrep = subprocess.Popen(('grep', '-i', 'Vendor ID'), stdin=vendorlscpu.stdout, stdout=subprocess.PIPE)
    vendorlscpu.stdout.close()
    vendorsed1 = subprocess.Popen(('sed', 's/.*: //'), stdin=vendorgrep.stdout, stdout=subprocess.PIPE)
    vendorgrep.stdout.close()
    vendorsed2 = subprocess.check_output(('sed', '-e', 's/[ \t]*//'), stdin=vendorsed1.stdout)
    vendorsed1.stdout.close()

    vendorname = str(vendorsed2).rstrip()

    if vendorname == "GenuineIntel":
        return 'Intel'
    elif vendorname == "AuthenticAMD":
        return 'AMD'
    elif vendorname == "":
        return "---"
    else:
        return vendorname


def codename():
    """
    Determines the product name of the actual motherboard/machine that it is used on
    :return: Returns the system's codename
    """
    sysman = str(subprocess.check_output(('dmidecode', '-s', 'system-manufacturer'))).rstrip() + " "
    sysprodname = str(subprocess.check_output(('dmidecode', '-s', 'system-product-name'))).rstrip() + " "
    sysver = str(subprocess.check_output(('dmidecode', '-s', 'system-version'))).rstrip()

    # Checks for incomplete information

    sysinfo = [sysman, sysprodname, sysver]

    for i in range(len(sysinfo)):
        if not any(c.isalpha for c in sysinfo[i]):
            sysinfo[i] = ""

    sysname = sysman + sysprodname + sysver

    if sysname is not None:
        return str(sysname)
    else:
        return "---"


def cpuspeed():
    """
    Determines the maximum speed of the processor
    :return: float that represents cpu speed in GHz
    """
    speeds = []

    # Method 1: lscpu
    lscpulscpu = subprocess.Popen('lscpu', stdout=subprocess.PIPE)
    lscpugrep = subprocess.Popen(('grep', '-i', 'CPU max MHz'), stdin=lscpulscpu.stdout, stdout=subprocess.PIPE)
    lscpulscpu.stdout.close()
    lscpuspeed = str(subprocess.check_output(('sed', 's/.*: //'), stdin=lscpugrep.stdout)).rstrip().lstrip()
    lscpugrep.stdout.close()

    if IS_DIG_DEC.match(str(lscpuspeed)):  # Verifies that the input is an integer or float.
        lscpuspeed = float(lscpuspeed) / 1000
        lscpuspeed = format(lscpuspeed, '.2f')
    else:
        lscpuspeed = "---"
    speeds.append(lscpuspeed)

    # Method 2: dmidecode
    dmidmi = subprocess.Popen('dmidecode', stdout=subprocess.PIPE)
    dmigrep = subprocess.Popen(('grep', '-m', '1', 'Max Speed'), stdin=dmidmi.stdout, stdout=subprocess.PIPE)
    dmidmi.stdout.close()
    dmised = str(subprocess.check_output(('sed', 's/.*: //'), stdin=dmigrep.stdout)).rstrip()
    dmigrep.stdout.close()
    dmispeed = re.sub("[^0-9]", "", dmised)
    dmispeed = float(dmispeed) / 1000
    dmispeed = format(dmispeed, '.2f')
    speeds.append(dmispeed)

    # Method 3.1 cat /sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq:
    syscat = str(subprocess.check_output(('cat', '/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq'))).rstrip()
    if IS_DIG_DEC.match(str(syscat)):
        sysspeed = float(syscat) / 1000000
        sysspeed = format(sysspeed, '.2f')
    else:
        sysspeed = "---"
    speeds.append(sysspeed)

    # Method 3.2 cat/sys/devices/system/cpu/cpu/cpufreq/cpuinfo_max_freq:
    cpucat = str(subprocess.check_output(('cat', '/sys/devices/system/cpu/cpu0/cpufreq/cpuinfo_max_freq'))).rstrip()
    if IS_DIG_DEC.match(str(cpucat)):
        cpuspeed = float(cpucat) / 1000000
        cpuspeed = format(cpuspeed, '.2f')
    else:
        cpuspeed = "---"
    speeds.append(cpuspeed)

    # Take the highest value out of all possible speeds and return it
    filterlist = []
    for i in range(len(speeds)):
        if IS_DIG_DEC.match(str(speeds[i])):
            filterlist.append(speeds[i])

    return max(filterlist)


def sockets():
    pass


def threads():
    pass


def hyperthreading():
    pass


def cpucores():
    pass


def ram():
    pass


def virttech():
    pass


def vtd():
    return 'VTD'


def hap():
    pass


def sriov():
    return 'SRIOV'


def numa():
    pass


def efi():
    pass


def pci():
    return 'PCI'


def pcix():
    return 'PCIX'


def pcie():
    return 'PCIE'


def usb3():
    pass


def networking():
    pass


def ssd():
    pass


def sata():
    pass


def space():
    pass


def boots():
    return 'Y'


def stable():
    pass


def cddvd():
    pass


def sra():
    return 'SRA'


def support():
    pass


sudocheck()
# prereqcheck()
hostname()
serialnumber()
makemodel()
vendor()
codename()
cpuspeed()