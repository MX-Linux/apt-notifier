#! /usr/bin/python3
# -*- coding: utf-8 -*-

BUILD_VERSION='24.09.01'
MODULES = "/usr/lib/apt-notifier/modules"

import subprocess
import sys
if MODULES not in sys.path:
    sys.path.append(MODULES)

import os
import dbus
import pwd
import tempfile
from os import environ

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from shutil import which
from time import sleep
from string import Template # for simple string substitution (popup_msg...)

import datetime

import gettext
gettext.bindtextdomain('apt-notifier', '/usr/share/locale')
gettext.textdomain('apt-notifier')

_ = gettext.gettext

ngettext = gettext.ngettext

HOME   = os.environ['HOME']
UID    = os.getuid()
UNAME  = pwd.getpwuid(UID)[0]

NOTIFICATION_DISMISS_CHECK = "apt-notifier-dismiss"
#-----------------------------------------------------------------------
# notification dismiss check: don't notify if restart through dbus-callback
try:
    runtime_dir = os.environ['XDG_RUNTIME_DIR']
except KeyError:
    runtime_dir = f"/run/user/{UID}"

if os.path.isdir(runtime_dir):
    DISMISS_CHECK = f"{runtime_dir}/{NOTIFICATION_DISMISS_CHECK}.chk"
else:
    DISMISS_CHECK = f"/tmp/{NOTIFICATION_DISMISS_CHECK}-{UNAME}.chk"


def set_package_manager():
    global package_manager
    global package_manager_enabled
    global package_manager_name
    global package_manager_exec
    global package_manager_path
    global show_package_manager
    global show_muon
    global show_synaptic
    global show_package_manager_help
    global package_manager_available
    global Package_Manager_Help
    global Upgrade_using_package_manager

    try:
        show_package_manager
    except:
        show_package_manager = False

    try: package_manager_path
    except:
         package_manager_path = ''

    #if show_package_manager and package_manager_path:
    #    return
    global conf
    try: conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()

    global xlate
    try: xlate
    except NameError:
        from aptnotifier_xlate import AptNotifierXlate
        xlate = AptNotifierXlate()

    show_muon = conf.config['show_muon']
    show_synaptic = conf.config['show_synaptic']
    # allowed package manger
    default_list =  "synaptic, muon"
    default_list =  default_list.replace(',', ' ').split()
    # get list from config settings
    preference_list = conf.get('package_manager_preference_list')
    preference_list = preference_list.replace(',', ' ').split()
    # accept only default_list entries
    check_list = [ x.lower() for x in preference_list if x in default_list ]

    from shutil import which

    # check available and preferred package manager
    for pm in check_list:
        if pm == 'synaptic':
            show_package_manager = conf.config['show_synaptic']
            show_package_manager_help = conf.get('show_synaptic_help')
            debug_p(f"find package_manager: {pm}")
            path = which("synaptic-pkexec")
            if path:
                package_manager = "synaptic"
                package_manager_exec = "synaptic-pkexec"
                package_manager_name = "Synaptic"
                package_manager_path = path
                package_manager_available = True
                package_manager_enabled = True
                debug_p(f"found package_manager: {package_manager_exec}")
                break

            path = which("synaptic")
            if path:
                package_manager = "synaptic"
                package_manager_exec = "su-to-root -X -c synaptic"
                package_manager_name = "Synaptic"
                package_manager_path = path
                package_manager_available = True
                package_manager_enabled = True
                debug_p(f"found package_manager: {package_manager_exec}")
                break
            else:
                package_manager = ""
                package_manager_exec = ""
                package_manager_name = ""
                package_manager_path = ''
                package_manager_available = False
                package_manager_enabled = False
                debug_p(f"no package_manager found: {pm}")

        if pm == 'muon':
            show_package_manager = conf.config['show_muon']
            show_package_manager_help = conf.get('show_muon_help')
            path = which(pm)
            if path:
                package_manager = "muon"
                package_manager_name = "Muon"
                package_manager_path = path
                package_manager_available = True
                package_manager_enabled = True
                path_pk = which("muon-pkexec")
                if path_pk:
                    package_manager_exec = "muon-pkexec"
                    package_manager_path = path_pk
                elif  which("mx-pkexec"):
                    package_manager_exec = f"mx-pkexec {path}"
                else:
                    package_manager_exec = "su-to-root -X -c muon"
            else:
                package_manager_available = False
                package_manager = ""
                package_manager_exec = ""
                package_manager_name = ""
                package_manager_path = ""
                package_manager_enabled = False

    if not package_manager:
        package_manager_available = False
        package_manager_enabled = False
        show_package_manager = False
        show_package_manager_help = False
        print("Info: No package manager found! Disable packagemanager actions")


    if package_manager_enabled or show_package_manager_help:
        Package_Manager_Help                        = xlate.get('package_manager_help')
        Package_Manager_Help = Package_Manager_Help.replace("Synaptic", package_manager_name)
        Upgrade_using_package_manager = Upgrade_using_package_manager.replace('Synaptic', package_manager_name)

    #left_click_package_manager                  = xlate.get('left_click_package_manager')

    if package_manager_name:
        xlate.left_click_package_manager = package_manager_name

def package_manager_is_available():
    from shutil import which
    if which('synaptic') or  which('muon'):
        return True
    else:
        False

def set_globals():
    global Updater_Name
    global Package_Installer
    global tooltip_0_updates_available
    global tooltip_1_new_update_available
    global tooltip_multiple_new_updates_available
    global popup_title
    global popup_msg_1_new_update_available
    global popup_msg_multiple_new_updates_available
    global View_and_Upgrade
    global Hide_until_updates_available
    global Quit_Apt_Notifier
    global Restart_Apt_Notifier
    global Apt_Notifier_Help
    global Upgrade_using_package_manager
    global Apt_Notifier_Preferences
    global Apt_History
    global Apt_History
    global View_Auto_Updates_Logs
    global View_Auto_Updates_Dpkg_Logs
    global Check_for_Updates
    global Force_Check_Counter
    Force_Check_Counter = 0
    global About
    global Check_for_Updates_by_User
    Check_for_Updates_by_User = False
    global ignoreClick
    ignoreClick = '0'
    global WatchedFilesAndDirsHashNow
    WatchedFilesAndDirsHashNow = ''
    global WatchedFilesAndDirsHashPrevious
    WatchedFilesAndDirsHashPrevious = ''
    global AvailableUpdates
    AvailableUpdates = ''
    global Reload
    global notification
    notification = None
    global check_for_updates_interval
    global check_for_updates_force_counter
    global unattended_upgrades
    global debug_p

    # check version_at_start
    global version_at_start
    version_at_start = version_installed()
    global rc_file_name
    rc_file_name = os.getenv('HOME') + '/.config/apt-notifierrc'

    global message_status
    message_status = "not displayed"
    global notification_icon
    notification_icon = "apt-notifier"

    global xlate
    try: xlate
    except NameError:
        from aptnotifier_xlate import AptNotifierXlate
        xlate = AptNotifierXlate()

    Updater_Name                                = xlate.get('updater_name')
    Apt_Notifier_Help                           = xlate.get('apt_notifier_help')
    Package_Installer                           = xlate.get('mx_package_installer')
    tooltip_0_updates_available                 = xlate.get('tooltip_0_updates_available')
    tooltip_0_updates_available                 = xlate.get('tooltip_0_updates_available')
    tooltip_1_new_update_available              = xlate.get('tooltip_1_new_update_available')
    tooltip_multiple_new_updates_available      = xlate.get('tooltip_multiple_new_updates_available')
    popup_title                                 = xlate.get('popup_title')
    popup_msg_1_new_update_available            = xlate.get('popup_msg_1_new_update_available')
    popup_msg_multiple_new_updates_available    = xlate.get('popup_msg_multiple_new_updates_available')
    Upgrade_using_package_manager               = xlate.get('upgrade_using_package_manager')
    View_and_Upgrade                            = xlate.get("view_and_upgrade")
    Hide_until_updates_available                = xlate.get("hide_until_updates_available")
    Quit_Apt_Notifier                           = xlate.get("quit_apt_notifier")
    Restart_Apt_Notifier                        = xlate.get("restart_apt_notifier")
    Apt_Notifier_Preferences                    = xlate.get("apt_notifier_preferences")
    Apt_History                                 = xlate.get("apt_history")
    View_Auto_Updates_Logs                      = xlate.get("view_auto_updates_logs")
    View_Auto_Updates_Dpkg_Logs                 = xlate.get("view_auto_updates_dpkg_logs")
    Check_for_Updates                           = xlate.get("check_for_updates")
    About                                       = xlate.get("about")
    Reload                                      = xlate.get("reload")
    unattended_upgrades                         = xlate.get("unattended_upgrades")

    global conf
    try: conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()

    check_for_updates_interval        = conf.get('check_for_updates_interval')
    check_for_updates_force_counter   = conf.get('check_for_updates_force_counter')

    if check_for_updates_interval is None:
        check_for_updates_interval        = 60
    check_for_updates_interval = int(check_for_updates_interval)
    if check_for_updates_interval < 15:
        check_for_updates_interval = 15
    elif check_for_updates_interval > 21600:
        check_for_updates_interval = 21600

    if check_for_updates_force_counter is None:
        check_for_updates_force_counter   = 720
    check_for_updates_force_counter = int(check_for_updates_force_counter)

    if check_for_updates_force_counter == 0:
        # disabled
        pass
    elif check_for_updates_force_counter > 720:
        check_for_updates_force_counter = 720
    elif check_for_updates_force_counter < 5:
        check_for_updates_force_counter = 5

    global show_apt_notifier_help
    show_apt_notifier_help = conf.get('show_apt_notifier_help')

    from aptnotifier_rc import AptNotifierRC
    apt_notifier_rc = AptNotifierRC()

    # UseNotifier
    global UseNotifier
    global use_dbus_notifications

    debug_p("set_globals():  if conf.get('use_dbus_notifications') == True:")
    debug_p(f"set_globals(): if {conf.get('use_dbus_notifications')} == True:")

    if conf.get('use_dbus_notifications') == True:
        use_dbus_notifications = True
        UseNotifier = 'dbus'
    else:
        use_dbus_notifications = False
        UseNotifier = 'qt'

    debug_p("set_globals(): if apt_notifier_rc.use_dbus_notifications == True:")
    debug_p(f"set_globals():if {apt_notifier_rc.use_dbus_notifications} == True:")
    if apt_notifier_rc.use_dbus_notifications == True:
        UseNotifier = 'dbus'
        use_dbus_notifications = True
    elif apt_notifier_rc.use_dbus_notifications == False:
        UseNotifier = 'qt'
        use_dbus_notifications = False
    debug_p(f"set_globals(): UseNotifier: {UseNotifier}")
    debug_p(f"set_globals(): use_dbus_notifications: {use_dbus_notifications}")
    notification_icon = conf.get('notify_icon')

