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
%{lua:
if rpm.expand("%{dist}") == "el6" then
  print("BuildRequires: python-argparse\n")
end
}

Requires: java
%{lua:
if rpm.expand("%{dist}") == "el6" then
  print("Requires: net-snmp-subagent\n")
else
  print("Requires: net-snmp-subagent-shell\n")
end
}
Requires: jmxterm
%{lua:
if rpm.expand("%{dist}") == "el6" then
  print("Requires: python-dictconfig\n")
  print("Requires: python-argparse\n")
end
}
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
mkdir %{buildroot}/etc/snmp/subagent/mibs
cp target/*.functions %{buildroot}/etc/snmp/subagent/
cp target/*.txt %{buildroot}/etc/snmp/subagent/mibs
find %{buildroot}/etc/snmp/subagent/mibs >> INSTALLED_FILES

%files -f INSTALLED_FILES
%defattr(-, root, root)

