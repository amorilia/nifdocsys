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

struct ni_object {
  attr_ref GetAttrByName( string const & name ) = 0;
};

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
def cpp_code(txt, indent):
    # create indentation string
    prefix = "  " * indent
    # strip trailing whitespace, including newlines
    txt = txt.rstrip()
    # replace tabs
    txt = txt.replace("\t", "  ");
    # indent, and add newline
    result = prefix + txt.replace("\n", "\n" + prefix) + "\n"
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

ATTR_NAME = 0
ATTR_TYPE = 1
ATTR_ARR1 = 2
ATTR_ARR2 = 3
ATTR_CPP_NAME = 4
ATTR_CPP_TYPE = 5
ATTR_CPP_ARR1 = 6
ATTR_CPP_ARR2 = 7
ATTR_VER1 = 8
ATTR_VER2 = 9
ATTR_ARG = 10
ATTR_CPP_ARG = 11
ATTR_COMMENT = 12

# This class has all the XML parser code.
class SAXtracer(ContentHandler):
    def __init__(self,objname):
        self.attr_idx = -1
        self.in_block = False
        self.in_attr = False

    def cpp_code(self, txt, extra_indent = False):
        if txt[:1] == "}":
            self.indent_cpp -= 1
        if extra_indent: self.indent_cpp += 1
        self.file_cpp.write(cpp_code(txt, self.indent_cpp))
        if extra_indent: self.indent_cpp -= 1
        if txt[-1:] == "{":
            self.indent_cpp += 1
    
    def h_code(self, txt, extra_indent = False):
        if txt[:1] == "}":
            self.indent_h -= 1
        if extra_indent: self.indent_h += 1
        self.file_h.write(cpp_code(txt, self.indent_h))
        if extra_indent: self.indent_h -= 1
        if txt[-1:] == "{":
            self.indent_h += 1

    def cpp_comment(self, txt):
        self.file_cpp.write(cpp_comment(txt, self.indent_cpp))

    def h_comment(self, txt):
        self.file_h.write(cpp_comment(txt, self.indent_h))

    def cpp_type_name(self, n):
        if n == None: return None
        try:
            return self.native_types[n]
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

    def cpp_attr_name(self, n):
        if n == None: return None
        return n.lower().replace(' ', '_').replace('?', '_')

    def h_code_decl(self, var, some_type, some_type_arg, sizevar, sizevarbis, sizevarbisdyn):
        some_type = self.cpp_type_name(some_type)
        some_type_arg = cpp_resolve(some_type_arg)
        sizevar = cpp_resolve(sizevar)
        sizevarbis = cpp_resolve(sizevarbis)

        # first handle the case of a string
        if ( ( some_type == "char" ) and ( sizevar != None ) and ( sizevarbis == None ) ):
            self.h_code( "string $var" )
            return

        result = some_type
        if sizevar: result = "vector<%s>"%result
        if sizevarbis: result = "vector<%s >"%result
        result += " " + var
        #if ( $some_type_arg and ! $sizevar )
        #    $result .= "($some_type_arg)";
        self.h_code(result + ";")

    def h_code_construct(self, var, some_type, some_type_arg, sizevar, sizevarbis, sizevarbisdyn):
        # skip native types; these should have standard constructors
        # TODO: handle these as well and provide them with default values
        if self.native_types.has_key(some_type): return
        
        some_type = self.cpp_type_name(some_type)
        some_type_arg = cpp_resolve(some_type_arg)
        sizevar = cpp_resolve(sizevar)
        sizevarbis = cpp_resolve(sizevarbis)
        
        result = ""
        # first handle the case of a string
        if ( some_type == "char" ) and sizevar and sizevarbis == None:
            self.h_code( "%s = string(%s, ' ');"%(var, sizevar))
            return
    
        # other cases
        if some_type_arg:
            result = some_type + "(%s)"%some_type_arg
        else:
            result = some_type + "()"
        if not sizevar:
            self.h_code( "%s = %s;"%(var, result))
        elif not sizevarbis:
            self.h_code( "%s = vector<%s>(%s, %s);"%(var, some_type, sizevar, result) )
        elif not sizevarbisdyn:
            self.h_code( "%s = vector<vector<%s> >(%s, vector<%s>(%s, %s));"%(var, some_type, sizevar, some_type, sizevarbis, result) )
        else:
            self.h_code( "%s = vector<vector<%s> >(%s);\nfor (int i; i<%s, i++)\n\t%s[i] = vector<%s(%s[i], %s))>;"%(var, some_type, sizevar, sizevar, var, sizevarbis, result) )

    def startDocument(self):
        self.indent_h = 0
        self.indent_cpp = 0
        self.native_types = {}
        self.file_h = open("xml_extract.h", "w")
        self.file_cpp = open("xml_extract.cpp", "w")
        self.file_h.write(H_HEADER)

        self.file_cpp.write(CPP_HEADER)

    def endDocument(self):
        self.file_h.write("\n#endif\n")
        self.file_h.close()
        self.file_cpp.close()

    def startElement(self, name, attrs):
        if name == "basic":
            if attrs.has_key('niflibtype'):
                self.native_types[attrs.get('name')] = attrs.get('niflibtype')
        elif name == "niblock" or name == "compound" or name == "ancestor":
            self.in_block = True
            self.attr_idx = -1
            self.block_name = self.cpp_type_name(attrs.get('name'))
            self.block_inherit = None
            self.block_attrs = []
            self.block_template = False
            self.block_comment = ''
        elif name == "inherit":
            self.block_inherit = self.cpp_type_name(attrs.get('name'))
        elif name == "add":
            self.in_attr = True
            self.attr_idx += 1
            attr = [ None ] * 13

            # read the raw values
            attr[ATTR_NAME] = attrs.get('name')
            attr[ATTR_TYPE] = attrs.get('type')
            if attrs.has_key('arg'): attr[ATTR_ARG] = attrs.get('arg')
            if attrs.has_key('arr1'): attr[ATTR_ARR1] = attrs.get('arr1')
            if attrs.has_key('arr2'): attr[ATTR_ARR2] = attrs.get('arr2')
            if attrs.has_key('ver1'): attr[ATTR_VER1] = attrs.get('ver1')
            if attrs.has_key('ver2'): attr[ATTR_VER2] = attrs.get('ver2')
            attr[ATTR_CPP_NAME] = self.cpp_attr_name(attr[ATTR_NAME])
            attr[ATTR_CPP_TYPE] = self.cpp_type_name(attr[ATTR_TYPE])
            attr[ATTR_CPP_ARR1] = self.cpp_attr_name(attr[ATTR_ARR1])
            attr[ATTR_CPP_ARR2] = self.cpp_attr_name(attr[ATTR_ARR2])
            attr[ATTR_CPP_ARG] = self.cpp_attr_name(attr[ATTR_ARG])
            attr[ATTR_COMMENT] = ''

            # post-processing
            if attr[ATTR_TYPE] == '(TEMPLATE)':
                self.block_template = True

            # store it
            self.block_attrs.append(attr)

    def endElement(self, name):
        if name == "niblock" or name == "compound" or name == "ancestor":
            self.in_block = False
            # header
            self.h_comment(self.block_comment.strip())
            hdr = "struct %s"%self.block_name
            if self.block_template:
                hdr += "<T>"
            if self.block_inherit:
                hdr += " : public %s"%self.block_inherit
            else:
                hdr += " : public ni_block"
            hdr += " {"
            self.h_code(hdr)
            
            # fields
            for attr in self.block_attrs:
                self.h_comment(attr[ATTR_COMMENT].strip())
                self.h_code_decl(attr[ATTR_CPP_NAME], attr[ATTR_TYPE], attr[ATTR_CPP_ARG], attr[ATTR_CPP_ARR1], attr[ATTR_CPP_ARR2], '')
            self.h_code("%s() {"%self.block_name)
            for attr in self.block_attrs:
                self.h_code_construct(attr[ATTR_CPP_NAME], attr[ATTR_TYPE], attr[ATTR_CPP_ARG], attr[ATTR_CPP_ARR1], attr[ATTR_CPP_ARR2], False)
            self.h_code("};")
            self.h_code("attr_ref GetAttrByName( string const & attr_name );")
            self.h_code("};")
            self.file_h.write("\n")
            self.cpp_code("attr_ref %s::GetAttrByName( string const & attr_name ) {"%self.block_name)
            for attr in self.block_attrs:
                self.cpp_code("if ( attr_name == \"%s\" )"%attr[ATTR_NAME])
                self.cpp_code("return attr_ref(%s);"%attr[ATTR_CPP_NAME], True)
            if name == "niblock":
                self.cpp_code("throw runtime_error(\"The attribute you requested does not exist in this block.\");")
            self.cpp_code("return attr_ref();")
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # istream
            self.h_code('void NifStream( %s & val, istream & in, uint version );'%self.block_name)
            self.cpp_code('void NifStream( %s & val, istream & in, uint version ) {'%self.block_name)
            for attr in self.block_attrs:
                self.cpp_code("NifStream( %s, in, version );"%attr[ATTR_CPP_NAME])
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # ostream
            self.h_code('void NifStream( %s const & val, ostream & out, uint version );'%self.block_name)
            self.cpp_code('void NifStream( %s const & val, ostream & out, uint version ) {'%self.block_name)
            for attr in self.block_attrs:
                self.cpp_code("NifStream( %s, out, version );"%attr[ATTR_CPP_NAME])
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # operator<< (meant for stdout)
            self.h_code('ostream & operator<<( ostream & lh, %s const & rh );'%self.block_name)
            self.file_h.write("\n")
            self.cpp_code('ostream & operator<<( ostream & lh, %s const & rh ) {'%self.block_name)
            for attr in self.block_attrs:
                self.cpp_code("lh << \"%s:  \" << rh.%s << endl;"%(attr[ATTR_NAME], attr[ATTR_CPP_NAME]))
            self.cpp_code("};")
            self.file_cpp.write("\n")

            # clean up
            del self.block_name
            del self.block_inherit
            del self.block_attrs
            del self.block_template
            
        elif name == "add":
            self.in_attr = False

    def characters(self, content):
        if self.in_attr:
            self.block_attrs[self.attr_idx][ATTR_COMMENT] += content
        elif self.in_block:
            self.block_comment += content

p = make_parser()

p.setContentHandler(SAXtracer("doc_handler"))
p.parse("nif.xml")
