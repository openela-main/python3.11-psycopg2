%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11

# RHEL python3.11: Python 3 and Python 3 debug enabled, both Python 2 builds disabled
%bcond_without python3
%bcond_without python3_debug
%bcond_with    python2
%bcond_with    python2_debug

%bcond_without tests

%global srcname	psycopg2
%global sum	A PostgreSQL database adapter for Python
%global desc	Psycopg is the most popular PostgreSQL adapter for the Python \
programming language. At its core it fully implements the Python DB \
API 2.0 specifications. Several extensions allow access to many of the \
features offered by PostgreSQL.

%global python_runtimes	\\\
	%{?with_python2:python2} \\\
	%{?with_python2_debug:python2-debug} \\\
	%{?with_python3:python%{python3_pkgversion}} \\\
	%{?with_python3_debug:python%{python3_pkgversion}d}

%{!?with_python2:%{!?with_python3:%{error:one python version needed}}}

# Python 2.5+ is not supported by Zope, so it does not exist in
# recent Fedora releases. That's why zope subpackage is disabled.
%global zope 0
%if %zope
%global ZPsycopgDAdir %{_localstatedir}/lib/zope/Products/ZPsycopgDA
%endif


Summary:	%{sum}
Name:     python%{python3_pkgversion}-%{srcname}
Version:	2.9.3
Release:	1%{?dist}
# The exceptions allow linking to OpenSSL and PostgreSQL's libpq
License:	LGPLv3+ with exceptions
Url:	    http://initd.org/psycopg/

Source0:	http://initd.org/psycopg/tarballs/PSYCOPG-2-8/psycopg2-%{version}.tar.gz

%{?with_python2:BuildRequires:	python2-devel python2-setuptools}
%{?with_python3:BuildRequires:	python%{python3_pkgversion}-devel python%{python3_pkgversion}-rpm-macros python%{python3_pkgversion}-setuptools}
%{?with_python2_debug:BuildRequires:	python2-debug}
%{?with_python3_debug:BuildRequires:	python%{python3_pkgversion}-debug}

BuildRequires:	gcc
BuildRequires:	libpq-devel

# For testsuite
%if %{with tests}
BuildRequires:	postgresql-test-rpm-macros
%endif

Conflicts:	python-psycopg2-zope < %{version}

# Remove test 'test_from_tables' for s390 architecture
# from ./tests/test_types_extras.py
Patch0: test_types_extras-2.9.3-test_from_tables.patch

%description
%{desc}


%if %{with python2}
%package -n python2-%{srcname}
%{?python_provide:%python_provide python2-%{srcname}}
Summary: %{sum} 2

%description -n python2-%{srcname}
%{desc}


%package -n python2-%{srcname}-tests
Summary: A testsuite for %sum 2
Requires: python2-%srcname = %version-%release

%description -n python2-%{srcname}-tests
%desc
This sub-package delivers set of tests for the adapter.
%endif


%if %{with python2_debug}
%package -n python2-%{srcname}-debug
Summary: A PostgreSQL database adapter for Python 2 (debug build)
# Require the base package, as we're sharing .py/.pyc files:
Requires:	python2-%{srcname} = %{version}-%{release}
%{?python_provide:%python_provide python2-%{srcname}-debug}

%description -n python2-%{srcname}-debug
This is a build of the psycopg PostgreSQL database adapter for the debug
build of Python 2.
%endif


%if %{with python3}
%package -n python%{python3_pkgversion}-%{srcname}-tests
Summary: A testsuite for %sum 2
Requires: python%{python3_pkgversion}-%{srcname} = %version-%release

%description -n python%{python3_pkgversion}-%{srcname}-tests
%desc
This sub-package delivers set of tests for the adapter.
%endif


%if %{with python3_debug}
%package -n python%{python3_pkgversion}-psycopg2-debug
Summary: A PostgreSQL database adapter for Python 3 (debug build)
# Require base python 3 package, as we're sharing .py/.pyc files:
Requires:	python%{python3_pkgversion}-psycopg2 = %{version}-%{release}

%description -n python%{python3_pkgversion}-%{srcname}-debug
This is a build of the psycopg PostgreSQL database adapter for the debug
build of Python 3.
%endif


%if %zope
%package zope
Summary:	Zope Database Adapter ZPsycopgDA
# The exceptions allow linking to OpenSSL and PostgreSQL's libpq
License:	GPLv2+ with exceptions or ZPLv1.0
Requires:	%{name} = %{version}-%{release}
Requires:	zope

%description zope
Zope Database Adapter for PostgreSQL, called ZPsycopgDA
%endif


%prep
%setup -q -n psycopg2-%{version}

# The patch is applied only for s390 architecture as 
# on other architectures the test works
%ifarch s390x s390
%patch0 -p0
%endif

%build
export CFLAGS=${RPM_OPT_FLAGS} LDFLAGS=${RPM_LD_FLAGS}
for python in %{python_runtimes} ; do
  $python setup.py build
done

%check
%if %{with tests}
export PGTESTS_LOCALE=C.UTF-8
%postgresql_tests_run

