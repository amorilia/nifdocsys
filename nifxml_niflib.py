# nifxml_niflib.py
#
# This script generates C++ code for Niflib.
#
# --------------------------------------------------------------------------
# Command line options
#
# -p /path/to/niflib : specifies the path where niflib can be found 
#
# -b : enable bootstrap mode (generates templates)
#
# --------------------------------------------------------------------------
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright (c) 2005, NIF File Format Library and Tools
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENCE BLOCK *****
# --------------------------------------------------------------------------

from nifxml import *
from distutils.dir_util import mkpath
import os

#
# global data
#

ROOT_DIR = "."
BOOTSTRAP = False

prev = ""
for i in sys.argv:
    if prev == "-p":
        ROOT_DIR = i
    elif i == "-b":
        BOOTSTRAP = True
    prev = i

# generate compound code

mkpath(os.path.join(ROOT_DIR, "obj"))
mkpath(os.path.join(ROOT_DIR, "gen"))

for n in compound_names:
    x = compound_types[n]
    
    # skip natively implemented types
    if x.niflibtype: continue
    if n[:3] == 'ns ': continue

    h = CFile(ROOT_DIR + '/gen/' + x.cname + '.h', 'w')  
    h.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    h.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    h.code()
    h.code( '#ifndef _' + x.cname.upper() + '_H_' )
    h.code( '#define _' + x.cname.upper() + '_H_' )
    h.code()
    h.code( '#include "../NIF_IO.h"' )
    h.code( x.code_include_h() )
    if n in ["Header", "Footer"]:
        h.code( '#include "../obj/NiObject.h"' )
    h.code()
    
    # header
    h.comment(x.description)
    hdr = "struct NIFLIB_API %s"%x.cname
    if x.template: hdr = "template <class T >\n%s"%hdr
    hdr += " {"
    h.code(hdr)
    
    #constructor/destructor
    if not x.template:
        h.code( '/*! Default Constructor */' )
        h.code( "%s()"%x.cname + ';' )
        h.code( '/*! Default Destructor */' )
        h.code( "~%s()"%x.cname + ';' )

    # declaration
    h.declare(x)

    # header and footer functions
    if n in ["Header", "Footer"]:
        h.code( 'void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
        h.code( 'void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
        h.code( 'string asString( bool verbose = false ) const;' )

    # done
    h.code("};")
    h.code()
    h.code( '#endif' )

    if not x.template:
        cpp = CFile(ROOT_DIR + '/gen/' + x.cname + '.cpp', 'w')
        cpp.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
        cpp.code( 'All rights reserved.  Please see niflib.h for licence. */' )
        cpp.code()
        cpp.code( x.code_include_cpp() )
        
        cpp.code()
        cpp.code( '//Constructor' )
        
        # constructor
        x_code_construct = x.code_construct()
        if x_code_construct:
            cpp.code("%s::%s()"%(x.cname,x.cname) + x_code_construct + " {};")
        cpp.code()

        cpp.code( '//Destructor' )
        
        # destructor
        cpp.code("%s::~%s()"%(x.cname,x.cname) + " {};")

        # header and footer functions
        if n in ["Header", "Footer"]:
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' )
            cpp.stream(x, ACTION_READ)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const {' )
            cpp.stream(x, ACTION_WRITE)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
            cpp.stream(x, ACTION_OUT)
            cpp.code( '}' )


# generate block code

h = CFile(ROOT_DIR + "/gen/obj_defines.h", "w")

# file header

h.write("""/* Copyright (c) 2006, NIF File Format Library and Tools
All rights reserved.  Please see niflib.h for licence. */

#ifndef _OBJ_DEFINES_H_
#define _OBJ_DEFINES_H_

#define MAXARRAYDUMP 20

""")

h.backslash_mode = True

for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
        
    # declaration
    h.code('#define %s_MEMBERS'%x_define_name)
    h.declare(x)
    h.code()
    
    # parents
    if not x.inherit:
        par = ""
    else:
        par = x.inherit.cname
    # declaration
    h.code('#define %s_INCLUDE \"%s.h\"'%(x_define_name, par))
    h.code()
    h.code('#define %s_PARENT %s'%(x_define_name, par))
    h.code()

    # constructor
    h.code("#define %s_CONSTRUCT "%x_define_name)
    x_code_construct = x.code_construct()
    if x_code_construct:
        h.code(x_code_construct)
    h.code()
    
    # istream
    h.code("#define %s_READ"%x_define_name)
    h.stream(x, ACTION_READ)
    h.code()

    # ostream
    h.code("#define %s_WRITE"%x_define_name)
    h.stream(x, ACTION_WRITE)
    h.code()
    
    # as string
    h.code("#define %s_STRING"%x_define_name)
    h.stream(x, ACTION_OUT)
    h.code()

    # fix links
    h.code("#define %s_FIXLINKS"%x_define_name)
    h.stream(x, ACTION_FIXLINKS)
    h.code()

    # get references
    h.code("#define %s_GETREFS"%x_define_name)
    h.stream(x, ACTION_GETREFS)
    h.code()



h.backslash_mode = False
        
h.code("#endif")

h.close()

# Factories

f = CFile(ROOT_DIR + "/gen/obj_factories.cpp", "w")
f.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
f.code( 'All rights reserved.  Please see niflib.h for licence. */' )
f.code()
f.code('#include "../obj/NiObject.h"')
f.code('typedef NiObject*(*blk_factory_func)();')
f.code('extern map<string, blk_factory_func> global_block_map;')
f.code()
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('#include "../obj/%s.h"'%x.cname)
        f.code('NiObject * Create%s() { return new %s; }'%(x.cname,x.cname))
f.code()
f.code('//This function registers the factory functions with global_block_map which is used by CreateBlock')
f.code('void RegisterBlockFactories() {')
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('global_block_map["%s"] = Create%s;'%(x.cname, x.cname))
f.code('}')

# SConstruct file names

scons = open(os.path.join(ROOT_DIR, "SConstruct"), "w")

scons.write("""
import sys
import os
import time
from distutils import sysconfig

Help(\"\"\"
'scons' to build niflib library and niflib python wrapper
'scons -c' to clean
\"\"\")

# detect platform
if sys.platform == 'linux2' or sys.platform == 'linux-i386':
    python_lib = ['python%d.%d' % sys.version_info[0:2]]
    python_libpath = [sysconfig.get_python_lib (0, 1) + '/config']
    python_include = [sysconfig.get_python_inc ()]
    cppflags = '-fPIC -Wall'
elif sys.platform == 'cygwin':
    python_lib = ['python%d.%d' % sys.version_info[0:2]]
    python_libpath = [sysconfig.get_python_lib (0, 1) + '/config']
    python_include = [sysconfig.get_python_inc ()]
    cppflags = '-Wall'
elif sys.platform == 'win32':
    python_include = [sysconfig.get_python_inc()]
    python_libpath = [sysconfig.get_python_lib(1, 1) + '/../libs']
    python_lib = ['python24']
    cppflags = '/EHsc /O2 /GS /Zi /TP'
else:
    print "Error: Platform %s not supported."%sys.platform
    Exit(1)

env = Environment(ENV = os.environ)

# detect SWIG
try:
    env['SWIG']
except KeyError:
    print \"\"\"
Error: SWIG not found.
Please install SWIG, it's needed to create the python wrapper.
You can get it from http://www.swig.org/\"\"\"
    if sys.platform == "win32": print "Also don't forget to add the SWIG directory to your %PATH%."
    Exit(1)

# build niflib and python wrapper

""")

scons.write("objfiles = '")
for n in compound_names:
    x = compound_types[n]
    if n[:3] != 'ns ' and not x.niflibtype and not x.template:
        scons.write('gen/' + n + '.cpp ')
for n in block_names:
    scons.write('obj/' + n + '.cpp ')
scons.write("'\n\n")

scons.write("""niflib = env.StaticLibrary('niflib', Split('niflib.cpp nif_math.cpp NIF_IO.cpp kfm.cpp Type.cpp gen/obj_factories.cpp ' + objfiles), CPPPATH = '.', CPPFLAGS = cppflags)
nifshlib = env.SharedLibrary('_niflib', 'pyniflib.i', LIBS=['niflib'] + python_lib, LIBPATH=['.'] + python_libpath, SWIGFLAGS = '-c++ -python', CPPPATH = ['.'] + python_include, CPPFLAGS = cppflags, SHLIBPREFIX='')
# makes sure niflib.lib is built before trying to build _niflib.dll
env.Depends(nifshlib, niflib)


# Here's how to compile niflyze:
#env.Program('niflyze', 'niflyze.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

# A test program:
#env.Program('test', 'test.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

""")

scons.close()

# generate the swig interface

swig = CFile(os.path.join(ROOT_DIR, 'pyniflib.i'), "w")

swig.code("""// Swig module description file for a C dynamic library source file
// Generate with: swig -c++ -python -o py_wrap.cpp pyniflib.i

/* Copyright (c) 2006, NIF File Format Library and Tools
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:

   * Redistributions of source code must retain the above copyright
     notice, this list of conditions and the following disclaimer.

   * Redistributions in binary form must reproduce the above
     copyright notice, this list of conditions and the following
     disclaimer in the documentation and/or other materials provided
     with the distribution.

   * Neither the name of the NIF File Format Library and Tools
     project nor the names of its contributors may be used to endorse
     or promote products derived from this software without specific
     prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE. */

%module niflib
%include "stl.i"
%include "std_map.i"
%include "exception.i"
%include "std_list.i"
%include "typemaps.i"

// enable string assignment in structure member functions
%typemap(in) std::string* ($*1_ltype tempstr) {
	char * temps; int templ;
 	if (PyString_AsStringAndSize($input, &temps, &templ)) return NULL;
 	tempstr = $*1_ltype(temps, templ);
 	$1 = &tempstr;
}
%typemap(out) std::string* "$result = PyString_FromStringAndSize($1->data(), $1->length());";

// we need a version of SWIG that has SWIG_CATCH_STDEXCEPT support
#if SWIG_VERSION >= 0x010322
%exception {
	try {
		$action
	}
	SWIG_CATCH_STDEXCEPT // catch std::exception
	catch (...) {
		SWIG_exception(SWIG_UnknownError, "Unknown exception");
	}
}
#endif

// we need to define this because the wrapper gets confused about NIFLIB_API'd functions otherwise
#define NIFLIB_API

%{
	#include "niflib.h"
%}

// we need the definition of the template classes before we define the template Python names below
template <class T> 
struct Key {
	float time;
	T data, forward_tangent, backward_tangent;
	float tension, bias, continuity;
};

%ignore Key;

""")

# vector and list templates

for n in basic_names:
    x = basic_types[n]
    if not x.template:
        swig.code("%%template(vector_%s) std::vector<%s>;"%(x.niflibtype, x.niflibtype))
for n in compound_names:
    x = compound_types[n]
    if not x.template:
        if not x.niflibtype:
            swig.code("%%template(vector_%s) std::vector<%s>;"%(x.cname, x.cname))
        else:
            swig.code("%%template(vector_%s) std::vector<%s>;"%(x.niflibtype, x.niflibtype))
for n in block_names:
    x = block_types[n]
    if not x.template:
        swig.code("%%template(vector_%s) std::vector<%s>;"%(x.cname, x.cname))

swig.code("""%template(pair_int_float) std::pair<int, float>;
%template(map_int_float) std::map<int, float>;
%template(Key_Quaternion) Key<Quaternion>;
%template(vector_Key_Quaternion) std::vector< Key<Quaternion> >;
%template(Key_Vector3) Key<Vector3>;
%template(vector_Key_Vector3) std::vector< Key<Vector3> >;
%template(Key_float) Key<float>;
%template(vector_Key_float) std::vector< Key<float> >;
%template(Key_Color4) Key<Color4>;
%template(vector_Key_Color4) std::vector< Key<Color4> >;
%template(Key_string) Key<std::string>;
%template(vector_Key_string) std::vector< Key<std::string> >;

%include "niflib.h"
""")

swig.close()

# all non-generated bootstrap code
if BOOTSTRAP:
    # Templates
    for n in block_names:
	x = block_types[n]
	x_define_name = define_name(x.cname)
	
	out = CFile(ROOT_DIR + '/obj/' + x.cname + '.h', 'w')
	out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
	out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
	out.code()
	out.code( '#ifndef _' + x.cname.upper() + '_H_' )
	out.code( '#define _' + x.cname.upper() + '_H_' )
	out.code()
	out.code( x.code_include_h() )
	out.code()
	out.code( '#include "gen/obj_defines.h"' )
	out.code()
	out.code( 'class ' + x.cname + ';' )
	out.code( 'typedef Ref<' + x.cname + '> ' + x.cname + 'Ref;' )
	out.code()
	out.comment( x.cname + " - " + x.description )
	out.code()
	out.code( 'class ' + x.cname + ' : public ' + x_define_name + '_PARENT {' )
	out.code( 'public:' )
	out.code( x.cname + '();' )
	out.code( '~' + x.cname + '();' )
	out.code( '//Run-Time Type Information' )
	out.code( 'static const Type TYPE;' )
	out.code( 'virtual void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
	out.code( 'virtual void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
	out.code( 'virtual string asString( bool verbose = false ) const;\n' )
	out.code( 'virtual void FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
	out.code( 'virtual list<NiObjectRef> GetRefs() const;' )
	out.code( 'virtual const Type & GetType() const;' )
	out.code( 'protected:' )
	for y in x.members:
	    if y.func:
		if not y.template:
		    out.code( '%s %s() const;'%(y.ctype, y.func) )
		else:
		    if y.ctype != "*":
			out.code( '%s<%s > %s::%s() const;'%(y.ctype, y.ctemplate, x.cname, y.func) )
		    else:
			out.code( '%s * %s::%s() const;'%(y.ctemplate, x.cname, y.func ) )
	out.code( x_define_name + '_MEMBERS' )
	out.code( '};' );
	out.code();
	out.code( '#endif' );
	out.close()

	out = CFile(ROOT_DIR + '/obj/' + x.cname + '.cpp', 'w')
	out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
	out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
	out.code()
	out.code( x.code_include_cpp() )
	out.code()
	out.code( '//Definition of TYPE constant' )
	out.code ( 'const Type ' + x.cname + '::TYPE(\"' + x.cname + '\", &' + x_define_name + '_PARENT::TYPE );' )
	out.code()
	out.code( x.cname + '::' + x.cname + '() ' + x_define_name + '_CONSTRUCT {}' )
	out.code()
	out.code( x.cname + '::' + '~' + x.cname + '() {}' )
	out.code()
	out.code( 'void ' + x.cname + '::Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' )
	out.code( x_define_name + '_READ' )
	out.code( '}' )
	out.code()
	out.code( 'void ' + x.cname + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const {' )
	out.code( x_define_name + '_WRITE' )
	out.code( '}' )
	out.code()
	out.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
	out.code( x_define_name + '_STRING' )
	out.code( '}' )
	out.code()
	out.code( 'void ' + x.cname + '::FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' );
	out.code( x_define_name + '_FIXLINKS' )
	out.code( '}' )
	out.code()
	out.code( 'list<NiObjectRef> %s::GetRefs() const {'%x.cname )
	out.code( x_define_name + '_GETREFS' )
	out.code( '}' )
	out.code()
	out.code( 'const Type & %s::GetType() const {'%x.cname )
	out.code( 'return TYPE;' )
	out.code( '};' )
	out.code()
	for y in x.members:
	    if y.func:
		if not y.template:
		    out.code( '%s %s::%s() const { return %s(); }'%(y.ctype, x.cname, y.func, y.ctype) )
		else:
		    if y.ctype != "*":
			out.code( '%s<%s > %s::%s() const { return %s<%s >(); }'%(y.ctype, y.ctemplate, x.cname, y.func, y.ctype, y.ctemplate) )
		    else:
			out.code( '%s * %s::%s() const { return NULL; }'%(y.ctemplate, x.cname, y.func ) )
	out.close()
	
