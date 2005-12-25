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

echo "<h1>File Format Browser - XML</h1>\n";

//echo '<p align="center">';
echo '<p>';
echo '<a href="index.php?mode=list&amp;table=block&amp;view=hier&amp;version=NULL">Hierarchical</a>';
echo ' | <a href="index.php?mode=list&amp;table=block&amp;view=alpha&amp;version=NULL">Alphabetical</a>';
echo ' | <a href="cstyle.php">C-Style</a>';
echo ' | <a href="python.php">Python</a>';
echo ' | <a href="xml.php">XML</a>';
echo "</p>\n";

echo "<pre>\n";

/**
 *  XML header, and basic types (we do these by hand)
 */

echo htmlify( <<<ENDHTML
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE niflotoxml>
<niflotoxml version="0.1.0.0">

	<type name="bool"   type="uint32"  display="bool"   value="0" ver2="67108866">a boolean</type>
	<type name="bool"   type="uint8"   display="bool"   value="0" ver1="67174412">a boolean</type>
	<type name="byte"   type="uint8"   display="dec"    value="0">a 8 bit byte</type>
	<type name="short"  type="uint16"  display="dec"    value="0">a 16 bit unsigned word</type>
	<type name="int"    type="uint32"  display="dec"    value="0">a 32 bit unsigned integer</type>
	<type name="flags"  type="uint16"  display="bin"    value="0">a 16 bit unsigned word containing bit flags</type>
	<type name="link"   type="int32"   display="link"   value="-1">a 32 signed integer, links to a different NiBlock in the same file</type>
	<type name="float"  type="float"   display="float"  value="0.0">a 32 bit floating point number</type>
	<type name="string" type="string"  display="string" value="">an ascii string preceeded by an int specifying the number of characters</type>
	<type name="color3" type="color3f" display="color">an rgb triple consisting of floats</type>
	<type name="color4" type="color4f" display="color">an rgba quadruple ( 4 floats )</type>
	<type name="alphaformat"  type="uint32"  display="dec"    value="3">an unsigned 32-bit integer, describing how transparency is handled in a texture. (0: None, 1: Binary, 2: Smooth, 3: Default)</type>
	<type name="applymode"    type="uint32"  display="dec"    value="2">an unsigned 32-bit integer, describing the apply mode of a texture. (0: Replace, 1: Decal, 2: Modulate (default), 3: Hilight, 4: Hilight2)</type>
	<type name="lightmode"    type="uint32"  display="dec"    value="1">an unsigned 32-bit integer, describing how vertex colors influence lighting. (0: Emissive, 1: Emissive + Ambient + Diffuse (default))</type>
	<type name="mipmapformat" type="uint32"  display="dec"    value="2">an unsigned 32-bit integer, describing how mipmaps are handled in a texture. (0: No, 1: Yes, 2: Default)</type>
	<type name="nodeancestor" type="int32"   display="link"   value="-1">a signed 32-bit integer, used in time controllers to refer to their parent node (called, their target). This should be their first ancestor that is a node.</type>
	<type name="pixellayout"  type="uint32"  display="dec"    value="5">An unsigned 32-bit integer, describing the color depth of a texture. (0: Palettised, 1: 16-bit High Color, 2: 32-bit True Color, 3: Compressed, 4: Bump Map, 5: Default)</type>
	<type name="skeletonroot" type="int32"   display="link"   value="-1">A signed 32-bit integer, which refers to the skeleton root of a NiSkinInstance block; should refer to the first node in the ancestry that has the 'not a skin influence' flag set.</type>
	<type name="parent" type="int32"   display="link"   value="-1">A signed 32-bit integer, which refers a parent.</type>
	<type name="boneref" type="int32"   display="link"   value="-1">A signed 32-bit integer, which refers a bone.</type>
	<type name="vertmode"     type="uint32"  display="dec"    value="2">An unsigned 32-bit integer, which describes how to apply vertex colors. (0: Source Ingore, 1: Source Emissive, 2: Source Ambient Diffuse (default))</type>

ENDHTML
);

echo "\n\n";

/**
 *  functions for formatting and htmlifying strings
 */

function xmlvariable($var, $some_type, $some_type_arg, $sizevar, $sizevarbis, $condvar, $condval, $condtype, $comment, $ver_from, $ver_to)
{
  $result = "\t\t<add name=\"" . $var . "\" type=\"" . $some_type . "\"";
  
  // type argument
  if ( $some_type_arg !== null )
    $result .= " arg=\"$some_type_arg\"";

  // array
  if ( $sizevar !== null ) {
    $result .= " arr1=\"$sizevar\"";
    if ( $sizevarbis !== null )
      $result .= " arr2=\"$sizevarbis\"";
  };

  // conditional: if statement
  if ( $condvar ) {
    $result .= " cond=";
    if ( $condval === null )
      $result .= "\"$condvar != 0\"";
    else {
      if ( ( $condtype === null ) or ( $condtype === 0 ) )
        $result .= "\"$condvar == $condval\"";
      else
        $result .= "\"$condvar != $condval\"";
    };
  };

  if ( $ver_from !== null ) $result .= " ver1=\"$ver_from\"";
  if ( $ver_to !== null ) $result .= " ver2=\"$ver_to\"";

  return htmlify( $result . " />\n" );
}

