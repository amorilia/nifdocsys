import sys
from xml.sax import *

H_HEADER = """/* --------------------------------------------------------------------------
 * xml_extract.h: C++ header file for raw reading, writing, and printing
 *                NetImmerse and Gamebryo files (.nif & .kf & .kfa)
 * --------------------------------------------------------------------------
 * ***** BEGIN LICENSE BLOCK *****
 *
 * Copyright (c) 2005, NIF File Format Library and Tools
 * All rights reserved.
 * 
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *    * Redistributions of source code must retain the above copyright
 *      notice, this list of conditions and the following disclaimer.
 *
 *    * Redistributions in binary form must reproduce the above
 *      copyright notice, this list of conditions and the following
 *      disclaimer in the documentation and/or other materials provided
 *      with the distribution.
 *
 *    * Neither the name of the NIF File Format Library and Tools
 *      project nor the names of its contributors may be used to endorse
 *      or promote products derived from this software without specific
 *      prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * ***** END LICENCE BLOCK *****
 * --------------------------------------------------------------------------
 */

#ifndef _XML_EXTRACT_H_
#define _XML_EXTRACT_H_

#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

"""

CPP_HEADER = """/* --------------------------------------------------------------------------
 * xml_extract.cpp: C++ code for raw reading, writing, and printing
 *                  NetImmerse and Gamebryo files (.nif & .kf & .kfa)
 * --------------------------------------------------------------------------
 * ***** BEGIN LICENSE BLOCK *****
 *
 * Copyright (c) 2005, NIF File Format Library and Tools
 * All rights reserved.
 * 
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 *    * Redistributions of source code must retain the above copyright
 *      notice, this list of conditions and the following disclaimer.
 *
 *    * Redistributions in binary form must reproduce the above
 *      copyright notice, this list of conditions and the following
 *      disclaimer in the documentation and/or other materials provided
 *      with the distribution.
 *
 *    * Neither the name of the NIF File Format Library and Tools
 *      project nor the names of its contributors may be used to endorse
 *      or promote products derived from this software without specific
 *      prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 * ***** END LICENCE BLOCK *****
 * --------------------------------------------------------------------------
 */

#include "xml_extract.h"

"""

# indent C++ code; the returned result always ends with a newline
def cpp_code(txt, indent, append_backslash = False):
    # create indentation string
    prefix = "  " * indent
    # strip trailing whitespace, including newlines
    txt = txt.rstrip()
    # replace tabs
    txt = txt.replace("\t", "  ");
    # indent, and add newline
    result = prefix + txt.replace("\n", "\n" + prefix)
    if append_backslash:
        result += " \\\n"
    else:
        result += "\n"
    return result

# create C++-style comments (handle multilined comments as well)
# result always ends with a newline
def cpp_comment(txt, indent):
    return cpp_code("// " + txt.replace("\n", "\n// "), indent)

# this returns this->$objectname if it's a class variable, $objectname
# otherwise; one array index is substituted as well.
def cpp_resolve(objectname):
    if objectname == None: return None
    
    posarr1begin = objectname.find("[")
    posarr1end = objectname.find("]")
    if ((posarr1begin >= 0) and (posarr1end > posarr1begin)):
        objectname = objectname[:posarr1begin + 1] + cpp_resolve(objectname[posarr1begin + 1:posarr1end - 1]) + objectname[posarr1end:]

    return objectname

