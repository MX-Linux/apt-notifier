#!/usr/bin/python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os
import tempfile
from os import environ

from PyQt5 import QtWidgets, QtGui
from PyQt5 import QtCore

from distutils import spawn 
from time import sleep

global version_at_start
version_at_start = subprocess.check_output(["dpkg-query -f '${Version}' -W apt-notifier" ], shell=True)
#.decode('utf-8')

def package_manager():
    global package_manager
    global package_manager_name
    global package_manager_exec
    
    if spawn.find_executable("synaptic-pkexec"):
        package_manager = "synaptic"
        package_manager_exec = "synaptic-pkexec"
        package_manager_name = "Synaptic"

        
    elif spawn.find_executable("muon"):
        package_manager = "muon"
        package_manager_name = "Muon"

        if spawn.find_executable("muon-pkexec"):
            package_manager_exec = "muon-pkexec"
        elif spawn.find_executable("mx-pkexec"):
            package_manager_exec = "mx-pkexec muon"
        else:
            package_manager_exec = "su-to-root -X -c muon"

    else:
        package_manager = None
        sys.exit("Error: No package manager found! Synaptic or Muon are required.")
    

package_manager()

rc_file_name = environ.get('HOME') + '/.config/apt-notifierrc'
message_status = "not displayed"

# ~~~ Localize 0 ~~~

# Use gettext and specify translation file locations
import gettext
gettext.bindtextdomain('apt-notifier', '/usr/share/locale')
gettext.textdomain('apt-notifier')
_ = gettext.gettext
gettext.install('apt-notifier.py')

from string import Template	# for simple string substitution (popup_msg...)


def set_translations():
    global tooltip_0_updates_available
    global tooltip_1_new_update_available
    global tooltip_multiple_new_updates_available
    global popup_title
    global popup_msg_1_new_update_available
    global popup_msg_multiple_new_updates_available
    global Upgrade_using_package_manager
    global View_and_Upgrade
    global Hide_until_updates_available
    global Quit_Apt_Notifier
    global Apt_Notifier_Help
    global Package_Manager_Help
    global Apt_Notifier_Preferences    
    global Apt_History
    global View_Auto_Updates_Logs
    global View_Auto_Updates_Dpkg_Logs
    global Check_for_Updates
    global Force_Check_Counter
    Force_Check_Counter = 0
    global About
    global Check_for_Updates_by_User
    Check_for_Updates_by_User = 'false'
    global ignoreClick
    ignoreClick = '0'
    global WatchedFilesAndDirsHashNow
    WatchedFilesAndDirsHashNow = ''
    global WatchedFilesAndDirsHashPrevious
    WatchedFilesAndDirsHashPrevious = ''
    global text
    text = ''
    global MX_Package_Installer

    # ~~~ Localize 1 ~~~

    tooltip_0_updates_available                 = unicode (_("0 updates available")                    ,'utf-8')
    tooltip_1_new_update_available              = unicode (_("1 new update available")                 ,'utf-8')
    tooltip_multiple_new_updates_available      = unicode (_("$count new updates available")           ,'utf-8')
    popup_title                                 = unicode (_("Updates")                                ,'utf-8')
    popup_msg_1_new_update_available            = unicode (_("You have 1 new update available")        ,'utf-8')
    popup_msg_multiple_new_updates_available    = unicode (_("You have $count new updates available")  ,'utf-8')
    Upgrade_using_package_manager               = unicode (_("Upgrade using Synaptic")                 ,'utf-8')
    Upgrade_using_package_manager = Upgrade_using_package_manager.replace('Synaptic', package_manager_name)
    
    View_and_Upgrade                            = unicode (_("View and Upgrade")                       ,'utf-8')         
    Hide_until_updates_available                = unicode (_("Hide until updates available")           ,'utf-8')
    Quit_Apt_Notifier                           = unicode (_("Quit")                                   ,'utf-8')
    Apt_Notifier_Help                           = unicode (_("MX Updater Help")                        ,'utf-8')
    Package_Manager_Help                        = unicode (_("Synaptic Help")                          ,'utf-8')
    Package_Manager_Help = Package_Manager_Help.replace("Synaptic", package_manager_name)
    
    Apt_Notifier_Preferences                    = unicode (_("Preferences")                            ,'utf-8')
    Apt_History                                 = unicode (_("History")                                ,'utf-8')
    View_Auto_Updates_Logs                      = unicode (_("Auto-update log(s)")                     ,'utf-8') 
    View_Auto_Updates_Dpkg_Logs                 = unicode (_("Auto-update dpkg log(s)")                ,'utf-8') 
    Check_for_Updates                           = unicode (_("Check for Updates")                      ,'utf-8')
    About                                       = unicode (_("About")                                  ,'utf-8')
    MX_Package_Installer                        = unicode (_("MX Package Installer")                   ,'utf-8')
  

# Check for updates, using subprocess.Popen
def check_updates():
    global message_status
    global text
    global WatchedFilesAndDirsHashNow
    global WatchedFilesAndDirsHashPrevious
    global Check_for_Updates_by_User
    global Force_Check_Counter
    
    """
    Don't bother checking for updates when /var/lib/apt/periodic/update-stamp
    isn't present. This should only happen in a Live session before the repository
    lists have been loaded for the first time.
    """ 
    command_string = "bash -c '[ ! -e /var/lib/apt/periodic/update-stamp ] && [ ! -e /var/lib/apt/lists/lock ]'"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        if text == '':
            text = '0'
        message_status = "not displayed"  # Resets flag once there are no more updates
        add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            command_string = "( [ -z $(apt-config shell U APT::Periodic::Unattended-Upgrade) ] )"
            exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
            if exit_state == 0:
                AptIcon.setToolTip(tooltip_0_updates_available)
            else:
                command_string = "( [ $(apt-config shell U APT::Periodic::Unattended-Upgrade | cut -c4) != 0 ] )"
                exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
                if exit_state == 0:
                    AptIcon.setToolTip("")
                else:
                    AptIcon.setToolTip(tooltip_0_updates_available)
        return
    
    """
    Don't bother checking for updates if processes for other package management tools
    appear to be runninng. For unattended-upgrade, use '/usr/bin/unattended-upgrade'
    to avoid getting a hit on /usr/share/unattended-upgrades/unattended-upgrade-shutdown
    which appears to be started automatically when using systemd as init.
    """ 
    command_string = "bash -c 'sudo lsof /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend /var/lib/apt/lists/lock /var/cache/apt/archives/lock 2>/dev/null | tail -1 | grep lock$\|lock-frontend$ -Eq'"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        Force_Check_Counter = 5
        return

    """
    Get a hash of files and directories we are watching
    """
    script = '''#!/bin/bash
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/etc/apt/apt.conf* "
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/etc/apt/preferences* "
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/lib/apt* "
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/lib/apt/lists "
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/lib/apt/lists/partial "
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/lib/dpkg "

    if which synaptic-pkexec > /dev/null; then
       WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/lib/synaptic/preferences "
    fi
    
    WatchedFilesAndDirs="$WatchedFilesAndDirs""/var/cache/apt "
    stat -c %Y,%Z $WatchedFilesAndDirs 2>/dev/null | md5sum
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    WatchedFilesAndDirsHashNow = run.stdout.read(128)
    script_file.close()

    """
    If
        no changes in hash of files and directories being watched since last checked
            AND
        the call to check_updates wasn't initiated by user   
    then don't bother checking for updates.
    """
    if WatchedFilesAndDirsHashNow == WatchedFilesAndDirsHashPrevious:    
        if Check_for_Updates_by_User == 'false':
            if Force_Check_Counter < 5:
                Force_Check_Counter = Force_Check_Counter + 1            
                if text == '':
                    text = '0'
                return

    WatchedFilesAndDirsHashPrevious = WatchedFilesAndDirsHashNow
    WatchedFilesAndDirsHashNow = ''
    
    Force_Check_Counter = 1
    
    Check_for_Updates_by_User = 'false'

    #Create an inline script (what used to be /usr/bin/apt-notifier-check-Updates) and then run it to get the number of updates.
    script = '''#!/bin/bash
    
    Updates=""
    
    #Suppress 'updates available' notification if Unattended-Upgrades are enabled (>=1) AND apt-get upgrade & dist-upgrade output are the same    
    Unattended_Upgrade=0
    eval $(apt-config shell Unattended_Upgrade APT::Periodic::Unattended-Upgrade)
    if [ $Unattended_Upgrade != 0 ]
        then
            Upgrade="$(    LC_ALL=en_US apt-get -o Debug::NoLocking=true --trivial-only -V      upgrade 2>/dev/null)"
            DistUpgrade="$(LC_ALL=en_US apt-get -o Debug::NoLocking=true --trivial-only -V dist-upgrade 2>/dev/null)"
            if [ "$Upgrade" = "$DistUpgrade" ]
               then
                   echo 0
                   exit
               else
                   Updates="$DistUpgrade"
            fi
    fi
    
    if [ -z "$Updates" ]
        then
            Updates="$(LC_ALL=en_US apt-get -o Debug::NoLocking=true --trivial-only -V $(grep ^UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=) 2>/dev/null)"
    fi
    
    #Suppress the 'updates available' notification if all of the updates are from a backports repo (jessie-backports, stretch-backports, etc.)
    if [ "$(grep " => " <<<"$Updates" | wc -l)" = "$(grep " => " <<<"$Updates" | grep -E ~bpo[0-9]+[+][0-9]+[\)]$ | wc -l)" ]
        then
            echo 0
            exit
    fi

    echo $(( $( grep ' => ' <<<"$Updates" | awk '{print $1}' | wc -l) 
           - $( ( grep ' => ' <<<"$Updates" | awk '{print $1}'; 
                  which synaptic-pkexec > /dev/null && \
                  sed -n 's/Package: //p' /var/lib/synaptic/preferences 2>/dev/null
                ) | \
                sort | uniq -d | wc -l
              ) 
              $(grep -o '[0-9]* not upgraded.' <<<"$Updates"| awk '{print "- "$1}')
          ))
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    # Read the output into a text string
    text = run.stdout.read(128)
    script_file.close()

    # Alter both Icon and Tooltip, depending on updates available or not 
    if text == "0":
        message_status = "not displayed"  # Resets flag once there are no more updates
        add_hide_action()
        if icon_config != "show":
            AptIcon.hide()
        else:
            AptIcon.setIcon(NoUpdatesIcon)
            command_string = "( [ $(apt-config shell U APT::Periodic::Unattended-Upgrade | cut -c4) != 0 ] && [ $(apt-config shell U APT::Periodic::Unattended-Upgrade | cut -c4) != '' ] )"
            exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
            if exit_state == 0:
                AptIcon.setToolTip("")
            else:
                AptIcon.setToolTip(tooltip_0_updates_available)
    else:
        if text == "1":
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            AptIcon.setToolTip(tooltip_1_new_update_available)
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before 
            if message_status == "not displayed":
                command_string = "for WID in $(wmctrl -l | cut -d\  -f1); do xprop -id $WID | grep NET_WM_STATE\(ATOM\); done | grep -sq _NET_WM_STATE_FULLSCREEN"
                exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
                if exit_state == 1:
                    def show_message():
                        AptIcon.showMessage(popup_title, popup_msg_1_new_update_available)
                    Timer.singleShot(1000, show_message)
                message_status = "displayed"
        else:
            AptIcon.setIcon(NewUpdatesIcon)
            AptIcon.show()
            tooltip_template=Template(tooltip_multiple_new_updates_available)
            tooltip_with_count=tooltip_template.substitute(count=text)
            AptIcon.setToolTip(tooltip_with_count)    
            add_rightclick_actions()
            # Shows the pop up message only if not displayed before 
            if message_status == "not displayed":
                command_string = "for WID in $(wmctrl -l | cut -d\  -f1); do xprop -id $WID | grep NET_WM_STATE\(ATOM\); done | grep -sq _NET_WM_STATE_FULLSCREEN"
                exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
                if exit_state == 1:
                    # ~~~ Localize 1b ~~~
                    # Use embedded count placeholder.
                    popup_template=Template(popup_msg_multiple_new_updates_available)
                    popup_with_count=popup_template.substitute(count=text)
                    def show_message():
                        #AptIcon.showMessage(popup_title, popup_msg_multiple_new_updates_available_begin + text + popup_msg_multiple_new_updates_available_end)
                        AptIcon.showMessage(popup_title, popup_with_count)
                    Timer.singleShot(1000, show_message)
                message_status = "displayed"
   
