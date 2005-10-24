<?php

define('IN_PHPBB', true);
$phpbb_root_path = '../forum/';
include($phpbb_root_path . 'extension.inc');
include($phpbb_root_path . 'common.'.$phpEx);
$docsys_root_path = './';
include($docsys_root_path . 'common.'.$phpEx);

// Connect to database and read tables.

include($docsys_root_path . 'readdb.' . $phpEx);

// Now sort the blocks.

include($docsys_root_path . 'sortdb.' . $phpEx);

require("../header.tpl");

echo <<<ENDHTML
<h1>File Format Browser - Python</h1>

<p align="center">
<a href="index.php?mode=list&amp;table=block&amp;view=hier">Hierarchical</a>
|
<a href="index.php?mode=list&amp;table=block&amp;view=alpha">Alphabetical</a>
|
<a href="cstyle.php">C-Style</a>
|
<a href="python.php">Python</a>
</p>

<pre>

ENDHTML;

/**
 *  python file header, and definition of low-level classes
 */

echo htmlify( <<<ENDHTML
# --------------------------------------------------------------------------
# nif4.py: a python interface for reading, writing, and printing
#          NetImmerse 4.0.0.2 files (.nif & .kf)
# --------------------------------------------------------------------------
# ***** BEGIN BSD LICENSE BLOCK *****
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
# ***** END BSD LICENCE BLOCK *****
# --------------------------------------------------------------------------
# Notes:
#
# - This file was generated from a database, and as a result, the code
#   is highly unoptimized.
# - Not all of the known code blocks are recognized. However, it should 
#   process most static models. See 'read' member of the 'NIF' class for a 
#   list of supported block types.
# - Happy modding!
#

import struct


MAX_ARRAYDUMPSIZE = 8 # we shall not dump arrays that have more elements than this number

MAX_STRLEN = 256 # reading/writing strings longer than this number will raise an exception

MAX_ARRAYSIZE = 1048576 # reading/writing arrays that have more elements than this number will raise an exception

MAX_HEXDUMP = 128 # number of bytes that should be dumped if something goes wrong (set to 0 to turn off hex dumping)

# 
# A simple custom exception class
# 
class NIFError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)




ENDHTML
);

/**
 *  functions for formatting python commands, and htmlifying strings
 */

$indent = 0; // use $indent++ and $indent-- to change the indentation level

// indent python code; the returned result always ends with a newline
function python_code( $txt )
{
  global $indent;

  // create indentation string
  $prefix = "";
  for ($t = 0; $t < $indent; $t++) $prefix .= "    "; // four spaces per level
  // strip trailing whitespace, including newlines
  $txt = rtrim( $txt );
  // replace tabs
  $txt = ereg_replace( "\t", "    ", $txt );
  // indent, and add newline
  $result = $prefix . ereg_replace( "\n", "\n" . $prefix, $txt ) . "\n";
  return $result;
}

// create python-style comments (handle multilined comments as well);
// result always ends with a newline
function python_comment( $txt )
{
  return python_code ( "# " . ereg_replace( "\n", "\n# ", htmlify( wordwrap( $txt ) ) ) );
}

// this returns self.$objectname if it's a class variable, $objectname
// otherwise; one array index is substituted as well.
function python_resolve( $objectname )
{
  $posarr1begin = strpos($objectname, "[");
  $posarr1end = strpos($objectname, "]");
  if (($posarr1begin >= 0) and ($posarr1end > $posarr1begin)) {
    $objectname = substr($objectname, 0, $posarr1begin + 1) . python_resolve(substr($objectname, $posarr1begin + 1, $posarr1end - $posarr1begin - 1)) . substr($objectname, $posarr1end, strlen($objectname));
  }

  if (substr($objectname, 0, 5) == "self.") return $objectname;
  if ($objectname) {
    if (((ord($objectname) >= ord("A")) and (ord($objectname) <= ord("Z"))) or ((ord($objectname) >= ord("0")) and (ord($objectname) <= ord("9"))))
      return $objectname;
    else
      return "self.$objectname";
  }
  return $objectname;
}

