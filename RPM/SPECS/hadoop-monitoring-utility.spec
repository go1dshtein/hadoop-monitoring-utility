Name: hadoop-monitoring-utility
Summary: hadoop cluster monitoring utility
Version: 0.0.1
Release: 1%{dist}
Source0: %{name}-%{version}.tar.gz
License: MIT
Group: Monitoring
BuildRoot:  %{_tmppath}/%{name}-%{version}-%{release}-buildroot
BuildArch: noarch
Vendor: Kirill Goldshtein <goldshtein.kirill@gmail.com>

BuildRequires: python-jinja2
BuildRequires: PyYAML
BuildRequires: python-setuptools

%if "%{?dist}" == ".el6"
BuildRequires: python-dictconfig
BuildRequires: python-argparse
Requires: python-dictconfig
Requires: python-argparse
%endif

Requires: java
Requires: jmxterm
Requires: PyYAML
Requires: python-psutil
Requires: python-requests

%description
Hadoop cluster monitoring utility:
 - service autodiscovery
 - snmp integration (snmp-subagent)
 - human readable output

%prep

%setup -n %{name}-%{version}

%build
python setup.py build
export PYTHONPATH=build/lib
bin/hadoop-monitoring-generate-mibs

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES
mkdir -p %{buildroot}/etc/snmp/subagent-shell/mibs
cp target/subagent-shell-hadoop.functions %{buildroot}/etc/snmp/subagent-shell/
cp target/SUBAGENT-SHELL-HADOOP-MIB.txt %{buildroot}/etc/snmp/subagent-shell/mibs
echo '/etc/snmp/subagent-shell/subagent-shell-hadoop.functions' >> INSTALLED_FILES
echo '/etc/snmp/subagent-shell/mibs/SUBAGENT-SHELL-HADOOP-MIB.txt' >> INSTALLED_FILES

%files -f INSTALLED_FILES
%defattr(-, root, root)

%changelog
* Wed Dec 23 2015  Kirill Goldshtein <goldshtein.kirill@gmail.com> - 0.0.1-1.el6
- initial release