def start_package_manager():
    global Check_for_Updates_by_User
    running_in_plasma = subprocess.call(["pgrep -x plasmashell >/dev/null && exit 1 || exit 0"], shell=True, stdout=subprocess.PIPE)
    if  running_in_plasma:
        systray_icon_hide()
        #run = subprocess.Popen([ "bash -c '%s; ionice -c3 nice -n19 python -m pdb /usr/bin/apt-notifier.py < <(sleep .250; echo c)& disown -h;'" % package_manager_exec ],shell=True)
        run = subprocess.Popen([ "bash -c '%s; ionice -c3 nice -n19 /usr/bin/python /usr/bin/apt-notifier.py & disown -h;'" % package_manager_exec ],shell=True)
        AptIcon.hide()
        sleep(1);
        sys.exit(0)
    else:
        run = subprocess.Popen([ package_manager_exec ],shell=True).wait()
        version_installed = subprocess.check_output(["dpkg-query -f '${Version}' -W apt-notifier" ], shell=True)
        if  version_installed != version_at_start:
            run = subprocess.Popen([ "nohup apt-notifier-unhide-Icon & >/dev/null 2>/dev/null" ],shell=True).wait()
            sleep(2)
        Check_for_Updates_by_User = 'true'
        check_updates()

def viewandupgrade():
    global Check_for_Updates_by_User
    systray_icon_hide()
    initialize_aptnotifier_prefs()
    
    # ~~~ Localize 2 ~~~

    # Accommodations for transformation from Python literals to Bash literals:
    #   t10: \\n will convert to \n
    #   t12: \\n will convert to \n
    #   t16: '( and )' moved outside of translatable string to protect from potential translator's typo
    #   t18: \\\"n\\\" will convert to \"n\" which will become "n" in shell (to avoid concatenating shell strings)

    # t01 thru t12, Yad 'View and Upgrade' strings 
    t01 = _("MX Updater--View and Upgrade, previewing: basic upgrade")
    t02 = _("MX Updater--View and Upgrade, previewing: full upgrade")
    #t03 = _("Automatically answer 'yes' to all prompts during full/basic upgrade")
    t03 = _("Automatically answer 'yes' to all prompts during upgrade")
    #t04 = _("automatically close terminal window when basic upgrade complete")
    t04 = _("automatically close terminal window when upgrade complete")
    #t05 = _("automatically close terminal window when full upgrade complete")
    t05 = _("automatically close terminal window when upgrade complete")
    t06 = _("basic upgrade")
    t07 = _("full upgrade")
    t08 = _("switch to basic upgrade")
    t09 = _("switch to full upgrade")
    t10 = _("Switches the type of Upgrade that will be performed, alternating back and forth between 'full upgrade' and 'basic upgrade'.")
    t11 = _("Reload")
    t12 = _("Reload the package information to become informed about new, removed or upgraded software packages. (apt-get update)")
    
    # t14 thru t19, strings for the upgrade (basic) / dist-upgrade (full) script that runs in the terminal window    
    t14 = _("basic upgrade complete (or was canceled)")
    t15 = _("full upgrade complete (or was canceled)")
    t16 = _("this terminal window can now be closed")
    t17 = "'(" + _("press any key to close") + ")'"
    t18 = _("Unneeded packages are installed that can be removed.")
    t19 = _("Running apt-get autoremove, if you are unsure type 'n'.")
    t20 = _("upgrade")
    t21 = _("Using full upgrade")
    t22 = _("Using basic upgrade (not recommended)")
    t23 = _("press any key to close")

    shellvar = (
    '    window_title_basic="'          + t01 + '"\n'
    '    window_title_full="'           + t02 + '"\n'
    '    use_apt_get_dash_dash_yes="'   + t03 + '"\n'
    '    auto_close_window_basic="'     + t04 + '"\n'
    '    auto_close_window_full="'      + t05 + '"\n'
    '    basic_upgrade="'               + t06 + '"\n'
    '    full_upgrade="'                + t07 + '"\n'
    '    switch_to_basic_upgrade="'     + t08 + '"\n'
    '    switch_to_full_upgrade="'      + t09 + '"\n'      
    '    switch_tooltip="'              + t10 + '"\n'
    '    reload="'                      + t11 + '"\n'
    '    reload_tooltip="'              + t12 + '"\n'
    '    done1basic="'                  + t14 + '"\n'
    '    done1full="'                   + t15 + '"\n'
    '    done2="'                       + t16 + '"\n'
    '    done3="'                       + t17 + '"\n'
    '    autoremovable_packages_msg1="'	+ t18 + '"\n'
    '    autoremovable_packages_msg2="' + t19 + '"\n'
    '    upgrade="'                     + t20 + '"\n'
    '    upgrade_tooltip_full="'        + t21 + '"\n'
    '    upgrade_tooltip_basic="'       + t22 + '"\n'
    '    PressAnyKey="'                 + t23 + '"\n'
    )
    
    script = '''#!/bin/bash
    
    #cancel updates available indication if 2 or more Release.reverify entries found
    #if [ $(ls -1 /var/lib/apt/lists/partial/ | grep Release.reverify$ | wc -l) -ge 2 ]; then exit; fi 

''' + shellvar + '''

    RunAptScriptInTerminal(){
    #for MEPIS remove "MX" branding from the $window_title string
    window_title_term=$window_title
    window_title_term=$(echo "$2"|sed 's/MX /'$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)" "'/')

        TermXOffset="$(xwininfo -root|awk '/Width/{print $2/4}')"
        TermYOffset="$(xwininfo -root|awk '/Height/{print $2/4}')"
        G=" --geometry=80x25+"$TermXOffset"+"$TermYOffset
        # I=" --icon=mnotify-some-""$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)"
        I=" --icon=mx-updater"
        if [ "$3" = "" ]
          then T=""; I=""
          else 
            if [ "$3" != "update" ]
              then T=" --title='""$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)"" Updater: "$3"'"
              else T=" --title='""$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)"" Updater: "$reload"'"
            fi
        fi
<<'Disabled'
        if (xprop -root | grep -i kde > /dev/null)
          then

            # Running KDE
            #
            # Can't get su-to-root to work in newer KDE's, so use kdesu for 
            # authentication.
            #  
            # If x-terminal-emulator is set to xfce4-terminal.wrapper, use     
            # xfce4-terminal instead because the --hold option doesn't work with
            # the wrapper. Also need to enclose the apt-get command in single 
            # quotes.
            #
            # If x-terminal-emulator is set to xterm, use konsole instead, if 
            # it's available (it should be).

            case $(readlink -e /usr/bin/x-terminal-emulator | xargs basename) in

              gnome-terminal.wrapper) if [ -e /usr/bin/konsole ]
                                        then
                                          $(kde4-config --path libexec)kdesu -c "konsole -e $3"
                                          sleep 5
                                          while [ "$(ps aux | grep [0-9]' konsole -e apt-get update')" != "" ]
                                            do
                                              sleep 1
                                            done
                                          sleep 1 
                                        else
                                          :
                                      fi
                                      ;;

                             konsole) $(kde4-config --path libexec)kdesu -c "konsole -e $3"
                                      pgrep -x plasmashell >/dev/null || sleep 5
                                      while [ "$(ps aux | grep [0-9]' konsole -e apt-get update')" != "" ]
                                        do
                                          sleep 1
                                        done
                                      sleep 1 
                                      ;;

                             roxterm) $(kde4-config --path libexec)kdesu -c "roxterm$G$T --separate -e $3"
                                      ;;

              xfce4-terminal.wrapper) $(kde4-config --path libexec)kdesu --noignorebutton -d -c "xfce4-terminal$G$I$T -e $3"
                                      ;;

                               xterm) if [ -e /usr/bin/konsole ]
                                        then
                                          $(kde4-config --path libexec)kdesu -c "konsole -e $3"
                                          pgrep -x plasmashell >/dev/null || sleep 5
                                          while [ "$(ps aux | grep [0-9]' konsole -e apt-get update')" != "" ]
                                            do
                                              sleep 1
                                            done
                                          sleep 1 
                                        else
                                          $(kde4-config --path libexec)kdesu -c "xterm -e $3"
                                      fi
                                      ;;

                                   *) $(kde4-config --path libexec)kdesu -c "x-terminal-emulator -e $3"
                                      sleep 5
                                      while [ "$(ps aux | grep [0-9]' konsole -e apt-get update')" != "" ]
                                        do
                                          sleep 1
                                        done
                                      sleep 1 
                                      ;;
            esac

          else

            # Running a non KDE desktop
            # 
            # Use pkexec for authentication.
            # 
            # If x-terminal-emulator is set to xfce4-terminal.wrapper, use 
            # xfce4-terminal instead because the --hold option doesn't work
            # with the wrapper. Also need to enclose the apt-get command in
            # single quotes.
            #
            # If x-terminal-emulator is set to xterm, use xfce4-terminal 
            # instead, if it's available (it is in MX)
Disabled
            case $(readlink -e /usr/bin/x-terminal-emulator | xargs basename) in

              gnome-terminal.wrapper) sh "$1" "gnome-terminal$G$T -e $4"
                                      ;;

                             konsole) sh "$1" "konsole -e $4"
                                      pgrep -x plasmashell >/dev/null || sleep 5
                                      while [ "$(ps aux | grep [0-9]' konsole -e apt-get update')" != "" ]
                                        do
                                          sleep 1
                                        done
                                      sleep 1 
                                      ;;

                             roxterm) sh "$1" "roxterm$G$T --separate -e $4"
                                      ;;

              xfce4-terminal.wrapper) sh "$1" "xfce4-terminal --hide-menubar $G$I$T -e $4" 2>/dev/null 1>/dev/null
                                      ;;

                               xterm) if [ -e /usr/bin/xfce4-terminal ]
                                        then
                                          sh "$1" "xfce4-terminal --hide-menubar $G$I$T -e $4"
                                        else
                                          sh "$1" "xterm -fa monaco -fs 12 -bg black -fg white -e $4"
                                      fi
                                      ;;

                                   *) sh "$1" "x-terminal-emulator -e $4"
                                      ;;

            esac
        #fi
    }    
        
    DoUpgrade(){
      case $1 in
        0)
        BP="1"
        chmod +x $TMP/upgradeScript      
        T="$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2) Updater: $UpgradeTypeUserFriendlyName"
        # I="mnotify-some-$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)"
        I="mx-updater"
        #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
        #  then
        #    if [ $(grep IconLook=wireframe ~/.config/apt-notifierrc) ]
        #      then
        #        I="/usr/share/icons/Papirus/64x64/apps/mx-updater.svg"
        #    fi
        #fi

        if [ "$(grep UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=)" = "dist-upgrade" ]
          then
            /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-full-upgrade  "$T" "$I" "$TMP/upgradeScript"
          else
            /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-basic-upgrade "$T" "$I" "$TMP/upgradeScript"
        fi
            
        if [ ! -x /usr/bin/xfce4-terminal ]; then
          while [ "$(ps aux | grep -v grep | grep bash.*/usr/lib/apt-notifier/pkexec-wrappers/mx-updater-full-upgrade.*MX.*mnotify-some.*/tmp/apt-notifier.*/upgradeScript)" ]
            do
	          sleep 1
            done
          sleep 1
        fi
        ;;

        2)
        BP="1"
        ;;
        
        4)
        BP="0"
        sed -i 's/UpgradeType='$UpgradeType'/UpgradeType='$OtherUpgradeType'/' ~/.config/apt-notifierrc
        ;;
        
        8)
        BP="0"
        #chmod +x $TMP/upgradeScript
        #RunAptScriptInTerminal "/usr/lib/apt-notifier/pkexec-wrappers/mx-updater-reload" "" "$reload" "$TMP/upgradeScript"
        #I="mnotify-some-$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)"
        #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
        #  then
        #    if [ $(grep IconLook=wireframe ~/.config/apt-notifierrc) ]
        #      then
        #        I="/usr/share/icons/Papirus/64x64/apps/mx-updater.svg"
        #    fi
        #fi
        I="mx-updater"
        /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-reload \
        " --title=""$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)"" Updater: $reload" \
        " --icon=$I" \
        #"$PressAnyKey"
        if [ ! -x /usr/bin/xfce4-terminal ]; then
          while [ "$(ps aux | grep -v grep | grep "bash -c".*"apt-get update".*"sleep".*"mx-updater_reload".*"read.*-p")" ]
            do
	      sleep 1
            done
          sleep 1
        fi
        ;;
        
        *)
        BP="1"
        ;;
        
       esac 
    }

    BP="0"
    while [ $BP != "1" ]
      do

        UpgradeType=$(grep ^UpgradeType ~/.config/apt-notifierrc | cut -f2 -d=)
        if [ "$UpgradeType" = "upgrade"      ]; then
          UpgradeTypeUserFriendlyName=$basic_upgrade
          OtherUpgradeType="dist-upgrade"
          upgrade_tooltip=$upgrade_tooltip_basic
        fi
        if [ "$UpgradeType" = "dist-upgrade" ]; then
          UpgradeTypeUserFriendlyName=$full_upgrade
          OtherUpgradeType="upgrade"
          upgrade_tooltip=$upgrade_tooltip_full
        fi
  
        UpgradeAssumeYes=$(grep ^UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)
        UpgradeAutoClose=$(grep ^UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)
      
        TMP=$(mktemp -d /tmp/apt-notifier.XXXXXX)
        echo "$UpgradeTypeUserFriendlyName" > "$TMP"/upgrades
        
        #The following 40 or so lines (down to the "APT_CONFIG" line) create a temporary etc/apt folder and subfolders
        #that for the most part match the root owned /etc/apt folder and it's subfolders.
        #
        #A symlink to /var/synaptic/preferences symlink ("$TMP"/etc/apt/preferences.d/synaptic-pins) will be created
        #if there isn't one already (note: the non-root user wouldn't be able to create one in /etc/apt/preferences.d/).
        #
        #With a /var/synaptic/preferences symlink in place, no longer need to remove the lines with Synaptic pinned packages
        #from the "$TMP"/upgrades file to keep them from being displayed in the 'View and Upgrade' window, also no longer
        #need to correct the upgrades count after removing the lines with the pinned updates.
        
        #create the etc/apt/*.d subdirectories in the temporary directory ("$TMP")
        for i in $(find /etc/apt -name *.d); do mkdir -p "$TMP"/$(echo $i | cut -f2- -d/); done

        #create symlinks to the files in /etc/apt and it's subdirectories with exception of /etc/apt and /etc/apt/apt.conf  
        for i in $(find /etc/apt | grep -v -e .d$ -e apt.conf$ -e apt$); do ln -s $i "$TMP"/$(echo $i | cut -f2- -d/) 2>/dev/null; done

        #in etc/preferences test to see if there's a symlink to /var/lib/synaptic/preferences
        ls -l /etc/apt/preferences* | grep ^l | grep -m1 /var/lib/synaptic/preferences$ > /dev/null

        #if there isn't, create one if there are synaptic pinned packages
        if [ $? -eq 1 ]
          then
            if which synaptic-pkexec > /dev/null && [ -s /var/lib/synaptic/preferences ]; then 
               ln -s /var/lib/synaptic/preferences "$TMP"/etc/apt/preferences.d/synaptic-pins 2>/dev/null
            fi
        fi

        #create a apt.conf in the temp directory by copying existing /etc/apt/apt.conf to it
        [ ! -e /etc/apt/apt.conf ] || cp /etc/apt/apt.conf "$TMP"/apt.conf

        #in apt.conf file set Dir to the path of the temp directory
        echo 'Dir "'"$TMP"'/";' >> "$TMP"/apt.conf
        #set Dir::State::* and Dir::Cache::* to the existing ones in /var/lib/apt, /var/lib/dpkg and /var/cache/apt
        echo 'Dir::State "/var/lib/apt/";' >> "$TMP"/apt.conf
        echo 'Dir::State::Lists "/var/lib/apt/lists/";' >> "$TMP"/apt.conf
        echo 'Dir::State::status "/var/lib/dpkg/status";' >> "$TMP"/apt.conf
        echo 'Dir::State::extended_states "/var/lib/apt/extended_states";' >> "$TMP"/apt.conf
        echo 'Dir::Cache "/var/cache/apt/";' >> "$TMP"/apt.conf
        echo 'Dir::Cache::Archives "/var/cache/apt/archives";' >> "$TMP"/apt.conf
        echo 'Dir::Cache::srcpkgcache "/var/cache/apt/srcpkgcache.bin";' >> "$TMP"/apt.conf
        echo 'Dir::Cache::pkgcache "/var/cache/apt/pkgcache.bin";' >> "$TMP"/apt.conf

        APT_CONFIG="$TMP"/apt.conf apt-get -o Debug::NoLocking=true --trivial-only -V $UpgradeType 2>/dev/null >> "$TMP"/upgrades

        #fix to display epochs
        #for i in $(grep [[:space:]]'=>'[[:space:]] "$TMP"/upgrades | awk '{print $1}')
        #do
        #  withoutEpoch="$(grep [[:space:]]$i[[:space:]] "$TMP"/upgrades | awk '{print $2}')"
        #  withEpoch="(""$(apt-cache policy $i | head -2 | tail -1 | awk '{print $NF}')"
        #  sed -i 's/'"$withoutEpoch"'/'"$withEpoch"'/' "$TMP"/upgrades
        #  withoutEpoch="$(grep [[:space:]]$i[[:space:]] "$TMP"/upgrades | awk '{print $4}')"
        #  withEpoch="$(apt-cache policy $i | head -3 | tail -1 | awk '{print $NF}')"")"
        #  sed -i 's/'"$withoutEpoch"'/'"$withEpoch"'/' "$TMP"/upgrades
        #done

        # ~~~ Localize 2a ~~~
        # Format switch label. switch_to contains %s. eg "switch to %s" or "zu %s wechseln"
        # Result output to switch_label could be eg "switch to 'apt-get upgrade'"
        # or "zu 'apt-get dist-upgrade' wechseln'"
        # Should be able to use statement like:
        #      printf -v switch_label "$switch_to" "$switch_type"
        # But fails, so use sed instead.
        # Format auto close message in same way.

        switch_type="'""$OtherUpgradeType""'"
        switch_label=$(echo "$switch_to" | sed 's/%s/'"$switch_type"'/')
        auto_close_label=$(echo "$auto_close_window" | sed 's/%s/'"$UpgradeType"'/')
        
        if [ "$UpgradeType" = "upgrade" ]
          then
            upgrade_label=$upgrade
            switch_label=$switch_to_full_upgrade
            auto_close_label=$auto_close_window_basic
            window_title="$window_title_basic"
          else
            upgrade_label=$upgrade
            switch_label=$switch_to_basic_upgrade
            auto_close_label=$auto_close_window_full
            window_title="$window_title_full"
        fi

        # IFS="x" read screenWidth screenHeight < <(xdpyinfo | grep dimensions | grep -o "[0-9x]*" | head -n 1)
        read screenWidth screenHeight < <(xdotool getdisplaygeometry)
        case "$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)" in 
          classic    ) windowIcon=mnotify-some-classic
                       ButtonIcon=mnotify-some-classic 
                       ;;
          pulse      ) windowIcon=mnotify-some-pulse
                       ButtonIcon=mnotify-some-pulse
                       ;;
          wireframe|*) #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
                       #  then
                       #    if [[ $(xfconf-query -lvc xsettings | grep IconThemeName | grep .*Papirus.* -i) ]]
                       #      then
                       #        windowIcon=mx-updater
                       #      else
                       #        windowIcon=mnotify-some-wireframe
                       #    fi                          
                       #    ButtonIcon=/usr/share/icons/mnotify-some-wireframe.png
                       #  else
                       #    windowIcon=/usr/share/icons/mnotify-some-wireframe.png
                       #    ButtonIcon=/usr/share/icons/mnotify-some-wireframe.png
                       #fi
                       #windowIcon=/usr/share/icons/mnotify-some-wireframe.png
                       windowIcon=mx-updater
                       ButtonIcon=/usr/share/icons/mnotify-some-wireframe.png
                       ;;
        esac
        windowIcon=mx-updater

        yad \\
        --window-icon="$windowIcon" \\
        --width=$(($screenWidth*2/3)) \\
        --height=$(($screenHeight*2/3)) \\
        --center \\
        --title "$(echo "$window_title"|sed 's/MX /'$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)" "'/')" \\
        --form \\
          --field=:TXT "$(sed 's/^/  /' $TMP/upgrades)" \\
          --field="$use_apt_get_dash_dash_yes":CHK $UpgradeAssumeYes \\
          --field="$auto_close_label":CHK $UpgradeAutoClose \\
        --button "$reload"!reload!"$reload_tooltip":8 \\
        --button ''"$upgrade_label"!"$ButtonIcon"!"$upgrade_tooltip":0 \\
        --button gtk-cancel:2 \\
        --buttons-layout=spread \\
        2>/dev/null \\
        > "$TMP"/results 

        echo $?>>"$TMP"/results

        # if the View and Upgrade yad window was closed by one of it's 4 buttons, 
        # then update the UpgradeAssumeYes & UpgradeAutoClose flags in the 
        # ~/.config/apt-notifierrc file to match the checkboxes
        if [ $(tail -n 1 "$TMP"/results) -eq 0 ]||\\
           [ $(tail -n 1 "$TMP"/results) -eq 2 ]||\\
           [ $(tail -n 1 "$TMP"/results) -eq 4 ]||\\
           [ $(tail -n 1 "$TMP"/results) -eq 8 ];
          then
            if [ "$(head -n 1 "$TMP"/results | rev | awk -F \| '{ print $3}' | rev)" = "TRUE" ];
              then
                grep UpgradeAssumeYes=true  ~/.config/apt-notifierrc > /dev/null || sed -i 's/UpgradeAssumeYes=false/UpgradeAssumeYes=true/' ~/.config/apt-notifierrc
              else
                grep UpgradeAssumeYes=false ~/.config/apt-notifierrc > /dev/null || sed -i 's/UpgradeAssumeYes=true/UpgradeAssumeYes=false/' ~/.config/apt-notifierrc
            fi
            if [ "$(head -n 1 "$TMP"/results | rev | awk -F \| '{ print $2}' | rev)" = "TRUE" ];
              then
                grep UpgradeAutoClose=true  ~/.config/apt-notifierrc > /dev/null || sed -i 's/UpgradeAutoClose=false/UpgradeAutoClose=true/' ~/.config/apt-notifierrc
              else
                grep UpgradeAutoClose=false ~/.config/apt-notifierrc > /dev/null || sed -i 's/UpgradeAutoClose=true/UpgradeAutoClose=false/' ~/.config/apt-notifierrc
            fi
          else
            :
        fi

        # refresh UpgradeAssumeYes & UpgradeAutoClose 
        UpgradeAssumeYes=$(grep ^UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)
        UpgradeAutoClose=$(grep ^UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)

        #create first part of upgradeScript
        cat << 'EOF' > "$TMP"/upgradeScript
#!/bin/bash

if [ ! -e /etc/apt/sources.list ]; then echo -e "#This source is empty by default in MX Linux and is only included to avoid\\n#error messages from some package install scripts that expect to find it.\\n#Sources are under /etc/apt/sources.list.d" > /etc/apt/sources.list; fi

EOF
        if [ $(tail -n 1 "$TMP"/results) -eq 8 ];
          then
            # build a upgrade script to do a apt-get update
            echo "echo 'apt-get update'">> "$TMP"/upgradeScript
            echo "apt-get update">> "$TMP"/upgradeScript

          else
            # build a upgrade script to do the apt-get upgrade (basic upgrade) or dist-upgrade (full upgrade)
            echo "echo ''"$UpgradeTypeUserFriendlyName>> "$TMP"/upgradeScript
            echo 'find /etc/apt/preferences.d | grep -E synaptic-[0-9a-zA-Z]{6}-pins | xargs rm -f'>> "$TMP"/upgradeScript 
            echo 'if [ -f /var/lib/synaptic/preferences -a -s /var/lib/synaptic/preferences ]'>> "$TMP"/upgradeScript
            echo '  then '>> "$TMP"/upgradeScript
            echo '    SynapticPins=$(mktemp /etc/apt/preferences.d/synaptic-XXXXXX-pins)'>> "$TMP"/upgradeScript
            echo '    ln -sf /var/lib/synaptic/preferences "$SynapticPins" 2>/dev/null'>> "$TMP"/upgradeScript
            echo 'fi'>> "$TMP"/upgradeScript
            echo 'file "$SynapticPins" | cut -f2- -d" " | grep -e"broken symbolic link" -e"empty" > /dev/null '>> "$TMP"/upgradeScript
            echo 'if [ $? -eq 0 ]; then find /etc/apt/preferences.d | grep -E synaptic-[0-9a-zA-Z]{6}-pins | xargs rm -f; fi'>> "$TMP"/upgradeScript
            if [ "$UpgradeAssumeYes" = "true" ];
              then
                echo "apt-get --assume-yes -V "$UpgradeType>> "$TMP"/upgradeScript
              else
                echo "apt-get -V "$UpgradeType>> "$TMP"/upgradeScript
            fi
            grep ^CheckForAutoRemovables=true ~/.config/apt-notifierrc > /dev/null
            if [ $? -eq 0 ]
              then
                echo "echo">> "$TMP"/upgradeScript
                echo 'apt-get autoremove -s | grep ^Remv > /dev/null'>> "$TMP"/upgradeScript
                echo 'if [ $? -eq 0 ]; '>> "$TMP"/upgradeScript
                echo '  then'>> "$TMP"/upgradeScript
                echo 'echo "'"$autoremovable_packages_msg1"'"'>> "$TMP"/upgradeScript
                echo 'echo "'"$autoremovable_packages_msg2"'"'>> "$TMP"/upgradeScript
                echo 'apt-get autoremove -qV'>> "$TMP"/upgradeScript
                echo '  else'>> "$TMP"/upgradeScript
                echo '    :'>> "$TMP"/upgradeScript
                echo 'fi'>> "$TMP"/upgradeScript
              else
                :
            fi
            echo "echo">> "$TMP"/upgradeScript
            echo 'find /etc/apt/preferences.d | grep -E synaptic-[0-9a-zA-Z]{6}-pins | xargs rm -f'>> "$TMP"/upgradeScript
            
            # ~~~ Localize 2b ~~~

            #donetype="$UpgradeType"
            #donetext=$(echo "$done1" | sed 's/%s/'"$donetype"'/')
            if [ "$UpgradeType" = "upgrade" ]
              then
                donetext="$done1basic"
              else
                donetext="$done1full"
            fi
            echo 'echo "'"$donetext"'"'>> "$TMP"/upgradeScript
            echo "echo">> "$TMP"/upgradeScript

            if [ "$UpgradeAutoClose" = "true" ];
              then
                echo "sleep 1">> "$TMP"/upgradeScript
                echo "exit 0">> "$TMP"/upgradeScript
              else
                echo "echo -n $done2' '">> "$TMP"/upgradeScript
                echo "read -sn 1 -p $done3 -t 999999999">> "$TMP"/upgradeScript
                echo "echo">> "$TMP"/upgradeScript
                echo "exit 0">> "$TMP"/upgradeScript
            fi
        fi

        DoUpgrade $(tail -n 1 "$TMP"/results)

        rm -rf "$TMP"

      done

    #sleep 2
    PID=`pidof apt-get | cut -f 1 -d " "`
    if [ $PID ]; then
        while (ps -p $PID > /dev/null); do
            sleep 2
        done
    fi
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()

    running_in_plasma = subprocess.call(["pgrep -x plasmashell >/dev/null && exit 1 || exit 0"], shell=True, stdout=subprocess.PIPE)
    if  running_in_plasma:
        systray_icon_hide()
        #run = subprocess.Popen(["bash -c 'S=%s; N=$S.$RANDOM$RANDOM$RANDOM; cp $S $N; bash $N; rm $N; ionice -c3 nice -n19 python -m pdb /usr/bin/apt-notifier.py < <(sleep .250; echo c)& disown -h;'" % script_file.name],shell=True)
        
        run = subprocess.Popen(["bash -c 'S=%s; N=$S.$RANDOM$RANDOM$RANDOM; cp $S $N; bash $N; rm $N; apt-notifier-unhide-Icon; rm $S'" % script_file.name],shell=True)
        sleep(1);
        script_file.close()
        sys.exit(1)
    else:
        run = subprocess.Popen(['bash %s' % script_file.name],shell=True).wait()
        script_file.close()
        version_installed = subprocess.check_output(["dpkg-query -f '${Version}' -W apt-notifier" ], shell=True)
        if  version_installed != version_at_start:
            run = subprocess.Popen([ "nohup apt-notifier-unhide-Icon & >/dev/null 2>/dev/null" ],shell=True).wait()
            sleep(2)
        
        Check_for_Updates_by_User = 'true'
        systray_icon_show()
        check_updates()

def initialize_aptnotifier_prefs():

    """Create/initialize preferences in the ~/.config/apt-notifierrc file  """
    """if they don't already exist. Remove multiple entries and those that """
    """appear to be invalid.                                               """ 

    script = '''#!/bin/bash

    #test if ~/.config/apt-notifierrc contains a UpgradeType=* line and that it's a valid entry
    grep -e ^"UpgradeType=upgrade" -e^"UpgradeType=dist-upgrade" ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeType=* line not present,
      #or not equal to "upgrade" or "dist-upgrade"
      #initially set it to "UpgradeType=dist-upgrade"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeType.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeType=dist-upgrade">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a UpgradeAssumeYes=* line and that it's a valid entry
    grep -e ^"UpgradeAssumeYes=true" -e^"UpgradeAssumeYes=false" ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeAssumeYes=* line not present,
      #or not equal to "true" or "false"
      #initially set it to "UpgradeAssumeYes=false"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeAssumeYes.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeAssumeYes=false">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a UpgradeAutoClose=* line and that it's a valid entry
    grep -e ^"UpgradeAutoClose=true" -e^"UpgradeAutoClose=false" ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a UpgradeAutoClose=* line not present,
      #or not equal to "true" or "false"
      #intially set it to "UpgradeAutoClose=false"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*UpgradeAutoClose.*/Id' ~/.config/apt-notifierrc 
      echo "UpgradeAutoClose=false">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a LeftClick=* line and that it's a valid entry
    grep -e ^"LeftClick=ViewAndUpgrade" -e^"LeftClick=PackageManager" ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a LeftClick line not present,
      #or not equal to "ViewAndUpgrade" or "PackageManager"
      #initially set it to "LeftClick=ViewAndUpgrade"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*LeftClick.*/Id' ~/.config/apt-notifierrc 
      echo "LeftClick=ViewAndUpgrade">> ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a CheckForAutoRemovables=* line and that it's a valid entry
    grep -e ^"CheckForAutoRemovables=true" -e^"CheckForAutoRemovables=false" ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
      #contains a valid entry so do nothing
        :
      else
      #
      #if a CheckForAutoRemovables=* line not present,
      #or not equal to "true" or "false"
      #intially set it to "CheckForAutoRemovables=false"
      #also delete multiple entries or what appears to be invalid entries
      sed -i '/.*CheckForAutoRemovables.*/Id' ~/.config/apt-notifierrc 
      echo "CheckForAutoRemovables=false">> ~/.config/apt-notifierrc
    fi

    #delete any 'CheckForAutoRemoves' config line(s), they've been replaced with 'CheckForAutoRemovables'
    grep CheckForAutoRemoves ~/.config/apt-notifierrc > /dev/null
    if [ "$?" -eq 0 ]
      then
        sed -i '/.*CheckForAutoRemoves.*/Id' ~/.config/apt-notifierrc
    fi

    #test if ~/.config/apt-notifierrc contains a IconLook=* line and that it's a valid entry
    #grep -e ^"IconLook=wireframe" -e^"IconLook=classic" -e^"IconLook=pulse" ~/.config/apt-notifierrc > /dev/null
    if grep -sqE "^IconLook=(wireframe(-dark|-light)|classic|pulse)" ~/.config/apt-notifierrc; then
      #contains a valid entry so do nothing
        :
      else
      #
      #delete multiple entries or what appears to be invalid entries
      sed -i '/.*IconLook.*/Id' ~/.config/apt-notifierrc 
      #
      #if a IconLook=* line not present,
      #or not equal to "wireframe" or "classic" or "pulse", then have default as follows for the various MX releases
      #
       case $(grep DISTRIB_RELEASE /etc/lsb-release | grep -Eo [0-9.]+ | head -n 1) in
         14  ) IconDefault="classic"   ;;
         15  ) IconDefault="classic"   ;;
         16  ) IconDefault="wireframe" ;;
         16.1) IconDefault="wireframe" ;;
         17  ) IconDefault="wireframe" ;;
         17.1) IconDefault="wireframe" ;;
         18  ) IconDefault="wireframe" ;;
         18.1) IconDefault="wireframe" ;;
         18.2) IconDefault="wireframe" ;;
         18.3) IconDefault="wireframe" ;;
         19  ) IconDefault="wireframe-dark" ;;
         19.1) IconDefault="wireframe-dark" ;;
            *) IconDefault="wireframe-dark" ;;
       esac
       echo "IconLook=$IconDefault">> ~/.config/apt-notifierrc
       # set transparent as default for wireframe-dark
       
       if [ "$IconDefault" = "wireframe-dark" ]; then
           sed -i '/WireframeTransparent=/d; $iWireframeTransparent=true' ~/.config/apt-notifierrc; 
       fi
       
    fi

    #test to see if ~/.config/apt-notifierrc contains any blank lines or lines with only whitespace
    grep ^[[:space:]]*$ ~/.config/apt-notifierrc > /dev/null
    if [ "$?" = "0" ]
      then
      #cleanup any blank lines or lines with only whitespace
        sed -i '/^[[:space:]]*$/d' ~/.config/apt-notifierrc
      else
      #no blank lines or lines with only whitespace so do nothing
        :
    fi

    #not really a preference, but remove obsolete *apt-notifier-menu.desktop files if present 
    rm -f ~/.local/share/applications/apt-notifier-menu.desktop
    rm -f ~/.local/share/applications/mx-apt-notifier-menu.desktop   

    #also not a preference, but remove obsolete ~/.config/autostart/apt-notifier-autostart-xdg.desktop file if present
    rm -f ~/.config/autostart/apt-notifier-autostart-xdg.desktop

    #------------------------------------------------------
    # remove obsolete desktop files
    #
    for desktopfile in mx-updater-menu-kde.desktop mx-updater-menu-non-kde.desktop; do
        desktoppath="$HOME/.local/share/applications/$desktopfile" 
        [ -f "$desktoppath" ] && rm -f "$desktoppath"
    done
    #------------------------------------------------------
    #
    # below not used anymore, as we keep only one mx-updater.desktop file with a fixed icon "mx-updater"
    #
    #copy mx-updater-menu-* .desktop files to the ~/.local/share/applications/ folder if they haven't been already
    #
    #
    #[ -e ~/.local/share/applications ] || mkdir -p  ~/.local/share/applications
    #if [ ! -e ~/.local/share/applications/mx-updater-menu-kde.desktop ]
    #  then
    #    cp /usr/share/applications/mx-updater-menu-kde.desktop ~/.local/share/applications/mx-updater-menu-kde.desktop
    #fi
    #if [ ! -e ~/.local/share/applications/mx-updater-menu-non-kde.desktop ]
    #  then
    #    cp /usr/share/applications/mx-updater-menu-non-kde.desktop ~/.local/share/applications/mx-updater-menu-non-kde.desktop
    #fi    

    #for desktopfile in mx-updater-menu-kde.desktop mx-updater-menu-non-kde.desktop
    #  do
    #    case "$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)" in 
    #      classic    ) if [ ! $(grep Icon=mnotify-some-classic ~/.local/share/applications/$desktopfile) ]
    #                     then
    #                       sed -i 's/Icon=.*/Icon=mnotify-some-classic/' ~/.local/share/applications/$desktopfile
    #                   fi
    #                   ;;
    #                 
    #      pulse      ) if [ ! $(grep Icon=mnotify-some-pulse ~/.local/share/applications/$desktopfile) ]
    #                     then
    #                       sed -i 's/Icon=.*/Icon=mnotify-some-pulse/' ~/.local/share/applications/$desktopfile
    #                   fi
    #                   ;;
    #               
    #      wireframe|*) if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
    #                     then
    #                       if [ ! $(grep Icon=mx-updater ~/.local/share/applications/$desktopfile) ]
    #                         then
    #                           sed -i 's/Icon=.*/Icon=mx-updater/' ~/.local/share/applications/$desktopfile
    #                       fi
    #                     else
    #                       if [ ! $(grep Icon=mnotify-some-wireframe ~/.local/share/applications/$desktopfile) ]
    #                         then
    #                           sed -i 's/Icon=.*/Icon=mnotify-some-wireframe/' ~/.local/share/applications/$desktopfile
    #                       fi
    #                   fi
    #                   ;;
    #    esac
    #    #Add a "Type=Application" line to beginning of the .desktop files if there isn't one.
    #    grep  -sq '^Type=Application' ~/.local/share/applications/$desktopfile || sed -i '/^\[Desktop Entry\]/aType=Application' ~/.local/share/applications/$desktopfile
    #  done
    #------------------------------------------------------
                                                      
    '''
           
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['bash %s' % script_file.name],shell=True).wait()

    script_file.close()


def aptnotifier_prefs():
    global Check_for_Updates_by_User
    systray_icon_hide()

    initialize_aptnotifier_prefs()
    
    # ~~~ Localize 3 ~~~

    t01 = _("MX Updater preferences")
    t02 = _("Upgrade mode")
    t03 = _("full upgrade   (recommended)")
    t04 = _("basic upgrade")
    t05 = _("Left-click behaviour   (when updates are available)")
    t06 = _("Other options")
    t07 = _("opens Synaptic")
    t07 = t07.replace("Synaptic", package_manager_name)

    t08 = _("opens MX Updater 'View and Upgrade' window")
    t09 = _("Automatically answer 'yes' to all prompts during full/basic upgrade")
    t10 = _("automatically close terminal window when full/basic upgrade complete")
    t11 = _("check for autoremovable packages after full/basic upgrade")
    t12 = _("Icons")
    t13 = _("classic")
    t14 = _("pulse")
    t15 = _("wireframe")
    t16 = _("Auto-update")
    t17 = _("update automatically   (will not add new or remove existing packages)")
    t18 = _("start MX Updater at login")
    t19 = _("use transparent interior for no-updates wireframe")

 
    shellvar = (
        '    window_title="'                             + t01 + '"\n'
        '    frame_upgrade_behaviour="'                  + t02 + '"\n'
        '    full_upgrade="'                             + t03 + '"\n'
        '    basic_upgrade="'                            + t04 + '"\n'
        '    frame_left_click_behaviour="'               + t05 + '"\n'
        '    frame_other_options="'                      + t06 + '"\n'
        '    left_click_package_manager="'               + t07 + '"\n'
        '    left_click_ViewandUpgrade="'                + t08 + '"\n'
        '    use_apt_get_dash_dash_yes="'                + t09 + '"\n'
        '    auto_close_term_window_when_complete="'     + t10 + '"\n'
        '    check_for_autoremoves="'                    + t11 + '"\n'
        '    frame_Icons="'                              + t12 + '"\n'
        '    label_classic="'                            + t13 + '"\n'
        '    label_pulse="'                              + t14 + '"\n'
        '    label_wireframe="'                          + t15 + '"\n'
        '    frame_Auto_update="'                        + t16 + '"\n' 
        '    auto_update_checkbox_txt="'                 + t17 + '"\n'
        '    label_autostart="'                          + t18 + '"\n'
        '    label_wireframe_transparent="'              + t19 + '"\n'
        )
    
    script = '''#!/bin/bash