function python_code_init($var, $some_type, $some_type_arg, $sizevar, $sizevarbis)
{
  $some_type_arg = python_resolve($some_type_arg);
  $sizevar = python_resolve($sizevar);
  $sizevarbis = python_resolve($sizevarbis);

  // first handle the case of a string
  if ( ( $some_type == "char" ) and ( $sizevar != null ) and ( $sizevarbis == null ) )
    return python_code( "self.$var = ' ' * $sizevar" );

  // other cases
  if ( ( $some_type == "byte" )
       or ( $some_type == "short" )
       or ( $some_type == "int" )
       or ( $some_type == "flags" ) )
    // byte, short, int => 32 bit signed integer
    $result = "0";
  elseif ( $some_type == "index" )
    // index -1 refers to nothing
    $result = "-1";
  elseif ( $some_type == "char" )
    // character => string of length 1
    $result = "' '";
  elseif ( $some_type == "float" )
    // float => C-style "double"
    $result = "0.0";
  else
    // standard constructor
    if ($some_type_arg)
	$result = "$some_type($some_type_arg)";
    else
      $result = "$some_type()";
  if ( ! $sizevar ) return python_code( "self.$var = " . $result );
  else
    if ( ! $sizevarbis )
      return python_code( "self.$var = [ None ] * $sizevar\nfor count in range($sizevar): self.${var}[count] = $result" );
    else
      return python_code( "self.$var = [ [ None ] * $sizevarbis ] * $sizevar\nfor count in range($sizevar):\n\tfor count2 in range($sizevarbis):\n\t\tself.${var}[count][count2] = $result" );
}

function python_code_read($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $condvar, $condval, $condtype)
{
  global $indent;
  $result = "";
  $some_type_arg = python_resolve($some_type_arg);
  $sizevar = python_resolve($sizevar);
  $sizevarbis = python_resolve($sizevarbis);
  $condvar = python_resolve($condvar);

  // array size check
  if ( $sizevar ) {
    $result .= python_code( "if ($sizevar > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%$sizevar)" );
    if ( $sizevarbis )
      $result .= python_code( "if ($sizevarbis > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%$sizevarbis)" );
  }

  // initialise the variable, if required
  if ( ( $sizevar ) or ( $condvar ) or
       ( ( $some_type != "byte" ) and ( $some_type != "short" ) and ( $some_type != "int" ) and ( $some_type != "char" ) and
	 ( $some_type != "flags" ) and ( $some_type != "index" ) and ( $some_type != "float" ) ) )
    $result .= python_code_init( $var, $some_type, $some_type_arg, $sizevar, $sizevarbis );

  // conditional: if statement
  if ( $condvar ) {
    if ( $condval === null )
      $result .= python_code( "if ($condvar != 0):" );
    else {
      if ( ( $condtype === null ) or ( $condtype === 0 ) )
        $result .= python_code( "if ($condvar == $condval):" );
      else
        $result .= python_code( "if ($condvar != $condval):" );
    };
    $indent++;
  }

  // first handle the case of a string
  if ( ( $some_type == "char" ) and ( $sizevar ) and ( ! $sizevarbis ) ) {
    $result .= python_code( "if ($sizevar > MAX_STRLEN): raise NIFError('string unreasonably long (size %i)'%$sizevar)" );
    $result .= python_code( "self.$var, = struct.unpack('<%us'%$sizevar, file.read($sizevar))" );
  } else {
    
    // other cases
    
    // array: for loop
    if ( $sizevar ) {
      $result .= python_code( "for count in range($sizevar):" );
      $indent++;
      $var .= "[count]"; // this is now the variable that we shall read
      // arraybis: for loop
      if ( $sizevarbis ) {
	$result .= python_code( "for count2 in range($sizevarbis):" );
	$indent++;
	$var .= "[count2]"; // this is now the variable that we shall read
      }
    }
    
    // main
    if ( $some_type == "byte" )
      $result .= python_code( "self.$var, = struct.unpack('<B', file.read(1))" );
    elseif ( $some_type == "short" )
      $result .= python_code( "self.$var, = struct.unpack('<H', file.read(2))" );
    elseif ( $some_type == "flags" )
      $result .= python_code( "self.$var, = struct.unpack('<H', file.read(2))" );
    elseif ( $some_type == "int" )
      $result .= python_code( "self.$var, = struct.unpack('<I', file.read(4))" );
    elseif ( $some_type == "index" )
      $result .= python_code( "self.$var, = struct.unpack('<i', file.read(4))" );
    elseif ( $some_type == "char" )
      $result .= python_code( "self.$var, = struct.unpack('<c', file.read(1))" );
    elseif ( $some_type == "float" )
      $result .= python_code( "self.$var, = struct.unpack('<f', file.read(4))" );
    else
      $result .= python_code( "self.$var.read(file)" );
    
    // restore indentation
    if ( $sizevar ) {
      $indent--;
      if ( $sizevarbis ) $indent--;
    };
  };
  
  if ( $condvar ) $indent--;
    
  return $result;
}

