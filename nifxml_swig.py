from nifxml import *
from distutils.dir_util import mkpath
import os
import guid

#Make sure output directory exists
mkpath( os.path.join('.', 'swig') )

#Generate a project file, and an i file, and a bat file entry for each NiObject
temp = Template()

#Start bat file list with niflib
temp.set_var("name", "niflib")
bat_list = temp.parse( "templates/swig.bat.template" )

#start solution file list with pyniflib
temp.set_var("name", "pyniflib")
temp.set_var( 'guid', guid.generate() )
solution_list = temp.parse( "templates/pywrap.sln.proj.template" )

#Cycle through all NiObjects
for n in block_names:
    x = block_types[n]

    #Mainly just the name is needed
    temp.set_var( "name", x.name )

    #Create a list of ancestors to import
    ancestors = ""
    c = x
    while c.inherit != None:
        ancestors = "%import \"obj/" + c.inherit.cname + ".h\";\n" + ancestors
        c = c.inherit
    temp.set_var( "import_ancestors", ancestors )

    #Write project and interface files
    f = file('./swig/' + x.name + '.vcproj', 'w')
    f.write( temp.parse( "templates/swig.vcproj.template" ) )
    f.close()

    f = file('./swig/' + x.name + '.i', 'w')
    f.write( temp.parse( "templates/swig_niobject.i.template" ) )
    f.close()

    #append a row to the bat file
    bat_list += temp.parse( "templates/swig.bat.template" )

    #apend a project to the solution file
    temp.set_var( 'guid', guid.generate() )
    solution_list += temp.parse( "templates/pywrap.sln.proj.template" )

#add "pause" to the end of bat file to keep window open
bat_list += "pause"

#Write bat file
f = file('./swig/run_swig.bat', 'w')
f.write( bat_list )
f.close()

#Write solution file
f = file('./swig/pywrap.sln', 'w')
temp.set_var( 'projects', solution_list )
result = temp.parse('templates/pywrap.sln.template')
f.write( result )
f.close()