''' + shellvar + '''    

    #for MEPIS remove "MX" branding from the $window_title and $left_click_ViewandUpgrade strings
    window_title=$(echo "$window_title"|sed 's/MX /'$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)" "'/')
    left_click_ViewandUpgrade=$(echo "$left_click_ViewandUpgrade"|sed 's/MX /'$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)" "'/')
    IconLookBegin=$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)
    WireframeTransparentBegin=$(grep -sq -m1 WireframeTransparent=true ~/.config/apt-notifierrc && echo true || echo false)
    
    # detect and set autostart

    XDG_AUTOSTART_FILE="/etc/xdg/autostart/mx-updater-autostart.desktop"
    USR_AUTOSTART_FILE="$HOME/.config/autostart/mx-updater-autostart.desktop"
    if grep -sq '^Hidden=true' "$USR_AUTOSTART_FILE"; then
       AutoStart='"false"'
    else
       AutoStart='"true"'
    fi
    # set dialog frame for PrefAutoStart
    Auto_Start_frame=" 
         <frame Auto-start>
          <checkbox active=${AutoStart}>
            <label>${label_autostart}</label>
            <variable>PrefAutoStart</variable>
            <action>:</action>
          </checkbox>
        </frame>"

    TMP=$(mktemp -d /tmp/apt_notifier_preferences_dialog.XXXXXX)
    touch "$TMP"/output
    cat << EOF > "$TMP"/DIALOG
    <window title="@title@" icon-name="mx-updater">
      <vbox>
        <frame @upgrade_behaviour@>
          <radiobutton active="@UpgradeBehaviourAptGetDistUpgrade@">
            <label>@full_upgrade@</label>
            <variable>UpgradeType_dist-upgrade</variable>
            <action>:</action>
          </radiobutton>
          <radiobutton active="@UpgradeBehaviourAptGetUpgrade@">
            <label>@basic_upgrade@</label>
            <variable>UpgradeType_upgrade</variable>
            <action>:</action>
          </radiobutton>
        </frame>
        <frame @leftclick_behaviour@>
          <radiobutton active="@LeftClickBehaviourPackageManager@">
            <label>@opens_package_manager@</label>
            <variable>LeftClickPackageManager</variable>
            <action>:</action>
          </radiobutton>
          <radiobutton active="@LeftClickBehaviourViewAndUpgrade@">
            <label>@opens_View_and_Upgrade@</label>
            <variable>LeftClickViewAndUpgrade</variable>
            <action>:</action>
          </radiobutton>
        </frame>
        <frame @Other_options@>
          <checkbox active="@UpgradeAssumeYes@">
            <label>@use_apt_get_yes@</label>
            <variable>UpgradeAssumeYes</variable>
            <action>:</action>
          </checkbox>
          <checkbox active="@UpgradeAutoClose@">
            <label>@auto_close_term_window@</label>
            <variable>UpgradeAutoClose</variable>
            <action>:</action>
          </checkbox>
         #<checkbox active="@CheckForAutoRemovables@">
         #  <label>@check_for_autoremoves@</label>
         #  <variable>CheckForAutoRemovables</variable>
         #  <action>:</action>
         #</checkbox>
        </frame>
        <frame @Icons@>
          <hbox homogeneous="true">
            <vbox>
              <radiobutton active="@IconLookWireframeDark@">
                <label>@wireframe@</label>
                <variable>IconLook_wireframe_dark</variable>
                <action>:</action>
              </radiobutton>
              <vseparator></vseparator>
              <radiobutton active="@IconLookWireframeLight@">
                <label>@wireframe@</label>
                <variable>IconLook_wireframe_light</variable>
                <action>:</action>
              </radiobutton>
              <vseparator></vseparator>
              <radiobutton active="@IconLookClassic@">
                <label>@classic@</label>
                <variable>IconLook_classic</variable>
                <action>:</action>
              </radiobutton>
              <vseparator></vseparator>
              <vseparator></vseparator>
              <radiobutton active="@IconLookPulse@">
                <label>@pulse@</label>
                <variable>IconLook_pulse</variable>
                <action>:</action>
              </radiobutton>
            </vbox>
            <vbox>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-some-wireframe.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-some-wireframe.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-some-classic.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-some-pulse.png</input></pixmap>
            </vbox>
            <vbox>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-none-wireframe-dark.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-none-wireframe-light.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-none-classic.png</input></pixmap>
              <pixmap icon_size="2"><input file>/usr/share/icons/mnotify-none-pulse.png</input></pixmap>
            </vbox>
          </hbox>
          <checkbox active="@WireframeTransparent@">
            <label>${label_wireframe_transparent}</label>
            <variable>WireframeTransparent</variable>
            <action>:</action>
          </checkbox>
        </frame>
        <frame @Auto_update_label@>
          <checkbox active="@Auto_Update_setting@">
            <label>@autoupdate_checkboxtxt@</label>
            <variable>AutoUpdate</variable>
            <action>:</action>
          </checkbox>
        </frame>
        $Auto_Start_frame
        <hbox>
          <button ok></button>
          <button cancel></button>
        </hbox>
      </vbox>
    </window>