# Check for updates, using subprocess.Popen
def check_updates():
    global check_for_updates_interval
    global check_for_updates_force_counter
    global check_updates_last_run
    global message_status
    global AvailableUpdates

    global AvailableUpdatesPrevious
    try: AvailableUpdatesPrevious
    except: AvailableUpdatesPrevious=""

    global unattatended_upgrade_last
    try:
        unattatended_upgrade_last
    except:
        unattatended_upgrade_last = unattended_upgrade_enabled()

    if unattatended_upgrade_last == unattended_upgrade_enabled():
        unattatended_upgrade_changed = False
    else:
        unattatended_upgrade_changed = True
    unattatended_upgrade_last = unattended_upgrade_enabled()

    global package_manager_path
    global show_package_manager

    global WatchedFilesAndDirsHashNow
    global WatchedFilesAndDirsHashPrevious
    global Check_for_Updates_by_User
    global Force_Check_Counter
    global AptIcon
    #global tool_tip
    #tool_tip = ''
    global version_at_start

    import datetime
    now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    import time
    # seconds since epoch
    check_updates_now_run = int(time.time())

    try:
        check_updates_last_run
    except NameError:
        check_updates_last_run = check_updates_now_run - check_for_updates_interval - 2

    delta = check_updates_now_run - check_updates_last_run
    debug_p(f"delta = {check_updates_now_run} - {check_updates_last_run} by User {Check_for_Updates_by_User}")

    debug_p(f"check_updates at {now} rep {check_for_updates_interval} last: {delta}")
    if delta >=  check_for_updates_interval or unattatended_upgrade_changed:
        short_run = False
        check_updates_last_run = check_updates_now_run
    else:
        short_run = True

    if Check_for_Updates_by_User:
        short_run = False
        check_updates_last_run = check_updates_now_run

    debug_p(f"short_run : {short_run}")

    now = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    debug_p(f"Start check_updates by user {Check_for_Updates_by_User} with {AvailableUpdates} updates at {now}")

    """ restart apt-notifier if another version have beeen installed
    """
    if  version_at_start != version_installed():
        restart_apt_notifier()

    """
    Don't bother checking for updates when /var/lib/apt/periodic/update-stamp
    isn't present. This should only happen in a Live session before the repository
    lists have been loaded for the first time.
    """
    update_stamp = os.path.isfile('/var/lib/apt/periodic/update-stamp')
    lock = os.path.isfile('/var/lib/apt/lists/lock')
    if not update_stamp and not lock:
        return

    """
    Get a hash of files and directories we are watching
    """
    WatchedFilesAndDirsHashNow = get_stat_hash_of_watched_files_and_dirs()
    """
    If
        no changes in hash of files and directories being watched since last checked
            AND
        the call to check_updates wasn't initiated by user
    then don't bother checking for updates.
    """
    debug_p(f"Hash: {WatchedFilesAndDirsHashNow} == {WatchedFilesAndDirsHashPrevious}")
    if WatchedFilesAndDirsHashNow == WatchedFilesAndDirsHashPrevious:
        hash_changed = False
        if not Check_for_Updates_by_User:
            if Force_Check_Counter < check_for_updates_force_counter and check_for_updates_force_counter != 0:
                Force_Check_Counter = Force_Check_Counter + 1
                if AvailableUpdates == '':
                    AvailableUpdates = '0'
                Check_for_Updates_by_User = False
                return
    else:
        hash_changed = True

    WatchedFilesAndDirsHashPrevious = WatchedFilesAndDirsHashNow

    """
    Don't bother checking for updates if processes for other package management tools
    appear to be runninng. For unattended-upgrade, use '/usr/bin/unattended-upgrade'
    to avoid getting a hit on /usr/share/unattended-upgrades/unattended-upgrade-shutdown
    which appears to be started automatically when using systemd as init.
    """
    if apt_dpkg_is_locked():
        Force_Check_Counter = check_for_updates_force_counter
        Check_for_Updates_by_User = False
        return

    if Check_for_Updates_by_User or hash_changed:
        short_run = False

    Force_Check_Counter = 1

    from aptnotifier_apt import Apt
    apt = Apt()

    # Suppress 'updates available' notification
    # if Unattended-Upgrades are enabled
    # AND apt-get upgrade & dist-upgrade output are the same

    debug_p(f"unattended_upgrade_enabled(): {unattended_upgrade_enabled()}")
    if unattended_upgrade_enabled():
        if not short_run:
            AvailableUpdates = apt.available_updates(['-d','-u']).split(':')
            if AvailableUpdates[0] == AvailableUpdates[1]:
                AvailableUpdates  = 0
            elif AvailableUpdates[2] == 'dist-upgrade':
                AvailableUpdates  = AvailableUpdates[0]
            else:
                AvailableUpdates  = AvailableUpdates[1]
    else:
        if not short_run:
            AvailableUpdates = apt.available_updates(['-c'])
    AvailableUpdates = str(AvailableUpdates)

    debug_p(f"check_updates AvailableUpdates {AvailableUpdates}")
    debug_p(f"check_updates AvailableUpdates {AvailableUpdatesPrevious} -> {AvailableUpdates}")
    package_manager_changed = False
    if package_manager_path and show_package_manager and not os.path.exists(package_manager_path):
        debug_p(f"[455] set_package_manager(): {package_manager_path}")
        package_manager_changed = True
    elif not package_manager_path and ( show_muon or show_synaptic) and package_manager_is_available():
        debug_p(f"[457] set_package_manager(): {package_manager_path}")
        package_manager_changed = True

    """
    elif AvailableUpdates == AvailableUpdatesPrevious:
        # don't  change icon and tooltip if previous availables have not changed
        # or available updates are still avaialble
        AvailableUpdatesPrevious = AvailableUpdates
        return
    elif AvailableUpdates != "0" and AvailableUpdatesPrevious != "0" and AvailableUpdatesPrevious != "":
        AvailableUpdatesPrevious = AvailableUpdates
        return
    """

    # Alter both Icon and Tooltip, depending on updates available or not
    if AvailableUpdates == "":
        AvailableUpdates = "0"

    if AvailableUpdates == "0":
        debug_p(f'if AvailableUpdates == "0":')
        message_status = "not displayed"  # Resets flag once there are no more updates
        add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            if unattended_upgrade_enabled():

                #tool_tip = unattended_upgrades
                debug_p(f"AptIcon.setToolTip(tool_tip): AptIcon.setToolTip('{unattended_upgrades}')")
                AptIcon.setToolTip(unattended_upgrades)
            else:
                #tool_tip = tooltip_0_updates_available
                AptIcon.setToolTip(tooltip_msg(0))
    else:
        set_icon_show()
        if AvailableUpdates == "1" and ( AvailableUpdates != AvailableUpdatesPrevious or  package_manager_changed):
            debug_p(f'if AvailableUpdates == "1":')
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            #tool_tip = tooltip_1_new_update_available
            AptIcon.setToolTip(tooltip_msg(1))
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before
            if message_status == "not displayed":
                """
                cmd = "for WID in $(wmctrl -l | cut -d' ' -f1); do xprop -id $WID | grep 'NET_WM_STATE(ATOM)'; done | grep -sq _NET_WM_STATE_FULLSCREEN"
                run = subprocess.run(cmd, shell=True)
                if run.returncode == 1:
                """
                if not fullscreen():
                    show_popup(popup_title, popup_msg(1), notification_icon)
                    message_status = "displayed"
                """
                    UseNotifier = use_notifier()
                    #print( "UseNotifier:" + UseNotifier)
                    if UseNotifier.startswith("qt"):
                        def show_message():
                            AptIcon.showMessage(popup_title, popup_msg_1_new_update_available)
                        Timer.singleShot(1000, show_message)
                    else:
                        desktop_notification(popup_title, popup_msg_1_new_update_available, notification_icon)
                """
        #elif AvailableUpdates != AvailableUpdatesPrevious or package_manager_changed:
        else:
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            #tooltip_template=Template(tooltip_multiple_new_updates_available)
            #tooltip_with_count = tooltip_template.substitute(count=AvailableUpdates)
            #tool_tip = tooltip_with_count
            AptIcon.setToolTip(tooltip_msg(AvailableUpdates))
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before
            if message_status == "not displayed":
                """
                cmd = "for WID in $(wmctrl -l | cut -d' ' -f1); do xprop -id $WID | grep 'NET_WM_STATE(ATOM)'; done | grep -sq _NET_WM_STATE_FULLSCREEN"
                run = subprocess.run(cmd, shell=True)
                if run.returncode == 1:
                """
                if not fullscreen():
                    # ~~~ Localize 1b ~~~
                    # Use embedded count placeholder.
                    #popup_template=Template(popup_msg_multiple_new_updates_available)
                    #popup_with_count=popup_template.substitute(count=AvailableUpdates)
                    show_popup(popup_title, popup_msg(AvailableUpdates), notification_icon)
                    message_status = "displayed"
    AvailableUpdatesPrevious = AvailableUpdates
    Check_for_Updates_by_User = False

