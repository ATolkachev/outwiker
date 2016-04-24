#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import os.path
import shutil
import glob

from fabric.api import local, lcd, settings

# Supported Ubuntu releases
distribs = ["wily", "trusty"]

# List of the supported plugins
plugins_list = [
    "autorenamer",
    "changepageuid",
    "counter",
    "diagrammer",
    "datagraph",
    "export2html",
    "externaltools",
    "htmlformatter",
    "htmlheads",
    "lightbox",
    "livejournal",
    "pagetypecolor",
    "readingmode",
    "sessions",
    "source",
    "spoiler",
    "statistics",
    "style",
    "thumbgallery",
    "tableofcontents",
    "texequation",
    "updatenotifier",
    "webpage",
]

BUILD_DIR = u'build'
LINUX_BUILD_DIR = os.path.join (BUILD_DIR, u"outwiker_linux")
DEB_SOURCE_BUILD_DIR = os.path.join (BUILD_DIR, 'deb_source')
DEB_BINARY_BUILD_DIR = os.path.join (BUILD_DIR, 'deb_binary')


def _getVersion():
    """
    Return a tuple: (version number, build number)
    """
    # The file with version number
    fname = u"src/version.txt"

    with open (fname) as fp_in:
        lines = fp_in.readlines()

    return (lines[0].strip(), lines[1].strip())


def _getCurrentUbuntuDistribName ():
    with open ('/etc/lsb-release') as fp:
        for line in fp:
            line = line.strip()
            if line.startswith (u'DISTRIB_CODENAME'):
                codename = line.split(u'=')[1].strip()
                return codename


def _getDebSourceDirName():
    """
    Return a folder name for sources for building the deb package
    """
    version = _getVersion()
    return "outwiker-{}+{}".format (version[0], version[1])


def _getOrigName (distname):
    version = _getVersion()
    return "outwiker_{}+{}~{}.orig.tar".format (version[0], version[1], distname)


def _debclean():
    """
    Clean build/<distversion> folder
    """
    dirname = os.path.join (DEB_SOURCE_BUILD_DIR, _getDebSourceDirName())
    if os.path.exists (dirname):
        shutil.rmtree (dirname)


def _source():
    """
    Create a sources folder for building the deb package
    """
    _debclean()

    dirname = os.path.join (DEB_SOURCE_BUILD_DIR, _getDebSourceDirName())
    os.makedirs (dirname)

    local ("rsync -avz * --exclude=.bzr --exclude=distrib --exclude=build --exclude=*.pyc --exclude=*.dll --exclude=*.exe --exclude=src/.ropeproject --exclude=src/test --exclude=src/setup.py --exclude=src/setup_tests.py --exclude=src/profile.py --exclude=src/tests.py --exclude=src/Microsoft.VC90.CRT.manifest --exclude=src/profiles --exclude=src/tools --exclude=doc --exclude=plugins --exclude=profiles --exclude=test --exclude=_update_version_bzr.py --exclude=outwiker_setup.iss --exclude=updateversion --exclude=updateversion.py --exclude=debian_tmp --exclude=Makefile_debbinary --exclude=debian_debbinary {dirname}/".format (dirname=dirname))

    os.rename (os.path.join (dirname, u'Makefile_debsource'),
               os.path.join (dirname, u'Makefile'))

    os.rename (os.path.join (dirname, u'debian_debsource'),
               os.path.join (dirname, u'debian'))


def _orig (distname):
    """
    Create an archive for "original" sources for building the deb package
    distname - Ubuntu release name
    """
    _source()

    origname = _getOrigName(distname)

    with lcd (DEB_SOURCE_BUILD_DIR):
        local ("tar -cvf {} {}".format (origname, _getDebSourceDirName()))

    orig_dirname = os.path.join (DEB_SOURCE_BUILD_DIR, origname)
    local ("gzip -f {}".format (orig_dirname))


def debsource():
    """
    Create files for uploading in PPA (including sources)
    """
    _debuild ("debuild -S -sa --source-option=--include-binaries --source-option=--auto-commit",
              distribs)


def deb():
    """
    Assemble the deb package
    """
    _debuild ("debuild --source-option=--include-binaries --source-option=--auto-commit",
              distribs)


def debsingle():
    """
    Assemble the deb package for the current Ubuntu release
    """
    _debuild ("debuild --source-option=--include-binaries --source-option=--auto-commit",
              [_getCurrentUbuntuDistribName()])