##function cpp_code_construct($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $sizevarbisdyn)
##{
##  $some_type_arg = cpp_resolve($some_type_arg);
##  $sizevar = cpp_resolve($sizevar);
##  $sizevarbis = cpp_resolve($sizevarbis);
##
##  $result = "";
##
##  // first handle the case of a string
##  if ( ( $some_type == "char" ) and ( $sizevar != null ) and ( $sizevarbis == null ) )
##    return python_code( "$var = string($sizevar, ' ');" );
##
##  // other cases
##  if ( ( $some_type == "byte" )
##       or ( $some_type == "short" )
##       or ( $some_type == "int" )
##       or ( $some_type == "bool" ) )
##    $result = "0";
##  elseif ( $some_type == "flags" )
##    $result = "0x0008";
##  elseif ( $some_type == "alphaformat" )
##    $result = "3";
##  elseif ( $some_type == "applymode" )
##    $result = "2";
##  elseif ( $some_type == "lightmode" )
##    $result = "1";
##  elseif ( $some_type == "mipmapformat" )
##    $result = "2";
##  elseif ( $some_type == "pixellayout" )
##    $result = "5";
##  elseif ( $some_type == "vertmode" )
##    $result = "2";
##    // byte, short, int => 32 bit signed integer
##  elseif ( ( $some_type == "link" )
##           or ( $some_type == "nodeancestor" )
##           or ( $some_type == "skeletonroot" ) )
##    // index -1 refers to nothing
##    $result = "-1";
##  elseif ( $some_type == "char" )
##    // character
##    $result = "' '";
##  elseif ( $some_type == "float" )
##    // float => C-style "double"
##    $result = "0.0";
##  else
##    // standard constructor
##    if ($some_type_arg)
##	$result = cpp_type($some_type) . "(version, $some_type_arg)";
##    else
##      $result = cpp_type($some_type) . "(version)";
##  if ( ! $sizevar ) return python_code( "$var = " . $result . ";" );
##  else
##    if ( ! $sizevarbis )
##      return python_code( "$var = vector<" . cpp_type($some_type) . ">(${sizevar}, $result);" );
##    else {
##      if ( ! $sizevarbisdyn )
##        return python_code( "$var = vector<vector<" . cpp_type($some_type) . "> >(${sizevar}, vector<" . cpp_type($some_type) . ">(${sizevarbis}, $result));" );
##      else
##        return python_code( "$var = vector<vector<" . cpp_type($some_type) . "> >(${sizevar});\nfor (int i; i<${sizevar}, i++)\n\t${var}[i] = vector<" . cpp_type($some_type) . "(${sizevarbis}[i], $result));>" );
##    };
##  
##  return $result;
##}
##
##function cpp_code_destruct($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $sizevarbisdyn)
##{
##  $some_type_arg = cpp_resolve($some_type_arg);
##  $sizevar = cpp_resolve($sizevar);
##  $sizevarbis = cpp_resolve($sizevarbis);
##
##  return; # nothing to do
##}
##
##function cpp_code_read($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $sizevarbisdyn, $condvar, $condval, $condtype, $ver_from, $ver_to)
##{
##  global $indent;
##  $result = "";
##  $some_type_arg = cpp_resolve($some_type_arg);
##  $sizevar = cpp_resolve($sizevar);
##  $sizevarbis = cpp_resolve($sizevarbis);
##  $condvar = cpp_resolve($condvar);
##
##  // check version
##  if ( ( $ver_from !== null ) or ( $ver_to !== null ) ) {
##    $version_str = '';
##    if ( $ver_from !== null ) $version_str .= "(self.version >= 0x" . dechex($ver_from) . ") and ";
##    if ( $ver_to !== null ) $version_str .= "(self.version <= 0x" . dechex($ver_to) . ") and ";
##    if ( $ver_from === $ver_to ) $version_str = "(self.version == 0x" . dechex($ver_from) . ") and ";
##    $version_str = substr($version_str, 0, -5); // remove trailing " and "
##    $result .= python_code( "if ($version_str) {" );
##    $indent++;
##  };
##
##  // array size check
##  if ( $sizevar ) {
##    $result .= cpp_code( "if ($sizevar > MAX_ARRAYSIZE) throw NIFException(\"array size unreasonably large\");" );
##    if ( $sizevarbis )
##      $result .= cpp_code( "if ($sizevarbis > MAX_ARRAYSIZE) throw NIFException(\"array size unreasonably large\");" );
##  }
##
##  // first, initialise the variable
##  $result .= cpp_code_destruct( $var, $some_type, $some_type_arg, $sizevar, $sizevarbis );
##  $result .= cpp_code_construct( $var, $some_type, $some_type_arg, $sizevar, $sizevarbis );
##
##  // conditional: if statement
##  if ( $condvar ) {
##    if ( $condval === null )
##      $result .= python_code( "if ($condvar != 0) {" );
##    else {
##      if ( ( $condtype === null ) or ( $condtype === 0 ) )
##        $result .= python_code( "if ($condvar == $condval) {" );
##      else
##        $result .= python_code( "if ($condvar != $condval) {" );
##    };
##    $indent++;
##  }
##
##  // array: for loop
##  if ( $sizevar ) {
##    $result .= cpp_code( "for (int i; i < $sizevar; i++)" );
##    $indent++;
##    $var .= "[i]"; // this is now the variable that we shall read
##    // arraybis: for loop
##    if ( $sizevarbis ) {
##      if ( ! $sizevarbisdyn )
##	$result .= cpp_code( "for (int j; j < $sizevarbis; j++)" );
##      else
##	$result .= cpp_code( "for (int j; j < ${sizevarbis}[i]; j++)" );
##      $indent++;
##      $var .= "[j]"; // this is now the variable that we shall read
##    }
##  }
##
##  // main
##  $type_size = cpp_type_size($some_type);
##  if ( $type_size != -1 )
##    $result .= cpp_code( "file.read((char *)&$var, $type_size);" );
##  else
##    $result .= cpp_code( "$var.read(file);" );
##
##  // restore indentation
##  if ( $sizevar ) {
##    $indent--;
##    if ( $sizevarbis ) $indent--;
##  }
##  if ( $condvar ) { $indent--; $result .= python_code("};"); };
##  if ( ( $ver_from !== null ) or ( $ver_to !== null ) ) { $indent--; $result .= python_code("};"); };
##
##  return $result;
##};