def run_with_restart(prog_exec=None):
    global AptIcon
    global Timer
    global version_at_start
    from subprocess import run, DEVNULL, Popen
    from time import sleep
    if not prog_exec:
        return False
    ret =''
    if run_in_plasma():
        restart = "ionice -c3 nice -n19 /usr/bin/python3 /usr/lib/apt-notifier/modules/apt-notifier.py & disown -h"
        cmd = prog_exec + ';' + restart
        run = Popen(cmd, shell=True, executable="/bin/bash")
        AptIcon.hide()
        from time import sleep
        sleep(1);
        sys.exit(0)
    else:
        cmd = "sudo -k"
        run(cmd.split())
        cmd = prog_exec
        ret = run(cmd.split()).returncode
    if  version_at_start != version_installed():
        restart_apt_notifier()
    return ret

def start_package_manager():
    global Check_for_Updates_by_User
    global package_manager_available
    global version_at_start

    cleanup_notifier_run()

    debug_p(f"run_with_restart({package_manager_exec})")
    if not package_manager_available:
        return

    ret = run_with_restart(package_manager_exec)

    if ret == 0:
        Check_for_Updates_by_User = True
        debug_p("check_updates()")
        check_updates()

def start_viewandupgrade(action=None):
    notification_close()
    global Check_for_Updates_by_User

    cleanup_notifier_run()

    systray_icon_hide()
    initialize_aptnotifier_prefs()

    from subprocess import run, PIPE
    global conf
    try: conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()

    from aptnotifier_rc import AptNotifierRC
    apt_notifier_rc = AptNotifierRC()

    from aptnotifier_viewandupgrade import ViewAndUpgrade
    view_and_upgrade = ViewAndUpgrade()

    systray_icon_hide()
    while True:
        view_and_upgrade.yad
        returncode = view_and_upgrade.yad_returncode
        if returncode not in [ 0, 8]:
            break
        else:
            apt_notifier_rc.upgrade_assume_yes = view_and_upgrade.upgrade_assume_yes
            apt_notifier_rc.upgrade_auto_close = view_and_upgrade.upgrade_auto_close
            apt_notifier_rc.update

        # reload
        if returncode == 8:
            run('/usr/lib/apt-notifier/bin/updater_reload_run')
            view_and_upgrade.apt_list_run

        # upgrade
        if returncode == 0:

            cmd = '/usr/lib/apt-notifier/bin/updater_upgrade_run'
            """
            pmd = "pgrep -x plasmashell >/dev/null && exit 1 || exit 0"
            running_in_plasma = subprocess.run(pmd, shell=True).returncode
            if  running_in_plasma: # and action is None:
                cmd = "( /usr/lib/apt-notifier/bin/updater_upgrade_run; apt-notifier-unhide-Icon; )& disown -h >/dev/null 2>/dev/null"
                subprocess.Popen(cmd, shell=True, executable="/bin/bash")
                AptIcon.hide()
                sleep(2)
                sys.exit(1)
            else:
            """
            run(cmd)
            if  version_at_start != version_installed():
                restart_apt_notifier()

            break

    Check_for_Updates_by_User = True
    systray_icon_show()
    debug_p(f"start_viewandupgrade : check_updates()")
    check_updates()

def initialize_aptnotifier_prefs():

    """Create/initialize preferences in the ~/.config/apt-notifierrc file  """
    """if they don't already exist. Remove multiple entries and those that """
    """appear to be invalid.                                               """
    global conf
    global icon_look
    global wireframe_transparent
    global tray_icon_noupdates
    global tray_icon_newupdates
    global use_dbus_notifications
    global window_icon
    global window_icon_kde

    from aptnotifier_rc import AptNotifierRC

    apt_notifier_rc = AptNotifierRC()

    try: conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()

    icon_look = apt_notifier_rc.icon_look
    wireframe_transparent = apt_notifier_rc.wireframe_transparent

    window_icon = conf.config['window_icon']
    window_icon_kde = conf.config['window_icon_kde']

    if icon_look == 'classic':
        tray_icon_newupdates = conf.config['classic_some']
        tray_icon_noupdates  = conf.config['classic_none']
    elif icon_look == 'pulse':
        tray_icon_newupdates = conf.config['pulse_some']
        tray_icon_noupdates  = conf.config['pulse_none']
    elif icon_look == 'wireframe-dark':
        tray_icon_newupdates = conf.config['wireframe_some']
        if  wireframe_transparent:
            tray_icon_noupdates = conf.config['wireframe_none_dark_transparent']
        else:
            tray_icon_noupdates = conf.config['wireframe_none_dark']
    elif icon_look == 'wireframe-light':
        tray_icon_newupdates = conf.config['wireframe_some']
        if  wireframe_transparent:
            tray_icon_noupdates = conf.config['wireframe_none_light_transparent']
        else:
            tray_icon_noupdates = conf.config['wireframe_none_light']
    else:
        # fallback
        tray_icon_newupdates = conf.config['wireframe_some']
        tray_icon_noupdates = conf.config['wireframe_none_dark']

