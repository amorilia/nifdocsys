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
<h1>File Format Browser - C-Style</h1>

<p align="center">
<a href="index.php?mode=list&amp;table=block&amp;view=hier&amp;version=NULL">Hierarchical</a>
|
<a href="index.php?mode=list&amp;table=block&amp;view=alpha&amp;version=NULL">Alphabetical</a>
|
<a href="cstyle.php">C-Style</a>
|
<a href="python.php">Python</a>
|
<a href="xml.php">XML</a>
</p>

ENDHTML;

/**
 *  functions for formatting and htmlifying strings
 */


$indent = 0; // use $indent++ and $indent-- to change the indentation level

// indent code; the returned result always ends with a newline
// result should be embedded in a <pre></pre> block
function txtcode( $txt )
{
  global $indent;

  // create indentation string
  $prefix = "";
  for ($t = 0; $t < $indent; $t++) $prefix .= "  "; // two spaces per level
  // strip trailing whitespace, including newlines
  $txt = rtrim( $txt );
  // replace tabs
  $txt = ereg_replace( "\t", "    ", $txt );
  // indent, and add newline
  $result = $prefix . ereg_replace( "\n", "\n" . $prefix, $txt ) . "\n";
  return $result;
}

function txtvariable($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $condvar, $condval, $condtype, $comment, $ver_from, $ver_to)
{
  global $indent;
  $result = "";

  // version: if statement
  
  if ( ( $ver_from !== null ) or ( $ver_to !== null ) ) {
    $version_str = '';
    if ( $ver_from !== null ) $version_str .= "(version >= 0x" . dechex($ver_from) . ") and ";
    if ( $ver_to !== null ) $version_str .= "(version <= 0x" . dechex($ver_to) . ") and ";
    $version_str = substr($version_str, 0, -5); // remove trailing " and "
    $result .= txtcode( "if $version_str: " );
    $indent++;
  };
  
  // conditional: if statement
  if ( $condvar ) {
    if ( $condval === null )
      $result .= txtcode( "if ($condvar != 0): " );
    else {
      if ( ( $condtype === null ) or ( $condtype === 0 ) )
        $result .= txtcode( "if ($condvar == $condval): " );
      else
        $result .= txtcode( "if ($condvar != $condval): " );
    };
    $indent++;
  }

  // main
  $spaceslen = 16 - 2 * $indent - strlen($some_type);
  if ( $spaceslen < 0 ) $spaceslen = 0;
  if ( $var !== null ) // not a basic type
    $tmptype = "<a href=\"#$some_type\">" . htmlify( $some_type ) . "</a>" . str_repeat(" ", $spaceslen );
  else // basic type
    $tmptype = "<span id=\"$some_type\">" . htmlify( $some_type ) . "</span>" . str_repeat(" ", $spaceslen );    
  $tmpvar  = $var;
  // array
  if ( $sizevar !== null ) {
    $tmpvar .= "[" . $sizevar . "]";
    if ( $sizevarbis !== null )
      $tmpvar .= "[" . $sizevarbis . "]";
  }
  $tmpvar = str_pad( $tmpvar, 36 );
  $tmp = $tmptype . " " . $tmpvar;
  if ( $comment ) {
    // wrap comment
    $spaces = str_repeat( ' ', 56 - 2 * $indent );
    $wrapcomment = wordwrap( $comment, 64 );
    $wrapcomment = ereg_replace( "\n", "\n$spaces", $wrapcomment);
    $tmp .= " - $wrapcomment";
  };
  $result .= txtcode( $tmp );

  // restore indentation
  if ( $condvar ) $indent--;
  if ( ( $ver_from !== null ) or ( $ver_to !== null ) ) $indent--;

  return $result;
}

// convert special characters to html, including single and double
// quotes
function htmlify( $txt )
{
  return htmlentities( $txt, ENT_QUOTES );
}

// file header

echo "<h2>File structure</h2>\n";

echo "<p>Begins with a <a href=\"#header\">header</a> struct, immediately followed by a sequence of <code>num_blocks</code> file blocks. The file ends with a <a href=\"#footer\">footer</a> struct.</p>\n<p>For versions < 10.x.x.x, all file blocks are preceeded by a file block type string.</p>\n<p>For versions >= 10.x.x.x, the first file block is of type <code>blocktype_name[blocktype_index[0]]</code>, the second of <code>blocktype_name[blocktype_index[1]]</code>, etc.</p>\n<p>For versions >= 10.x.x.x but <= 10.1.0.0, all file blocks are preceeded by a zero 32-bit integer.</p>";

echo "<h2>File blocks</h2>\n";

echo "<p>Every file block is preceeded by a file block type string.</p>\n";

display_blocks( 3 );

// basic types

echo "<h2>Basic types</h2>\n";
echo "<pre>\n";

foreach ( $block_ids_sort as $b_id ) {
  if ( $block_category[$b_id] >= 2 ) continue;
  echo txtvariable( null, $block_name[$b_id], null, null, null, null, null, null, $block_description[$b_id], null, null );
};

echo "</pre>\n";

// compound types

echo "<h2>Compound types</h2>\n";

display_blocks( 2 );

/**
 *  main loop: read attribute table, and generate text-style classes
 *  for each block
 */

function display_blocks( $b_category ) {
  global $block_ids_sort;
  global $block_attributes, $block_category, $block_description, $block_cname, $block_parent_cname, $attr_cname, $attr_description, $block_parent_id, $attr_type_cname, $attr_arg_cname, $attr_arr1_cname, $attr_arr2_cname, $attr_cond_cname, $attr_cond_val, $attr_cond_type, $attr_precedence, $attr_ver_from, $attr_ver_to;

  foreach ( $block_ids_sort as $b_id ) {
    if ( $block_category[$b_id] !== $b_category ) continue;
    if ( $block_parent_id[$b_id] !== null )
      echo "<h3 id=\"$block_cname[$b_id]\">" . htmlify( $block_cname[$b_id] ) . " :: <a href=\"#$block_parent_cname[$b_id]\">" . htmlify( $block_parent_cname[$b_id] ) . "</a></h3>";
    else
      echo "<h3 id=\"$block_cname[$b_id]\">" . htmlify( $block_cname[$b_id] ) . "</h3>";
    echo "<p>\n";
    echo ereg_replace( "\n", "<br />\n", htmlify( $block_description[$b_id] . "\n" ) );
    echo "</p>\n";
    if ( $block_attributes[$b_id] ) {
      echo "<pre>\n";
      foreach ( $block_attributes[$b_id] as $a_id )
        if ( $attr_precedence[$a_id] >= 0 )
          echo txtvariable( $attr_cname[$a_id],
                            $attr_type_cname[$a_id],
                            $attr_arg_cname[$a_id],
                            $attr_arr1_cname[$a_id],
                            $attr_arr2_cname[$a_id],
                            $attr_cond_cname[$a_id],
                            $attr_cond_val[$a_id],
                            $attr_cond_type[$a_id],
                            $attr_description[$a_id],
			    $attr_ver_from[$a_id],
			    $attr_ver_to[$a_id]);
      echo "</pre>\n";
    };
  };
};

require("../footer.tpl");

?>