native_types = {}
native_types['(TEMPLATE)'] = 'T'

def cpp_type_name(n):
    if n == None: return None
    try:
        return native_types[n]
    except KeyError:
        return n.replace(' ', '_')

    # old code
    if n == None: return None
    try:
        return native_types[n]
    except KeyError:
        pass
    if n == '(TEMPLATE)': return 'T'
    n2 = ''
    for i, c in enumerate(n):
        if ('A' <= c) and (c <= 'Z'):
            if i > 0: n2 += '_'
            n2 += c.lower()
        elif (('a' <= c) and (c <= 'z')) or (('0' <= c) and (c <= '9')):
            n2 += c
        else:
            n2 += '_'
    return n2

def cpp_define_name(n):
    n2 = ''
    for i, c in enumerate(n):
        if ('A' <= c) and (c <= 'Z'):
            if i > 0:
                n2 += '_'
                n2 += c
            else:
                n2 += c
        elif (('a' <= c) and (c <= 'z')) or (('0' <= c) and (c <= '9')):
            n2 += c.upper()
        else:
            n2 += '_'
    return n2

def cpp_attr_name(n):
    if n == None: return None
    return n.lower().replace(' ', '_').replace('?', '_')



class Attrib:
    def __init__(self):
        self.name = None
        self.type = None
        self.arg = None
        self.template = None
        self.arr1 = None
        self.arr2 = None
        self.cond = None
        self.func = None
        self.default = None
        self.description = ''
        self.ver1 = None
        self.ver2 = None
        self.type_is_native = False
        self.arr2_dynamic = False
        self.arr1_ref = None # name of the attribute it is a size of
        self.arr2_ref = None # name of the attribute it is a size of
        # cpp names
        self.update_cnames()

    def __init__(self, attrs): # attrs are the XML attributes
        # attribute stuff
        self.name      = attrs.get('name')
        self.type      = attrs.get('type')
        self.arg       = attrs.get('arg')
        self.template  = attrs.get('template')
        self.arr1      = attrs.get('arr1')
        self.arr2      = attrs.get('arr2')
        self.cond      = attrs.get('cond')
        self.func      = attrs.get('function')
        self.default   = attrs.get('default')
        self.description = '' # read by "characters" function
        self.ver1      = attrs.get('ver1')
        self.ver2      = attrs.get('ver2')
        # other flags: set them to their defaults
        self.type_is_native = native_types.has_key(self.name) # true if the type is implemented natively
        self.arr1_ref = None # name of the attribute it is a size of
        self.arr2_ref = None # name of the attribute it is a size of
        self.arr2_dynamic   = False # true if arr2 refers to an array
        # cpp names
        self.update_cnames()

        # override default for attributes that have an argument
        if self.arg:
            self.default = "%s(%s)"%(self.ctype,self.carg)

    def update_cnames(self):
        pass
        self.cname     = cpp_attr_name(self.name)
        self.ctype     = cpp_type_name(self.type)
        self.carg      = cpp_attr_name(self.arg)
        self.ctemplate = cpp_type_name(self.template)
        self.carr1     = cpp_attr_name(self.arr1)
        self.carr2     = cpp_attr_name(self.arr2)
        self.arr1_ref  = cpp_attr_name(self.arr1_ref)
        self.arr2_ref  = cpp_attr_name(self.arr2_ref)
 
    def declare(self, counts = False):
        # don't declare array sizes
        # but only declare array sizes if counts is True
        if self.arr1_ref or self.arr2_ref:
            if counts == False:
                return None
        else:
            if counts == True:
                return None
        
        # first handle the case of a string
        if self.type == "char" and self.arr1 and not self.arr2:
            return "string %s"%self.cname

        result = self.ctype
        if self.arr1: result = "vector<%s>"%result
        if self.arr2: result = "vector<%s >"%result
        result += " " + self.cname + ";"
        return result

    def construct(self):
        # don't construct array sizes
        if self.arr1_ref or self.arr2_ref:
            return None

        if not self.default:
            return self.cname + "()"
        else:
            return "%s(%s)"%(self.cname, self.default)

    def read(self):
        pass

    def write(self):
        pass

    def dump(self):
        pass