def _debuild (command, distriblist):
    """
    Run command with debuild. The function assembles the deb packages for all releases in distriblist.
    """
    current_distrib_name = _getCurrentUbuntuDistribName()
    for distrib_name in distriblist:
        _orig(distrib_name)
        current_debian_dirname = os.path.join (DEB_SOURCE_BUILD_DIR,
                                               _getDebSourceDirName(),
                                               'debian')

        # Change release name in the changelog file
        changelog_path = os.path.join (current_debian_dirname, u'changelog')
        _makechangelog (changelog_path, current_distrib_name, distrib_name)

        with lcd (current_debian_dirname):
            local (command)

        # Return the source release name
        _makechangelog (changelog_path, distrib_name, current_distrib_name)


def ppaunstable ():
    """
    Upload the current OutWiker version in PPA (unstable)
    """
    version = _getVersion()

    for distname in distribs:
        with lcd (DEB_SOURCE_BUILD_DIR):
            local ("dput ppa:outwiker-team/unstable outwiker_{}+{}~{}_source.changes".format (version[0], version[1], distname))


# def ppastable ():
#     """
#     Upload the current OutWiker version in PPA (unstable)
#     """
#     version = _getVersion()
#
#     for distname in distribs:
#         with lcd (DEB_SOURCE_BUILD_DIR):
#             local ("dput ppa:outwiker-team/ppa outwiker_{}+{}~{}_source.changes".format (version[0], version[1], distname))


def plugins():
    """
    Create an archive with plugins (7z required)
    """
    _remove (u"build/plugins/outwiker-plugins-all.zip")

    for plugin in plugins_list:
        _remove (u"build/plugins/{}.zip".format (plugin))

        with lcd ("plugins/{}".format (plugin)):
            local ("7z a -r -aoa -xr!*.pyc -xr!.ropeproject ../../build/plugins/{}.zip ./*".format (plugin))
            local ("7z a -r -aoa -xr!*.pyc -xr!.ropeproject -w../ ../../build/plugins/outwiker-plugins-all.zip ./*".format (plugin))


def source ():
    """
    Create the sources archives.
    """
    version = _getVersion()

    sourcesdir = os.path.join ("build", "sources")

    if not os.path.exists (sourcesdir):
        os.makedirs (sourcesdir)

    fullfname = u"outwiker-src-full.zip"
    srcfname = u"outwiker-src-min.zip"

    _remove (fullfname)
    _remove (srcfname)

    local ('git archive --prefix=outwiker-{}.{}/ -o "{}/{}" HEAD'.format (version[0], version[1], sourcesdir, fullfname))

    with lcd ("src"):
        local ("7z a -r -aoa -xr!*.pyc -xr!.ropeproject -xr!tests.py -xr!profile.py -xr!setup_tests.py -xr!setup.py -xr!test -xr!profiles ../{}/{} ./*".format (sourcesdir, srcfname))


def win (skipinstaller=False):
    """
    Assemble builds under Windows
    """
    build_dir = u'build'
    src_pluginsdir = u"plugins"
    pluginsdir = os.path.join ("src", "plugins")
    win_build_dir = os.path.join (build_dir, u"outwiker_win")
    build_pluginsdir = os.path.join (win_build_dir, u'plugins')

    # Create the plugins folder (it is not appened to the git repository)
    _remove (pluginsdir)
    os.mkdir (pluginsdir)

    # Build by cx_Freeze
    with lcd ("src"):
        local ("python setup.py build --build-exe ../{}".format (win_build_dir))

    _remove (build_pluginsdir)
    os.mkdir (build_pluginsdir)

    # Remove old versions
    _remove ("build/outwiker_win_unstable.zip")
    _remove ("build/outwiker_win_unstable.7z")

    # Create archive without plugins
    with lcd (win_build_dir):
        local ("7z a ..\outwiker_win_unstable.zip .\* .\plugins -r -aoa")
        local ("7z a ..\outwiker_win_unstable.7z .\* .\plugins -r -aoa")

    # Compile installer
    if not skipinstaller:
        local ("iscc outwiker_setup.iss")

    # Copy plugins to build folder
    for plugin in plugins_list:
        shutil.copytree (
            os.path.join (src_pluginsdir, plugin, plugin),
            os.path.join (build_pluginsdir, plugin),
        )

    # Archive versions with plugins
    with lcd (win_build_dir):
        local ("7z a ..\outwiker_win_unstable_all_plugins.zip .\* .\plugins -r -aoa -xr!*.pyc -xr!.ropeproject")
        local ("7z a ..\outwiker_win_unstable_all_plugins.7z .\* .\plugins -r -aoa -xr!*.pyc -xr!.ropeproject")


