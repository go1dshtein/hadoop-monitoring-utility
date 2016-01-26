.. image:: https://travis-ci.org/go1dshtein/hadoop-monitoring-utility.svg?branch=master

hadoop-monitoring-utility
-------------------------
It is an easiest way to implement SNMP monitoring  over Hadoop cluster.

third party
-----------

**jmxterm** is used to retrieve information from JMX mbeans.
See official `home page <http://wiki.cyclopsgroup.org/jmxterm/>`_.
RPM is available `here <https://github.com/go1dshtein/hadoop-monitoring-utility/releases/tag/0.0.1>`_.

some internals
--------------

The package consists of several parts:
* schema processor and default schema for it
* mib generator
* subagent-shell function and configuration
* cli utility to work with jmxterm

The utility can be used aside from subagent or SNMP. It produces ini-like output parceable with anything:

```
hadoopYarnResourceManagerContainersPending = 18
hadoopImpalaCatalogTcmallocTotalBytesReserved = 95830016
hadoopYarnResourceManagerSchedulerQueuePendingApps.1877334299 = 0
```

Values the utility prodoces are configured through schema. You can find default one in
```monitoring/data/schema```. Default service ports are configured in ```data/monitoring/locator.yml```