function python_code_write($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $condvar, $condval, $condtype)
{
  global $indent;
  $result = "";
  $sizevar = python_resolve($sizevar);
  $sizevarbis = python_resolve($sizevarbis);
  $condvar = python_resolve($condvar);

  // array size check
  if ( $sizevar ) {
    $result .= python_code( "if ($sizevar > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%$sizevar)" );
    if ( $sizevarbis )
      $result .= python_code( "if ($sizevarbis > MAX_ARRAYSIZE): raise NIFError('array size unreasonably large (size %i)'%$sizevarbis)" );
  }

  // conditional: if statement
  if ( $condvar ) {
    if ( $condval === null )
      $result .= python_code( "if ($condvar != 0):" );
    else {
      if ( ( $condtype === null ) or ( $condtype === 0 ) )
        $result .= python_code( "if ($condvar == $condval):" );
      else
        $result .= python_code( "if ($condvar != $condval):" );
    };
    $indent++;
  }

  // first handle the case of a string
  if ( ( $some_type == "char" ) and ( $sizevar ) and ( ! $sizevarbis ) )
    $result .= python_code( "file.write(struct.pack('<%us'%$sizevar, self.$var))" );
  else {
    
    // other cases
    
    // array: for loop
    if ( $sizevar ) {
      $result .= python_code( "for count in range($sizevar):" );
      $indent++;
      $var .= "[count]"; // this is now the variable that we shall write
      // arraybis: for loop
      if ( $sizevarbis ) {
	$result .= python_code( "for count2 in range($sizevarbis):" );
	$indent++;
	$var .= "[count2]"; // this is now the variable that we shall write
      }
    }
    
    // main
    if ( $some_type == "byte" )
      $result .= python_code( "file.write(struct.pack('<b', self.$var))" );
    elseif ( $some_type == "short" )
      $result .= python_code( "file.write(struct.pack('<H', self.$var))" );
    elseif ( $some_type == "flags" )
      $result .= python_code( "file.write(struct.pack('<H', self.$var))" );
    elseif ( $some_type == "int" )
      $result .= python_code( "file.write(struct.pack('<I', self.$var))" );
    elseif ( $some_type == "index" )
      $result .= python_code( "file.write(struct.pack('<i', self.$var))" );
    elseif ( $some_type == "char" )
      $result .= python_code( "file.write(struct.pack('<c', self.$var))" );
    elseif ( $some_type == "float" )
      $result .= python_code( "file.write(struct.pack('<f', self.$var))" );
    else
      $result .= python_code( "self.$var.write(file)" );  
    
    // restore indentation
    if ( $sizevar ) {
      $indent--;
      if ( $sizevarbis ) $indent--;
    }
  };
  
  if ( $condvar ) $indent--;

  return $result;
}