# This class has all the XML parser code.
class SAXtracer(ContentHandler):

    def __init__(self):
        self.current_block = None
        self.current_attr = None # index into the attrib table
        self.indent_h = 0
        self.indent_cpp = 0
        self.file_h = open("xml_extract.h", "w")
        self.file_cpp = open("xml_extract.cpp", "w")

    def startDocument(self):
        self.file_h.write(H_HEADER)
        self.file_cpp.write(CPP_HEADER)

    def endDocument(self):
        self.file_h.write("\n#endif\n")
        self.file_h.close()
        self.file_cpp.close()

    def startElement(self, name, attrs):
        global native_types
        
        # basic types
        if name == "basic":
            assert(self.current_block == None) # debug
            assert(self.current_attr == None) # debug
            
            if attrs.has_key('niflibtype'):
                native_types[attrs.get('name')] = attrs.get('niflibtype')
                
            # store block data
            self.block_name = attrs.get('name')
            self.block_cname = cpp_type_name(self.block_name)
            self.block_comment = ''
            self.block_attr_names = [] # sorts the names

            # keep track of where we are
            self.current_block = self.block_name
        # compound types (including blocks and ancestors)
        elif name == "niblock" or name == "compound" or name == "ancestor":
            assert(self.current_block == None) # debug
            assert(self.current_attr == None) # debug
            
            # store block data
            self.block_name = attrs.get('name')
            self.block_cname = cpp_type_name(self.block_name)
            self.block_inherit = None
            self.block_attrs = {}
            self.block_template = False
            self.block_comment = ''
            self.block_attr_names = [] # sorts the names
            self.block_interface = None

            # keep track of where we are
            self.current_block = self.block_name
        elif name == "inherit":
            assert(self.current_block != None) # debug
            assert(self.current_attr == None) # debug
            
            self.block_inherit = cpp_type_name(attrs.get('name'))
        elif name == "interface":
            assert(self.current_block != None) # debug
            assert(self.current_attr == None) # debug
            
            self.block_interface = attrs.get('name')
        elif name == "add":
            assert(self.current_block != None) # debug
            assert(self.current_attr == None) # debug
            
            # read the raw values
            attrib = Attrib(attrs)

            # update current attribute
            self.current_attr = attrib.name

            # detect templates
            if attrib.type == '(TEMPLATE)':
                self.block_template = True

            # detect array sizes
            if attrib.arr1 in self.block_attr_names:
                self.block_attrs[attrib.arr1].arr1_ref = attrib.name
            if attrib.arr2 in self.block_attr_names:
                self.block_attrs[attrib.arr2].arr2_ref = attrib.name

            # store it
            self.block_attr_names.append(self.current_attr)
            self.block_attrs[self.current_attr] = attrib

    def endElement(self, name):
        if name == "compound":
            num_block_attrs = len(self.block_attr_names)
            
            assert(self.current_block != None) # debug
            assert(self.current_attr == None) # debug
            
            # header
            self.h_comment("\n" + self.block_comment.strip() + "\n")
            hdr = "struct %s"%self.block_cname
            if self.block_template: hdr += "<T>"
            hdr += " {"
            self.h_code(hdr)

            # constructor
            self.h_code("%s() : "%self.block_cname)
            self.indent_h += 1
            for i, attr in enumerate([self.block_attrs[n] for n in self.block_attr_names]):
                construct = attr.construct()
                if construct:
                    if i == num_block_attrs - 1: # last one
                        self.h_code(attr.construct() + ' {};')
                    else:
                        self.h_code(attr.construct() + ',')
            self.indent_h -= 1
            
            # members
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                declare = attr.declare()
                if declare:
                    self.h_comment(attr.description.strip())
                    self.h_code(declare)
            self.h_code("};")
            self.file_h.write("\n")
            
            # istream
            self.h_code('void NifStream( %s & val, istream & in, uint version );'%self.block_cname)
            self.cpp_code('void NifStream( %s & val, istream & in, uint version ) {'%self.block_cname)
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                self.cpp_code("NifStream( %s, in, version );"%attr.cname)
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # ostream
            self.h_code('void NifStream( %s const & val, ostream & out, uint version );'%self.block_cname)
            self.cpp_code('void NifStream( %s const & val, ostream & out, uint version ) {'%self.block_cname)
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                self.cpp_code("NifStream( %s, out, version );"%attr.cname)
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # operator<< (meant for stdout)
            self.h_code('ostream & operator<<( ostream & lh, %s const & rh );'%self.block_cname)
            self.cpp_code('ostream & operator<<( ostream & lh, %s const & rh ) {'%self.block_cname)
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                self.cpp_code("lh << \"%s:  \" << rh.%s << endl;"%(attr.name, attr.cname))
            self.cpp_code("};")
            self.file_cpp.write("\n")
            self.file_h.write("\n")
            
            # done!
            self.current_block = None
            
        if name == "niblock" or name == "ancestor":
            assert(self.current_block != None) # debug
            assert(self.current_attr == None) # debug
            
            # members
            self.h_comment("\n" + self.block_comment.strip() + "\n")
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                declare = attr.declare()
                if declare:
                    self.h_comment(attr.description.strip())
            self.h_code('#define %s_MEMBERS'%cpp_define_name(self.block_cname), append_backslash = True)
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                declare = attr.declare()
                if declare:
                    self.h_code(declare + "\\")
            self.file_h.write("\n")
            
            # header
            self.h_comment(self.block_comment.strip())
            inherit = self.block_inherit
            if not inherit:
                inherit = "ABlock"
            self.h_code('#define %s_PARENTS %s'%(cpp_define_name(self.block_cname), inherit))
            
            # methods
            self.h_code('void Read( %s & val, istream & in, uint version );'%self.block_cname)
            self.h_code('void Write( %s const & val, ostream & out, uint version ) const;'%self.block_cname)
            self.h_code('string asString() const;')
            self.h_code('string GetBlockType() const { return "%s"};'%self.block_cname)
            self.h_code("attr_ref GetAttr( string const & attr_name ) const;")
            self.cpp_code("attr_ref %s::GetAttr( string const & attr_name ) const {"%self.block_cname)
            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
                self.cpp_code("if ( attr_name == \"%s\" )"%attr.name)
                self.cpp_code("return attr_ref(%s);"%attr.cname, True)
            if name == "niblock":
                self.cpp_code("throw runtime_error(\"The attribute you requested does not exist in this block.\");")
            self.cpp_code("return attr_ref();")
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # constructor
##            self.h_code("%s() {"%self.block_name)
##            self.file_h.write('// __BEGIN_CONSTRUCT_%s\n'%self.block_cname.upper())
##            for attr in [self.block_attrs[n] for n in self.block_attr_names]:
##                self.h_code_construct(attr)
##            self.file_h.write('// __END_CONSTRUCT_%s\n'%self.block_cname.upper())
##            self.h_code("};")

            # done!
            self.current_block = None
        elif name == "basic":
            self.current_block = None
        elif name == "add":
            # done!
            self.current_attr = None

    def characters(self, content):
        if self.current_attr:
            self.block_attrs[self.current_attr].description += content
        elif self.current_block:
            self.block_comment += content

    def h_construct(self, attr):
        # first handle the case of a string
        if attr.type == "char" and attr.arr1 and not attr.arr2:
            self.h_code( "%s = string(%s, ' ');"%(attr.cname, attr.carr1))
            return
    
        # other cases
        if not attr.arr1:
            # no array
            if attr.default:
                self.h_code( "%s = %s"%(attr.cname, attr.default) )
            else:
                pass
                # no need to construct
                #self.h_code( "%s = %s;"%(attr.cname, result))
        elif not attr.arr2:
            # 1-dim array
            if attr.default:
                self.h_code( "%s = vector<%s>(%s, %s);"%(attr.cname, attr.ctype, attr.carr1, attr.default) )
            else:
                self.h_code( "%s = vector<%s>(%s);"%(attr.cname, attr.ctype, attr.carr1) )
        elif not attr.arr2_dynamic:
            # 2-dim array, non-dynamic
            if attr.default:
                self.h_code(\
                    "%s = vector<vector<%s> >(%s, vector<%s>(%s, %s));"%(\
                    attr.cname, attr.ctype, attr.carr1, attr.ctype, attr.carr2, attr.default) )
            else:
                self.h_code(\
                    "%s = vector<vector<%s> >(%s, vector<%s>(%s));"%(\
                    attr.cname, attr.ctype, attr.carr1, attr.ctype, attr.carr2) )
        else:
            # 2-dim array, dynamic
            self.h_code(\
                "%s = vector<vector<%s> >(%s);\nfor (int i; i<%s, i++)\n\t%s[i] = vector<%s(%s[i], %s))>;"%(\
                    attr.cname, attr.ctype, attr.carr1, attr.carr1, attr.cname, attr.carr2, default) )

    def cpp_code(self, txt, extra_indent = False):
        if txt[:1] == "}":
            self.indent_cpp -= 1
        if extra_indent: self.indent_cpp += 1
        self.file_cpp.write(cpp_code(txt, self.indent_cpp))
        if extra_indent: self.indent_cpp -= 1
        if txt[-1:] == "{":
            self.indent_cpp += 1
    
    def h_code(self, txt, extra_indent = False, append_backslash = False):
        if txt[:1] == "}":
            self.indent_h -= 1
        if txt[-1:] == ":":
            self.indent_h -= 1
        if extra_indent: self.indent_h += 1
        self.file_h.write(cpp_code(txt, self.indent_h, append_backslash))
        if extra_indent: self.indent_h -= 1
        if txt[-1:] == ":":
            self.indent_h += 1
        if txt[-1:] == "{":
            self.indent_h += 1

    def cpp_comment(self, txt):
        self.file_cpp.write(cpp_comment(txt, self.indent_cpp))

    def h_comment(self, txt):
        self.file_h.write(cpp_comment(txt, self.indent_h))

p = make_parser()
p.setContentHandler(SAXtracer())
p.parse("nif.xml")