EOF
    sed '/\x23/d' -i "$TMP"/DIALOG

    cat << EOF > "$TMP"/enable_unattended_upgrades
    #!/bin/bash
    for i in @(grep 'APT::Periodic::Unattended-Upgrade "[0-9]+";' /etc/apt/apt.conf.d/* -E | cut -f1 -d: | grep -v ~$); \
    do sed -i 's/[ ]*APT::Periodic::Unattended-Upgrade.*"0".*;/   APT::Periodic::Unattended-Upgrade "1";/' @i; done  
    exit 0
EOF
    sed -i 's/@/\$/g' "$TMP"/enable_unattended_upgrades

    cat << EOF > "$TMP"/disable_unattended_upgrades
    #!/bin/bash
    for i in @(grep 'APT::Periodic::Unattended-Upgrade "[0-9]+*";' /etc/apt/apt.conf.d/* -E | cut -f1 -d: | grep -v ~$); \
    do sed -i 's/[ ]*APT::Periodic::Unattended-Upgrade.*"1".*;/   APT::Periodic::Unattended-Upgrade "0";/' @i; done
    exit 0
EOF
    sed -i 's/@/\$/g' "$TMP"/disable_unattended_upgrades

# edit translateable strings placeholders in "$TMP"/DIALOG
    sed -i 's/@title@/'"$window_title"'/' "$TMP"/DIALOG
    sed -i 's/@upgrade_behaviour@/'"$frame_upgrade_behaviour"'/' "$TMP"/DIALOG
    sed -i 's/@full_upgrade@/'"$full_upgrade"'/' "$TMP"/DIALOG
    sed -i 's/@basic_upgrade@/'"$basic_upgrade"'/' "$TMP"/DIALOG
    sed -i 's/@leftclick_behaviour@/'"$frame_left_click_behaviour"'/' "$TMP"/DIALOG
    sed -i 's/@Other_options@/'"$frame_other_options"'/' "$TMP"/DIALOG
    sed -i 's/@Icons@/'"$frame_Icons"'/' "$TMP"/DIALOG
    sed -i 's/@opens_package_manager@/"'"$left_click_package_manager"'"/' "$TMP"/DIALOG
    sed -i 's/@opens_View_and_Upgrade@/"'"$left_click_ViewandUpgrade"'"/' "$TMP"/DIALOG
    sed -i 's|@use_apt_get_yes@|"'"$use_apt_get_dash_dash_yes"'"|' "$TMP"/DIALOG
    sed -i 's|@auto_close_term_window@|"'"$auto_close_term_window_when_complete"'"|' "$TMP"/DIALOG
    sed -i 's|@check_for_autoremoves@|"'"$check_for_autoremoves"'"|' "$TMP"/DIALOG
    sed -i 's/@classic@/"'"$label_classic"'"/' "$TMP"/DIALOG
    sed -i 's/@pulse@/"'"$label_pulse"'"/' "$TMP"/DIALOG
    sed -i 's/@wireframe@/"'"$label_wireframe"'"/' "$TMP"/DIALOG

    # edit placeholders in "$TMP"/DIALOG to set initial settings of the radiobuttons & checkboxes 
    sed -i 's/@UpgradeBehaviourAptGetUpgrade@/'$(if [ $(grep UpgradeType=upgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeBehaviourAptGetDistUpgrade@/'$(if [ $(grep UpgradeType=dist-upgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@LeftClickBehaviourPackageManager@/'$(if [ $(grep LeftClick=PackageManager ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@LeftClickBehaviourViewAndUpgrade@/'$(if [ $(grep LeftClick=ViewAndUpgrade ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeAssumeYes@/'$(grep UpgradeAssumeYes ~/.config/apt-notifierrc | cut -f2 -d=)'/' "$TMP"/DIALOG
    sed -i 's/@UpgradeAutoClose@/'$(grep UpgradeAutoClose ~/.config/apt-notifierrc | cut -f2 -d=)'/' "$TMP"/DIALOG
    sed -i 's/@CheckForAutoRemovables@/'$(grep CheckForAutoRemovables ~/.config/apt-notifierrc | cut -f2 -d=)'/' "$TMP"/DIALOG

    sed -i 's/@IconLookWireframeDark@/'$(if [ $(grep IconLook=wireframe-dark ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@IconLookWireframeLight@/'$(if [ $(grep IconLook=wireframe-light ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG

    sed -i 's/@IconLookClassic@/'$(if [ $(grep IconLook=classic ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG
    sed -i 's/@IconLookPulse@/'$(if [ $(grep IconLook=pulse ~/.config/apt-notifierrc) ]; then echo -n true; else echo -n false; fi)'/' "$TMP"/DIALOG

    sed -i "s/@WireframeTransparent@/$(grep -sq WireframeTransparent=true ~/.config/apt-notifierrc && echo true || echo false)/" "$TMP"/DIALOG

    # edit placeholder for window icon placeholder in "$TMP"/DIALOG
    
    #--------------------------------------------------------------
    # commented out below, to use mx-updater as windowIcon
    #
    #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
    #  then
    #    if [[ $(grep IconLook=wireframe ~/.config/apt-notifierrc) ]]
    #      then
    #        if [[ $(xfconf-query -lvc xsettings | grep IconThemeName | grep .*Papirus.* -i) ]]
    #          then
    #            sed -i 's/@mnotify-some@/mx-updater/' "$TMP"/DIALOG
    #          else
    #            sed -i 's/@mnotify-some@/mnotify-some-wireframe/' "$TMP"/DIALOG
    #        fi
    #      else
    #        sed -i 's/@mnotify-some@/mnotify-some-'$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d= | xargs echo -n)'/' "$TMP"/DIALOG
    #    fi
    #  else       
    #    sed -i 's/@mnotify-some@/mnotify-some-'$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d= | xargs echo -n)'/' "$TMP"/DIALOG
    #fi    
    #
    #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
    #  then
    #    sed -i 's/file>"\/usr\/share\/icons\/mnotify-some-wireframe.png"/file icon="mx-updater">/' "$TMP"/DIALOG
    #fi    
    #--------------------------------------------------------------
    
    # edit AutoUpdate related translateable string placeholders in "$TMP"/DIALOG
    sed -i 's/@Auto_update_label@/'"$frame_Auto_update"'/' "$TMP"/DIALOG
    sed -i 's/@autoupdate_checkboxtxt@/'"$auto_update_checkbox_txt"'/' "$TMP"/DIALOG
    
    # get what the Unattended-Upgrade status is before bringing up the preferences dialog
    Unattended_Upgrade_before_pref_dialog=0
    eval $(apt-config shell Unattended_Upgrade_before_pref_dialog APT::Periodic::Unattended-Upgrade)
    
    # also use it to set the checkbox setting
    if [ $Unattended_Upgrade_before_pref_dialog = "1" ]
      then
        sed -i 's/@Auto_Update_setting@/true/' "$TMP"/DIALOG
      else
        sed -i 's/@Auto_Update_setting@/false/' "$TMP"/DIALOG
    fi
        
    gtkdialog --file="$TMP"/DIALOG >> "$TMP"/output

    grep EXIT=.*OK.* "$TMP"/output > /dev/null

    if [ "$?" -eq 0 ];
      then
        if [ $(grep UpgradeType_upgrade=.*true.*      "$TMP"/output) ]; then sed -i 's/UpgradeType=dist-upgrade/UpgradeType=upgrade/'       ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeType_dist-upgrade=.*true.* "$TMP"/output) ]; then sed -i 's/UpgradeType=upgrade/UpgradeType=dist-upgrade/'       ~/.config/apt-notifierrc; fi
        if [ $(grep LeftClickViewAndUpgrade=.*true.*  "$TMP"/output) ]; then sed -i 's/LeftClick=PackageManager/LeftClick=ViewAndUpgrade/'        ~/.config/apt-notifierrc; fi
        if [ $(grep LeftClickPackageManager=.*true.*        "$TMP"/output) ]; then sed -i 's/LeftClick=ViewAndUpgrade/LeftClick=PackageManager/'        ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAssumeYes=.*false.*        "$TMP"/output) ]; then sed -i 's/UpgradeAssumeYes=true/UpgradeAssumeYes=false/'       ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAssumeYes=.*true.*         "$TMP"/output) ]; then sed -i 's/UpgradeAssumeYes=false/UpgradeAssumeYes=true/'       ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAutoClose=.*false.*        "$TMP"/output) ]; then sed -i 's/UpgradeAutoClose=true/UpgradeAutoClose=false/'       ~/.config/apt-notifierrc; fi
        if [ $(grep UpgradeAutoClose=.*true.*         "$TMP"/output) ]; then sed -i 's/UpgradeAutoClose=false/UpgradeAutoClose=true/'       ~/.config/apt-notifierrc; fi
        if [ $(grep CheckForAutoRemovables=.*false.*     "$TMP"/output) ]; then sed -i 's/CheckForAutoRemovables=true/CheckForAutoRemovables=false/' ~/.config/apt-notifierrc; fi
        if [ $(grep CheckForAutoRemovables=.*true.*   "$TMP"/output) ]; then sed -i 's/CheckForAutoRemovables=false/CheckForAutoRemovables=true/' ~/.config/apt-notifierrc; fi

        if [ $(grep IconLook_wireframe_dark=.*true.*   "$TMP"/output) ]; then sed -i '/^IconLook=.*/s//IconLook=wireframe-dark/'                ~/.config/apt-notifierrc; fi
        if [ $(grep IconLook_wireframe_light=.*true.*  "$TMP"/output) ]; then sed -i '/^IconLook=.*/s//IconLook=wireframe-light/'                ~/.config/apt-notifierrc; fi
        if [ $(grep IconLook_classic=.*true.*         "$TMP"/output) ]; then sed -i '/^IconLook=.*/s//IconLook=classic/'                ~/.config/apt-notifierrc; fi
        if [ $(grep IconLook_pulse=.*true.*           "$TMP"/output) ]; then sed -i '/^IconLook=.*/s//IconLook=pulse/'                  ~/.config/apt-notifierrc; fi

        grep -sq 'WireframeTransparent=.*true.*' "$TMP"/output && V=true || V=false; sed -i '/WireframeTransparent=/d; $iWireframeTransparent='"$V" ~/.config/apt-notifierrc; 

        if [ $Unattended_Upgrade_before_pref_dialog = "0" ] && [ $(grep AutoUpdate=.*true.* "$TMP"/output) ]
          then
            sh /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-enable-auto-update  sh "$TMP"/enable_unattended_upgrades 2>/dev/null 1>/dev/null
        fi
        if [ $Unattended_Upgrade_before_pref_dialog = "1" ] && [ $(grep AutoUpdate=.*false.* "$TMP"/output) ]
          then
            sh /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-disable-auto-update  sh "$TMP"/disable_unattended_upgrades 2>/dev/null 1>/dev/null
        fi
      else
        :
    fi

    # set autostart
    if grep -sq "^PrefAutoStart=${AutoStart}" $TMP/output; then
       : already set, no change, do nothing
    else
        [ -d "$CONFIG_AUTOSTART" ] || mkdir -p "$CONFIG_AUTOSTART"
        
        # clear autostart file
        if [  -f "$USR_AUTOSTART_FILE" ]; then
           rm -f "$USR_AUTOSTART_FILE"
        fi
        
        # switch Autostart
        if [ "$AutoStart" = '"false"' ]; then
          PrefAutoStart="true" 
          # enable autostart (or alternatively leave "$USR_AUTOSTART_FILE" removed )
          sed  -e '/^Hidden=/d; /^Exec=/aHidden=false' "$XDG_AUTOSTART_FILE" > "$USR_AUTOSTART_FILE"
        else
          PrefAutoStart="false" 
          # disable autostart
          # set autostart to false 
          sed  -e '/^Hidden=/d; /^Exec=/aHidden=true' "$XDG_AUTOSTART_FILE" > "$USR_AUTOSTART_FILE"
        fi
        # fluxbox autostart
        FLUXBOX_STARTUP="$HOME/.fluxbox/startup"
        if [ -w "$FLUXBOX_STARTUP" ]; then
          if [ "$PrefAutoStart" = "true" ]; then
             # enable fluxbox startup 
             sed -i -r -e '\:^([#[:space:]]*)(.*/usr/bin/apt-notifier.*&)[[:space:]]*$:s::\\2:'  "$FLUXBOX_STARTUP" 
          else
             # disable fluxbox startup 
             sed -i -r -e '\:^([#[:space:]]*)(.*/usr/bin/apt-notifier.*&)[[:space:]]*$:s::#\\2:' "$FLUXBOX_STARTUP" 
          fi
        fi
    fi

    rm -rf "$TMP"

    #restart apt-notifier if IconLook setting has been changed
    IconLookNew=$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)
    WireframeTransparentNew=$(grep -sq -m1 WireframeTransparent=true ~/.config/apt-notifierrc && echo true || echo false)
 
    if [ "$IconLookNew" != "$IconLookBegin" ] || [ "$WireframeTransparentNew" != "$WireframeTransparentBegin" ];
      then
        rm $0; apt-notifier-unhide-Icon
    fi

    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['bash %s' % script_file.name],shell=True).wait()
        
    script_file.close()
    Check_for_Updates_by_User = 'true'
    systray_icon_show()
    check_updates()