function python_code_dump($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $condvar, $condval, $condtype)
{
  global $indent;
  $result = "";
  $displayvar = "'$var'"; // how the name $var will be printed
  $origvar = $var; // we need this if an array is not dumped
  $sizevar = python_resolve($sizevar);
  $sizevarbis = python_resolve($sizevarbis);
  $condvar = python_resolve($condvar);

  // conditional: if statement
  if ( $condvar ) {
    if ( $condval === null )
      $result .= python_code( "if ($condvar != 0):" );
    else {
      if ( ( $condtype === null ) or ( $condtype === 0 ) )
        $result .= python_code( "if ($condvar == $condval):" );
      else
        $result .= python_code( "if ($condvar != $condval):" );
    };
    $indent++;
  }

  // first handle the case of a string
  if ( ( $some_type == "char" ) and ( $sizevar ) and ( ! $sizevarbis ) )
    $result .= python_code( "s += $displayvar + ': %s\\n'%self.$var" );
  // double arrays
  else if ($sizevarbis)
    $result .= python_code( "s += '$var: array[%i][%i]\\n'%($sizevar,$sizevarbis)");
  else {
    
    // other cases
    
    if ( $sizevar ) {
      $result .= python_code( "if ($sizevar <= MAX_ARRAYDUMPSIZE):" );
      $indent++;
      $result .= python_code( "for count in range($sizevar):" );
      $indent++;
      $displayvar .= " + '[%i]'%count"; // also print the index
      $var .= "[count]"; // this is now the variable that we shall dump
    }
    
    if ( ( $some_type == "byte" )
	 or ( $some_type == "short" )
	 or ( $some_type == "int" )
	 or ( $some_type == "index" ) )
      $result .= python_code ( "s += $displayvar + ': %i\\n'%self.$var" );
    elseif  ( $some_type == "char" ) 
      $result .= python_code ( "s += $displayvar + ': %s\\n'%self.$var" );
    elseif  ( $some_type == "float" )
      $result .= python_code ( "s += $displayvar + ': %f\\n'%self.$var" );
    elseif ( $some_type == "flags" )
      $result .= python_code ( "s += $displayvar + ': 0x%04X\\n'%self.$var" ); // hex format
    else
      $result .= python_code ( "s += $displayvar + ':\\n'\ns += str(self.$var) + '\\n'" );
    
    // restore indentation
    if ( $sizevar ) {
      $indent--;
      $indent--;
      // if we didn't print the array's contents, then...
      $result .= python_code( "else:" );
      $indent++;
      $result .= python_code( "s += '$origvar: array[%i]\\n'%$sizevar" );
      $indent--;
    }
  };
  
  if ( $condvar ) $indent--;

  return $result;
}

// convert special characters to html, including single and double
// quotes
function htmlify( $txt )
{
  return htmlentities( $txt, ENT_QUOTES );
}

/**
 *  main loop: generate python classes for each block
 */

