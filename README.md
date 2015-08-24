check-mk plugin for Cisco Digital Optical Monitoring
====================================================


About
-----

This check-mk package monitors the power level states of SFPs with
Cisco DOM (DDM) support.


Install
-------

Download the provided *check-mk package file* `cisco_dom-x.y.mkp` and
install it using *check-mk*'s package manager[1].

[1] https://mathias-kettner.de/checkmk_packaging.html#H1:Installation,%20Update%20and%20Removal

```console
# check_mk -P install cisco_dom-x.y.mkp
```

Setup
-----

This package enumerates *entSensorValueTable*, *entPhysicalTable* and
*entSensorThresholdTable* from *CISCO-ENTITY-SENSOR-MIB*[2] to find
transmit (Tx) and receive (Rx) power sensor levels. Any DOM aware SFP
is detected once reinventoring it.

[2] http://tools.cisco.com/Support/SNMP/do/BrowseMIB.do?local=en&step=2&mibName=CISCO-ENTITY-SENSOR-MIB

Interfaces which are administrative shutdown report (critical) Rx values.
You need to build ignore rules within check_mk to drop those services
since it is not easily possible to detect if an interface is shutdown.
