from nifxml import *
from distutils.dir_util import mkpath
import os
import guid
import sys

#Allow user to specify path where files will be generated with -p argument
#By default, they will be generated in ../contrib/niflib/pywrap/swig
ROOT_DIR = os.path.join('..', 'pyniflib' )

prev = ""
for i in sys.argv:
    if prev == "-p":
        ROOT_DIR = i
    prev = i

#Make sure output directory exists
mkpath( os.path.join(ROOT_DIR) )

#Generate a project file, and an i file, and a bat file entry for each NiObject
temp = Template()

#Start bat file list and solution file list with pyniflib
temp.set_var("name", "pyniflib")
temp.set_var('prefix', '')
temp.set_var( 'guid', guid.generate() )
bat_list = temp.parse( os.path.join('templates', 'swig.bat.template' ) )
solution_list = temp.parse( os.path.join('templates', 'pywrap.sln.proj.template') )
config_list = temp.parse( os.path.join('templates', 'pywrap.sln.config.template') )

if sys.platform == 'win32':
    #Write pyniflib project
    f = file( os.path.join( ROOT_DIR, 'vcproj', 'pyniflib.vcproj'), 'w' )
    f.write( temp.parse( os.path.join('templates', 'swig.vcproj.template' ) ) )
    f.close()

#variable to report number of files generated
files_generated = 1

temp.set_var('prefix', 'obj/')

#Cycle through all NiObjects
for n in block_names:
    x = block_types[n]

    #Mainly just the name is needed
    temp.set_var( "name", x.name )

    #MSVC projects need a unique GUID as well
    temp.set_var( 'guid', guid.generate() )

    #Create a list of ancestors to import
    ancestors = ""
    if x.inherit:
        ancestors = "%import \"obj/" + x.inherit.cname + ".i\";\n" + ancestors

    #Create a list of structures that need their header file imported
    used_structs = []
    for y in x.members:
        file_name = None
        if y.type != x.name:
            if y.type in compound_names:
                if not compound_types[y.type].niflibtype:
                    file_name = "gen/%s.h"%(y.ctype)
        if file_name and file_name not in used_structs:
            used_structs.append( file_name )
    if used_structs:
        ancestors += "\n//Include Structures\n"
    for file_name in used_structs:
        ancestors += '%import "' + file_name + '"\n'

    temp.set_var( "import_ancestors", ancestors )

    #Write project and interface files
    if sys.platform == 'win32':
        f = file( os.path.join( ROOT_DIR, 'vcproj', x.name + '.vcproj'), 'w' )
        f.write( temp.parse( os.path.join('templates', 'swig.vcproj.template') ) )
        f.close()
        files_generated += 1

    f = file( os.path.join( ROOT_DIR, 'obj', x.name + '.i'), 'w' )
    f.write( temp.parse( os.path.join('templates', 'swig_niobject.i.template') ) )
    f.close()
    files_generated += 1

    #append a row to the bat file
    bat_list += temp.parse( os.path.join('templates', 'swig.bat.template') )

    #apend a project to the solution file
    solution_list += temp.parse( os.path.join('templates', 'pywrap.sln.proj.template') )

    #append project config to the solution file.  This is not strictly necessary as MSVC will create
    #on the first load, but it will make the solution open faster.
    config_list += temp.parse( os.path.join('templates', 'pywrap.sln.config.template') )

#add "pause" to the end of bat file to keep window open
bat_list += "pause"

if sys.platform == 'win32':
    #Write bat file
    f = file( os.path.join( ROOT_DIR, 'run_swig.bat'), 'w' )
    f.write( bat_list )
    f.close()
    files_generated += 1

    #Write solution file
    f = file( os.path.join( ROOT_DIR, 'pyniflib.sln'), 'w' )
    temp.set_var( 'projects', solution_list )
    temp.set_var( 'config', config_list )
    result = temp.parse(os.path.join('templates', 'pywrap.sln.template') )
    f.write( result )
    f.close()
    files_generated += 1

print "nifxml_swig.py:  %d files successfully generated in %s"%(files_generated, ROOT_DIR)