foreach ( $block_ids_sort as $block_id ) {
  if ( $block_category[$block_id] < 2 ) continue;
  // description
  echo python_comment( "\n" . $block_description[$block_id] . "\n" );
  // class header
  if ( $block_parent_id[$block_id] )
    echo htmlify( python_code ( "class $block_cname[$block_id]($block_parent_cname[$block_id]):" ) );
  else
    echo htmlify( python_code ( "class $block_cname[$block_id]:" ) );
  
  // increase indentation level
  $indent++;
  
  // in python, members are defined in the constructor
  // so that's what we start with
  echo python_comment ( "constructor" );
  if ( $attr_precedence[$block_attributes[$block_id][0]] == -1 )
    echo htmlify( python_code ( "def __init__(self, init_arg):" ) );
  else
    echo htmlify( python_code ( "def __init__(self):" ) );
  $indent++;
  // non-abstract blocks (which have no children), declare a block_type string variable
  if ( ! $block_is_abstract[$block_id] )
    echo htmlify( python_code ( "self.block_type = mystring(\"$block_cname[$block_id]\")" ) );
  // call base class constructor (which btw. should not have an initialization argument!)
  if ( $block_parent_id[$block_id] )
    echo htmlify( python_code ( "$block_parent_cname[$block_id].__init__(self)" ) );
  // here we iterate over all rows
  foreach ( $block_attributes[$block_id] as $attr_id ) {
    if ( $attr_description[$attr_id] )
      echo python_comment( $attr_description[$attr_id] );
    if ( $attr_precedence[$attr_id] == -1 )
      echo htmlify( python_code( "self.$attr_cname[$attr_id] = init_arg" ) );
    else
      echo htmlify( python_code_init( $attr_cname[$attr_id],
				      $attr_type_cname[$attr_id],
				      $attr_arg_cname[$attr_id],
				      $attr_arr1_cname[$attr_id],
				      $attr_arr2_cname[$attr_id] ) );
  }
  $indent--;
  echo "\n\n\n";
  
  // read from file
  if ( $block_is_abstract[$block_id] )
    echo python_comment ( "read from file" );
  else
    echo python_comment ( "read from file, excluding type string" );
  echo htmlify( python_code ( "def read(self, file):" ) );
  $indent++;
  // call base class reader
  if ( $block_parent_id[$block_id] )
    echo htmlify( python_code ( "$block_parent_cname[$block_id].read(self, file)" ) );
  // again, iterate over all rows
  foreach ( $block_attributes[$block_id] as $attr_id )
    if ( $attr_precedence[$attr_id] != -1 )
      echo htmlify( python_code_read( $attr_cname[$attr_id],
				      $attr_type_cname[$attr_id],
				      $attr_arg_cname[$attr_id],
				      $attr_arr1_cname[$attr_id],
				      $attr_arr2_cname[$attr_id],
				      $attr_cond_cname[$attr_id],
				      $attr_cond_val[$attr_id],
				      $attr_cond_type[$attr_id] ) );
  $indent--;
  echo "\n\n\n";
  
  // write to file
  if ( $block_is_abstract[$block_id] )
    echo python_comment ( "write to file" );
  else
    echo python_comment ( "write to file, including type string" );
  echo htmlify( python_code ( "def write(self, file):" ) );
  $indent++;
  // non-abstract blocks (which have no children), first write a block_type string variable
  if ( ! $block_is_abstract[$block_id] )
    echo htmlify( python_code ( "self.block_type.write(file)" ) );
  // call base class writer
  if ( $block_parent_id[$block_id] )
    echo htmlify( python_code ( "$block_parent_cname[$block_id].write(self, file)" ) );
  // again, iterate over all rows
  foreach ( $block_attributes[$block_id] as $attr_id )
    if ( $attr_precedence[$attr_id] != -1 )
      echo htmlify( python_code_write( $attr_cname[$attr_id],
				       $attr_type_cname[$attr_id],
				       $attr_arg_cname[$attr_id],
				       $attr_arr1_cname[$attr_id],
				       $attr_arr2_cname[$attr_id],
				       $attr_cond_cname[$attr_id],
				       $attr_cond_val[$attr_id],
				       $attr_cond_type[$attr_id] ) );
  $indent--;
  echo "\n\n\n";
  
  // dump to screen
  echo python_comment ( "dump to screen" );
  echo htmlify( python_code ( "def __str__(self):" ) );
  $indent++;
  // non-abstract blocks (which have no children), dump their block_type string variable
  echo htmlify( python_code ( "s = ''" ) );
  if ( ! $block_is_abstract[$block_id] )
    echo htmlify( python_code ( "s += str(self.block_type)" ) );
  // call base class dumper
  if ( $block_parent_id[$block_id] )
    echo htmlify( python_code ( "s += $block_parent_cname[$block_id].__str__(self)" ) );
  // again, iterate over all rows
  foreach ( $block_attributes[$block_id] as $attr_id )
    if ( $attr_precedence[$attr_id] != -1 )
      echo htmlify( python_code_dump( $attr_cname[$attr_id],
				      $attr_type_cname[$attr_id],
				      $attr_arg_cname[$attr_id],
				      $attr_arr1_cname[$attr_id],
				      $attr_arr2_cname[$attr_id],
				      $attr_cond_cname[$attr_id],
				      $attr_cond_val[$attr_id],
				      $attr_cond_type[$attr_id] ) );
  echo htmlify( python_code ( "return s" ) );
  $indent--;
  echo "\n\n\n";
  
  // return one level
  $indent--;
};