def aptnotifier_prefs():
    notification_close()

    global Check_for_Updates_by_User
    global package_manager

    systray_icon_hide()

    initialize_aptnotifier_prefs()
    global use_dbus_notifications
    debug_p(f"*** use_dbus_notifications={use_dbus_notifications}")

    sys.path.append("/usr/lib/apt-notifier/modules")
    from aptnotifier_autostart import AutoStart
    from aptnotifier_autoupdate import UnattendedUpgrade
    from aptnotifier_form import Form
    from aptnotifier_rc import AptNotifierRC


    start = AutoStart()
    debug_p(f"form = Form() : {package_manager}")

    form = Form()

    if not package_manager_available:
        form.show_left_click_behaviour_frame = False

    form.left_click_package_manager = package_manager

    apt_notifier_rc = AptNotifierRC()

    global autoupdate
    try:
        autoupdate
    except NameError:
        autoupdate = UnattendedUpgrade()

    global conf
    try:
        conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()

    conf_use_dbus_notifications  = conf.get('use_dbus_notifications')
    rc_use_dbus_notifications    = apt_notifier_rc.use_dbus_notifications
    show_switch_desktop_notifications = conf.get('show_switch_desktop_notifications')
    if rc_use_dbus_notifications in [ True, False ]:
        use_dbus_notifications = rc_use_dbus_notifications
    else:
        use_dbus_notifications = conf_use_dbus_notifications

    if show_switch_desktop_notifications:
        form.use_dbus_notifications = use_dbus_notifications

    form.icon_look                = apt_notifier_rc.icon_look
    form.left_click               = apt_notifier_rc.left_click
    form.upgrade_assume_yes       = apt_notifier_rc.upgrade_assume_yes
    form.upgrade_auto_close       = apt_notifier_rc.upgrade_auto_close
    form.upgrade_type             = apt_notifier_rc.upgrade_type
    form.wireframe_transparent    = apt_notifier_rc.wireframe_transparent

    form.autostart                = start.autostart
    form.autoupdate               = autoupdate.unattended_upgrade

    debug_p("form.use_dbus_notifications   = apt_notifier_rc.use_dbus_notifications")
    debug_p(f"{form.use_dbus_notifications}   = {apt_notifier_rc.use_dbus_notifications}")

    form.fill_form()

    debug_p("form.form_token")
    debug_p(f"{form.form_token}")
    debug_p(f"{form.form}")

    form.dialog()

    apt_notifier_rc.icon_look                = form.icon_look
    apt_notifier_rc.left_click               = form.left_click
    apt_notifier_rc.upgrade_assume_yes       = form.upgrade_assume_yes
    apt_notifier_rc.upgrade_auto_close       = form.upgrade_auto_close
    apt_notifier_rc.upgrade_type             = form.upgrade_type
    apt_notifier_rc.wireframe_transparent    = form.wireframe_transparent
    debug_p("form.use_dbus_notifications   = apt_notifier_rc.use_dbus_notifications")
    debug_p(f"{form.use_dbus_notifications}   = {apt_notifier_rc.use_dbus_notifications}")

    debug_p("form.use_dbus_notifications   = apt_notifier_rc.use_dbus_notifications")
    debug_p(f"{form.use_dbus_notifications}   = {apt_notifier_rc.use_dbus_notifications}")

    if show_switch_desktop_notifications:
        if form.use_dbus_notifications in [ True, False ]:
            if not form.use_dbus_notifications == use_dbus_notifications:
                apt_notifier_rc.use_dbus_notifications = form.use_dbus_notifications
                use_dbus_notifications = form.use_dbus_notifications

    apt_notifier_rc.update

    start.autostart  = form.autostart
    autoupdate.autoupdate = form.autoupdate

    global icon_look
    global wireframe_transparent

    icon_look = apt_notifier_rc.icon_look
    wireframe_transparent = apt_notifier_rc.wireframe_transparent

    global tray_icon_noupdates
    global tray_icon_newupdates

    if icon_look == "classic":
        tray_icon_newupdates =  conf.get('classic_some')
        tray_icon_noupdates  =  conf.get('classic_none')
    elif icon_look == "pulse":
        tray_icon_newupdates =  conf.get('pulse_some')
        tray_icon_noupdates  =  conf.get('pulse_none')
    elif icon_look == "wireframe-light":
        tray_icon_newupdates =  conf.get('wireframe_some')
        if wireframe_transparent:
            tray_icon_noupdates  = conf.get('wireframe_none_light_transparent')
        else:
            tray_icon_noupdates  = conf.get('wireframe_none_light')
    else:
        #icon_look == "wireframe-dark":
        tray_icon_newupdates =  conf.get('wireframe_some')
        if wireframe_transparent:
            tray_icon_noupdates  = conf.get('wireframe_none_dark_transparent')
        else:
            tray_icon_noupdates  = conf.get('wireframe_none_dark')

    set_QIcons()

    global AptIcon
    global AvailableUpdates
    global NoUpdatesIcon
    if AvailableUpdates == "0":
        AptIcon.setIcon(NoUpdatesIcon)
    else:
        AptIcon.setIcon(NewUpdatesIcon)
    AptIcon.show()
    add_rightclick_actions()

    Check_for_Updates_by_User = True
    systray_icon_show()


def apt_history():
    notification_close()
    systray_icon_hide()
    global apt
    try: apt
    except NameError:
        from aptnotifier_apt import Apt
        apt = Apt()

    apt.apt_history()

    systray_icon_show()

def apt_get_update():
    notification_close()
    global Check_for_Updates_by_User
    systray_icon_hide()

    run = subprocess.run([ "/usr/lib/apt-notifier/bin/updater_reload_run" ])

    Check_for_Updates_by_User = True
    systray_icon_show()
    check_updates()

def start_package_installer():
    global Check_for_Updates_by_User
    global version_at_start
    systray_icon_hide()

    cleanup_notifier_run()

    # find usable package installer
    pl = "mx-packageinstaller packageinstaller"
    from shutil import which
    package_installer = list(filter( lambda x: which(x), pl.split()))[0]
    if not package_installer:
        return
    if "mx-packageinstaller" in package_installer:
        cmd = package_installer
    else:
        cmd = f"su-to-root -X -c {package_installer}"
    debug_p(f"start_package_installer(): {cmd}")
    ret = run_with_restart(cmd)
    debug_p(f"start_package_installer(): run_with_restart{cmd}: {ret}")

    if  version_at_start != version_installed():
        restart_apt_notifier()
        sleep(2)

    if ret == 0:
        Check_for_Updates_by_User = True
        debug_p("check_updates()")
        check_updates()
    systray_icon_show()


def re_enable_click():
    global ignoreClick
    ignoreClick = '0'

def start_package_manager0():
    notification_close()
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        start_package_manager()
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

def start_viewandupgrade0():
    notification_close()
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        start_viewandupgrade()
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

def start_package_installer_0():
    notification_close()
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        start_package_installer()
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

# Define the command to run when left clicking on the Tray Icon
def left_click():
    if AvailableUpdates == "0":
        debug_p(f"package_manager_path: '{package_manager_path}'")
        if package_manager_path:
            start_package_manager0()
        else:
            start_package_installer_0()
    else:
        """Test ~/.config/apt-notifierrc for LeftClickViewAndUpgrade"""
        cmd = "grep -sq ^LeftClick=ViewAndUpgrade"
        cmd = cmd.split() + [rc_file_name]
        ret = subprocess.run(cmd).returncode
        if ret == 0:
            start_viewandupgrade0()
        else:
            start_package_manager0()

