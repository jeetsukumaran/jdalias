#! /usr/bin/env python

############################################################################
##  jdalias.py
##
##  Copyright 2007 Jeet Sukumaran (jeetsukumaran@frogweb.org)
##
##  This program is free software; you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation; either version 2 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License along
##  with this program; if not, write to the Free Software Foundation, Inc.,
##  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
##
############################################################################

"""
Command-line directory navigation utility. Manages file of directory
aliases, and can be called to evaluate aliases into
directories. Inspired by the 'go' command found at:
http://opensource.devdaily.com/goCommand.shtml.

Use "jdalias.py --install" to install.
Then invoke using "jd".

"""

SHELLFUN_NAME = "jd"

import datetime
import os
import sys
import shutil
#from operator import itemgetter
from optparse import OptionParser

def jdalias_default_directory():
    return os.path.join(os.path.expanduser('~'), '.jdalias')

def shell_func(jdalias_path):

    expansion = {
        'timestamp': str(datetime.datetime.today()),
        'SHELLFUN_NAME': SHELLFUN_NAME, 
        'jdalias_path': jdalias_path
         }

    template = """#####################################################
# Wrapper and bash completion for jadlias.py, 
# Auto-written by installer on %(timestamp)s.
# Source/copy this into bash.bashrc or the equivalent.
# Invoke via "%(SHELLFUN_NAME)s".

# if 'jdalias.py' is not on this path, modify this 
# to point at the correct location
JDALIAS='%(jdalias_path)s' 

function %(SHELLFUN_NAME)s() {
 
    if [ $# = 0 ]
    then
        # no parameters specified on command line:
        # list aliases
        #echo "Please select a destination directory using one of the aliases"
        #echo "below, specified by number or by sufficient initial characters"
        #echo "to be resolved unambiguously."
        #echo ""
        $JDALIAS -l
    elif [ ${1:0:1} = '-' ]
    then
        # parameter specified is a command option
        # to the alias manager:
        # pass all arguments to program as separate strings
        $JDALIAS "$@"
    else
        target=$($JDALIAS -e $1)
        if [ $target ]
        then
            # parameter is an alias, and an unambiguous matching value was found
            echo $target
            #export OLDPWD=pwd
            cd $target
        else
            # parameter is an alias, but it is not found in the dictionary
           echo "Directory alias \\"$1\\" not found or could not be matched unambigiously"
           echo "to a known alias. Use %(SHELLFUN_NAME)s --list to see available aliases."
        fi
    fi
}

######################################################
# Bash completion for %(SHELLFUN_NAME)s
_%(SHELLFUN_NAME)s() 
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    opts=$($JDALIAS --choices)

    if [[ ${cur} == * ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi
}

complete -F _%(SHELLFUN_NAME)s %(SHELLFUN_NAME)s 
""" % expansion

    return template

def source_into_shellrc(shellrc, shellfun_path, quiet=False, force_create=False):
    if os.path.exists(shellrc):
        modbash = True
        b = open(shellrc, 'r')
        for i in b.readlines():
            if i.count('. %s' % shellfun_path):
                # destination script already sourced in .bashrc ...
                # skip modifying bash
                if not quiet:
                    print '    Skipping modification: "%s" already sources "%s".' % (shellrc, shellfun_path)
                    modbash = False
                    break
    else:
        if force_create:
            modbash = True
        else:
            modbash = False
    if modbash:
        if not quiet:
            print
            print '    Modifying shell resource file "%s" to source "%s" ...' % (shellrc, shellfun_path)
        b = open(shellrc, 'a')
        b.write('\n')
        b.write('# source jdalias wrapper function\n')
        b.write('. %s\n' % shellfun_path)
        b.write('\n')
        b.close()
    return modbash
    