def apt_history():
    global Check_for_Updates_by_User

    systray_icon_hide()
    # ~~~ Localize 5 ~~~

    t01 = _("History")
    shellvar = '    AptHistory="' + t01 + '"\n'

    script = '''#!/bin/bash
''' + shellvar + '''
    
    TMP=$(mktemp -d /tmp/apt_history.XXXXXX)
    
    apt-history | sed 's/:all/ all/;s/:i386/ i386/;s/:amd64/ amd64/' | column -t > "$TMP"/APT_HISTORY

    read screenWidth screenHeight < <(xdotool getdisplaygeometry)
    
    case "$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)" in 
      classic    ) windowIcon=/usr/share/icons/mnotify-some-classic.png
                   windowIcon=mnotify-some-classic
                   ;;
      pulse      ) windowIcon=/usr/share/icons/mnotify-some-pulse.png
                   windowIcon=mnotify-some-pulse
                   ;;
      wireframe|*)# if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]] 
                  #   then
                  #     if [[ $(xfconf-query -lvc xsettings | grep IconThemeName | grep .*Papirus.* -i) ]]
                  #       then
                  #         windowIcon=mx-updater
                  #       else
                  #         windowIcon=mnotify-some-wireframe
                  #     fi
                  #   else
                  #      windowIcon=/usr/share/icons/mnotify-some-wireframe.png
                  # fi
                   ;;
    esac
    windowIcon=mx-updater

    yad --window-icon=$windowIcon \\
        --width=$(($screenWidth*3/4)) \\
        --height=$(($screenHeight*2/3))  \\
        --center \\
        --title "$AptHistory" \\
        --text-info \\
        --filename="$TMP"/APT_HISTORY \\
        --fontname=mono \\
        --button=gtk-close \\
        --margins=7 \\
        --borders=5
        
    rm -rf "$TMP"    
    
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['bash %s' % script_file.name],shell=True).wait()
    
    script_file.close()
    Check_for_Updates_by_User = 'true'
    systray_icon_show()
    check_updates()
    
def apt_get_update():
    global Check_for_Updates_by_User
    systray_icon_hide()

    # ~~~ Localize 4 ~~~

    t01 = _("Reload")
    
    shellvar = (
    '    reload="' + t01 + '"\n'
    )
    
    script = '''#!/bin/bash