# Define the action when left clicking on Tray Icon
def left_click_activated(reason):
    if reason == QtWidgets.QSystemTrayIcon.Trigger:
        left_click()

def read_icon_config():
    """Reads ~/.config/apt-notifierrc, returns 'show' if file doesn't exist or does not contain DontShowIcon"""
    cmd = "grep -sq ^[[]DontShowIcon[]]"
    cmd = cmd.split() + [rc_file_name]
    ret = subprocess.run(cmd).returncode
    if ret != 0:
        return "show"

def read_icon_look():
    cmd = "grep -m1 -soP ^IconLook=\K.*"
    cmd = cmd.split() + [rc_file_name]
    run = subprocess.run(cmd, capture_output=True, universal_newlines=True)
    iconLook = run.stdout.strip()
    return iconLook

def set_noicon():
    """Inserts a '[DontShowIcon]' line into  ~/.config/apt-notifierrc."""
    cmd = "sed -i -e '1i[DontShowIcon] "
    cmd+= "#Remove this entry if you want the apt-notify icon to show "
    cmd+= "even when there are no upgrades available' "
    cmd+= "-e '/DontShowIcon/d' "

    cmd = ['sed', '-i', '-e',
        '1i[DontShowIcon] #Remove this entry if you want the apt-notify icon to show even when there are no upgrades available',
        '-e', '/DontShowIcon/d', rc_file_name]
    run = subprocess.run(cmd)
    AptIcon.hide()
    icon_config = "donot show"

def set_icon_show():
    """Remove a '[DontShowIcon]' line into  ~/.config/apt-notifierrc."""
    #cmd = "sed -i -e '/[[]DontShowIcon[]]/d'
    cmd = ['sed', '-i', '-e', '/[[]DontShowIcon[]]/d', rc_file_name]
    run = subprocess.run(cmd)
    global icon_config
    icon_config = "show"

def add_rightclick_actions():
    global show_package_manager
    global package_manager_enabled
    global show_package_manager_help
    global package_manager_path
    global rc_file_name

    from shutil import which
    from subprocess import run, DEVNULL

    set_package_manager()

    ActionsMenu.clear()
    debug_p(f"add_rightclick_actions with {package_manager_path}")
    cmd = f"grep -sq ^LeftClick=ViewAndUpgrade {rc_file_name}"
    cmd = cmd.split()
    ret = run(cmd, stdout=DEVNULL, stderr=DEVNULL).returncode
    if ret == 0:
        ActionsMenu.addAction(View_and_Upgrade).triggered.connect( start_viewandupgrade0 )
        if show_package_manager and package_manager_enabled:
            if package_manager_path:
                ActionsMenu.addSeparator()
                ActionsMenu.addAction(Upgrade_using_package_manager).triggered.connect( start_package_manager0 )
    else:
        if show_package_manager and package_manager_enabled:
            if package_manager_path:
                ActionsMenu.addAction(Upgrade_using_package_manager).triggered.connect( start_package_manager0)
                ActionsMenu.addSeparator()
        ActionsMenu.addAction(View_and_Upgrade).triggered.connect( start_viewandupgrade0 )

    # check we have a package installer
    pl = "mx-packageinstaller packageinstaller"

    package_installer = None
    try:
        package_installer = list(filter( lambda x: which(x), pl.split()))[0]
        if package_installer:
            add_Package_Installer_action()
    except IndexError:
        pass

    add_apt_history_action()

    if unattended_upgrade_enabled():
       add_view_unattended_upgrades_logs_action()
       add_view_unattended_upgrades_dpkg_logs_action()

    add_apt_get_update_action()
    add_apt_notifier_help_action()

    if show_package_manager_help and package_manager_enabled:
        if package_manager_path:
            add_package_manager_help_action()

    add_aptnotifier_prefs_action()
    add_about_action()
    add_restart_action()
    add_quit_action()
    """
    probaly not needed anymore - so for now disabled
    cmd = '[ "$XDG_CURRENT_DESKTOP" = "XFCE" ] && '
    cmd+= 'which deartifact-xfce-systray-icons && '
    cmd+= 'deartifact-xfce-systray-icons 1 &'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    """
def add_hide_action():
    global show_package_manager
    global package_manager_enabled
    global show_package_manager_help
    global package_manager_path
    from shutil import which
    if package_manager_path:
        if not which(package_manager_path):
            set_package_manager()

    ActionsMenu.clear()
    if icon_config == "show":
        hide_action = ActionsMenu.addAction(Hide_until_updates_available)
        hide_action.triggered.connect( set_noicon )
        if package_manager_path:
            if show_package_manager and package_manager_enabled:
                ActionsMenu.addSeparator()
                ActionsMenu.addAction(package_manager_name).triggered.connect( start_package_manager0 )

    # check we have a package installer
    pl = "mx-packageinstaller packageinstaller"
    from shutil import which
    package_installer = None
    try:
        package_installer = list(filter( lambda x: which(x), pl.split()))[0]
        if package_installer:
            add_Package_Installer_action()
    except IndexError:
        pass

    add_apt_history_action()

    if unattended_upgrade_enabled():
        add_view_unattended_upgrades_logs_action()
        add_view_unattended_upgrades_dpkg_logs_action()

    add_apt_get_update_action()
    add_apt_notifier_help_action()
    if package_manager_path:
        if show_package_manager_help and package_manager_enabled:
            add_package_manager_help_action()

    add_aptnotifier_prefs_action()
    add_about_action()
    add_restart_action()
    add_quit_action()
    """
    cmd = '[ "$XDG_CURRENT_DESKTOP" = "XFCE" ] && '
    cmd+= 'which deartifact-xfce-systray-icons && '
    cmd+= 'deartifact-xfce-systray-icons 1 &'
    subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    """

def add_restart_action():
    ActionsMenu.addSeparator()
    restart_action = ActionsMenu.addAction(Restart_Apt_Notifier)
    restart_action.triggered.connect( restart_apt_notifier )

def add_quit_action():
    ActionsMenu.addSeparator()
    quit_action = ActionsMenu.addAction(QuitIcon,Quit_Apt_Notifier)
    quit_action.triggered.connect( close_notifier )

def close_notifier():
    notification_close()
    sys.exit(0)



def add_apt_notifier_help_action():
    global show_apt_notifier_help
    if show_apt_notifier_help:
        ActionsMenu.addSeparator()
        apt_notifier_help_action = ActionsMenu.addAction(HelpIcon,Apt_Notifier_Help)
        apt_notifier_help_action.triggered.connect(open_apt_notifier_help)

def open_apt_notifier_help():
    systray_icon_hide()
    global conf
    try: conf
    except NameError:
        from aptnotifier_config import AptNotifierConfig
        conf = AptNotifierConfig()
    global show_apt_notifier_help
    show_apt_notifier_help = conf.get("show_apt_notifier_help")
    if not show_apt_notifier_help:
        return

    global apt_notifier_help
    try: apt_notifier_help
    except NameError:
        from aptnotifier_help import AptNotifierHelp
        apt_notifier_help = AptNotifierHelp()

    apt_notifier_help.apt_notifier_help()
    systray_icon_show()

def add_package_manager_help_action():
    global show_package_manager_help
    global package_manager
    debug_p(f"add_package_manager_help_action : {package_manager}")
    if show_package_manager_help:
        ActionsMenu.addSeparator()
        package_manager_help_action = ActionsMenu.addAction(HelpIcon,Package_Manager_Help)
        package_manager_help_action.triggered.connect(open_package_manager_help)

def open_package_manager_help():
    global show_package_manager_help
    global package_manager
    if not show_package_manager_help:
        return
    if not package_manager:
        return
    systray_icon_hide()

    global apt_notifier_help
    try: apt_notifier_help
    except NameError:
        from aptnotifier_help import AptNotifierHelp
        apt_notifier_help = AptNotifierHelp()

    apt_notifier_help.open_package_manager_help(package_manager)

    systray_icon_show()

def add_aptnotifier_prefs_action():
    ActionsMenu.addSeparator()
    aptnotifier_prefs_action =  ActionsMenu.addAction(Apt_Notifier_Preferences)
    aptnotifier_prefs_action.triggered.connect( aptnotifier_prefs )