def install_jdalias(install_path=None, quiet=False):

    # set up directory
    if not install_path:
        install_path = jdalias_default_directory()
    if not quiet:
        print
        print 'STARTING BOOTSTRAP INSTALL FROM: "%s"' % os.path.abspath(sys.argv[0]) 
        #print 'INSTALLING TO: "%s" ...' % install_path

    # directory creation
    if not quiet:
        print
        print 'CREATING INSTALLATION DIRECTORY: "%s"' % install_path
    if os.path.exists(install_path):
        if os.path.isdir(install_path):
            if not quiet:
                print "    Skipping directory creation: already exists."
        else:
            print >>sys.stderr, 'File called "%s" already exists. Cannot create installation directory.'
            sys.exit(1)
    else:
        os.makedirs(install_path)
        print "    Directory created."

    # set up alias manager script
    if not quiet:
        print
        print 'COPYING ALIAS MANAGER SCRIPT ...'
    source = os.path.abspath(sys.argv[0])
    destfname = os.path.basename(sys.argv[0])
    dest = os.path.join(install_path, destfname)
    if os.path.exists(dest) and os.path.samefile(source, dest):
        # probably can also use if (os.path.abspath(source))==(os.path.abspath(dest)):
        print '    Script is trying to install itself on top of itself!'
        print '    Invoked script was "%s"' % os.path.abspath(sys.argv[0])
        print '    If you meant to invoke a script of the same name in another'
        print '    location please call the script explicitly using its full path.'
        print '    Skipping copying of script for now.'
    else:
        shutil.copyfile(source, dest)
        os.chmod(dest, 0755)        
        if not quiet:
            print '    Alias manager script copied to installation directory, "%s".' % dest

    # set up bash script
    shellfun_path = os.path.join(install_path, 'jd.sh')
    sh = open(shellfun_path, 'w')
    sh.write(shell_func(dest)+'\n')
    sh.close()
    
    modbash = True
    
    ## TODO: deal with alternate rc files: cshrc etc.
    ## by searching through all possibilities
    shellrc = os.path.expanduser('~/.bashrc')
    if not quiet:
        print
        print 'SOURCING SHELL FUNCTIONS INTO RESOURCE FILE: "%s"' % shellrc
    if os.path.exists(shellrc):
        source_into_shellrc(shellrc, shellfun_path, quiet)
        if not quiet:
            print
            print "INSTALLATION COMPLETE!"
            print "    You will need to relogin or start a new shell to use the utility."
            print '    Use "%s -a <ALIAS> </PATH/TO/DIRECTORY>" to begin defining aliases.' % SHELLFUN_NAME
            print '    Use "%s --help" to see available options.' % SHELLFUN_NAME

    else:
        print >>sys.stderr, ''
        print >>sys.stderr, 'Could not find default shell resource file "%s".' % shellrc
        print >>sys.stderr, 'Please edit the appropriate file yourself, and include the following'
        print >>sys.stderr, 'line at the end of the file:'
        print >>sys.stderr, ''
        print >>sys.stderr, '    . %s' % shellfun_path
        print >>sys.stderr, ''
        print >>sys.stderr, 'You will then need to relogin to use this utility.'
        print >>sys.stderr, 'Use "%s -a <ALIAS> </PATH/TO/DIRECTORY>" to begin defining aliases.' % SHELLFUN_NAME
        print >>sys.stderr, 'Use "%s --help" to see available options.' % SHELLFUN_NAME
    
        