''' + shellvar + '''
    #I="mnotify-some-""$(grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=)"
    #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
    #  then 
    #    if [ $(grep IconLook=wireframe ~/.config/apt-notifierrc) ]
    #      then 
    #        I="/usr/share/icons/Papirus/64x64/apps/mx-updater.svg"
    #    fi
    #fi 
    I="mx-updater"   
    T=" --title=""$(grep -o MX.*[1-9][0-9] /etc/issue|cut -c1-2)"" Updater: $reload"
    /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-reload "$T" "$I"
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(['bash %s' % script_file.name],shell=True).wait()
    script_file.close()
    Check_for_Updates_by_User = 'true'
    systray_icon_show()
    check_updates()

def start_MXPI():
    global Check_for_Updates_by_User
    systray_icon_hide()
    run = subprocess.Popen(['su-to-root -X -c mx-packageinstaller'],shell=True).wait()

    version_installed = subprocess.check_output(["dpkg-query -f '${Version}' -W apt-notifier" ], shell=True)
    if  version_installed != version_at_start:
        run = subprocess.Popen([ "nohup apt-notifier-unhide-Icon & >/dev/null 2>/dev/null" ],shell=True).wait()
        sleep(2)

    Check_for_Updates_by_User = 'true'
    systray_icon_show()
    check_updates()