def linux (create_archives=True):
    """
    Assemble builds under Linux
    """
    pluginsdir = os.path.join ("src", "plugins")
    build_pluginsdir = os.path.join (LINUX_BUILD_DIR, u'plugins')

    toRemove = [
        os.path.join (LINUX_BUILD_DIR, u'tcl'),
        os.path.join (LINUX_BUILD_DIR, u'tk'),
        os.path.join (LINUX_BUILD_DIR, u'PyQt4.QtCore.so'),
        os.path.join (LINUX_BUILD_DIR, u'PyQt4.QtGui.so'),
        os.path.join (LINUX_BUILD_DIR, u'_tkinter.so'),
    ]

    # Create the plugins folder (it is not appened to the git repository)
    _remove (LINUX_BUILD_DIR)
    _remove (pluginsdir)
    os.mkdir (pluginsdir)

    # Build by cx_Freeze
    with lcd ("src"):
        local ("python setup.py build --build-exe ../{}".format (LINUX_BUILD_DIR))

    map (_remove, toRemove)

    _remove (build_pluginsdir)
    os.mkdir (build_pluginsdir)

    if create_archives:
        # Remove old versions
        _remove (os.path.join (BUILD_DIR, 'outwiker_linux_unstable_x64.7z'))

        # Create archive without plugins
        with lcd (LINUX_BUILD_DIR):
            local ("7z a ../outwiker_linux_unstable_x64.7z ./* ./plugins -r -aoa")


def nextversion():
    """
    Increment a version number (execute under Linux only, incremented the deb package version also)
    """
    # The file with version number
    fname = u"src/version.txt"

    with open (fname) as fp_in:
        lines = fp_in.readlines()

    lines[1] = str (int (lines[1]) + 1) + "\n"

    result = u"".join (lines)

    with open (fname, "w") as fp_out:
        fp_out.write (result)

    local ('dch -v "{}+{}~{}"'.format (lines[0].strip(),
                                       lines[1].strip(),
                                       _getCurrentUbuntuDistribName()))



def debinstall():
    """
    Assemble deb package for current Ubuntu release
    """
    debsingle()

    version = _getVersion()

    with lcd (DEB_SOURCE_BUILD_DIR):
        local ("sudo dpkg -i outwiker_{}+{}~{}_all.deb".format (
            version[0],
            version[1],
            _getCurrentUbuntuDistribName()))


def locale():
    """
    Update the localization file (outwiker.pot)
    """
    with lcd ("src"):
        local (r'find . -iname "*.py" | xargs xgettext -o locale/outwiker.pot')


def localeplugin (pluginname):
    """
    Create or update the localization file for pluginname plug-in
    """
    with lcd (os.path.join ("plugins", pluginname, pluginname)):
        local (r'find . -iname "*.py" | xargs xgettext -o locale/{}.pot'.format (pluginname))


def run ():
    """
    Run OutWiker from sources
    """
    with lcd ("src"):
        local ("python runoutwiker.py")


def test (section=u'', params=u''):
    """
    Run the unit tests
    """
    testdir = u'src'
    files = [fname[len(testdir) + 1:]
             for fname
             in glob.glob (u'{}/tests_*.py'.format (testdir))]
    files.sort()

    with lcd ("src"):
        if section:
            local ("python tests_{}.py {}".format (section, params))
        else:
            with settings (warn_only=True):
                for fname in files:
                    local ("python {}".format (fname, params))


def debbinary ():
    linux(create_archives=False)


def _makechangelog (changelog_path, distrib_src, distrib_new):
    """
    Update the changelog file for current Ubuntu release.
    """
    with open (changelog_path) as fp:
        lines = fp.readlines()

    lines[0] = lines[0].replace (distrib_src, distrib_new)

    with open (changelog_path, "w") as fp:
        fp.write (u"".join (lines))


def _remove (path):
    """
    Remove the fname file if it exists. The function not catch exceptions.
    """
    if os.path.exists (path):
        if os.path.isfile (path):
            os.remove (path)
        elif os.path.isdir (path):
            shutil.rmtree (path)
