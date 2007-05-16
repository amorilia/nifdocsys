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
# ***** END LICENSE BLOCK *****
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
    h.code( 'All rights reserved.  Please see niflib.h for license. */' )
    h.code()
    h.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
    h.code()
    h.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
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
    hdr = "struct %s"%x.cname
    if x.template: hdr = "template <class T >\n%s"%hdr
    hdr += " {"
    h.code(hdr)
    
    #constructor/destructor/assignment
    if not x.template:
        h.code( '/*! Default Constructor */' )
        h.code( "NIFLIB_API %s();"%x.cname )
        h.code( '/*! Default Destructor */' )
        h.code( "NIFLIB_API ~%s();"%x.cname )
        h.code( '/*! Copy Constructor */' )
        h.code( 'NIFLIB_API %s( const %s & src );'%(x.cname, x.cname) )
        h.code( '/*! Copy Operator */' )
        h.code( 'NIFLIB_API %s & operator=( const %s & src );'%(x.cname, x.cname) )



    # declaration
    h.declare(x)

    # header and footer functions
    if n  == "Header":
        h.code( 'NIFLIB_HIDDEN NifInfo Read( istream& in );' )
        h.code( 'NIFLIB_HIDDEN void Write( ostream& out, const NifInfo & info = NifInfo() ) const;' )
        h.code( 'NIFLIB_HIDDEN string asString( bool verbose = false ) const;' )
    
    if n == "Footer":
        h.code( 'NIFLIB_HIDDEN void Read( istream& in, list<unsigned int> & link_stack, const NifInfo & info );' )
        h.code( 'NIFLIB_HIDDEN void Write( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const;' )
        h.code( 'NIFLIB_HIDDEN string asString( bool verbose = false ) const;' )

    # done
    h.code("};")
    h.code()
    h.write( "}\n" )
    h.code( '#endif' )
    h.close()

    if not x.template:
        cpp = CFile(ROOT_DIR + '/src/gen/' + x.cname + '.cpp', 'w')
        cpp.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
        cpp.code( 'All rights reserved.  Please see niflib.h for license. */' )
        cpp.code()
        cpp.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
        cpp.code()
        cpp.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
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

        cpp.code('//Copy Constructor')
        cpp.code( '%s::%s( const %s & src ) {'%(x.cname,x.cname,x.cname) )
        cpp.code( '*this = src;' )
        cpp.code('};')
        cpp.code()

        cpp.code('//Copy Operator')
        cpp.code( '%s & %s::operator=( const %s & src ) {'%(x.cname,x.cname,x.cname) )
        for m in x.members:
            if m.is_declared and not m.is_duplicate:
                cpp.code('this->%s = src.%s;'%(m.cname, m.cname) )
        cpp.code('return *this;')
        cpp.code('};')
        cpp.code()

        cpp.code( '//Destructor' )
        
        # destructor
        cpp.code("%s::~%s()"%(x.cname,x.cname) + " {};")

        # header and footer functions
        if n  == "Header":
            cpp.code( 'NifInfo ' + x.cname + '::Read( istream& in ) {' )
            cpp.code( '//Declare NifInfo structure' )
            cpp.code( 'NifInfo info;' )
            cpp.code()
            cpp.stream(x, ACTION_READ)
            cpp.code()
            cpp.code( '//Copy info.version to local version var.' )
            cpp.code( 'version = info.version;' )
            cpp.code()
            cpp.code( '//Fill out and return NifInfo structure.' )
            cpp.code( 'info.userVersion = userVersion;' )
            cpp.code( 'info.endian = EndianType(endianType);' )
            cpp.code( 'info.creator = creator.str;' )
            cpp.code( 'info.exportInfo1 = exportInfo1.str;' )
            cpp.code( 'info.exportInfo2 = exportInfo2.str;' )
            cpp.code()
            cpp.code( 'return info;' )
            cpp.code()
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Write( ostream& out, const NifInfo & info ) const {' )
            cpp.stream(x, ACTION_WRITE)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
            cpp.stream(x, ACTION_OUT)
            cpp.code( '}' )
        
        if n == "Footer":
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Read( istream& in, list<unsigned int> & link_stack, const NifInfo & info ) {' )
            cpp.stream(x, ACTION_READ)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Write( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const {' )
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
All rights reserved.  Please see niflib.h for license. */

//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//

//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.

#ifndef _OBJ_DEFINES_H_
#define _OBJ_DEFINES_H_

#define MAXARRAYDUMP 20

""")
h.backslash_mode = True
for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)

    # declaration
    h.code('#define %s_MEMBERS '%x_define_name)
    h.declare(x)
    h.code()
h.backslash_mode = False

h.code()

for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
    # parents
    if not x.inherit:
        #h.code('#define %s_INCLUDE'%(x_define_name) )
        h.code('#define %s_PARENT'%(x_define_name) )
    else:
        #h.code('#define %s_INCLUDE \"%s.h\"'%(x_define_name, x.inherit.cname))
        #h.code()
        h.code('#define %s_PARENT %s'%(x_define_name, x.inherit.cname))
    h.code()
        
    # declaration

    # constructor
    h.write("#define %s_CONSTRUCT "%x_define_name)
    x_code_construct = x.code_construct()
    if x_code_construct:
        h.code(x_code_construct)
    h.code()
        
h.code("#endif")

h.close()

# Internal Implementations

if GENIMPL:
  m = CFile(ROOT_DIR + "/src/gen/obj_impl.cpp", "w")
  m.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
  m.code( 'All rights reserved.  Please see niflib.h for license. */' )
  m.code()
  m.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
  m.code()
  m.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
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
  m.backslash_mode = False

  m.write( """
const char FIX_LINK_POP_ERROR[] = "Trying to pop a link from empty stack. This is probably a bug.";
const char FIX_LINK_INDEX_ERROR[] = "Object index was not found in object map.  This NIF file may be invalid or imporperly supported.";
const char FIX_LINK_CAST_ERROR[] = "Link could not be cast to required type during file read. This NIF file may be invalid or improperly supported.";

template <class T>
Ref<T> FixLink( const map<unsigned,NiObjectRef> & objects, list<unsigned int> & link_stack, const NifInfo & info ) {
	if (link_stack.empty()) {
		throw runtime_error(FIX_LINK_POP_ERROR);
	}
	unsigned int index = link_stack.front();
	link_stack.pop_front();

	//Check if link is NULL
	if ( info.version > VER_3_3_0_13) {
	    if ( index == 0xFFFFFFFF) {
		    return NULL;
	    }
	} else {
	    if ( index == 0 ) {
		return NULL;
	    }
	}

	map<unsigned int,NiObjectRef>::const_iterator it = objects.find(index);
	if ( it == objects.end() ) {
		if ( info.version > VER_3_3_0_13 ) {
			throw runtime_error(FIX_LINK_INDEX_ERROR);
		} else {
			return NULL;
		}
	}
		
	Ref<T> object = DynamicCast<T>(it->second);
	if ( object == NULL ) {
		stringstream ss;
		ss << FIX_LINK_CAST_ERROR << endl;
		ss << "Type of object with index " << index << " was:  " << it->second->GetType().GetTypeName() << endl;
		ss << "Required type was:  " << T::TYPE.GetTypeName() << endl;
		throw runtime_error( ss.str().c_str() );
	}

	return object;
}

""" )

  for n in block_names:
      x = block_types[n]
      x_define_name = define_name(x.cname)
          
      m.code("void %s::InternalRead( istream& in, list<unsigned int> & link_stack, const NifInfo & info ) {"%x.cname)
      m.stream(x, ACTION_READ)
      m.code("}")
      m.code()
      
      m.code("void %s::InternalWrite( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const {"%x.cname)
      m.stream(x, ACTION_WRITE)
      m.code("}")
      m.code()
      
      m.code("std::string %s::InternalAsString( bool verbose ) const {"%x.cname)
      m.stream(x, ACTION_OUT)
      m.code("}")
      m.code()

      m.code("void %s::InternalFixLinks( const map<unsigned int,NiObjectRef> & objects, list<unsigned int> & link_stack, const NifInfo & info ) {"%x.cname)
      m.stream(x, ACTION_FIXLINKS)
      m.code("}")
      m.code()

      m.code("std::list<NiObjectRef> %s::InternalGetRefs() const {"%x.cname)
      m.stream(x, ACTION_GETREFS)
      m.code("}")
      m.code()

  m.backslash_mode = False

  m.close();

# Write out Public Enumeration header Enumerations
out = CFile(ROOT_DIR + '/include/gen/enums.h', 'w')
out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
out.code( 'All rights reserved.  Please see niflib.h for license. */' )
out.code('#ifndef _NIF_ENUMS_H_')
out.code('#define _NIF_ENUMS_H_')
out.code()
out.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
out.code()
out.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
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
out.code( 'All rights reserved.  Please see niflib.h for license. */' )
out.code()
out.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
out.code()
out.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
out.code()
out.code('#ifndef _NIF_ENUMS_INTL_H_')
out.code('#define _NIF_ENUMS_INTL_H_')
out.code()
out.code( '#include <iostream>' )
out.code( 'using namespace std;' )
out.code()
out.code('#include "../nif_basic_types.h"')
out.code()
out.write('namespace Niflib {\n')
out.code()
for n in enum_types:
  x = enum_types[n]
  if x.options:
    if x.description:
        out.code()
        out.code( '//---' + x.cname + '---//')
        out.code()
    out.code('void NifStream( %s & val, istream& in, const NifInfo & info = NifInfo() );'%x.cname)
    out.code('void NifStream( %s const & val, ostream& out, const NifInfo & info = NifInfo() );'%x.cname)
    out.code()

out.write('}\n')
out.code('#endif')
out.close()



#Write out Enumeration Implementation
out = CFile(ROOT_DIR + '/src/gen/enums.cpp', 'w')
out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
out.code( 'All rights reserved.  Please see niflib.h for license. */' )
out.code()
out.code( '//---THIS FILE WAS AUTOMATICALLY GENERATED.  DO NOT EDIT---//' )
out.code()
out.code( '//To change this file, alter the niftools/docsys/nifxml_niflib.py Python script.' )
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
    out.code()
    out.code('//--' + x.cname + '--//')
    out.code()
    out.code('void NifStream( %s & val, istream& in, const NifInfo & info ) {'%(x.cname))
    out.code('%s temp;'%(x.storage))
    out.code('NifStream( temp, in, info );')
    out.code('val = %s(temp);'%(x.cname))
    out.code('}')
    out.code()
    out.code('void NifStream( %s const & val, ostream& out, const NifInfo & info ) {'%(x.cname))
    out.code('NifStream( (%s)(val), out, info );'%(x.storage))
    out.code('}')
    out.code()
    out.code('ostream & operator<<( ostream & out, %s const & val ) { '%(x.cname))
    out.code('switch ( val ) {')
    for o in x.options:
      out.code('case %s: return out << "%s";'%(o.name, o.name))
    out.code('default: return out << "Invalid Value! - " << (unsigned int)(val);')
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
    out.code( 'All rights reserved.  Please see niflib.h for license. */' )
    out.code()
    out.code( '#ifndef _' + x.cname.upper() + '_H_' )
    out.code( '#define _' + x.cname.upper() + '_H_' )
    out.code()
    out.code( x.code_include_h() )
    out.write( "namespace Niflib {\n" )
    out.code( x.code_fwd_decl() )
    out.code( 'class ' + x.cname + ';' )
    out.code( 'typedef Ref<' + x.cname + '> ' + x.cname + 'Ref;' )
    out.code()
    out.comment( x.cname + " - " + x.description )
    out.code()
    out.code( 'class ' + x.cname + ' : public ' + x_define_name + '_PARENT {' )
    out.code( 'public:' )
    out.code( 'NIFLIB_API ' + x.cname + '();' )
    out.code( 'NIFLIB_API ~' + x.cname + '();' )
    out.code( '//Run-Time Type Information' )
    out.code( 'NIFLIB_API static const Type TYPE;' )
    out.code( 'NIFLIB_API static NiObject * Create();' )
    out.code( 'NIFLIB_API virtual const Type & GetType() const;' )
    out.code( 'NIFLIB_HIDDEN virtual void Read( istream& in, list<unsigned int> & link_stack, const NifInfo & info );' )
    out.code( 'NIFLIB_HIDDEN virtual void Write( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const;' )
    out.code( 'NIFLIB_API virtual string asString( bool verbose = false ) const;' )
    out.code( 'NIFLIB_HIDDEN virtual void FixLinks( const map<unsigned int,NiObjectRef> & objects, list<unsigned int> & link_stack, const NifInfo & info );' )
    out.code( 'NIFLIB_HIDDEN virtual list<NiObjectRef> GetRefs() const;' )
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
    out.code( 'private:' )
    out.code( 'void InternalRead( istream& in, list<unsigned int> & link_stack, const NifInfo & info );' )
    out.code( 'void InternalWrite( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const;' )
    out.code( 'string InternalAsString( bool verbose ) const;' )
    out.code( 'void InternalFixLinks( const map<unsigned int,NiObjectRef> & objects, list<unsigned int> & link_stack, const NifInfo & info );' )
    out.code( 'list<NiObjectRef> InternalGetRefs() const;' )
    out.code( '};' )
    out.code()
    out.write( "}\n" )
    out.code( '#endif' )
    out.close()

    out = CFile(ROOT_DIR + '/src/obj/' + x.cname + '.cpp', 'w')
    out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    out.code( 'All rights reserved.  Please see niflib.h for license. */' )
    out.code()
    out.code( x.code_include_cpp( True, "../../include/gen/", "../../include/obj/" ) )
    out.code( "using namespace Niflib;" );
    out.code()
    out.code( '//Definition of TYPE constant' )
    out.code ( 'const Type ' + x.cname + '::TYPE(\"' + x.cname + '\", &' + x_define_name + '_PARENT::TYPE );' )
    out.code()
    out.code( x.cname + '::' + x.cname + '() ' + x_define_name + '_CONSTRUCT {}' )
    out.code()
    out.code( x.cname + '::' + '~' + x.cname + '() {}' )
    out.code() 
    out.code( 'void ' + x.cname + '::Read( istream& in, list<unsigned int> & link_stack, const NifInfo & info ) {' )
    out.code( 'InternalRead( in, link_stack, info );' )
    out.code( '}' )
    out.code()
    out.code( 'void ' + x.cname + '::Write( ostream& out, const map<NiObjectRef,unsigned int> & link_map, const NifInfo & info ) const {' )
    out.code( 'InternalWrite( out, link_map, info );' )
    out.code( '}' )
    out.code()
    out.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
    out.code( 'return InternalAsString( verbose );' )
    out.code( '}' )
    out.code()
    out.code( 'void ' + x.cname + '::FixLinks( const map<unsigned int,NiObjectRef> & objects, list<unsigned int> & link_stack, const NifInfo & info ) {' );
    out.code( 'InternalFixLinks( objects, link_stack, info );' )
    out.code( '}' )
    out.code()
    out.code( 'list<NiObjectRef> %s::GetRefs() const {'%x.cname )
    out.code( 'return InternalGetRefs();' )
    out.code( '}' )
    out.code()
    out.code( 'const Type & %s::GetType() const {'%x.cname )
    out.code( 'return TYPE;' )
    out.code( '}' )
    out.code()
    out.code( 'namespace Niflib {' )
    out.code( 'typedef NiObject*(*obj_factory_func)();' )
    out.code( 'extern map<string, obj_factory_func> global_object_map;' )
    out.code()
    out.code( '//Initialization function' )
    out.code( 'static bool Initialization();' )
    out.code()
    out.code( '//A static bool to force the initialization to happen pre-main' )
    out.code( 'static bool obj_initialized = Initialization();' )
    out.code()
    out.code( 'static bool Initialization() {' )
    out.code( '//Add the function to the global object map' )
    out.code( 'global_object_map["' + x.cname + '"] = ' + x.cname + '::Create;' )
    out.code()
    out.code( '//Do this stuff just to make sure the compiler doesn\'t optimize this function and the static bool away.' )
    out.code( 'obj_initialized = true;' )
    out.code( 'return obj_initialized;' )
    out.code( '}' )
    out.code( '}' )
    out.code()
    out.code( 'NiObject * ' + x.cname + '::Create() {' )
    out.code( 'return new ' + x.cname + ';' )
    out.code( '}' )
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

i = 0
for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)

    if i == 0:
        doxy.write( "PREDEFINED             = " )
    else:
        doxy.write( "                         " )

    if i == len(block_names) - 1:
        doxy.backslash_mode = False
        
    # parents
    if not x.inherit:
        par = ""
    else:
        par = x.inherit.cname
    # declaration
    doxy.code('%s_PARENT=%s'%(x_define_name, par))
    i += 1

doxy.code()
doxy.close()