def add_Package_Installer_action():
    ActionsMenu.addSeparator()
    Package_Installer_action =  ActionsMenu.addAction(Package_Installer)
    Package_Installer_action.triggered.connect( start_package_installer_0 )

def add_apt_history_action():
    ActionsMenu.addSeparator()
    apt_history_action =  ActionsMenu.addAction(Apt_History)
    apt_history_action.triggered.connect( apt_history )

def add_view_unattended_upgrades_logs_action():
    ActionsMenu.addSeparator()
    view_unattended_upgrades_logs_action =  ActionsMenu.addAction(View_Auto_Updates_Logs)
    view_unattended_upgrades_logs_action.triggered.connect( view_unattended_upgrades_logs )

def add_view_unattended_upgrades_dpkg_logs_action():
    ActionsMenu.addSeparator()
    view_unattended_upgrades_logs_action =  ActionsMenu.addAction(View_Auto_Updates_Dpkg_Logs)
    view_unattended_upgrades_logs_action.triggered.connect( view_unattended_upgrades_dpkg_logs )

def add_apt_get_update_action():
    ActionsMenu.addSeparator()
    apt_get_update_action =  ActionsMenu.addAction(Check_for_Updates)
    apt_get_update_action.triggered.connect( apt_get_update )

def add_about_action():
    ActionsMenu.addSeparator()
    about_action =  ActionsMenu.addAction( About )
    about_action.triggered.connect( displayAbout )

def displayAbout():
    notification_close()
    """
    from aptnotifier_about import AptnotifierAbout
    about = AptnotifierAbout()
    about.displayAbout()
    #-------------------
    got those known and not yet fixed error messages:
    qt.qpa.xcb: QXcbConnection: XCB error: 3 (BadWindow), sequence: 1069,
    resource id: 19379270, major code: 40 (TranslateCoords), minor code: 0
    Silenced with:
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.xcb.warning=false"
    """
    from subprocess import run
    run(['/usr/bin/python3', '/usr/lib/apt-notifier/modules/aptnotifier_about.py'])

def view_unattended_upgrades_logs():
    notification_close()
    global autoupdate
    try:
        autoupdate
    except NameError:
        from aptnotifier_autoupdate import UnattendedUpgrade
        autoupdate = UnattendedUpgrade()
    autoupdate.view_unattended_upgrades_logs()

def view_unattended_upgrades_dpkg_logs():
    notification_close()
    global autoupdate
    try:
        autoupdate
    except NameError:
        from aptnotifier_autoupdate import UnattendedUpgrade
        autoupdate = UnattendedUpgrade()
    autoupdate.view_unattended_upgrades_dpkg_logs()

def set_QIcons():
    # Define Core objects, Tray icon and QTimer
    global AptIcon
    global QuitIcon
    global icon_config
    global icon_look

    global NoUpdatesIcon
    global NewUpdatesIcon
    global HelpIcon
    global icon_config

    global tray_icon_noupdates
    global tray_icon_newupdates

    NoUpdatesIcon   = QtGui.QIcon(tray_icon_noupdates)
    NewUpdatesIcon  = QtGui.QIcon(tray_icon_newupdates)
    HelpIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/apps/help-browser.png")
    QuitIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/actions/system-shutdown.png")
    # Create the right-click menu and add the Tooltip text


def systray_icon_hide():
    notification_close()

    #cmd = "pgrep -x plasmashell >/dev/null && exit 1 || exit 0"
    #running_in_plasma = subprocess.run(cmd, shell=True).returncode
    #if not running_in_plasma:
    if not run_in_plasma():
       return

    if not which("qdbus"):
       return

    Script='''
    var iconName = 'apt-notifier.py';
    for (var i in panels()) {
        p = panels()[i];
        for (var j in p.widgets()) {
            w = p.widgets()[j];
            if (w.type == 'org.kde.plasma.systemtray') {
                s = desktopById(w.readConfig('SystrayContainmentId'));
                s.currentConfigGroup = ['General'];
                var shownItems = s.readConfig('shownItems').split(',');
                if (shownItems.indexOf(iconName) >= 0) {
                    shownItems.splice(shownItems.indexOf(iconName), 1);
                }
                if ( shownItems.length == 0 ) {
                    shownItems = [ 'auto' ];
                }
                s.writeConfig('shownItems', shownItems);
                s.reloadConfig();
            }
        }
    }
    '''
    run = subprocess.Popen(['qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "' + Script + '" '],shell=True)

def systray_icon_show():

    #cmd = "pgrep -x plasmashell >/dev/null && exit 1 || exit 0"
    #running_in_plasma = subprocess.run(cmd, shell=True).returncode
    #if not running_in_plasma:
    if not run_in_plasma():
       return

    if not which("qdbus"):
       return

    Script='''
    var iconName = 'apt-notifier.py';
    for (var i in panels()) {
        p = panels()[i];
        for (var j in p.widgets()) {
            w = p.widgets()[j];
            if (w.type == 'org.kde.plasma.systemtray') {
                s = desktopById(w.readConfig('SystrayContainmentId'));
                s.currentConfigGroup = ['General'];
                var shownItems = s.readConfig('shownItems').split(',');
                if (( shownItems.length == 0 ) || ( shownItems.length == 1 && shownItems[0].length == 0 )) {
                    shownItems = [ iconName ];
                }
                else if (shownItems.indexOf(iconName) === -1) {
                    shownItems.push(iconName)
                }
                if (shownItems.indexOf('auto') >= 0) {
                    shownItems.splice(shownItems.indexOf('auto'), 1);
                }
                s.writeConfig('shownItems', shownItems);
                s.reloadConfig();
            }
        }
    }
    '''
    run = subprocess.Popen(['qdbus org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "' + Script + '" '],shell=True)

#---------------------------------------------
# notification with actions
#---------------------------------------------

def dbus_closed():
    global AptIcon
    global dbus_callback_closed
    #global tool_tip
    #try: tool_tip
    #except: tool_tip = ""
    dbus_callback_closed = True
    debug_p(f"dbus_callback_closed: {dbus_callback_closed} ")
    debug_p(f"Notification is closed")
    try: AptIcon
    except: return
    #AptIcon.setToolTip(tool_tip)

def upgrade_cb(n, action):
    assert action == "upgrade"
    #print("You clicked 'View and Upgrade'")
    #cmd = "apt-notifier-unhide-Icon"
    #run = subprocess.Popen(cmd,shell=True)
    AptIcon.hide()
    try:
        with open(DISMISS_CHECK, "w") as x:
            pass
    except:
        pass
    start_viewandupgrade(action)
    restart_apt_notifier()
    n.close()
    dbus_closed()

def reload_cb(n, action):
    assert action == "reload"
    #print("You clicked Reload")
    AptIcon.hide()
    apt_get_update()
    restart_apt_notifier()
    n.close()
    dbus_closed()

def closed_cb(n):
    #print("Notification closed")
    n.close()
    dbus_closed()

def notification_close():
    global notification
    global dbus_callback_closed
    try:
        dbus_callback_closed
    except:
        dbus_callback_closed = True
    try:
        if notification:
            notification.close()
            dbus_callback_closed = True
    except:
        pass

def desktop_notification(title, msg, icon):
    notify2_initiated = False
    global notification
    notification = False
    try:
        #import notify2
        import notify2_0_3_1_latest  as notify2
    except ImportError:
        return False

    try:
        notify2.init(Updater_Name, 'glib')
        notify2_initiated = True
    except:
        return False

    if  notify2_initiated:
        notification = notify2.Notification(None, icon=icon)
        if ('actions' not in notify2.get_server_caps()):
            return False

        if ('actions' in notify2.get_server_caps()):
            notification.add_action("upgrade", View_and_Upgrade, upgrade_cb)
            # not used:
            # notification.add_action("reload", Reload, reload_cb)
        notification.connect('closed', closed_cb)
        notification.timeout = 10000
        notification.update(title, msg)
        notification.show()
        return True
    else:
        return False