/**
 *  high-level classes
 */

echo htmlify( <<<END
# 
# Customized string class
# 
class mystring(string):
    def __init__(self, s):
        self.length = len(s)
	self.value = s



# 
# NIF file header
#
class NiHeader:
    # constructor
    def __init__(self):
        # Morrowind files read: "NetImmerse File Format, Version 4.0.0.2"
        # (followed by a line feed (0x0A) which we however do not store)
        self.headerstr = "NetImmerse File Format, Version 4.0.0.2"
        # Morrowind files say: 0x04000002
        self.version = 0x04000002
        # number of blocks
        self.nblocks = 0



    # read from file
    def read(self, file):
        # find the header (method taken from Brandano's import script)
	file.seek(0)
	try:
	    tmp, = struct.unpack('<100s', file.read(100))
	except:
            pass # if file is less than 100 bytes long...
        # roughly check if it's a nif file
        if (tmp[0:22] != "NetImmerse File Format") and (tmp[0:20] != "Gamebryo File Format"):
            raise NIFError("Invalid header: not a NIF file")
        # if it is a nif file, this will get the header
        headerstr_len = tmp.find('\\x0A')
        if (headerstr_len < 0):
            raise NIFError("Invalid header: not a NIF file.")
        file.seek(0)
        self.headerstr, dummy, self.version, = struct.unpack('<%isci'%headerstr_len, file.read(headerstr_len + 5))
        assert(dummy == '\\x0A') # debug
        if (self.version == 0x04000002): # morrowind
	    assert(self.headerstr == "NetImmerse File Format, Version 4.0.0.2");
	    self.nblocks, = struct.unpack('<i', file.read(4))
	else:
	    raise NIFError("Unsupported NIF format (%s; 0x%X)."%(self.headerstr, self.version))



    # write to file
    def write(self, file):
        if (self.headerstr.find('\\x0A') >= 0):
            raise NIFError("Cannot write NIF file header (invalid character).")
        file.write(struct.pack('<%iscii'%len(self.headerstr), self.headerstr, '\\x0A', self.version, self.nblocks))



    # dump to screen
    def __str__(self):
        s = 'header:  ' + '%s'%self.headerstr + '\\n'
        s += 'version: ' + '%i'%self.version + '\\n'
        s += 'nblocks: ' + '%i'%self.nblocks + '\\n'
        return s



# 
# NIF file footer
#
class NiFooter:
    # constructor
    def __init__(self):
        # usually 1
        self.dunno1 = 1
        # usually 0
        self.dunno2 = 0



    # read from file
    def read(self, file):
        self.dunno1, self.dunno2 = struct.unpack('<ii', file.read(8))
	#assert((self.dunno1 == 1) and (self.dunno2 == 0)) # ?



    # write to file
    def write(self, file):
        file.write(struct.pack('<ii', self.dunno1, self.dunno2))



    # dump to screen
    def __str__(self):
        s = 'dunno1: ' + '%i'%self.dunno1 + '\\n'
        s += 'dunno2: ' + '%i'%self.dunno2 + '\\n'
        return s

# 
# The NIF base class
# 
class NIF:
    def __init__(self):
        self.header = NiHeader()
        self.blocks = []
        self.footer = NiFooter()



    def read(self, file):
        # read header
        self.header.read(file)
        # read all the blocks
        self.blocks = []
        for block_id in range(self.header.nblocks):
            # each block starts with a string, describing the type of the block,

            # so first we read this string
            block_id_str = mystring('')
	    try:
                block_pos = file.tell()
                block_id_str.read(file)
            except NIFError:
	        # something to investigate! hex dump
    	        try:
                    hexdump(file, block_pos)
                except:
                    pass
                raise NIFError("failed to get next block (does not start with a string)")

            # check the string
	    if (0): pass

END
);

