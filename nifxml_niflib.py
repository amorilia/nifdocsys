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
# -i : do NOT generate implmentation; place all code in defines.h
#
# -a : generate accessors for data in classes
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
GENIMPL = True
GENACCESSORS = False

prev = ""
for i in sys.argv:
    if prev == "-p":
        ROOT_DIR = i
    elif i == "-b":
        BOOTSTRAP = True
    elif i == "-i":
        GENIMPL = False
    elif i == "-a":
        GENACCESSORS = True
    prev = i

    
# Fix known manual update attributes. For now hard code here.
block_types["NiKeyframeData"].find_member("Num Rotation Keys").is_manual_update = True
#block_types["NiTriStripsData"].find_member("Num Triangles").is_manual_update = True
    
#
# generate compound code
#

mkpath(os.path.join(ROOT_DIR, "include/obj"))
mkpath(os.path.join(ROOT_DIR, "include/gen"))

mkpath(os.path.join(ROOT_DIR, "src/obj"))
mkpath(os.path.join(ROOT_DIR, "src/gen"))

for n in compound_names:
    x = compound_types[n]
    
    # skip natively implemented types
    if x.niflibtype: continue
    if n[:3] == 'ns ': continue

    h = CFile(ROOT_DIR + '/include/gen/' + x.cname + '.h', 'w')  
    h.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    h.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    h.code()
    h.code( '#ifndef _' + x.cname.upper() + '_H_' )
    h.code( '#define _' + x.cname.upper() + '_H_' )
    h.code()
    h.code( '#include "../NIF_IO.h"' )
    if n in ["Header", "Footer"]:
        h.code( '#include "../obj/NiObject.h"' )
    h.code( x.code_include_h() )
    h.write( "namespace Niflib {\n" )
    h.code( x.code_fwd_decl() )
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
    if n  == "Header":
        h.code( 'void Read( istream& in );' )
        h.code( 'void Write( ostream& out ) const;' )
        h.code( 'string asString( bool verbose = false ) const;' )
    
    if n == "Footer":
        h.code( 'void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
        h.code( 'void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
        h.code( 'string asString( bool verbose = false ) const;' )

    # done
    h.code("};")
    h.code()
    h.write( "}\n" )
    h.code( '#endif' )
    h.close()

    if not x.template:
        cpp = CFile(ROOT_DIR + '/src/gen/' + x.cname + '.cpp', 'w')
        cpp.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
        cpp.code( 'All rights reserved.  Please see niflib.h for licence. */' )
        cpp.code()
        cpp.code( x.code_include_cpp( True, "../../include/gen/", "../../include/obj/" ) )
        cpp.code( "using namespace Niflib;" )
        cpp.code()
        cpp.code( '//Constructor' )
        
        # constructor
        x_code_construct = x.code_construct()
        #if x_code_construct:
        cpp.code("%s::%s()"%(x.cname,x.cname) + x_code_construct + " {};")
        cpp.code()

        cpp.code( '//Destructor' )
        
        # destructor
        cpp.code("%s::~%s()"%(x.cname,x.cname) + " {};")

        # header and footer functions
        if n  == "Header":
            cpp.code( 'void ' + x.cname + '::Read( istream& in ) {' )
            cpp.stream(x, ACTION_READ)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Write( ostream& out ) const {' )
            cpp.stream(x, ACTION_WRITE)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
            cpp.stream(x, ACTION_OUT)
            cpp.code( '}' )
        
        if n == "Footer":
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

        cpp.close()


#
# generate block code
#

h = CFile(ROOT_DIR + "/include/gen/obj_defines.h", "w")

# file header

h.write("""/* Copyright (c) 2006, NIF File Format Library and Tools
All rights reserved.  Please see niflib.h for licence. */

#ifndef _OBJ_DEFINES_H_
#define _OBJ_DEFINES_H_

#define MAXARRAYDUMP 20
""")

if GENIMPL:
  h.write("""
#define STANDARD_INTERNAL_METHODS \\
private:\\
  void InternalRead( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );\\
  void InternalWrite( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;\\
  string InternalAsString( bool verbose ) const;\\
  void InternalFixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version );\\
  list<NiObjectRef> InternalGetRefs() const;
""")
else:
  h.code("#define STANDARD_INTERNAL_METHODS")
  h.code()
  
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
    if GENIMPL:
      h.code("InternalRead( in, link_stack, version, user_version );")
    else:
      h.stream(x, ACTION_READ)
    h.code()
      
    # ostream
    h.code("#define %s_WRITE"%x_define_name)
    if GENIMPL:
      h.code("InternalWrite( out, link_map, version, user_version );")
    else:
      h.stream(x, ACTION_WRITE)
    h.code()
    
    # as string
    h.code("#define %s_STRING"%x_define_name)
    if GENIMPL:
      h.code("return InternalAsString( verbose );")
    else:
      h.stream(x, ACTION_OUT)
    h.code()

    # fix links
    h.code("#define %s_FIXLINKS"%x_define_name)
    if GENIMPL:
      h.code("InternalFixLinks( objects, link_stack, version, user_version );")
    else:
      h.stream(x, ACTION_FIXLINKS)
    h.code()

    # get references
    h.code("#define %s_GETREFS"%x_define_name)
    if GENIMPL:
      h.code("return InternalGetRefs();")
    else:
      h.stream(x, ACTION_GETREFS)
    h.code()



h.backslash_mode = False
        
h.code("#endif")

h.close()

# Internal Implementations

if GENIMPL:
  m = CFile(ROOT_DIR + "/src/gen/obj_impl.cpp", "w")
  m.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
  m.code( 'All rights reserved.  Please see niflib.h for licence. */' )
  m.code()
  # m.code('#include <assert.h>')
  m.code('#include "../../include/obj/NiObject.h"')
  m.code('using namespace Niflib;')
  m.code('using namespace std;')
  m.code()
  for n in block_names:
      x = block_types[n]
      if not x.is_ancestor:
          m.code('#include "../../include/obj/%s.h"'%x.cname)
  m.code()
  m.backslash_mode = False

  for n in block_names:
      x = block_types[n]
      x_define_name = define_name(x.cname)
          
      m.code("void %s::InternalRead( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {"%x.cname)
      m.stream(x, ACTION_READ)
      m.code("}")
      m.code()
      
      m.code("void %s::InternalWrite( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const {"%x.cname)
      m.stream(x, ACTION_WRITE)
      m.code("}")
      m.code()
      
      m.code("std::string %s::InternalAsString( bool verbose ) const {"%x.cname)
      m.stream(x, ACTION_OUT)
      m.code("}")
      m.code()

      m.code("void %s::InternalFixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {"%x.cname)
      m.stream(x, ACTION_FIXLINKS)
      m.code("}")
      m.code()

      m.code("std::list<NiObjectRef> %s::InternalGetRefs() const {"%x.cname)
      m.stream(x, ACTION_GETREFS)
      m.code("}")
      m.code()

  m.backslash_mode = False

  m.close();

# Factories

f = CFile(ROOT_DIR + "/src/gen/obj_factories.cpp", "w")
f.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
f.code( 'All rights reserved.  Please see niflib.h for licence. */' )
f.code()
f.code('#include "../../include/obj/NiObject.h"')
f.code('using namespace Niflib;')
f.code('using namespace std;')
f.write('namespace Niflib {\n')
f.code('typedef NiObject*(*blk_factory_func)();')
f.code('extern map<string, blk_factory_func> global_block_map;')
f.write('}\n')
f.code()
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('#include "../../include/obj/%s.h"'%x.cname)
        f.code('NiObject * Create%s() { return new %s; }'%(x.cname,x.cname))
f.code()
f.write('namespace Niflib {\n')
f.code('//This function registers the factory functions with global_block_map which is used by CreateNiObject')
f.code('void RegisterBlockFactories() {')
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('global_block_map["%s"] = Create%s;'%(x.cname, x.cname))
f.code('}')

f.write('}\n')



#
# SCons
#

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
        scons.write('src/gen/' + n + '.cpp ')
for n in block_names:
    scons.write('src/obj/' + n + '.cpp ')
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

#
# generate the SWIG interface
#

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

//Ignore the const versions of these functions
%ignore DynamicCast( const NiObject * object );
%ignore StaticCast ( const NiObject * object );

//Do not use smart pointer support as it doubles the size of the library
//and makes it take twice as long to be imported
%ignore Niflib::Ref::operator->;
%ignore Niflib::Ref::operator=;

//Import the symbols from these but do not include them in the wrapper
%import "gen/obj_defines.h"
%import "NIF_IO.h"
%import "dll_export.h"
""")

swig.code('%{')
swig.code('\t#include "niflib.h"')
swig.code('\t#include "Ref.h"')
swig.code('\t#include "Type.h"')
swig.code('\t#include "nif_math.h"')

for n in block_names:
    x = block_types[n]
    swig.code('\t#include "obj/%s.h"'%x.cname)
    
for n in compound_names:
    x = compound_types[n]
    if x.niflibtype: continue
    if n[:3] == "ns ": continue
    swig.code('\t#include "gen/%s.h"'%x.cname)
swig.code("using namespace Niflib;")

swig.indent -= 1 # '%%}' hack
swig.code('%}')
swig.code()

# vector and list templates

##for n in basic_names:
##    x = basic_types[n]
##    if not x.template:
##        if not x.niflibtype in swig_types:
##            swig_types.append(x.niflibtype)
##    else:
##        if not x.niflibtype in swig_template_types and x.niflibtype != "*":
##            swig_template_types.append(x.niflibtype)
##            
##for n in compound_names:
##    x = compound_types[n]
##    if n[:3] == "ns ": continue
##    if not x.template:
##        if not x.niflibtype:
##            if not x.cname in swig_types:
##                swig_types.append(x.cname)
##        else:
##            if not x.niflibtype in swig_types:
##                swig_types.append(x.niflibtype)
##    else:
##        if not x.niflibtype:
##            if not x.cname in swig_template_types:
##                swig_template_types.append(x.cname)
##        else:
##            if not x.niflibtype in swig_template_types:
##                swig_template_types.append(x.niflibtype)
##for n in block_names:
##    x = block_types[n]
##    assert(not x.template) # debug
##    assert(not x.niflibtype) # debug
##    if not x.cname in swig_types:
##        swig_types.append(x.cname)
##
##for swig_type in swig_types:
##    if swig_type == "string":
##        real_swig_type = "std::string"
##    else:
##        real_swig_type = swig_type
##    swig.code("%%template(vector_%s) std::vector<%s>;"%(swig_type, real_swig_type))
##    for swig_template_type in swig_template_types:
##        swig.code("%%template(%s_%s) %s<%s >;"%(swig_template_type, swig_type, swig_template_type, real_swig_type))
##        swig.code("%%template(vector_%s_%s) std::vector<%s<%s > >;"%(swig_template_type, swig_type, swig_template_type, real_swig_type))
##

swig_v = []

for n in compound_names + block_names:
    try:
        x = compound_types[n]
    except KeyError:
        x = block_types[n]
    if n[:3] == "ns ": continue
    if x.niflibtype: continue
    for y in x.members:
        if not y.template:
            if y.arr1.lhs and not y.arr2.lhs:
                if not y.ctype in swig_v: swig_v.append(y.ctype)

for ctype in swig_v:
    if ctype == "string":
        real_ctype = "std::string"
    elif ctype not in ['int', 'float', 'char', 'short', 'double', 'long']:
        real_ctype = "Niflib::" + ctype
    else:
        real_ctype = ctype
    swig.code("%%template(vector_%s) std::vector<%s>;"%(ctype, real_ctype))

swig.code("""%template(pair_int_float) std::pair<int, float>;
%template(map_int_float) std::map<int, float>;

%include "niflib.h"
%include "Ref.h"
%include "Type.h"
%include "nif_math.h"

""")

for n in block_names:
    x = block_types[n]
    swig.code('%%include "obj/%s.h"'%x.cname)
    swig.code("%%template(%sRef) Niflib::Ref<Niflib::%s>;"%(x.cname, x.cname))
    swig.code("%%template(DynamicCastTo%s) Niflib::DynamicCast<Niflib::%s>;"%(x.cname, x.cname))
    swig.code("%%template(StaticCastTo%s) Niflib::StaticCast<Niflib::%s>;"%(x.cname, x.cname))

for n in compound_names:
    x = compound_types[n]
    if x.niflibtype: continue
    if n[:3] == "ns ": continue
    swig.code('%%include "gen/%s.h"'%x.cname)
    
swig.code()
swig.code("%template(vector_NiAVObjectRef) std::vector<Niflib::NiAVObjectRef>;")

swig.close()

# Write out Public Enumeration header Enumerations
out = CFile(ROOT_DIR + '/include/gen/enums.h', 'w')
out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
out.code('#ifndef _NIF_ENUMS_H_')
out.code('#define _NIF_ENUMS_H_')
out.code()
out.code( '#include <iostream>' )
out.code( 'using namespace std;' )
out.code()
out.write('namespace Niflib {\n')
out.code()
for n in enum_types:
  x = enum_types[n]
  if x.options:
    if x.description:
      out.comment(x.description)
    out.code('enum %s {'%(x.cname))
    for o in x.options:
      out.code('%s = %s, /*!< %s */'%(o.name, o.value, o.description))
    out.code('};')
    out.code()
    out.code('ostream & operator<<( ostream & out, %s const & val );'%x.cname)
    out.code()

out.write('}\n')
out.code('#endif')
out.close()

# Write out Internal Enumeration header (NifStream functions)
out = CFile(ROOT_DIR + '/include/gen/enums_intl.h', 'w')
out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
out.code('#ifndef _NIF_ENUMS_INTL_H_')
out.code('#define _NIF_ENUMS_INTL_H_')
out.code()
out.code( '#include <iostream>' )
out.code( 'using namespace std;' )
out.code()
out.code('#include "nif_basic_types.h"')
out.code()
out.write('namespace Niflib {\n')
out.code()
for n in enum_types:
  x = enum_types[n]
  if x.options:
    if x.description:
      out.comment(x.description)
    out.code('void NifStream( %s & val, istream& in, uint version = 0 );'%x.cname)
    out.code('void NifStream( %s const & val, ostream& out, uint version = 0  );'%x.cname)
    out.code()

out.write('}\n')
out.code('#endif')
out.close()



#Write out Enumeration Implementation
out = CFile(ROOT_DIR + '/src/gen/enums.cpp', 'w')
out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
out.code()
out.code('#include <string>')
out.code('#include <iostream>')
out.code('#include "../../include/NIF_IO.h"')
out.code('#include "../../include/gen/enums.h"')
out.code('#include "../../include/gen/enums_intl.h"')
out.code()
out.code('using namespace std;')
out.code()
out.write('namespace Niflib {\n')
out.code()

out.code()
for n in enum_types:
  x = enum_types[n]
  if x.options:
    out.comment(x.cname)
    out.code('void NifStream( %s & val, istream& in, uint version ) {'%(x.cname))
    out.code('%s temp;'%(x.storage))
    out.code('NifStream( temp, in, version );')
    out.code('val = %s(temp);'%(x.cname))
    out.code('}')
    out.code()
    out.code('void NifStream( %s const & val, ostream& out, uint version ) {'%(x.cname))
    out.code('NifStream( %s(val), out, version );'%(x.storage))
    out.code('}')
    out.code()
    out.code('ostream & operator<<( ostream & out, %s const & val ) { '%(x.cname))
    out.code('switch ( val ) {')
    for o in x.options:
      out.code('case %s: return out << "%s";'%(o.name, o.name))
    out.code('default: return out << "Invalid Value! - " << uint(val);')
    out.code('}')
    out.code('}')
    out.code()
    
out.write('}\n')
out.close()

#
# all non-generated bootstrap code
#

if BOOTSTRAP:

  # Templates
  for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
    
    out = CFile(ROOT_DIR + '/include/obj/' + x.cname + '.h', 'w')
    out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    out.code()
    out.code( '#ifndef _' + x.cname.upper() + '_H_' )
    out.code( '#define _' + x.cname.upper() + '_H_' )
    out.code()
#    out.code( '#include "../Ref.h"')
    out.code( x.code_include_h() )
    out.write( "namespace Niflib {\n" )
    out.code( x.code_fwd_decl() )
    out.code()
    out.code( '#include "../gen/obj_defines.h"' )
    out.code()
    out.code( 'class ' + x.cname + ';' )
    out.code( 'typedef Ref<' + x.cname + '> ' + x.cname + 'Ref;' )
    out.code()
    out.comment( x.cname + " - " + x.description )
    out.code()
    out.code( 'class NIFLIB_API ' + x.cname + ' : public ' + x_define_name + '_PARENT {' )
    out.code( 'public:' )
    out.code( x.cname + '();' )
    out.code( '~' + x.cname + '();' )
    out.code( '//Run-Time Type Information' )
    out.code( 'static const Type & TypeConst() { return TYPE; }' )
    out.code( 'private:' )
    out.code( 'static const Type TYPE;' )
    out.code( 'public:' )  
    out.code( 'virtual void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
    out.code( 'virtual void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
    out.code( 'virtual string asString( bool verbose = false ) const;\n' )
    out.code( 'virtual void FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
    out.code( 'virtual list<NiObjectRef> GetRefs() const;' )
    out.code( 'virtual const Type & GetType() const;' )
    out.code()
  
    # Declare Helper Methods
    if GENACCESSORS:
      for y in x.members:
        if not y.func:
          if not y.arr1_ref and not y.arr2_ref and y.cname.lower().find("unk") == -1: #not y.cname.startswith("num") :
            out.comment(y.description)
            out.code( y.getter_declare("", ";") )
            out.code( y.setter_declare("", ";") )
            out.code()
        
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
    out.code( "STANDARD_INTERNAL_METHODS" )
    out.code( '};' )
    out.code()
    out.write( "}\n" )
    out.code( '#endif' )
    out.close()

    out = CFile(ROOT_DIR + '/src/obj/' + x.cname + '.cpp', 'w')
    out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    out.code()
    out.code( x.code_include_cpp() )
    out.code( "using namespace Niflib;" );
    out.code()
    out.code( '//Definition of TYPE constant' )
    out.code ( 'const Type ' + x.cname + '::TYPE(\"' + x.cname + '\", &' + x_define_name + '_PARENT::TypeConst() );' )
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
    
    # Implement Public Getter/Setter Methods
    if GENACCESSORS:
      for y in x.members:
        if not y.func:
          if not y.arr1_ref and not y.arr2_ref and y.cname.lower().find("unk") == -1: # and not y.cname.startswith("num") :
            out.code( y.getter_declare(x.name + "::", " {") )
            out.code( "return %s;"%y.cname )
            out.code( "}" )
            out.code()
            
            out.code( y.setter_declare(x.name + "::", " {") )
            out.code( "%s = value;"%y.cname )
            out.code( "}" )
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
    

#Doxygen pre-define file
doxy = CFile(os.path.join(ROOT_DIR, 'DoxygenPredefines.txt'), "w")
doxy.backslash_mode = True
doxy.code( "PREDEFINED             =" )

for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
        
    # parents
    if not x.inherit:
        par = ""
    else:
        par = x.inherit.cname
    # declaration
    doxy.code('%s_PARENT=%s'%(x_define_name, par))

doxy.code()
doxy.close()