def use_notifier():
    global UseNotifier
    global use_dbus_notifications

    if use_dbus_notifications:
        UseNotifier = "dbus"
    else:
        UseNotifier = "qt"
        """ not used:
        ret = subprocess.run("pgrep -x xfdesktop".split(), stdout=subprocess.DEVNULL).returncode
        if ret == 0:
            running_in_xfce = True
        else:
            running_in_xfce = False
        if running_in_xfce:
            run = subprocess.run("dpkg-query -f ${Version} -W xfdesktop4".split(), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, universal_newlines=True)
            xfce_version = run.stdout.strip()
            if xfce_version.startswith("4.16"):
                UseNotifier = "dbus"
            else:
                UseNotifier = "qt"
        """
    debug_p(f"use_notifier(): UseNotifier: {UseNotifier}")
    return UseNotifier

def show_popup(popup_title, popup_msg, popup_icon):
    UseNotifier = use_notifier()
    #print( "UseNotifier:" + UseNotifier)

    if not UseNotifier.startswith("qt"):
        if os.path.exists(DISMISS_CHECK):
            try:
                os.remove(DISMISS_CHECK)
                return True
            except:
                pass

        if desktop_notification(popup_title, popup_msg, popup_icon):
            return True
        else:
            UseNotifier = "qt"

    if UseNotifier.startswith("qt"):
        def show_message():
            AptIcon.showMessage(popup_title, popup_msg)
        Timer.singleShot(1000, show_message)
        return True

def another_apt_notifer_is_running():
    """
    simple process check for running apt-notifier
    TODO: add a lock
    """
    from subprocess import run
    import os
    from time import sleep
    euid = str(os.geteuid())
    # python2
    # cmd = [ 'pgrep', '-u' , euid , '-c', '-f',  '/usr/bin/python /usr/bin/apt-notifier.py' ]
    # python3
    # count running apt-notifier processes of current user

    cmd = [ 'pgrep', '-u' , euid , '-c', '-f',  'python3 /usr/lib/apt-notifier/modules/apt-notifier.py' ]
    # check max n times whether another apt-notifer is running
    N=3
    delay = 0.7
    check = True
    for i in range(N):
        if check:
            res = run(cmd, capture_output=True, text=True)
            ret = res.returncode
            cnt = int(res.stdout.strip())
            debug_p(f"Check aptnotifer is running: {ret} : {cnt}")
            debug_p(f"{cmd}")
            debug_p(f"{' '.join(cmd)}")
            if ret == 0 and cnt > 1:
                # another instance of apt-notifer.py found
                # wait a bit and check again
                if i+1 < N:
                    sleep(0.7)
                else:
                    break
            else:
                check = False

    return check

def run_in_plasma():
    global running_in_plasma
    try:
        running_in_plasma
    except:
        from subprocess import run
        cmd = "pidof -q plasmashell"
        if run(cmd.split(), capture_output=True).returncode:
            running_in_plasma = False
        else:
            running_in_plasma = True
    #------------------------------
    #if debugging():
    #    running_in_plasma = False
    #    running_in_plasma = True
    #-------------------------------

    return running_in_plasma

def debug_p(text=''):
    """
    simple debug print helper -  msg get printed to stderr
    """
    if debugging():
        print("Debug: " + text, file = sys.stderr)

def debugging():
    """
    simple debugging helper
    """
    import os
    global debug_apt_notifier
    try:
        debug_apt_notifier
    except:
        try:
            debug_apt_notifier = os.getenv('DEBUG_APT_NOTIFIER')
        except:
            debug_apt_notifier = False

    return debug_apt_notifier

def version_installed():
    from subprocess import run
    cmd = "dpkg-query -f ${Version} -W apt-notifier"
    version_installed = run(cmd.split(), capture_output=True, text=True).stdout.strip()
    return version_installed

def restart_apt_notifier():
    from subprocess import run, DEVNULL
    debug_p("restart_apt_notifier.")
    notification_close()
    cmd = "sleep 1; apt-notifier-unhide-Icon & disown -h >/dev/null 2>/dev/null"
    cmd = "apt-notifier-unhide-Icon & disown -h >/dev/null 2>/dev/null"
    #run(cmd, shell=True, executable="/bin/bash", start_new_session=True, stdout=DEVNULL, stderr=DEVNULL)
    run(cmd, shell=True, executable="/bin/bash", stdout=DEVNULL, stderr=DEVNULL)
    sleep(2)
    sys.exit(1)

def unattended_upgrade_enabled():
    """
    check whether Unattended-Upgrade is enabled
    """
    from subprocess import run

    cmd = "apt-config shell x APT::Periodic::Unattended-Upgrade/b"
    ret = subprocess.run(cmd.split(), capture_output=True, text=True).stdout
    # ret = "x='true'" : Unattended-Upgrade enabled
    # ret = else       : Unattended-Upgrade not enabled
    if 'true' in ret:
        return True
    else:
        return False

def get_stat_hash_of_watched_files_and_dirs():
    import os
    import hashlib

    WatchedFiles = """
        /etc/apt/apt.conf
        /etc/apt/preferences
        /etc/apt/sources.list
        /var/cache/apt/pkgcache.bin
        /var/lib/dpkg/status
        /var/lib/synaptic/preferences
    """
    watched_files = [ x for x in WatchedFiles.split() if os.path.isfile(x) ]

    '''
    # changed to reduced list below
    WatchedDirs = """
        /etc/apt/apt.conf.d
        /etc/apt/preferences.d
        /etc/apt/sources.list.d
        /var/lib/apt
        /var/lib/apt/lists
        /var/lib/apt/lists/partial
        /var/lib/dpkg
        /var/cache/apt
    """
    '''

    '''
    # not used
    conf_dirs = """
        /etc/apt/apt.conf.d
    """
    conf_files = [ f"{d}/{x}" for d in conf_dirs.split() for x in sorted(os.listdir(d)) if os.path.isfile(f"{d}/{x}") ]
    '''

    pref_dirs = """
        /etc/apt/preferences.d
    """
    pref_files = [ f"{d}/{x}" for d in pref_dirs.split() for x in sorted(os.listdir(d)) if os.path.isfile(f"{d}/{x}") ]

    sources_list_dir = "/etc/apt/sources.list.d"
    sources_list_files = sorted([ f"{sources_list_dir}/{x}" for x in os.listdir(sources_list_dir) if x.endswith((".list", ".sources"))])

    apt_lists_dir = "/var/lib/apt/lists"
    release_files = sorted([ f"{apt_lists_dir}/{x}" for x in os.listdir(apt_lists_dir) if x.endswith("Release") ])

    #list_of_files =  watched_files + sources_list_files + release_files + pref_files
    list_of_files =  watched_files + sources_list_files + pref_files

    strings_of_times = list( map( lambda c : f"{c.st_mtime}:{c.st_ctime}", [ os.stat(x) for x in list_of_files ]))

    """
    # orig:
    tuples_of_times = [ ( os.stat(x).st_mtime, os.stat(x).st_ctime )
                        for x in list_of_files if os.path.exists(x)]


    list_of_times = [ str(time)
                      for tuple in tuples_of_times
                      for time in tuple ]
    """

    msg = '\n'.join(strings_of_times)

    md5 = hashlib.md5(msg.encode(encoding='ascii')).hexdigest()
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

    # hash_debug
    try:
        if os.environ['DEBUG_APT_NOTIFIER'] == "true":
            with open(f"/tmp/apt_notifier_debug_updater_count_{UNAME}.log", "a") as f:
                f.write(f"Debug[{now}] timestamp hash of {len(strings_of_times)} files: {md5} \n")
                lof =  "\n".join(list_of_files)
                f.write(f"{lof}\n")
    except:
        pass
    return md5

def set_debug():
    """ simply set debug environment through commadn line options """
    import os
    debug =  [ '-d', '--debug']
    # using comprehensive
    debug_opts = [x for x in sys.argv if x in debug ]
    # or with lambda filter
    # debug_opts = list(filter(lambda x: x in debug, sys.argv))
    if len(debug_opts) > 0:
        os.environ['DEBUG_APT_NOTIFIER'] = "true"
        debug_p(f" Debugging {os.getenv('DEBUG_APT_NOTIFIER')}")