class AliasManager(object):
    def __init__(self, alias_filepath=None):
        self.__alias_filepath = None
        self.alias_filepath = alias_filepath
        self.aliases = []
        self.alias_mappings = {}
        self.load_aliases()
        self.quiet = False
    def _get_alias_filepath(self):
        return self.__alias_filepath
    def _set_alias_filepath(self, p):
        if not p:
            evar = os.environ.get('JDALIAS_DEFS')
            if not evar:
                p = os.path.join(jdalias_default_directory(), 'jdalias.defs')
            else:
                p = os.path.expanduser(evar)
        self.__alias_filepath = os.path.expanduser(p)
    alias_filepath = property(_get_alias_filepath, _set_alias_filepath)
    def match_alias(self, alias, ignore_case=True, minimal_match=True):
        if alias in self.aliases:
            return alias
        else:
            # see if it can be cast to a number
            try:
                a = int(alias)
                if a <= len(self.aliases):
                    # if a is a valid integer, and is a valid 1-based index
                    # into the list of aliases, then assign it correctly (IF
                    # there is no alias already defined for that integer).
                    # In other words, treat an integer alias as a numerical
                    # index unless a proper alias is defined for it
                    return self.aliases[a-1]
                else:
                    return None
            except:
                found = []
                for a in self.aliases:
                    if a.startswith(alias):
                        found.append(a)
                if len(found) == 1:
                    return found[0]
                else:
                    return None
    def parse_error(self, line_number, line, message):
        # probably should raise an exception
        # here in production code
        print 'Error parsing alias file "%s", line %d:' % (self.alias_filepath, line_number)
        print '>>',line
        print message
        sys.exit(1)
    def save_aliases(self):
        afile = open(self.alias_filepath, 'w')
        for a in self.aliases:
            afile.write("%s = %s\n" % (a, self.alias_mappings[a]))
        afile.close()
    def load_aliases(self):
        self.aliases = []
        self.alias_mappings = {}        
        if os.path.exists(self.alias_filepath):
            afile = open(self.alias_filepath,'r')
            lines = afile.readlines()
            i = 0
            for entry in lines:
                if entry and not entry.strip().startswith('#'):
                    i = i + 1
                    entry = entry.strip('\n')
                    elements = entry.split('=',1)
                    if len(elements) < 2:
                        self.parse_error(i, entry, 'Badly formed alias definition.\n' \
                                                   'Must be in the form of: "alias = /path/to/directory".')
                    else:
                        alias = elements[0].strip()
                        if elements[1].count('#'):
                            target = (elements[1][:elements[1].index('#')]).strip()
                        else:
                            target = elements[1].strip()
                        if not target:
                            # maybe we should flag this as an error?
                            target = '~'
                        target = os.path.abspath(os.path.expanduser(target))
                        self.aliases.append(alias)
                        self.alias_mappings[alias] = target
    def add_alias(self, alias, directory, prompt_to_overwrite=True):
        directory = os.path.abspath(os.path.expanduser(directory))
        if self.alias_mappings.has_key(alias) and prompt_to_overwrite:
            ok = raw_input('Alias "%s" (=> "%s") already exists.\nReplace with new definition (y/N)? ' % (alias, self.alias_mappings[alias]))
            if not ok.lower().strip().startswith('y'):
                return
        if alias not in self.aliases:
            self.aliases.append(alias)
        self.alias_mappings[alias] = directory
        self.save_aliases()
    def remove_alias(self, raw_alias, prompt_to_confirm=True):
        alias = self.match_alias(raw_alias)
        if alias:
            if prompt_to_confirm:
                ok = raw_input('Alias "%s" (=> "%s") will be deleted. Proceed (y/N)? ' % (alias, self.alias_mappings[alias]))
                if not ok.lower().strip().startswith('y'):
                    return
            try:
                self.aliases.remove(alias)
            except:
                pass
            try:
                del self.alias_mappings[alias]
            except:
                pass
            self.save_aliases()
        else:
            print 'Alias "%s" not found.' % raw_alias
    def sort_aliases(self):
        if len(self.aliases) > 0:
            self.aliases.sort()
            self.save_aliases()
            self.load_aliases()
        self.list_aliases()
    def clean_aliases(self, quiet=False):
        if len(self.aliases):
            for alias in self.aliases:
                aliased_dir = self.alias_mappings[alias]
                if os.path.exists(aliased_dir) and os.path.isdir(aliased_dir):
                    pass
                else:
                    if not quiet:
                        print 'Removing broken alias "%s": %s' % (alias, aliased_dir)
                    self.remove_alias(alias, prompt_to_confirm=False)
    def list_aliases(self, show_broken=False):
        if len(self.aliases) > 0:
            max_len = max([len(a) for a in self.aliases]) + 4
            i = 0
            for a in self.aliases:
                mapping = self.alias_mappings[a]
                alias = "%3d: %s %s" % (i+1, (a + ' ').ljust(max_len), mapping)
                if show_broken:                    
                    if os.path.exists(self.alias_mappings[a]):
                        if os.path.isdir(self.alias_mappings[a]):
                            #print '     OK'
                            pass
                        else:
                            print alias
                            print '     ERROR: Path is not a directory'
                    else:
                        print alias
                        print '     ERROR: Path does not exist'
                else:
                    print alias
                i = i + 1
        else:
            print 'No aliases defined in "%s".' % self.alias_filepath
            print 'Use "%s -a </path/to/directory>" to define an alias.' % SHELLFUN_NAME 
    def jump_to(self, alias):
        """
        Unfortunately any directory change executed within this script
        only effects the process that the script is executing in, and
        not the parent shell that invoked the script. Thus, THERE IS
        NO WAY to change the calling shell directory from within this
        script. Hence the following hack. A bash shell script (see
        comments at beginning of this file) that calls this script
        with the appropriate parameters and gets passed back the
        correct directory name which it then uses to go to the correct
        place.
        """
    def evaluate(self, alias):
        alias = self.match_alias(alias)
        if alias and self.alias_mappings.has_key(alias):
            return self.alias_mappings[alias]
        else:
            return ''
    def check_alias(self, alias):
        alias = self.match_alias(alias)
        if alias and self.alias_mappings.has_key(alias):
            return True
        else:
            return False
    def choices(self):
        if self.aliases:
            return ' '.join(self.aliases)
        else:
            return ""