foreach ( $block_ids_sort as $block_id ) {
  if ( ! $block_is_abstract[$block_id] ) {
    echo "            elif (block_id_str.value == \"$block_cname[$block_id]\"): this_block = $block_cname[$block_id]()\n";
  };
};

echo htmlify( <<<END
            else:
	        # something to investigate! hex dump
    	        try:
                    hexdump(file, block_pos)
                except:
                    pass
                btype = ""
                for c in block_id_str.value:
                    if (ord(c) >= 32) and (ord(c) <= 127):
                        btype += c
                    else:
                        btype += "."
                raise NIFError("unknown block type (%s)"%btype)

            # read the data
	    try:
                this_block.read(file)
	    except:
                # we failed to read: dump what we did read, and do a hex dump
                print "%s data dump:"%block_id_str.value
	        try: 
                    print this_block
                except:
                    pass # we do not care about errors during dumping
	        try: 
	            hexdump(file, block_pos)
                except:
                    pass # we do not care about errors during dumping
                raise

             # and store it
            self.blocks.append(this_block)
        # read the footer
        block_pos = file.tell()
	try:
            self.footer.read(file)
        except:
            # we failed to read the footer: hex dump
	    try: 
	        hexdump(file, block_pos)
            except:
                pass # we do not care about errors during dumping
            raise



    # writing all the data
    def write(self, file):
        if (self.header.nblocks != len(self.blocks)):
            raise NIFError("Invalid NIF object: wrong number of blocks specified in header.")
        self.header.write(file)
        for block in self.blocks:
            block.write(file)
        self.footer.write(file)



    # dump all the data
    def __str__(self):
        s = str(self.header) + '\\n'
        count = 0
        for block in self.blocks:
            s += "\\n%i\\n"%count
	    s += str(block);
            count += 1
	s += str(self.footer)
        return s



# 
# a hexdump function
# 
def hexdump(file, pos):
    if (MAX_HEXDUMP <= 0): return
    file.seek(0, 2) # seek end
    num_bytes = file.tell() - pos
    if (num_bytes > MAX_HEXDUMP): num_bytes = MAX_HEXDUMP
    file.seek(pos)
    print "hex dump (at position 0x%08X, %i bytes):"%(pos,num_bytes)
    count = num_bytes
    cur_pos = pos
    while (count > 0):
       if (count >= 16):
           num = 16
       else:
           num = count
       bytes = struct.unpack("<%iB"%num, file.read(num))
       hexstr = '0x%08X: '%cur_pos
       for b in bytes:
           hexstr += '%02X '%b
       for b in bytes:
           if (b >= 32) and (b <= 127):
               hexstr += chr(b)
           else:
               hexstr += '.'
       print hexstr
       count -= num
       cur_pos += num
    return # comment this line for float dump
    num_floats = (num_bytes / 4) - 1
    if (num_floats <= 0): return
    for ofs in range(1): # set range(4) to have a more complete analysis
        print "float dump (at position 0x%08X, %i floats):"%(pos+ofs,num_floats)
        file.seek(pos+ofs)
        bytes = struct.unpack("<%iB"%(num_floats * 4), file.read(num_floats * 4))
        file.seek(pos+ofs)
        floats = struct.unpack('<%if'%num_floats, file.read(num_floats * 4))
        for i in range(num_floats):
            print '%02i: '%i, '(%02X %02X %02X %02X)'%(bytes[i*4], bytes[i*4+1], bytes[i*4+2], bytes[i*4+3]), floats[i]
END
);

echo "</pre>\n";

require("../footer.tpl");

?>
