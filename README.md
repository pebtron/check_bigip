# check_bigip
Nagios checks for F5 BIG-IP

A Python port of Timo Schlueter's excellent check_bigip_pools.pl
https://github.com/timoschlueter/check_bigip_pools.

My goal is to eventually create a companion script to check F5 GTM
pools.

## check_bigip_pools.py
Checks an F5 LTM pool for available members. If all members are
available then return OK. If not all members are available then return a
WARN. If zero members are available return CRIT.