export PSYCOPG2_TESTDB=${PGTESTS_DATABASES##*:}
export PSYCOPG2_TESTDB_HOST=$PGHOST
export PSYCOPG2_TESTDB_PORT=$PGPORT

cmd="import tests; tests.unittest.main(defaultTest='tests.test_suite')"

%if %{with python2}
PYTHONPATH=%buildroot%python2_sitearch %__python2 -c "$cmd" --verbose
%endif
%if %{with python3}
PYTHONPATH=%buildroot%python3_sitearch %__python3 -c "$cmd" --verbose
%endif
%endif


%install
export CFLAGS=${RPM_OPT_FLAGS} LDFLAGS=${RPM_LD_FLAGS}
for python in %{python_runtimes} ; do
  $python setup.py install --no-compile --root %{buildroot}
done

# Upstream removed tests from the package so we need to add them manually
%if %{with python2}
cp -r tests/ %{buildroot}%{python2_sitearch}/%{srcname}/tests/
for i in `find %{buildroot}%{python2_sitearch}/%{srcname}/tests/ -iname "*.py"`; do
  sed -i 's|#!/usr/bin/env python|#!/usr/bin/python2|' $i
done
%endif
%if %{with python3}
cp -r tests/ %{buildroot}%{python3_sitearch}/%{srcname}/tests/
for i in `find %{buildroot}%{python3_sitearch}/%{srcname}/tests/ -iname "*.py"`; do
  sed -i 's|#!/usr/bin/env python|#!%{__python3}|' $i
done
%endif

%if %zope
%{__install} -d %{buildroot}%{ZPsycopgDAdir}
%{__cp} -pr ZPsycopgDA/* %{buildroot}%{ZPsycopgDAdir}
%endif

%if %{with python2}
%files -n python2-psycopg2
%license LICENSE
%doc AUTHORS NEWS README.rst
%dir %{python2_sitearch}/psycopg2
%{python2_sitearch}/psycopg2/*.py
%{python2_sitearch}/psycopg2/*.pyc
%{python2_sitearch}/psycopg2/_psycopg.so
%{python2_sitearch}/psycopg2/*.pyo
%{python2_sitearch}/psycopg2-%{version}-py2*.egg-info


%files -n python2-%{srcname}-tests
%{python2_sitearch}/psycopg2/tests
%endif


%if %{with python2_debug}
%files -n python2-%{srcname}-debug
%license LICENSE
%{python2_sitearch}/psycopg2/_psycopg_d.so
%endif


%if %{with python3}
%files -n python%{python3_pkgversion}-psycopg2
%license LICENSE
%doc AUTHORS NEWS README.rst
%dir %{python3_sitearch}/psycopg2
%{python3_sitearch}/psycopg2/*.py
%{python3_sitearch}/psycopg2/_psycopg.cpython-%{python3_version_nodots}[!d]*.so
%dir %{python3_sitearch}/psycopg2/__pycache__
%{python3_sitearch}/psycopg2/__pycache__/*.py{c,o}
%{python3_sitearch}/psycopg2-%{version}-py3*.egg-info


%files -n python%{python3_pkgversion}-%{srcname}-tests
%{python3_sitearch}/psycopg2/tests
%endif


%if %{with python3_debug}
%files -n python%{python3_pkgversion}-psycopg2-debug
%license LICENSE
%{python3_sitearch}/psycopg2/_psycopg.cpython-%{python3_version_nodots}d*.so
%endif


%if %zope
%files zope
%license LICENSE
%dir %{ZPsycopgDAdir}
%{ZPsycopgDAdir}/*.py
%{ZPsycopgDAdir}/*.pyo
%{ZPsycopgDAdir}/*.pyc
%{ZPsycopgDAdir}/dtml/*
%{ZPsycopgDAdir}/icons/*
%endif


%changelog
* Tue Nov 29 2022 Charalampos Stratakis <cstratak@redhat.com> - 2.9.3-1
- Initial package
- Fedora contributions by:
      Bill Nottingham <notting@fedoraproject.org>
      Charalampos Stratakis <cstratak@redhat.com>
      David Malcolm <dmalcolm@redhat.com>
      Dennis Gilmore <dennis@ausil.us>
      Devrim GÜNDÜZ <devrim@fedoraproject.org>
      Filip Januš <fjanus@redhat.com>
      Honza Horak <hhorak@redhat.com>
      Ignacio Vazquez-Abrams <ivazquez@fedoraproject.org>
      Igor Gnatenko <ignatenkobrain@fedoraproject.org>
      Jason Tibbitts <tibbs@math.uh.edu>
      Jesse Keating <jkeating@fedoraproject.org>
      Jozef Mlich <jmlich@redhat.com>
      Lumir Balhar <lbalhar@redhat.com>
      Miro Hrončok <miro@hroncok.cz>
      Ondřej Sloup <ondrej.sloup@protonmail.com>
      Patrik Novotný <panovotn@redhat.com>
      Pavel Raiskup <praiskup@redhat.com>
      Peter Robinson <pbrobinson@fedoraproject.org>
      Petr Kubat <pkubat@redhat.com>
      Slavek Kabrda <bkabrda@redhat.com>
      Todd Zullinger <tmz@fedoraproject.org>
      Tomas Hrnciar <thrnciar@redhat.com>
      Tom Lane <tgl@fedoraproject.org>
