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
*entSensorThresholdTable* from *CISCO-ENTITY-SENSOR-MIB* to find
transmit (Tx) and receive (Rx) power sensor levels. Any DOM aware SFP
of a host is detected once reinventoring it.

Interfaces which are administrative shutdown report (critical) Rx values.
You need to build ignore rules within check_mk to drop those services.
