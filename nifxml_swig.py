from nifxml import *
from distutils.dir_util import mkpath
import os
import guid

#Allow user to specify path where files will be generated with -p argument
#By default, they will be generated in ../contrib/niflib/pywrap/swig
ROOT_DIR = os.path.join('..', 'contrib', 'niflib', 'pywrap', 'swig' )

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
temp.set_var( 'guid', guid.generate() )
bat_list = temp.parse( os.path.join('templates', 'swig.bat.template' ) )
solution_list = temp.parse( os.path.join('templates', 'pywrap.sln.proj.template') )

#Write pyniflib project
f = file( os.path.join( ROOT_DIR, 'pyniflib.vcproj'), 'w' )
f.write( temp.parse( os.path.join('templates', 'swig.vcproj.template' ) ) )
f.close()

#variable to report number of files generated
files_generated = 1

#Cycle through all NiObjects
for n in block_names:
    x = block_types[n]

    #Mainly just the name is needed
    temp.set_var( "name", x.name )

    #MSVC projects need a unique GUID as well
    temp.set_var( 'guid', guid.generate() )

   #Find ancestor to import
    ancestor = ""
    c = x
    if c.inherit != None:
        ancestor = "%import \"" + c.inherit.cname + ".i\";"
    else:
        ancestor = "%import \"pyniflib.i\""
    temp.set_var( "import_ancestor", ancestor )

    #Write project and interface files
    f = file( os.path.join( ROOT_DIR, x.name + '.vcproj'), 'w' )
    f.write( temp.parse( os.path.join('templates', 'swig.vcproj.template') ) )
    f.close()
    files_generated += 1

    f = file( os.path.join( ROOT_DIR, x.name + '.i'), 'w' )
    f.write( temp.parse( os.path.join('templates', 'swig_niobject.i.template') ) )
    f.close()
    files_generated += 1

    #append a row to the bat file
    bat_list += temp.parse( os.path.join('templates', 'swig.bat.template') )

    #apend a project to the solution file
    solution_list += temp.parse( os.path.join('templates', 'pywrap.sln.proj.template') )

#add "pause" to the end of bat file to keep window open
bat_list += "pause"

#Write bat file
f = file( os.path.join( ROOT_DIR, 'run_swig.bat'), 'w' )
f.write( bat_list )
f.close()
files_generated += 1

#Write solution file
f = file( os.path.join( ROOT_DIR, 'pywrap.sln'), 'w' )
temp.set_var( 'projects', solution_list )
result = temp.parse(os.path.join('templates', 'pywrap.sln.template') )
f.write( result )
f.close()
files_generated += 1

print "nifxml_swig.py:  %d files successfully generated in %s"%(files_generated, ROOT_DIR)
