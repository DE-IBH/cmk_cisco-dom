#!/usr/bin/python
# -*- encoding: utf-8; py-indent-offset: 4 -*-

# cmk_cisco-dom - check-mk plugin for SNMP-based Cisco Digital-Optical-Monitoring monitoring
#
# Authors:
#   Thomas Liske <liske@ibh.de>
#
# Copyright Holder:
#   2015 - 2016 (C) IBH IT-Service GmbH [http://www.ibh.de/]
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

def perfometer_cisco_dom(row, check_command, perf_data):
    color = { 0: "#a4f", 1: "#ff2", 2: "#f22", 3: "#fa2" }[row["service_state"]]
    return "%.1f dBm" % perf_data[0][1], perfometer_logarithmic(perf_data[0][1] + 20, 20, 2, color)

perfometers["check_mk-cisco_dom"] = perfometer_cisco_dom