def re_enable_click():
    global ignoreClick
    ignoreClick = '0'

def start_package_manager0():
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        start_package_manager()    
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

def viewandupgrade0():
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        viewandupgrade()    
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

def start_MXPI_0():
    global ignoreClick
    global Timer
    if ignoreClick != '1':
        start_MXPI()    
        ignoreClick = '1'
        Timer.singleShot(50, re_enable_click)
    else:
        pass

# Define the command to run when left clicking on the Tray Icon
def left_click():
    if text.startswith( "0" ):
        start_package_manager0()
    else:
        """Test ~/.config/apt-notifierrc for LeftClickViewAndUpgrade"""
        command_string = "grep LeftClick=ViewAndUpgrade " + rc_file_name + " > /dev/null"
        exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
        if exit_state == 0:
            viewandupgrade0()
        else:
            start_package_manager0()

# Define the action when left clicking on Tray Icon
def left_click_activated(reason):
    if reason == QtWidgets.QSystemTrayIcon.Trigger:
        left_click()

def read_icon_config():
    """Reads ~/.config/apt-notifierrc, returns 'show' if file doesn't exist or does not contain DontShowIcon"""
    command_string = "grep DontShowIcon " + rc_file_name + " > /dev/null"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state != 0:
        return "show"

def read_icon_look():
    script = '''#!/bin/bash
    grep IconLook ~/.config/apt-notifierrc | cut -f2 -d=
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    # Read the output into a text string
    iconLook = run.stdout.read(128)
    script_file.close()
    return iconLook

def set_noicon():
    """Reads ~/.config/apt-notifierrc. If "DontShowIcon blah blah blah" is already there, don't write it again"""
    command_string = "grep DontShowIcon " + rc_file_name + " > /dev/null"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state != 0:
        file = open(rc_file_name, 'a')
        file.write ('[DontShowIcon] #Remove this entry if you want the apt-notify icon to show even when there are no upgrades available\n')
        file.close()
        subprocess.call(["/usr/bin/apt-notifier"], shell=True, stdout=subprocess.PIPE)
    AptIcon.hide()
    icon_config = "donot show"

def add_rightclick_actions():
    ActionsMenu.clear()
    """Test ~/.config/apt-notifierrc for LeftClickViewAndUpgrade"""
    command_string = "grep LeftClick=ViewAndUpgrade " + rc_file_name + " > /dev/null"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        ActionsMenu.addAction(View_and_Upgrade).triggered.connect( viewandupgrade0 )
        ActionsMenu.addSeparator()
        ActionsMenu.addAction(Upgrade_using_package_manager).triggered.connect( start_package_manager0 )
    else:
        ActionsMenu.addAction(Upgrade_using_package_manager).triggered.connect( start_package_manager0)
        ActionsMenu.addSeparator()
        ActionsMenu.addAction(View_and_Upgrade).triggered.connect( viewandupgrade0 )
    command_string = "test -e /usr/bin/mx-packageinstaller > /dev/null"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        add_MXPI_action()
    add_apt_history_action()        
    command_string = "test $(apt-config shell U APT::Periodic::Unattended-Upgrade | cut -f2 -d= | cut -c2- | rev | cut -c2- | rev) != 0"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        add_view_unattended_upgrades_logs_action()
        add_view_unattended_upgrades_dpkg_logs_action()
    add_apt_get_update_action()
    add_apt_notifier_help_action()
    add_package_manager_help_action()
    add_aptnotifier_prefs_action()
    add_about_action()
    add_quit_action()
    command_string = "deartifact-xfce-systray-icons 1 &"
    subprocess.call([command_string], shell=True)               

def add_hide_action():
    ActionsMenu.clear()
    if icon_config == "show":
        hide_action = ActionsMenu.addAction(Hide_until_updates_available)
        hide_action.triggered.connect( set_noicon )
        ActionsMenu.addSeparator()
        ActionsMenu.addAction(package_manager_name).triggered.connect( start_package_manager0 )
    command_string = "test -e /usr/bin/mx-packageinstaller > /dev/null"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        add_MXPI_action()
    add_apt_history_action()    
    command_string = "test $(apt-config shell U APT::Periodic::Unattended-Upgrade | cut -f2 -d= | cut -c2- | rev | cut -c2- | rev) != 0"
    exit_state = subprocess.call([command_string], shell=True, stdout=subprocess.PIPE)
    if exit_state == 0:
        add_view_unattended_upgrades_logs_action()
        add_view_unattended_upgrades_dpkg_logs_action()
    add_apt_get_update_action()
    add_apt_notifier_help_action()
    add_package_manager_help_action()
    add_aptnotifier_prefs_action()
    add_about_action()
    add_quit_action()
    command_string = "deartifact-xfce-systray-icons 1 &"
    subprocess.call([command_string], shell=True)                  

def add_quit_action():
    ActionsMenu.addSeparator()
    quit_action = ActionsMenu.addAction(QuitIcon,Quit_Apt_Notifier)
    quit_action.triggered.connect( exit )

def add_apt_notifier_help_action():
    ActionsMenu.addSeparator()
    apt_notifier_help_action = ActionsMenu.addAction(HelpIcon,Apt_Notifier_Help)
    apt_notifier_help_action.triggered.connect(open_apt_notifier_help)
    
def open_apt_notifier_help():
    systray_icon_hide()
    script = '''#!/bin/bash
    case $(echo $LANG | cut -f1 -d_) in
      fr) HelpUrl="https://mxlinux.org/wiki/help-files/help-mx-apt-notifier-notificateur-dapt" ;;
       *) HelpUrl="https://mxlinux.org/wiki/help-files/help-mx-apt-notifier" ;;
    esac
    test -e /usr/bin/mx-viewer
    if [ $? -eq 0 ]
      then
        mx-viewer $HelpUrl
      else
        xdg-open  $HelpUrl
    fi
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    run.stdout.read(128)
    script_file.close()
    systray_icon_show()

def add_package_manager_help_action():
    ActionsMenu.addSeparator()
    package_manager_help_action = ActionsMenu.addAction(HelpIcon,Package_Manager_Help)
    package_manager_help_action.triggered.connect(open_package_manager_help)
    
def open_package_manager_help():
    systray_icon_hide()
    
    HelpUrlBase="https://mxlinux.org/wiki/help-files/help-" + package_manager
    script = '''#!/bin/bash

    '''
    script = script +  "HelpUrlBase=" + HelpUrlBase
    script = script +  '''

    #english     HelpUrl = HelpUrlBase
    #non-english HelpUrl = HelpUrlBase + "-" + "{2 character suffix - de, es, fr, it, etc.}"
    case $(echo $LANG | cut -f1 -d_) in
      en) HelpUrl="$HelpUrlBase"                                 ;;
       *) HelpUrl="$HelpUrlBase""-""$(echo $LANG | cut -f1 -d_)" ;;
    esac
    #test to see if HelpUrl page exists, if it doesn't change it to HelpUrlBase (english version)
    wget $HelpUrl --spider -q
    if [ $? -eq 0 ]
      then : 
      else HelpUrl="$HelpUrlBase"
    fi
    #test to see if pdf or html (a 0 result = pdf)
    echo $HelpUrl | grep \.pdf > /dev/null
    if [ $? -eq 0 ]
      then
        TMP=$(mktemp -d /tmp/package_manager_help.XXXXXX)
        curl $HelpUrl -o "$TMP"/$(basename $HelpUrl)
        qpdfview "$TMP"/$(basename $HelpUrl)#$SynapticPage
        rm -rf "$TMP"        
      else
        test -e /usr/bin/mx-viewer
        if [ $? -eq 0 ]
          then
            mx-viewer $HelpUrl
          else
            xdg-open  $HelpUrl
        fi
    fi        
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    run.stdout.read(128)
    script_file.close()
    systray_icon_show()

def add_aptnotifier_prefs_action():
    ActionsMenu.addSeparator()
    aptnotifier_prefs_action =  ActionsMenu.addAction(Apt_Notifier_Preferences)
    aptnotifier_prefs_action.triggered.connect( aptnotifier_prefs )

def add_MXPI_action():
    ActionsMenu.addSeparator()
    MXPI_action =  ActionsMenu.addAction(MX_Package_Installer)
    MXPI_action.triggered.connect( start_MXPI_0 )

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

    # Not really using the string variables below, but it makes it so that gettext is
    # able to find translations for the strings in the embedded script that follows.

    # ~~~ Localize 5 ~~~

    MX_Updater                                  = unicode (_("MX Updater")                                              ,'utf-8')
    About_MX_Updater                            = unicode (_("About MX Updater")                                        ,'utf-8')
    Changelog                                   = unicode (_("Changelog")                                               ,'utf-8')
    License                                     = unicode (_("License")                                                 ,'utf-8')
    Cancel                                      = unicode (_("Cancel")                                                  ,'utf-8')
    Close                                       = unicode (_("Close")                                                  ,'utf-8')
    Description                                 = unicode (_("Tray applet to notify of system and application updates") ,'utf-8')

    # Using an embedded script to display the 'About' dialog text, because when run within the main python
    # script, closing the dialog window was also causing the main python script (apt-notifier.py) to quit.
    script = """#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import subprocess
import gettext
import locale
from PyQt5 import QtWidgets, QtGui
from PyQt5.QtWidgets import QApplication, QPushButton, QMessageBox
from PyQt5.QtGui import QIcon
from string import Template
#----------------------------------------------------
# not used
#gettext.bindtextdomain('apt-notifier', '/usr/share/locale')
#gettext.textdomain('apt-notifier')
#_ = gettext.gettext
#gettext.install('apt-notifier')
#----------------------------------------------------
#class gettextFallback(gettext.NullTranslations):
#    def gettext(self, msg):
#        if msg == "Close":
#            msg = _("Cancel")
#        return msg

class gettextFallback(gettext.NullTranslations):
    def gettext(self, msg):
        if msg == "Close":
            if  gettext.find("gtk30", "/usr/share/locale" ) is not None:
                msg = gettext.translation("gtk30", "/usr/share/locale").gettext(msg)
            elif gettext.find("okular", "/usr/share/locale" ) is not None:
                msg = gettext.translation('okular', '/usr/share/locale').gettext(msg)
        return msg


class gettextTranslations(gettext.GNUTranslations, object):
    def __init__(self, *args, **kwargs):
        super(gettextTranslations, self).__init__(*args, **kwargs)
        self.add_fallback(gettextFallback())

locale, _data = locale.getdefaultlocale()

tr = gettext.translation(
    "apt-notifier",
    "/usr/share/locale",
    [locale],
    class_=gettextTranslations,
    fallback=True
)

tr.install()
_ = tr.gettext

#----------------------------------------------------


def About(aboutBox):
    me      = _('MX Updater')
    about   = _('Tray applet to notify of system and application updates')
    version = subprocess.check_output(["dpkg-query -f '${Version}' -W apt-notifier" ], shell=True).decode('utf-8')

    aboutText= '''
    <p align=center><b><h2>$me</h2></b></p>
    <p align=center>Version: $version</p>
    <p align=center><h3>$about</h3></p>
    <p align=center><a href=http://mxlinux.org>http://mxlinux.org</a>
    <br></p><p align=center>Copyright (c) MX Linux<br /><br/></p>
     '''
    aboutText=Template(aboutText).substitute(about=about, me=me, version=version)
    #aboutBox = QMessageBox()
    aboutBox.setWindowTitle(_('About MX Updater'))
    aboutBox.setWindowIcon(QtGui.QIcon('/usr/share/icons/hicolor/scalable/mx-updater.svg'))
    aboutBox.setText(aboutText)
    changelogButton = aboutBox.addButton( (_('Changelog')), QMessageBox.ActionRole)
    licenseButton   = aboutBox.addButton( (_('License'))  , QMessageBox.ActionRole)
    closeButton     = aboutBox.addButton( (_('Close'))    , QMessageBox.RejectRole)
    aboutBox.setDefaultButton(closeButton)
    aboutBox.setEscapeButton(closeButton)
    
    reply = aboutBox.exec_()

    if aboutBox.clickedButton() == closeButton:
        sys.exit(reply)

    if aboutBox.clickedButton() == licenseButton:
        p=subprocess.run(["/usr/bin/mx-viewer", 
                           "/usr/share/doc/apt-notifier/license.html", 
                           "MX Apt-notifier license"], 
                           stdin=None, stdout=None, stderr=None)
        sys.exit(reply)

    if aboutBox.clickedButton() == changelogButton:
        command_string = '''
            windowIcon=mx-updater; 
            read width height < <(xdotool getdisplaygeometry); 
            width=$(($width*3/4)); 
            height=$(($height*2/3)); 
            title=$(gettext -d apt-notifier Changelog); 
            zcat /usr/share/doc/apt-notifier/changelog.gz | 
            yad --width=$width 
              --height=$height 
              --center           
              --button=gtk-close 
              --window-icon=$windowIcon 
              --title="$title" 
              --fontname=mono    
              --margins=7        
              --borders=5        
              --text-info
            '''
        command = " ".join(command_string.split())
        command = "bash -c '%s'" % command
        p=subprocess.call([command], shell=True)
        sys.exit(reply)

def main():
    app = QApplication(sys.argv)
    aboutBox = QMessageBox()
    About(aboutBox)
    aboutBox.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
"""
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["python3 %s 2>/dev/null >/dev/null" % script_file.name],shell=True).wait()
    script_file.close()
    
    
def view_unattended_upgrades_logs():
    # ~~~ Localize 6 ~~~
    t01 = _("MX Auto-update  --  unattended-upgrades log viewer")
    t02 = _("No logs found.")
    t03 = _("For a less detailed view see 'Auto-update dpkg log(s)' or 'History'.")
    t04 = _("Press 'h' for help, 'q' to quit")
    shellvar = (
        '    Title="'                  + t01 + '"\n'
        '    NoLogsFound="'            + t02 + '"\n'
        '    SeeHistory="'             + t03 + '"\n'
        '    LessPrompt="'             + t04 + '"\n'
        )
    script = '''#!/bin/bash