def fix_path():
    '''
    set fixed path environment for apt-notifier to run
    '''
    import os
    path = '/usr/local/bin:/usr/bin:/bin:/sbin:/usr/sbin'
    os.environ['PATH'] = path

def fix_fluxbox_startup():
    from aptnotifier_autostart import AutoStart
    ast = AutoStart()
    ast.fix_fluxbox_autostart()

def tooltip_msg(num):
    num = int(num)
    if num == 0:
        # untranslated old non-plurals msg
        umsg = '0 updates available'
        tmsg = _(umsg)

        numsg = 'No updates available'
        nmsg = _('No updates available')
    else:
        if num == 1:
            # untranslated old non-plurals msg
            umsg = '1 new update available'
            # translated old non-plurals msg
            tmsg = _(umsg)
        else:
            # untranslated old non-plurals msg
            umsg = '$count new updates available'
            # translated old non-plurals msg
            tmsg = _(umsg).replace('$count', str(num))
            # polpulate with the number
            umsg  = umsg.replace('$count', str(num))

        # TRANSLATORS: Fill in all plural forms. The parenthesized expression '{num}'
        # is replaced by the actual number of updates available at runtime.
        # For the singular form, you can replace '{num}' with 'one'.
        # Example with 2 plural forms:
        # msgstr[0] -> singular form: use 'one new update' or '{num} new update'.
        # msgstr[1] -> plural form: use '{num} new updates'.
        nmsg = ngettext('{num} new update available', '{num} new updates available', num)

        # new translated plurals msg
        nmsg = nmsg.format(num=num)
        # new untranslated plurals msg
        if num == 1:
            numsg = '{num} new update available'.format(num=num)
        else:
            numsg = '{num} new updates available'.format(num=num)

    # check we have translations of the plurals msg
    if nmsg not in numsg:
        # yep, translated - we take the new plurals msg
        msg = nmsg
    else:
        # check we have translated old non-plurals msg
        if tmsg not in umsg:
            # yep, so we take the old translated one
            msg = tmsg
        else:
            # neither old non-plurals nor new plurals are translated
            # se we take the new plurals msg
            msg = nmsg
    return msg


def popup_msg(num):
    num = int(num)
    if num == 0:
        # untranslated old non-plurals msg
        umsg = '0 updates available'
        tmsg = _(umsg)

        numsg = 'No updates available'
        nmsg = _('No updates available')
        """
        # untranslated old non-plurals msg
        umsg = 'You have $count new updates available'
        tmsg = _(umsg)
        umsg = umsg.replace('$count', '0')
        tmsg = tmsg.replace('$count', '0')

        numsg = 'You have no new updates available'
        nmsg = _('You have no new updates available')
        """
    else:
        if num == 1:
            # untranslated old non-plurals msg
            umsg = 'You have 1 new update available'
            # translated old non-plurals msg
            tmsg = _(umsg)
        else:
            # untranslated old non-plurals msg
            umsg = 'You have $count new updates available'
            # translated old non-plurals msg
            tmsg = _(umsg).replace('$count', str(num))
            # polpulate with the number
            umsg  = umsg.replace('$count', str(num))

        # TRANSLATORS: Fill in all plural forms. The parenthesized expression '{num}'
        # is replaced by the actual number of updates available at runtime.
        # For the singular form, you can replace '{num}' with 'one'.
        # Example with 2 plural forms:
        # msgstr[0] -> singular form: use 'one new update' or '{num} new update'.
        # msgstr[1] -> plural form: use '{num} new updates'.
        nmsg = ngettext('You have {num} new update available', 'You have {num} new updates available', num)

        # new translated plurals msg
        nmsg = nmsg.format(num=num)
        # new untranslated plurals msg
        if num == 1:
            numsg = 'You have {num} new update available'.format(num=num)
        else:
            numsg = 'You have {num} new updates available'.format(num=num)

    # check we have translations of the plurals msg
    if nmsg not in numsg:
        # yep, translated - we take the new plurals msg
        msg = nmsg
    else:
        # check we have translated old non-plurals msg
        if tmsg not in umsg:
            # yep, so we take the old translated one
            msg = tmsg
        else:
            # neither old non-plurals nor new plurals are translated
            # se we take the new plurals msg
            msg = nmsg
    return msg


def apt_dpkg_is_locked():
    """
    check for apt/dpkg locks
    """
    locks = """
            /var/lib/dpkg/lock
            /var/lib/dpkg/lock-frontend
            /var/lib/apt/lists/lock
            /var/cache/apt/archives/lock
            """

    locks = locks.strip().split()

    from shutil import which
    path = which("pkexec")
    if path:
        sudo = "pkexec"
    else:
        sudo = "sudo"

    cmd = f"{sudo} /usr/bin/lslocks --noheadings --notruncate --output PATH".split()

    lslocks = subprocess.run(cmd, capture_output=True, text=True).stdout
    lslocks = lslocks.strip().split()


    if list(filter(lambda x : x in locks, lslocks)):
        return True
    else:
        return False

def cleanup_notifier_run():
    import os
    from subprocess import Popen, DEVNULL
    cleanup_notifier = "/usr/bin/cleanup-notifier-mx"
    if os.path.exists(cleanup_notifier):
        ret = Popen(f"sleep 1; {cleanup_notifier} & disown", shell=True, executable="/usr/bin/bash", stdout=DEVNULL, stderr=DEVNULL)

def fullscreen():
    from ewmh import EWMH
    check = False
    for w in EWMH().getClientList():
        if '_NET_WM_STATE_FULLSCREEN' in EWMH().getWmState(w, True):
            check = True
            break
    return check

#### main #######
def main():
    # Define Core objects, Tray icon and QTimer
    global AptNotify
    global AptIcon
    global AvailableUpdates
    global QuitIcon
    global icon_config
    global quit_action
    global Timer
    global initialize_aptnotifier_prefs
    global icon_look

    fix_path()

    set_debug()

    if another_apt_notifer_is_running():
        debug_p("apt-notifier is already running - exit.")
        sys.exit(1)

    # some early globals
    # check version_at_start
    global version_at_start
    version_at_start = version_installed()

    global rc_file_name
    rc_file_name = os.getenv('HOME') + '/.config/apt-notifierrc'
    global message_status
    message_status = "not displayed"
    global notification_icon
    notification_icon = "apt-notifier"


    # fix  fluxbox startup if needed
    fix_fluxbox_startup()

    set_globals()
    set_package_manager()
    debug_p(f"set_package_manager() : {package_manager}")
    initialize_aptnotifier_prefs()
    AptNotify = QtWidgets.QApplication(sys.argv)
    AptIcon = QtWidgets.QSystemTrayIcon()
    Timer = QtCore.QTimer()
    icon_config = read_icon_config()

    # Define the icons:
    global NoUpdatesIcon
    global NewUpdatesIcon
    global HelpIcon

    set_QIcons()

    # Create the right-click menu and add the Tooltip text
    global ActionsMenu
    ActionsMenu = QtWidgets.QMenu()
    AptIcon.activated.connect( left_click_activated )
    Timer.timeout.connect( check_updates )
    # Integrate it together,apply checking of updated packages and set timer to every 1 minute(s) (1 second = 1000)
    AptIcon.setIcon(NoUpdatesIcon)
    AptIcon.setContextMenu(ActionsMenu)
    update_stamp = os.path.isfile('/var/lib/apt/periodic/update-stamp')
    lock = os.path.isfile('/var/lib/apt/lists/lock')
    if not update_stamp and not lock:
        AvailableUpdates = "0"
        if AvailableUpdates == "0":
            message_status = "not displayed"  # Resets flag once there are no more updates
            add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            if unattended_upgrade_enabled():
                AptIcon.setToolTip(unattended_upgrades)
            else:
                AptIcon.setToolTip(tooltip_msg(0))
    else:
        check_updates()

    if icon_config == "show":
        systray_icon_show()
        AptIcon.show()

    global check_for_updates_interval

    Timer.start(int(check_for_updates_interval)*1000)
    if AptNotify.isSessionRestored():
        sys.exit(1)
    sys.exit(AptNotify.exec_())


if __name__ == '__main__':
    main()
