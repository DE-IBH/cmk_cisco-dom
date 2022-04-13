#!/usr/bin/env python3

# cmk_cisco-dom - check-mk plugin for SNMP-based Cisco Digital-Optical-Monitoring monitoring
#
# Authors:
#   Thomas Liske <liske@ibh.de>
#
# Copyright Holder:
#   2015 - 2022 (C) IBH IT-Service GmbH [http://www.ibh.de/]
#
# License:
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 2 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this package; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#

import re
from typing import NamedTuple, List, Mapping, Any
from .agent_based_api.v1 import exists, register, Result, Service, SNMPTree, State, OIDEnd, Metric
from .agent_based_api.v1.type_defs import CheckResult, StringTable, InventoryResult


class SNMPInfo(NamedTuple):
    sidx: str
    stype: str
    sprecis: str
    svalue: str
    sstatus: str
    spower: int
    name: str
    stresh: list


CISDOM_SNMP_RELS = {'1': '<', '2': '≤', '3': '>', '4': '≥', '5': '=', '6': '≠'}
CISDOM_DEV_WARN = 1.0
CISDOM_DEV_CRIT = 2.0


# filter thresholds from SNMP values for a given sensor index
def filter_thresh_cisdom(sidx, sthresh):
    return [t for t in sthresh if t[0].startswith(f"{sidx}.")]


# get performance thresholds
def get_thresh_fmt(severities, precision, thresholds):
    for severity in severities:
        threshold_range = [None, None]
        for threshold_oid, threshold_severity, threshold_relation, threshold_value, threshold_triggered in thresholds:
            if threshold_severity in severity:
                if threshold_relation in ['1', '2']:
                    threshold_range[0] = float('{:.{}f}'.format(int(threshold_value) * 10 ** (-1 * int(precision)), precision))
                elif threshold_relation in ['3', '4']:
                    threshold_range[1] = float('{:.{}f}'.format(int(threshold_value) * 10 ** (-1 * int(precision)), precision))
        if not threshold_range[0] and not threshold_range[1]:
            continue
        else:
            return threshold_range[0], threshold_range[1]
    return None, None


# get worst threshold trigger
def get_thresh_trigger(precision, thresholds):
    severity = None
    threshold = None
    for threshold_oid, threshold_severity, threshold_relation, threshold_value, threshold_triggered in thresholds:
        if threshold_triggered == '1' and (severity == None or severity < int(threshold_severity)):
            severity = int(threshold_severity)
            threshold = (CISDOM_SNMP_RELS[threshold_relation] + "%." + str(precision) + "f dBm") % (int(threshold_value) * 10 ** (-1 * int(precision)))

    # critical
    if severity in [20, 30]:
        return State.CRIT, threshold

    # warning
    if severity in [10]:
        return State.WARN, threshold

    # unknown
    if severity:
        return State.UNKNOWN, threshold

    return State.OK, ''


def parse_cisco_dom(string_table: List[StringTable]) -> List[SNMPInfo]:
    snmp_data_list = []
    name_dict = dict(string_table[1])
    for sidx, stype, sprecis, svalue, sstatus in string_table[0]:
        snmp_data = SNMPInfo(
            sidx=sidx,
            stype=stype,
            sprecis=sprecis,
            svalue=svalue,
            sstatus=sstatus,
            spower=int(svalue) * 10 ** (-1 * int(sprecis)),
            name=re.sub(r' (\w)(ransmit|eceive) ', r' \1x ', name_dict.get(sidx, f"#{sidx}")),
            stresh=filter_thresh_cisdom(sidx, string_table[2])
        )

        snmp_data_list.append(snmp_data)
    return snmp_data_list


register.snmp_section(
    name="cisco_dom",
    parse_function=parse_cisco_dom,
    fetch=[
        # entSensorValueEntry
        SNMPTree(
            base='.1.3.6.1.4.1.9.9.91.1.1.1.1',
            oids=[OIDEnd(), '1', '3', '4', '5']
        ),
        # entPhysicalEntry
        SNMPTree(
            base='.1.3.6.1.2.1.47.1.1.1.1',
            oids=[OIDEnd(), '2'],
        ),
        # entSensorThresholdEntry
        SNMPTree(
            base='.1.3.6.1.4.1.9.9.91.1.2.1.1',
            oids=[OIDEnd(), '2', '3', '4', '5']
        )
    ],
    detect=exists(".1.3.6.1.4.1.9.9.91.1.1.1.1.*")
)


# generate list of valid monitors
def discovery_cisdom(section: SNMPInfo) -> InventoryResult:
    for snmp_info in section:
        if snmp_info.stype == '14' and snmp_info.sstatus == '1':
            if snmp_info.name:
                yield Service(item=snmp_info.name, parameters={"original_power": snmp_info.spower})


# eval service state
def check_cisdom(item, params: Mapping[str, Any], section: List[SNMPInfo]) -> CheckResult:
    for snmp_info in section:
        if item == snmp_info.name:
            deviation = snmp_info.spower - params["original_power"]
            sdescr = f"Power Level {'{:.{}f}'.format(snmp_info.spower, snmp_info.sprecis)} dBm (Δ {'{:.{}f}'.format(deviation, snmp_info.sprecis)} dB)"
            tsever, tstr = get_thresh_trigger(snmp_info.sprecis, snmp_info.stresh)

            if tsever == State.CRIT:
                sdescr += f" - SNMP threshold critical {tstr}"
            elif tsever == State.WARN:
                sdescr += f" - SNMP threshold warning {tstr}"
            elif tsever == State.UNKNOWN:
                sdescr += f" - SNMP threshold other {tstr}"

            dsever = State.OK
            if snmp_info.sstatus != '1':
                sdescr += " - sensor status unknown"
                dsever = State.UNKNOWN
            elif abs(deviation) > CISDOM_DEV_CRIT:
                sdescr += " - deviation critical"
                dsever = State.CRIT
            elif abs(deviation) > CISDOM_DEV_WARN:
                sdescr += " - deviation warning"
                dsever = State.WARN

            if dsever == tsever:
                yield Result(state=tsever, summary=sdescr)
            else:  # check_mk checks for the worst entry
                yield Result(state=tsever, summary=sdescr)
                yield Result(state=dsever, summary=sdescr)

            yield Metric('power_level', snmp_info.spower)
            yield Metric('deviation', deviation, )


register.check_plugin(
    name="cisco_dom",
    service_name="DOM %s",
    discovery_function=discovery_cisdom,
    check_function=check_cisdom,
    check_default_parameters={"original_power": 0.0}
)