''' + shellvar + '''
    Title="$(sed "s|[']|\\\\'|g" <<<"${Title}")"
    User=$(who | grep '(:0)' -m1 | awk '{print $1}')
    if [ "$User" != "root" ]
      then IconLook="$(grep IconLook /home/"$User"/.config/apt-notifierrc | cut -f2 -d=)"
      else IconLook="$(grep IconLook /root/.config/apt-notifierrc | cut -f2 -d=)"
    fi
    Icon="mx-updater"
    #pkexecWrapper="/usr/lib/apt-notifier/pkexec-wrappers/mx-updater-view-auto-update-logs"
    #terminalCMD="mx-updater_unattended_upgrades_log_view"
    #Uncomment lines below to pass strings as arguments
    #NoLogsFound="$(sed "s|[']|\\\\\\'|g" <<<"$NoLogsFound")"
    #NoLogsFound="$(sed 's/ /\\\\ /g' <<<"$NoLogsFound")"
    #SeeHistory="$(sed "s|[']|\\\\\\'|g" <<<"$SeeHistory")"
    #SeeHistory="$(sed 's/ /\\\\ /g' <<<"$SeeHistory")"
    #LessPrompt="$(sed "s|[']|\\\\\\'|g" <<<"$LessPrompt")"
    #LessPrompt="$(sed 's/ /\\\\ /g' <<<"$LessPrompt")"
    #terminalCMD="${terminalCMD}"" ""${SeeHistory}"
    #terminalCMD="${terminalCMD}"" ""${NoLogsFound}"
    #terminalCMD="${terminalCMD}"" ""${LessPrompt}"
    #if [ -x /usr/bin/xfce4-terminal ]
    #  then
    #    sh "${pkexecWrapper}" xfce4-terminal --icon=/usr/share/icons/mnotify-some-"$IconLook".png\
    #       --title='"'"${Title}"'"' --hide-menubar -e "${terminalCMD}" 2>/dev/null
    #  else
    #    sh "${pkexecWrapper}" x-terminal-emulator  -e "${terminalCMD}" 2>/dev/null
    #fi
    /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-view-auto-update-logs \
    "${Title}" \
    "$Icon"
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    run.stdout.read(128)
    script_file.close()

def view_unattended_upgrades_dpkg_logs():
    # ~~~ Localize 7 ~~~
    t01 = _("MX Auto-update  --  unattended-upgrades dpkg log viewer")
    t02 = _("No unattended-upgrades dpkg log(s) found.")
    t03 = _("Press 'h' for help, 'q' to quit")
    shellvar = (
        '    Title="'                  + t01 + '"\n'
        '    NoLogsFound="'            + t02 + '"\n'
        '    LessPrompt="'             + t03 + '"\n'
        )
    script = '''#!/bin/bash
''' + shellvar + '''
    Title="$(sed "s|[']|\\\\'|g" <<<"${Title}")"
    #User=$(who | grep '(:0)' -m1 | awk '{print $1}')
    #if [ "$User" != "root" ]
    #  then IconLook="$(grep IconLook /home/"$User"/.config/apt-notifierrc | cut -f2 -d=)"
    #  else IconLook="$(grep IconLook /root/.config/apt-notifierrc | cut -f2 -d=)"
    #fi
    
    #Icon="mnotify-some-""$IconLook"
    #if [[ $(find /usr/share/{icons,pixmaps} -name mx-updater.svg) ]]
    #  then
    #    if [ $(grep IconLook=wireframe ~/.config/apt-notifierrc) ]
    #      then
    #        if [[ $(xfconf-query -lvc xsettings | grep IconThemeName | grep .*Papirus.* -i) ]]
    #          then
    #            Icon=mx-updater
    #          else
    #            Icon=mnotify-some-wireframe
    #        fi
    #    fi
    #fi     
    #pkexecWrapper="/usr/lib/apt-notifier/pkexec-wrappers/mx-updater-view-auto-update-dpkg-logs"
    #terminalCMD="mx-updater_unattended_upgrades_dpkg_log_view"
    #Uncomment lines below to pass the strings as arguments
    #NoLogsFound="$(sed "s|[']|\\\\\\'|g" <<<"$NoLogsFound")"
    #NoLogsFound="$(sed 's/ /\\\\ /g' <<<"$NoLogsFound")"
    #LessPrompt="$(sed "s|[']|\\\\\\'|g" <<<"$LessPrompt")"
    #LessPrompt="$(sed 's/ /\\\\ /g' <<<"$LessPrompt")"
    #terminalCMD="${terminalCMD}"" ""${NoLogsFound}"
    #terminalCMD="${terminalCMD}"" ""${LessPrompt}"
    #if [ -x /usr/bin/xfce4-terminal ]
    #  then
    #    sh "${pkexecWrapper}" xfce4-terminal --icon=/usr/share/icons/mnotify-some-"$IconLook".png\
    #       --title='"'"${Title}"'"' --hide-menubar -e "${terminalCMD}" 2>/dev/null
    #  else
    #    sh "${pkexecWrapper}" x-terminal-emulator  -e "${terminalCMD}" 2>/dev/null
    #fi
    Icon=mx-updater
    /usr/lib/apt-notifier/pkexec-wrappers/mx-updater-view-auto-update-dpkg-logs \
    "${Title}" \
    "$Icon"
    '''
    script_file = tempfile.NamedTemporaryFile('wt')
    script_file.write(script)
    script_file.flush()
    run = subprocess.Popen(["echo -n `bash %s`" % script_file.name],shell=True, stdout=subprocess.PIPE)
    run.stdout.read(128)
    script_file.close()

# General application code	
def main():
    # Define Core objects, Tray icon and QTimer 
    global AptNotify
    global AptIcon
    global QuitIcon
    global icon_config
    global quit_action    
    global Timer
    global initialize_aptnotifier_prefs
    global read_icon_look
    global icon_set
    
    set_translations()
    initialize_aptnotifier_prefs()
    AptNotify = QtWidgets.QApplication(sys.argv)
    AptIcon = QtWidgets.QSystemTrayIcon()
    Timer = QtCore.QTimer()
    icon_config = read_icon_config()
    # Define the icons:
    global NoUpdatesIcon
    global NewUpdatesIcon
    global HelpIcon
    
    # read in icon look into a variable
    icon_set = read_icon_look()
    tray_icon_noupdates  =  "/usr/share/icons/mnotify-none-" + icon_set + ".png"
    tray_icon_newupdates =  "/usr/share/icons/mnotify-some-" + icon_set + ".png"

    # Detect WireframeTransparent is set ~/.config/apt-notifierrc
    if "wireframe" in icon_set:
        tray_icon_newupdates =  "/usr/share/icons/mnotify-some-wireframe.png"
        WireframeTransparent = subprocess.call(["grep -sq WireframeTransparent=true ~/.config/apt-notifierrc && exit 1 || exit 0"], shell=True, stdout=subprocess.PIPE)
        if WireframeTransparent:
            tray_icon_noupdates =  "/usr/share/icons/mnotify-none-" + icon_set + "-transparent.png"
        
    NoUpdatesIcon   = QtGui.QIcon(tray_icon_noupdates)
    NewUpdatesIcon  = QtGui.QIcon(tray_icon_newupdates)
    HelpIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/apps/help-browser.png")
    QuitIcon = QtGui.QIcon("/usr/share/icons/oxygen/22x22/actions/system-shutdown.png")
    # Create the right-click menu and add the Tooltip text
    global ActionsMenu
    ActionsMenu = QtWidgets.QMenu()
    AptIcon.activated.connect( left_click_activated )
    Timer.timeout.connect( check_updates )
    # Integrate it together,apply checking of updated packages and set timer to every 1 minute(s) (1 second = 1000)
    AptIcon.setIcon(NoUpdatesIcon)
    check_updates()
    AptIcon.setContextMenu(ActionsMenu)
    if icon_config == "show":
        systray_icon_show()
        AptIcon.show()
    Timer.start(60000)
    if AptNotify.isSessionRestored():
        sys.exit(1)
    sys.exit(AptNotify.exec_())

def systray_icon_hide():

    running_in_plasma = subprocess.call(["pgrep  -x plasmashell >/dev/null && exit 1 || exit 0"], shell=True, stdout=subprocess.PIPE)
    if not running_in_plasma:
       return

    if not spawn.find_executable("qdbus"):
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

    running_in_plasma = subprocess.call(["pgrep -x plasmashell >/dev/null && exit 1 || exit 0"], shell=True, stdout=subprocess.PIPE)
    if not running_in_plasma:
       return

    if not spawn.find_executable("qdbus"):
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

if __name__ == '__main__':
    main()
