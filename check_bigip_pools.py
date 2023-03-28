#!/usr/bin/env python3
"""Nagios check for an F5 LTM pool

Checks an F5 LTM pool for available members. If all members are available then
return OK. If not all members are available then return a WARN. If zero members
are available return CRIT.

Based heavily on:
https://github.com/timoschlueter/check_bigip_pools
http://blog.simiya.com/2013/06/08/python-example-script-snmpwalk-snmpget/
"""

from easysnmp import Session
import argparse
import sys


class ParseArgs():
    """Return a list of SNMP-related options

    Parse command line arguments. The self.snmpcmd contains mostly SNMP-related
    options and also the F5 pool we will be checking.
    """
    def __init__(self):
        parser = argparse.ArgumentParser(
            description='Check the status of an LTM pool')
        parser.add_argument('-v', '--version', type=int, required=True,
            help='SNMP version')
        parser.add_argument('-C', '--community', required=True,
            help='SNMPv2 community string')
        parser.add_argument('-i', '--ipaddress', required=True,
            help='ip address or hostname')
        parser.add_argument('-p', '--port', type=int, default=161,
            help='port')
        parser.add_argument('-c', '--critical', type=int, default=0,
            help='Threshold for critical')
        parser.add_argument('-w', '--warning', type=int, default=1,
            help='Threshold for warning')
        parser.add_argument('pool', help='pool to check')
        args = parser.parse_args()

        self.snmpcmd = {}
        self.snmpcmd['version'] = args.version
        if self.snmpcmd['version'] != 2:
            print('ERROR: Only SNMPv2 is supported')
            sys.exit(2)
        self.snmpcmd['community'] = args.community
        self.snmpcmd['ipaddress'] = args.ipaddress
        self.snmpcmd['port'] = args.port
        self.snmpcmd['critical'] = args.critical
        self.snmpcmd['warning'] = args.warning
        self.snmpcmd['pool'] = args.pool


def snmp_query(snmpcmd, oid):
    """Query SNMP for a specific OID

    Pass in a list of SNMP options and the OID
    """
    try:
        session = Session(hostname=snmpcmd['ipaddress'], community=snmpcmd['community'], version=snmpcmd['version'])
        return_results = {}
        return_results = session.walk(oid)

    except Exception as exception_error:
        # Check for errors and print out results
        print('ERROR: Occurred during walk for OID %s from %s: '
              '(%s)') % (oid, snmpcmd['ipaddress'], exception_error)
        sys.exit(2)

    return return_results


def main():
    activeMemberCountOID = '.1.3.6.1.4.1.3375.2.2.5.1.2.1.8'
    availableMemberCountOID = '.1.3.6.1.4.1.3375.2.2.5.1.2.1.23'
    poolAvailabilityCountOID = '.1.3.6.1.4.1.3375.2.2.5.5.2.1.2'
    activeMembers = availableMembers = poolStatus = ''

    snmpcmd = ParseArgs().snmpcmd

    # Sanity check critical and warning
    critical = snmpcmd['critical']
    warning = snmpcmd['warning']
    if critical > warning:
        print("ERROR: critical (%d) > warning (%d)" % (critical, warning))
        sys.exit(3)

    # Translate the pool name to an OID
    pool = snmpcmd['pool']
    poolOID = ''
    for letter in pool:
        poolOID += '.' + str(ord(letter))

    activeMemberCount = snmp_query(snmpcmd, activeMemberCountOID)
    for item in activeMemberCount:
        if item.oid.endswith(poolOID):
            activeMembers = item.value

    availableMemberCount = snmp_query(snmpcmd, availableMemberCountOID)
    for item in availableMemberCount:
        if item.oid.endswith(poolOID):
            availableMembers = item.value

    poolAvailabilityCount = snmp_query(snmpcmd, poolAvailabilityCountOID)
    for item in poolAvailabilityCount:
        if item.oid.endswith(poolOID):
            poolStatus = item.value

    output = '- Pool: ' + pool + ', Active members: ' + activeMembers + \
             '/' + availableMembers + ' | activeMembers=' + activeMembers + \
             ';' + str(warning) + ';' + str(critical) + \
             ' availableMembers=' + availableMembers + ';' + str(warning) + \
             ';' + str(critical)

    if poolStatus == '':
        print("CRITICAL - Can't find pool: %s" % pool)
        sys.exit(2)
    elif int(activeMembers) == int(availableMembers):
        print('OK %s' % output)
        sys.exit(0)
    elif int(activeMembers) <= critical:
        print('CRITICAL %s' % output)
        sys.exit(2)
    elif int(activeMembers) <= warning:
        print('WARNING %s' % output)
        sys.exit(1)
    else:
        print('OK %s' % output)
        sys.exit(0)


if __name__ == '__main__':
    main()