def main():
    usage = "%s [options] <alias> [<directory>]" % SHELLFUN_NAME
    description = "If no options given, jumps to directory specified by ALIAS (which can "\
                  "specified by its numerical list index or partially, as long as " \
                  "sufficient characters are given so that it is unambigously specified). "\
                  "Otherwise, performs alias management as dictated by options."
    parser = OptionParser(usage=usage, add_help_option=True, description=description, version='1.0')

    parser.add_option("-?", action="help", help="show this help message and exit")
    parser.add_option("-a", "--add", dest="add_alias", default=False, action="store_true", help="add new <alias>, mapping it to <directory>, or current directory if <directory> not given")
    parser.add_option("-l", "--list", dest="list_aliases", default=False, action="store_true", help="list available aliases")
    parser.add_option("-r", "--remove", dest="remove_alias", default=False, action="store_true", help="remove <alias>")
    parser.add_option("-y", "--no-confirm", dest="no_confirm", default=False, action="store_true", help="do not prompt for confirmation when overwriting or removing aliases")
    parser.add_option("-e", "--eval", dest="evaluate", default=False, action="store_true", help="evaluate and return (print) alias if found/matched, or blank if otherwise")
    parser.add_option("--sort-aliases", dest="sort_aliases", default=False, action="store_true", help="sort alias definitions alphabetically by aliases and resave")
#    parser.add_option("--sort-dirs", dest="sort_directories", default=False, action="store_true", help="sort alias definitions alphabetically by directory paths and resave")
    parser.add_option("--broken", dest="broken", default=False, action="store_true", help="list broken/invalid aliases")
    parser.add_option("--clean", dest="clean", default=False, action="store_true", help="clean (remove) broken/invalid aliases")    
    parser.add_option("--install", dest="install", default=False, action="store_true", help="install the jdalias system for the current user")
    parser.add_option("--choices", dest="choices", default=False, action="store_true", help="list all alias choices (for bash autocompletion)")
    (options, args) = parser.parse_args()

    if options.install:
        install_jdalias()
    else:
        jd_aliases = AliasManager()
        #jd_aliases.quiet = options.quiet
        if options.list_aliases:
            jd_aliases.list_aliases()
        elif options.sort_aliases:
            jd_aliases.sort_aliases()
##         elif options.sort_directories:
##             jd_aliases.sort_directories()
        elif options.broken:
            jd_aliases.list_aliases(show_broken=True)
        elif options.clean:
            jd_aliases.clean_aliases()
        elif options.choices:
            print jd_aliases.choices()
        else:
            if len(args) == 0:
                print 'Please install the system by calling: "python jdalias.py --install".'
                print 'Once installation is completed successfully, invoke by using "jd".'
                sys.exit(1)
            else:
                if options.add_alias:
                    if len(args) < 2:
                        # if no directory argument is specified
                        # use the current directory
                        target = os.path.abspath('.')
                    else:
                        target = args[1]
                    jd_aliases.add_alias(args[0], target, not options.no_confirm)
                elif options.remove_alias:
                    jd_aliases.remove_alias(args[0], not options.no_confirm)
                else:
                    print jd_aliases.evaluate(args[0])
                
if __name__ == "__main__":
    main()