// convert special characters to html, including single and double
// quotes
function htmlify( $txt )
{
  return htmlentities( $txt, ENT_QUOTES );
}

// compound types

display_blocks( 2 );

// file block types

display_blocks( 3 );

/**
 *  main loop: read attribute table, and generate text-style classes
 *  for each block
 */

function display_blocks( $b_category ) {
  global $block_ids_sort;
  global $block_attributes, $block_category, $block_description, $block_name, $block_parent_name, $block_is_abstract, $block_ver_from, $block_ver_to, $attr_name, $attr_description, $block_parent_id, $attr_type_name, $attr_arg_name, $attr_arr1_name, $attr_arr2_name, $attr_cond_name, $attr_cond_val, $attr_cond_type, $attr_precedence, $attr_ver_from, $attr_ver_to, $attr_arg_id, $attr_arr1_id, $attr_arr2_id, $attr_cond_id;

  foreach ( $block_ids_sort as $b_id ) {
    if ( $block_category[$b_id] !== $b_category ) continue;
    if ( ( $block_name[$b_id] === "color3" ) or ( $block_name[$b_id] === "color4" ) or ( $block_name[$b_id] === "string" ) ) continue; 
    if ( $block_category[$b_id] === 2 )
      echo htmlify( "\t<compound name=\"" . $block_name[$b_id] . "\">\n" );
    elseif ( ( $block_category[$b_id] === 3 ) and ( $block_is_abstract[$b_id] ) )
      echo htmlify( "\t<ancestor name=\"" . $block_name[$b_id] . "\">\n" );
    elseif ( ( $block_category[$b_id] === 3 ) and ( ! $block_is_abstract[$b_id] ) )
      echo htmlify( "\t<niblock name=\"" .  $block_name[$b_id] . "\">\n" );
    if ( $block_parent_id[$b_id] !== null )
      echo htmlify( "\t\t<inherit name=\"" . $block_parent_name[$b_id] . "\"/>\n" );
    //echo htmlify( "\t\t<description=\"" . ereg_replace( "\n", " ", htmlify( $block_description[$b_id] ) ) . "\">\n" );
    if ( $block_attributes[$b_id] ) {
      foreach ( $block_attributes[$b_id] as $a_id ) {
	if ( ! check_version( $version, $attr_ver_from[$a_id], $attr_ver_to[$a_id] ) ) continue;
        if ( $attr_precedence[$a_id] >= 0 ) {
          if ( $attr_arg_id[$a_id] !== null )
            if ( $attr_precedence[$attr_arg_id[$a_id]] === -1 )
              $attr_arg_name[$a_id] = "(ARG)";
          if ( $attr_arr1_id[$a_id] !== null )
            if ( $attr_precedence[$attr_arr1_id[$a_id]] === -1 )
              $attr_arr1_name[$a_id] = "(ARG)";
          if ( $attr_arr2_id[$a_id] !== null )
            if ( $attr_precedence[$attr_arr2_id[$a_id]] === -1 )
              $attr_arr2_name[$a_id] = "(ARG)";
          if ( $attr_cond_id[$a_id] !== null )
            if ( $attr_precedence[$attr_cond_id[$a_id]] === -1 )
              $attr_cond_name[$a_id] = "(ARG)";
          echo xmlvariable( $attr_name[$a_id],
                            $attr_type_name[$a_id],
                            $attr_arg_name[$a_id],
                            $attr_arr1_name[$a_id],
                            $attr_arr2_name[$a_id],
                            $attr_cond_name[$a_id],
                            $attr_cond_val[$a_id],
                            $attr_cond_type[$a_id],
                            $attr_description[$a_id],
			    $attr_ver_from[$a_id],
			    $attr_ver_to[$a_id] );
        };
      };
    };
    if ( $block_category[$b_id] === 2 )
      echo htmlify( "\t</compound>\n" );
    elseif ( ( $block_category[$b_id] === 3 ) and ( $block_is_abstract[$b_id] ) )
      echo htmlify( "\t</ancestor>\n" );
    elseif ( ( $block_category[$b_id] === 3 ) and ( ! $block_is_abstract[$b_id] ) )
      echo htmlify( "\t</niblock>\n" );
  };
};

echo htmlify( "\n</niflotoxml>\n" );

require("../footer.tpl");

?>

