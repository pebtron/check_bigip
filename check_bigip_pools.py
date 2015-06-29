#!/usr/bin/env python
"""Nagios check for an F5 LTM pool

Checks an F5 LTM pool for available members. If all members are available then
return OK. If not all members are available then return a WARN. If zero members
are available return CRIT.

Based heavily on:
https://github.com/timoschlueter/check_bigip_pools
http://blog.simiya.com/2013/06/08/python-example-script-snmpwalk-snmpget/
"""

from __future__ import print_function
import argparse
import netsnmp
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


def snmp_query(snmpcmd, oid, method):
    """Query SNMP for a specific OID

    Pass in a list of SNMP options, the OID, and either get or walk and return a
    list of results.
    """
    try:
        session = netsnmp.Session(DestHost=snmpcmd['ipaddress'], Version=snmpcmd['version'], Community=snmpcmd['community'])
        results_objs = netsnmp.VarList(netsnmp.Varbind(oid))
        if method == 'get':
            session.get(results_objs)
        else:
            session.walk(results_objs)

    except Exception as exception_error:
        # Check for errors and print out results
        print('ERROR: Occurred during SNMPget for OID %s from %s: '
              '(%s)') % (oid, snmpcmd['ipaddress'], exception_error)
        sys.exit(2)

    # Crash on error
    if (session.ErrorStr):
        print('ERROR: Occurred during SNMPget for OID %s from %s: '
              '(%s) ErrorNum: %s, ErrorInd: %s') % (
               oid, snmpcmd['ipaddress'], session.ErrorStr,
               session.ErrorNum, session.ErrorInd)
        sys.exit(2)

    return_results = {}
    for result in results_objs:
        return_results[('%s') % (result.iid)] = (result.val)

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

    activeMemberCount = snmp_query(snmpcmd, activeMemberCountOID, 'walk')
    for key in activeMemberCount.keys():
        if key.endswith(poolOID):
            activeMembers = activeMemberCount[key]

    availableMemberCount = snmp_query(snmpcmd, availableMemberCountOID, 'walk')
    for key in availableMemberCount.keys():
        if key.endswith(poolOID):
            availableMembers = availableMemberCount[key]

    poolAvailabilityCount = snmp_query(snmpcmd, poolAvailabilityCountOID, 'walk')
    for key in poolAvailabilityCount.keys():
        if key.endswith(poolOID):
            poolStatus = poolAvailabilityCount[key]

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
