import sys
from xml.sax import *

INDENT = 0 # indent level

# indent C++ code; the returned result never ends with a newline
def cpp_code(txt):
    global INDENT

    # create indentation string
    prefix = "  " * INDENT
    # strip trailing whitespace, including newlines
    txt = txt.rstrip()
    # replace tabs
    txt = txt.replace("\t", "  ");
    # indent, and add newline
    result = prefix + txt.replace("\n", "\n" + prefix)
    return result

# create C++-style comments (handle multilined comments as well)
# result always ends with a newline
def cpp_comment(txt):
    return cpp_code( "// " . txt.replace("\n", "\n// ") );

# this returns this->$objectname if it's a class variable, $objectname
# otherwise; one array index is substituted as well.
def cpp_resolve(objectname):
    posarr1begin = objectname.find("[")
    posarr1end = objectname.find("]")
    if ((posarr1begin >= 0) and (posarr1end > posarr1begin)):
        objectname = objectname[:posarr1begin + 1] + cpp_resolve(objectname[posarr1begin + 1:posarr1end - 1]) + objectname[posarr1end:]

    return objectname

def cpp_type_size(some_type):
    if ( some_type == "byte" ): return 1
    elif ( some_type == "bool" ): return 1
    elif ( some_type == "short" ): return 2
    elif ( some_type == "int" or some_type == "alphaformat" or some_type == "applymode" or some_type == "lightmode" or some_type == "mipmapformat" or some_type == "pixellayout" or some_type == "vertmode" ): return 4
    elif ( some_type == "flags" ): return 2
    elif ( some_type == "link" or some_type == "nodeancestor" or some_type == "skeletonroot" or some_type == "crossref" or some_type == "parent" ): return 4
    elif ( some_type == "char" ): return 1
    elif ( some_type == "float" ): return 4
    else: return -1

def cpp_type(some_type):
    if ( some_type == "byte" ): return "unsigned char"
    elif ( some_type == "bool" ): return "bool"
    elif ( some_type == "short" ): return "unsigned short" 
    elif ( some_type == "int" or some_type == "alphaformat" or some_type == "applymode" or some_type == "lightmode" or some_type == "mipmapformat" or some_type == "pixellayout" or some_type == "vertmode" ): return "unsigned int"
    elif ( some_type == "flags" ): return "unsigned short"
    elif ( some_type == "link" or some_type == "nodeancestor" or some_type == "skeletonroot" or some_type == "crossref" or some_type == "parent" ): return "int"
    elif ( some_type == "char" ): return "char"
    elif ( some_type == "float" ): return "float"
    else: return some_type

def cpp_code_decl(var, some_type, some_type_arg, sizevar, sizevarbis, sizevarbisdyn):
    some_type_arg = cpp_resolve(some_type_arg)
    sizevar = cpp_resolve(sizevar)
    sizevarbis = cpp_resolve(sizevarbis)

    # first handle the case of a string
    if ( ( some_type == "char" ) and ( sizevar != None ) and ( sizevarbis == None ) ):
        return python_code( "string $var" )

    result = cpp_type( some_type )
    if sizevar: result = "vector<%s>"%result
    if sizevarbis: result = "vector<%s >"%result
    result += " " + var
    #if ( $some_type_arg and ! $sizevar )
    #    $result .= "($some_type_arg)";
    return cpp_code( result + ";" )

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

# This class has all the XML parser code.
class SAXtracer(ContentHandler):
    def __init__(self,objname):
        self.objname=objname
        self.met_name=""
        self.block_name = None
        self.block_inherit = None
        self.block_attrs = None

    def startElement(self, name, attrs):
        global INDENT
        if name == "niblock" or name == "compound" or name == "ancestor":
            self.block_name = attrs.get('name', '').replace(' ', '_')
            self.block_inherit = None
            self.block_attrs = []
        elif name == "inherit":
            self.block_inherit = attrs.get('name', '').replace(' ', '_')
        elif name == "add":
            attr = [ None, None, None, None ]
            attr[ATTR_NAME] = attrs.get('name', '').lower().replace(' ', '_')
            attr[ATTR_TYPE] = attrs.get('type', '').replace(' ', '_')
            attr[ATTR_ARR1] = attrs.get('arr1', "").lower().replace(' ', '_')
            attr[ATTR_ARR2] = attrs.get('arr2', "").lower().replace(' ', '_')
            self.block_attrs.append(attr)

    def endElement(self, name):
        global INDENT
        if name == "niblock" or name == "compound" or name == "ancestor":
            if self.block_inherit:
                print cpp_code("struct ext_%s : ext_%s {" % (self.block_name, self.block_inherit))
            else:
                print cpp_code("struct ext_%s {" % self.block_name)
            INDENT += 1
            for attr in self.block_attrs:
                print cpp_code_decl(attr[ATTR_NAME], attr[ATTR_TYPE], '', attr[ATTR_ARR1], attr[ATTR_ARR2], '')
            INDENT -= 1
            print cpp_code("}")
            self.block_name = None
            self.block_inherit = None
            self.block_attrs = None

print """/* --------------------------------------------------------------------------
 * nif_struct.h: C++ header file for raw reading, writing, and printing
 *               NetImmerse and Gamebryo files (.nif & .kf & .kfa)
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

#ifndef _NIF_STRUCT_H_
#define _NIF_STRUCT_H_

#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

#define MAX_ARRAYDUMPSIZE 8       // we shall not dump arrays that have more elements than this number
#define MAX_STRLEN        1024    // reading/writing NiStrings longer than this number will raise an exception
#define MAX_ARRAYSIZE     8388608 // reading/writing arrays that have more elements than this number will raise an exception
#define MAX_HEXDUMP       128     // number of bytes that should be dumped if something goes wrong (set to 0 to turn off hex dumping)

// 
// A simple custom exception class
//
class NIFException {
public:
  char* message;
  NIFException( char* m ) { message = m; };
};



"""

p = make_parser()

p.setContentHandler(SAXtracer("doc_handler"))
p.parse("nif.xml")
