<?php

/******************************************************************************
 * File Format Browser v0.5
 *
 *   a collection of php scripts to edit and view a file format
 *   description over a MySQL database.
 *
 *-----------------------------------------------------------------------------
 ****** BEGIN BSD LICENSE BLOCK *****
 *
 * Copyright (c) 2005, NIF File Format Library and Tools
 * All rights reserved.
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
 ****** END BSD LICENCE BLOCK *****
 *-----------------------------------------------------------------------------

/******************************************************************************
 * History:
 *
 * 0.0 (Amorilia, Sep 14, 2005): first try, editing the block table
 * 0.1 (Amorilia, Sep 18, 2005): added support for attributes
 * 0.2 (Amorilia, Sep 20, 2005):
 *  - introduced four type categories
 *  - added support for extra type arguments (array counters, conditional values, type arguments)
 * 0.3 (Amorilia, Oct 1, 2005):
 *  - removed the result page
 *  - form data is sent by POST method
 * 0.4 (Amorilia, Oct 6, 2005):
 *  - improved interface
 * 0.5 (Amorilia, Oct 10, 2005):
 *  - separated mysql part, code runs now much faster
 *  - authentication (using phpbb cookie)
 *  - security enhancements
 * 0.6 (Amorilia, Oct 11, 2005):
 *  - added support for long block descriptions with line breaks
 * 0.7 (Amorilia, Oct 15, 2005):
 *  - added column to check for inequality in conditional attributes
 * 0.8 (Amorilia, Nov 3, 2005):
 *  - multiple version support
 */

define('IN_PHPBB', true);

$phpbb_root_path = '../forum/';
$docsys_root_path = './';
include($phpbb_root_path . 'extension.inc');
include($phpbb_root_path . 'common.'.$phpEx);
include($docsys_root_path . 'common.'.$phpEx);

//
// Start session management
//
$userdata = session_pagestart($user_ip, PAGE_SEARCH);
init_userprefs($userdata);
//
// End session management
//

// Parse and validate arguments.

include($docsys_root_path . 'readarg.' . $phpEx);

// Do the requested action.

include($docsys_root_path . 'action.' . $phpEx);

// Read and sort the database.

include($docsys_root_path . 'readdb.' . $phpEx);

/****************
 * Main program *
 ****************
 *
 * The $mode variable controls the page subject: "list", "edit", or "action".
 * The $table varialbe says on which table the $mode applies: "block" or "attr".
 * The $action variable controls any actions (mysql queries) to be performed prior to display: "New", "Delete", "Up", or "Modify".
 * In "list" $mode, the $view variable controls the page layout: "alpha" or "hier".
 *
 */

// Load the HTML QuickForm class

include('HTML/QuickForm.php');

// HTML header

require("../header.tpl");

echo "<h1>File Format Browser (";
if ( $version === null ) {
  echo " All Versions ";
} else {
  echo " " . $version_description[$version] . " : " . $version_games[$version] . " ";
};
echo ")</h1>\n";

/*
 * Are we in listing mode?
 **************************/

if ( $mode === "list" and $table === "block" ) {
  
  // HTML main menu
  
  echo '<p align="center">';
  echo '<a href="index.php?mode=list&amp;table=block&amp;view=hier&amp;version=NULL">Hierarchical</a>';
  echo ' | <a href="index.php?mode=list&amp;table=block&amp;view=alpha&amp;version=NULL">Alphabetical</a>';
  echo ' | <a href="cstyle.php">C-Style</a>';
  echo ' | <a href="python.php">Python</a><br />';
  echo '<a href="index.php?mode=list&amp;table=block&amp;view=' . $view . '&amp;version=NULL">All Versions</a>';
  foreach ( $version_description as $ver_num => $ver_desc ) {
    echo ' | <a href="index.php?mode=list&amp;table=block&amp;view=' . $view . '&amp;version=' . $ver_num . '">' . $ver_desc . '</a>';
  };
  echo "</p>\n";
 
  // Display basic types
  
  if ( $docsys_admin ) {
    echo '<h2>Basic types (<a href="index.php?mode=edit&amp;table=block&amp;block_category=0&amp;version=' . $version . '">New Count</a>, <a href="index.php?mode=edit&amp;table=block&amp;block_category=1&amp;version=' . $version . '">New Non-Count</a>)</h2>' . "\n";
    
    if ( $view === "alpha" ) {
      echo "<table>\n";
      echo "<tr>\n";
      echo "<th>Name</th>\n";
      echo "<th>Count</th>\n";
      echo "<th>Description</th>\n";
      if ( $docsys_admin ) echo '<th colspan="2">Admin</th>' . "\n";
      echo "</tr>\n";
      
      $bgcol = 'reg0';
      foreach ( $block_ids as $b_id ) {
	if ( $block_category[$b_id] >= 2 ) continue;
	if ( ! check_version( $version, $block_ver_from[$b_id], $block_ver_to[$b_id] ) ) continue;
	echo '<tr class="' . $bgcol . '">' . "\n";
	echo "<td><b>" . htmlify( $block_name[$b_id] ) . "</b></td>\n";
	if ( $block_category[$b_id] === 0 )
	  echo "<td>yes</td>\n";
	else
	  echo "<td>no</td>\n";
	echo "<td>" . nl2br( htmlify( $block_description[$b_id] ) ) . "</td>\n";
	if ( $docsys_admin ) {
	  echo '<td><a href="index.php?mode=edit&amp;table=block&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Edit</a></td>' . "\n";
	  echo '<td><a href="index.php?mode=action&amp;table=block&amp;action=Delete&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Delete</a></td>' . "\n";
	};
	echo "</tr>\n";
	if ($bgcol === 'reg0') {
	  $bgcol = 'reg1';
	} else {
	  $bgcol = 'reg0';
	};
      };
      echo "</table>\n";
    } else if ( $view === "hier" ) {
      echo "<ul>\n<li>\nCount:\n";
      display_children( 0, null );
      echo "</li>\n<li>\nNon-Count:\n";
      display_children( 1, null );
      echo "</li>\n</ul>\n";
    };
  };

  // Display compound types
  
  if ( $docsys_admin ) {
    echo '<h2>Compound types (<a href="index.php?mode=edit&amp;table=block&amp;block_category=2&amp;version=' . $version . '">New</a>)</h2>' . "\n";
    
    if ( $view === "alpha" ) {
      
      // Now build type table.
      
      echo "<table>\n";
      echo "<tr>\n";
      echo "<th>Name</th>\n";
      echo "<th>Description</th>\n";
      if ( $docsys_admin ) echo '<th colspan="2">Admin</th>' . "\n";
      echo "</tr>\n";
      $bgcol = 'reg0';
      foreach ( $block_ids as $b_id ) {
	if ( $block_category[$b_id] !== 2 ) continue;
	if ( ! check_version( $version, $block_ver_from[$b_id], $block_ver_to[$b_id] ) ) continue;
	echo '<tr class="' . $bgcol . '">' . "\n";
	echo '<td><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $b_id . '&amp;version=' . $version . '"><b>' . htmlify( $block_name[$b_id] ) . "</b></a></td>\n";
	echo "<td>" . nl2br( htmlify( $block_description[$b_id] ) ) . "</td>\n";
	if ( $docsys_admin ) {
	  echo '<td><a href="index.php?mode=edit&amp;table=block&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Edit</a></td>' . "\n";
	  echo '<td><a href="index.php?mode=action&amp;table=block&amp;action=Delete&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Delete</a></td>' . "\n";
	};
	echo "</tr>\n";
	if ($bgcol === 'reg0') {
	  $bgcol = 'reg1';
	} else {
	  $bgcol = 'reg0';
	};
      };
      echo "</table>\n";
    } else if ( $view === "hier" ) {
      // Parse the hierarchy.
      display_children( 2, null );
    };
  };

  // Display block types
  
  if ( $docsys_admin )
    echo '<h2>File block types (<a href="index.php?mode=edit&amp;table=block&amp;block_category=3&amp;version=' . $version . '">New</a>)</h2>' . "\n";
  else
    echo "<h2>File block types</h2>\n";

  if ( $view === "alpha" ) {

    // Now build type table.

    echo "<table>\n";
    echo "<tr>\n";
    echo "<th>Name</th>\n";
    echo "<th>Description</th>\n";
    echo "<th>Parent</th>\n";
    if ( $docsys_admin ) echo '<th colspan="2">Admin</th>' . "\n";
    echo "</tr>\n";

    $bgcol = 'reg0';
    foreach ( $block_ids as $b_id ) {
      if ( $block_category[$b_id] !== 3 ) continue;
      if ( ! check_version( $version, $block_ver_from[$b_id], $block_ver_to[$b_id] ) ) continue;
      echo '<tr class="' . $bgcol . '">' . "\n";
      echo '<td><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $b_id . '&amp;version=' . $version . '"><b>' . htmlify( $block_name[$b_id] ) . "</b></a></td>\n";
      echo "<td>" . nl2br( htmlify( $block_description[$b_id] ) ) . "</td>\n";
      if ( $block_parent_id[$b_id] !== null )
	echo '<td><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $block_parent_id[$b_id] . '&amp;version=' . $version . '"><b>' . htmlify( $block_parent_name[$b_id] ) . "</b></a></td>\n";
      else
	echo "<td></td>\n"; 
      if ( $docsys_admin ) {
	echo '<td><a href="index.php?mode=edit&amp;table=block&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Edit</a></td>' . "\n";
	echo '<td><a href="index.php?mode=action&amp;table=block&amp;action=Delete&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Delete</a></td>' . "\n";
      };
      echo "</tr>\n";
      if ($bgcol === 'reg0') {
	$bgcol = 'reg1';
      } else {
	$bgcol = 'reg0';
      };
    };
    echo "</table>\n";
  } else if ( $view === "hier" ) {
    // Parse the hierarchy.
    display_children( 3, null );
  };
};

if ( $mode === "list" and $table === "attr" ) {
  // HTML main menu
  
  echo '<p align="center">';
  echo '<a href="index.php?mode=list&amp;table=block&amp;view=hier&amp;version=' . $ver_num . '">Hierarchical</a>';
  echo ' | <a href="index.php?mode=list&amp;table=block&amp;view=alpha&amp;version=' . $ver_num . '">Alphabetical</a>';
  echo ' | <a href="cstyle.php">C-Style</a> | <a href="python.php">Python</a><br />'; 
  echo '<a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $req_block_id . '&amp;version=NULL">All Versions</a>';
  foreach ( $version_description as $ver_num => $ver_desc ) {
    echo ' | <a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $req_block_id . '&amp;version=' . $ver_num . '">' . $ver_desc . '</a>';
  };
  echo "</p>\n";
 
  // Show block header.
  
  if ( $block_parent_id[$req_block_id] )
    echo "<h2>" . htmlify( $block_name[$req_block_id] ) . ' ::  <a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $block_parent_id[$req_block_id] . '&amp;version=' . $version . '">' . htmlify( $block_parent_name[$req_block_id]). "</a></h2>\n";
  else
    echo "<h2>" . htmlify( $block_name[$req_block_id] ) . ' ::  <a href="index.php?mode=list&amp;table=block&amp;view=hier&amp;version=' . $version . '">(None)</a></h2>' . "\n";
  echo "<p>" . nl2br( htmlify( $block_description[$req_block_id] ) ) . "</p>\n";

  // Block derived classes.

  if ( $block_children[$req_block_id] ) {
    echo "<h3>Parent of...</h3>\n";
    echo "<ul>\n";
    foreach ( $block_children[$req_block_id] as $b_id ) 
      echo '<li><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $b_id . '&amp;version=' . $version . '">' . htmlify( $block_name[$b_id] ). "</a></li>\n";
    echo "</ul>\n";
  };

  // Attribute of...

  if ( $block_category[$req_block_id] !== 3 ) {
    $is_attribute_of = false;
    foreach ( $block_ids as $b_id ) {
      foreach ( $block_attributes[$b_id] as $a_id ) {
	if ( $attr_type_id[$a_id] === $req_block_id ) {
	  if ( $is_attribute_of === false ) {
	    $is_attribute_of = true;
	    echo "<h3>Attribute of...</h3>\n";
	    echo "<ul>\n";
	  };
	  echo '<li><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $b_id . '&amp;version=' . $version . '">' . htmlify( $block_name[$b_id] ). "</a></li>\n";
	  break;
	};
      };
    };
    if ( $is_attribute_of ) echo "</ul>\n";
  };

  
  // Block attributes.
  if ( $block_category[$req_block_id] >= 2 ) {
    
    if ( $docsys_admin ) {
      echo '<h3>Attributes (<a href="index.php?mode=edit&amp;table=attr&amp;block_id=' . $req_block_id . '&amp;version=' . $version . '">New Regular</a>';
      // Present option to create external attribute, if we have none.
      if ( $block_category[$req_block_id] === 2 ) // only compound types can have have external attributes
	if ( ( ! $block_attributes[$req_block_id] ) or $attr_precedence[$block_attributes[$req_block_id][0]] !== -1 ) // must have no external attributes yet
	  echo ', <a href="index.php?mode=edit&amp;table=attr&amp;block_id=' . $req_block_id . '&amp;attr_precedence=-1&amp;version=' . $version . '">New External</a>';
      echo ") </h3>\n";
    } else
      echo "<h3>Attributes</h3>\n";
    
    // Build attribute table.
    echo "<table>\n";
    echo "<tr>\n";
    echo "<th>Name</th>\n";
    echo "<th>Type</th>\n";
    echo "<th>Arg</th>\n";
    echo "<th>Arr1</th>\n";
    echo "<th>Arr2</th>\n";
    echo "<th>Cond</th>\n";
    echo "<th>Description</th>\n";
    if ( $version === null ) echo "<th>From</th><th>To</th>\n";
    if ( $docsys_admin ) echo '<th colspan="3">Admin</th>' . "\n";
    echo "</tr>\n";
    
    display_attributes( $req_block_id, true, 0 );
    
    echo "</table>\n";
  };
};

/*
 * Are we in edit mode?
 ***********************/

if ( $mode === "edit" and $table === "block" ) {
  // If block_id was passed, we are editing; if not, we create a new type.

  if ( $req_block_id ) {
    $b_name = $block_name[$req_block_id];
    $b_description = $block_description[$req_block_id];
    $b_parent_id = $block_parent_id[$req_block_id];
    $b_ver_from = $block_ver_from[$req_block_id];
    $b_ver_to = $block_ver_to[$req_block_id];
    $b_category = $block_category[$req_block_id];
    echo '<h2>Edit ' . $b_name . '</h2>' . "\n";
  } else {
    if ( $req_block_category === 0 ) echo "<h2>Create basic count type</h2>";
    else if ( $req_block_category === 1 ) echo "<h2>Create basic non-count type</h2>";
    else if ( $req_block_category === 2 ) echo "<h2>Create compound type</h2>";
    else if ( $req_block_category === 3 ) echo "<h2>Create file block type</h2>";
    $b_name = '';
    $b_description = '';
    $b_parent_id = null;
    $b_ver_from = $version;
    $b_ver_to = null;
    $b_category = $req_block_category; // this must be passed!
  };

  // Construct map: version => description
  $version_table_from = array();
  if ( $b_ver_from !== null )
    $version_table_from[ $b_ver_from ] = '-Oops-';
  else
    $version_table_from['NULL'] = "-Oops-";
  
  $version_table_to = array();
  if ( $b_ver_to !== null )
    $version_table_to[ $b_ver_to ] = '-Oops-';
  else
    $version_table_to[ 'NULL' ] = "-Oops-";
  
  $version_table_from['NULL'] = "(Any)";  
  foreach ( $version_description as $ver_num => $ver_desc ) {
    $version_table_from[$ver_num] = $ver_desc;
    $version_table_to[$ver_num] = $ver_desc;
  };
  $version_table_to['NULL'] = "(Any)";

  // Construct map: block_id => name. Make sure that block_parent_id
  // comes first (the <select> html attribute has no default
  // value...): first assign a value
  // to $parent_id_table[$b_parent_id].

  $parent_id_table = array();
  if ( $b_category === 3 ) { // only parenting for file block types
    if ( $b_parent_id !== null )
      $parent_id_table[ $b_parent_id ] = '-Oops-';
    $parent_id_table['NULL'] = "(No Parent)";
    foreach ( $block_ids as $b_id )
      if ( ( $block_category[$b_id] === 3 ) and ( $b_id !== $req_block_id ) )
	$parent_id_table[$b_id] = $block_name[$b_id];
  };
  
  // Now we can do the edit type form.

  $form = new HTML_QuickForm('edit', 'post');
  $form->addElement('hidden', 'mode', 'action'); // bug? ... why does this not work? workaround in code: check for action parameter
  $form->addElement('hidden', 'table', 'block');
  $form->addElement('hidden', 'block_category', $b_category);
  $form->addElement('text', 'block_name', 'Name:', array('size' => 50, 'maxlength' => 64 ));
  $form->addElement('textarea', 'block_description', 'Description:', array('rows' => 3, 'cols' => 50 ));
  if ( $b_category === 3 )
    $form->addElement('select', 'block_parent_id', 'Parent:', $parent_id_table );
  else
    $form->addElement('hidden', 'block_parent_id', 'NULL');
  $form->addElement('select', 'block_ver_from', 'Appears first in:', $version_table_from );
  $form->addElement('select', 'block_ver_to', 'Appears last in:', $version_table_to );
  $form->addElement('hidden', 'version', $version);
  if ( $req_block_id ) {
    $form->addElement('hidden', 'block_id', $req_block_id);
    $form->addElement('submit', 'action', 'Modify');
  } else 
    $form->addElement('submit', 'action', 'New');
  $form->applyFilter('block_name', 'trim');
  $form->applyFilter('block_description', 'trim');
  $form->addRule('block_name', 'Please enter a name', 'required', null, 'client');
  $form->addRule('block_name', 'Name too long', 'maxlength', 64, 'client');
  //$form->addRule('block_name', 'Invalid characters in name', 'regex', REGEX_NAME, 'client'); // bug in html_quickform
  $form->addRule('block_description', 'Please enter a description', 'required', null, 'client');
  $form->addRule('block_description', 'Description too long (max 4096 characters)', 'maxlength', 4096, 'client');
  //$form->addRule('block_description', 'Invalid characters in description', 'regex', REGEX_DESC, 'client'); // bug in html_quickform
  $form->setDefaults( array( 'block_name' => $b_name,
			     'block_description' => $b_description,
			     'block_parent_id' => $b_parent_id,
			     'block_ver_from' => $b_ver_from,
			     'block_ver_to' => $b_ver_to ) );
  $form->display();
};

if ( $mode === "edit" and $table === "attr" ) {
  // Get to know about the block.
  
  if ( $req_block_id === null ) oops( $errcode_val, $req_block_id );
  $req_block_name = $block_name[$req_block_id];

  // If attr_id was passed, we are editing; if not, we create a new
  // attribute.

  if ( $req_attr_id ) {
    echo '<h2>Edit ' . $req_block_name . "." . $attr_name[$req_attr_id] . '</h2>' . "\n";
    $a_name = $attr_name[$req_attr_id];
    $a_description = $attr_description[$req_attr_id];
    $a_parent_id = $attr_parent_id[$req_attr_id];
    $a_type_id = $attr_type_id[$req_attr_id];
    $a_precedence = $attr_precedence[$req_attr_id];
    $a_arg_id = $attr_arg_id[$req_attr_id];
    $a_arr1_id = $attr_arr1_id[$req_attr_id];
    $a_arr2_id = $attr_arr2_id[$req_attr_id];
    $a_arr1_num = $attr_arr1_num[$req_attr_id];
    $a_arr2_num = $attr_arr2_num[$req_attr_id];
    $a_cond_id = $attr_cond_id[$req_attr_id];
    $a_cond_val = $attr_cond_val[$req_attr_id];
    $a_cond_type = $attr_cond_type[$req_attr_id];
    $a_ver_from = $attr_ver_from[$req_attr_id];
    $a_ver_to = $attr_ver_to[$req_attr_id];
  } else {
    echo "<h2>Create " . $req_block_name . " attribute</h2>";
    $a_name = '';
    $a_description = '';
    $a_parent_id = $req_block_id;
    $a_type_id = null;
    // to calculate the precedence we need another query
    if ( ! $req_attr_precedence ) {
      $a_precedence = 0;
      foreach ( $block_attributes[$req_block_id] as $a_id )
	if ( $attr_precedence[$a_id] > $a_precedence) $a_precedence = $attr_precedence[$a_id];
      $a_precedence = $a_precedence + 1; // if there are no attributes, $a_precedence is 1.
    } else {// for external attributes the precedence (-1) is passed as an argument
      if ( $req_attr_precedence !== -1 ) oops( $errcode_val, $req_attr_precedence );
      $a_precedence = $req_attr_precedence;
    };
    $a_arg_id = null;
    $a_arr1_id = null;
    $a_arr2_id = null;
    $a_arr1_num = null;
    $a_arr2_num = null;
    $a_cond_id = null;
    $a_cond_val = null;
    $a_cond_type = null;
    $a_ver_from = $version;
    $a_ver_to = null;
  };

  // Construct map: version => description
  $version_table_from = array();
  if ( $b_ver_from !== null )
    $version_table_from[ $b_ver_from ] = '-Oops-';
  else
    $version_table_from['NULL'] = "-Oops-";
  
  $version_table_to = array();
  if ( $b_ver_to !== null )
    $version_table_to[ $b_ver_to ] = '-Oops-';
  else
    $version_table_to[ 'NULL' ] = "-Oops-";
  
  $version_table_from['NULL'] = "(Any)";  
  foreach ( $version_description as $ver_num => $ver_desc ) {
    $version_table_from[$ver_num] = $ver_desc;
    $version_table_to[$ver_num] = $ver_desc;
  };
  $version_table_to['NULL'] = "(Any)";

  // Construct map: block_id => name. Make sure that attr_type_id
  // comes first (the <select> html attribute has no default
  // value...): first assign a value
  // to $type_table[$a_type_id].
  
  $type_table = array();
  if ( $a_type_id !== null ) $type_table[ $a_type_id ] = '-Oops-';
  foreach ( $block_ids as $b_id ) {
    if ( ( $a_precedence === -1 ) and ( $block_category[$b_id] > 0 ) ) continue; // external attribute must be a count
    if ( $b_id === $req_block_id ) continue; // no recursion
    if ( $a_type_id === null ) $a_type_id = $b_id; // get default value
    $type_table[$b_id] = $block_name[$b_id];
  };
  
  // Construct map: attr_id => name, for each type in $type_table.
  
  $type_arg_table = array();
  if ( $a_arg_id !== null ) $type_arg_table[ $a_type_id ][ $a_arg_id ] = '-Oops-';
  // iterate over all selectable types
  foreach ( $type_table as $key => $value ) {
    if ( ! $block_attributes[$key] ) { // does the type have attributes?
      $type_arg_table[$key]['NULL'] = '(None)';
      continue;
    };
    if ( $attr_precedence[$block_attributes[$key][0]] !== -1 ) { // does it have an external attribute?
      $type_arg_table[$key]['NULL'] = '(None)';
      continue;
    };
    foreach ( $block_attributes[$req_block_id] as $a_id ) {
      if ( $attr_precedence[$a_id] >= $a_precedence ) continue; // argument must come before
      if ( $attr_type_id[$block_attributes[$key][0]] !== $attr_type_id[$a_id] ) continue; // does it have the same type?
      if ( $a_arg_id === null ) $a_arg_id = $a_id; // default value
      $type_arg_table[$key][$a_id] = $attr_name[$a_id];
    };
    if ( ! $type_arg_table[$key] ) // no arguments found...
      unset( $type_table[$key] );
  };
  
  // Construct map: attr_id => name, for all count attributes.

  if ( $a_arr1_id !== null )
    $attr_arr1_table[ $a_arr1_id ] = "-Oops-";
  $attr_arr1_table['NULL'] = "(None)";
  if ( $a_arr2_id !== null )
    $attr_arr2_table[ $a_arr2_id ] = "-Oops-";
   $attr_arr2_table['NULL'] = "(None)";
  if ( $a_cond_id !== null )
    $attr_cond_table[ $a_cond_id ] = "-Oops-";
  $attr_cond_table['NULL'] = "(None)";
  // parent attributes (we only go down two levels; TODO go down arbitrary level)
  if ( $block_parent_id[$req_block_id] !== null ) {
    if ( $block_parent_id[$block_parent_id[$req_block_id]] !== null ) {
      foreach ( $block_attributes[$block_parent_id[$block_parent_id[$req_block_id]]] as $a_id ) {
	if ( $block_category[$attr_type_id[$a_id]] !== 0 ) continue; // argument must be a count
	$attr_cond_table[$a_id] = $attr_name[$a_id];
	$attr_arr1_table[$a_id] = $attr_name[$a_id];
	$attr_arr2_table[$a_id] = $attr_name[$a_id];
      };
    };
    foreach ( $block_attributes[$block_parent_id[$req_block_id]] as $a_id ) {
      if ( $block_category[$attr_type_id[$a_id]] !== 0 ) continue; // argument must be a count
      $attr_cond_table[$a_id] = $attr_name[$a_id];
      $attr_arr1_table[$a_id] = $attr_name[$a_id];
      $attr_arr2_table[$a_id] = $attr_name[$a_id];
    };
  };
  // the block attributes itself
  foreach ( $block_attributes[$req_block_id] as $a_id ) {
    if ( $attr_precedence[$a_id] >= $a_precedence ) continue; // argument must come before
    if ( $block_category[$attr_type_id[$a_id]] !== 0 ) continue; // argument must be a count
    $attr_cond_table[$a_id] = $attr_name[$a_id];
    $attr_arr1_table[$a_id] = $attr_name[$a_id];
    $attr_arr2_table[$a_id] = $attr_name[$a_id];
  };

  // Now do the edit attribute form.

  $form = new HTML_QuickForm('edit', 'post');
  $form->addElement('hidden', 'mode', 'action'); // BUG!!! aaargh... why does this not work? workaround in code: check for action parameter
  $form->addElement('hidden', 'table', 'attr');
  $form->addElement('hidden', 'attr_parent_id', $req_block_id);
  $form->addElement('hidden', 'attr_precedence', $a_precedence);
  $form->addElement('text', 'attr_name', 'Name:', array('size' => 50, 'maxlength' => 64 ));
  $sel =& $form->addElement('hierselect', 'attr_type_id', 'Type:');
  $sel->setOptions(array($type_table, $type_arg_table));
  if ( $a_precedence === -1 ) {
    $form->addElement('hidden', 'attr_arr1_id', 'NULL' );
    $form->addElement('hidden', 'attr_arr2_id', 'NULL' );
    $form->addElement('hidden', 'attr_arr1_num', 'NULL' );
    $form->addElement('hidden', 'attr_arr2_num', 'NULL' );
    $form->addElement('hidden', 'attr_cond_id', 'NULL'  );
    $form->addElement('hidden', 'attr_cond_val', 'NULL' );
    $form->addElement('hidden', 'attr_cond_type', 'NULL' );
  } else {
    $form->addElement('select', 'attr_arr1_id', 'Array Index:', $attr_arr1_table );
    $form->addElement('text', 'attr_arr1_num', '' );
    $form->addElement('select', 'attr_arr2_id', '2nd Array Index:', $attr_arr2_table );
    $form->addElement('text', 'attr_arr2_num', '' );
    $form->addElement('select', 'attr_cond_id', 'Conditional On:', $attr_cond_table );
    $form->addElement('text', 'attr_cond_val', 'Conditional Value:');
    $form->addElement('advcheckbox', 'attr_cond_type', 'Negate:', null, null, array( 0, 1 ) );
  };
  $form->addElement('textarea', 'attr_description', 'Description:', array('rows' => 3, 'cols' => 50 ));
  $form->addElement('select', 'attr_ver_from', 'Appears first in:', $version_table_from );
  $form->addElement('select', 'attr_ver_to', 'Appears last in:', $version_table_to );
  $form->addElement('hidden', 'version', $version);
  if ( $req_attr_id ) {
    $form->addElement('hidden', 'attr_id', $req_attr_id);
    $form->addElement('submit', 'action', 'Modify');
  } else 
    $form->addElement('submit', 'action', 'New');
  $form->applyFilter('attr_name', 'trim');
  $form->applyFilter('attr_description', 'trim');
  $form->addRule('attr_name', 'Please enter a name', 'required', null, 'client');
  $form->addRule('attr_name', 'Name too long', 'maxlength', 64, 'client');
  //$form->addRule('attr_name', 'Invalid characters in name', 'regex', REGEX_NAME, 'client'); // bug in html_quickform
  $form->addRule('attr_description', 'Please enter a description', 'required', null, 'client');
  $form->addRule('attr_description', 'Description too long (max 2048 characters)', 'maxlength', 2048, 'client');
  //$form->addRule('attr_description', 'Invalid characters in description', 'regex', REGEX_DESC, 'client'); // bug in html_quickform
  $form->addRule('attr_cond_val', 'Please enter a conditional value', 'numerical', null, 'client');
  $form->addRule('attr_arr1_num', 'Leave empty, or enter a numerical value for the 1st array index', 'numerical', null, 'client');
  $form->addRule('attr_arr2_num', 'Leave empty, or enter a numerical value for the 2nd array index', 'numerical', null, 'client');
  $form->setDefaults( array( 'attr_name' => $a_name,
			     'attr_description' => $a_description,
			     'attr_cond_val' => $a_cond_val,
			     'attr_arr1_num' => $a_arr1_num,
			     'attr_arr2_num' => $a_arr2_num, 
                             'attr_cond_type' => $a_cond_type,
			     'attr_ver_from' => $a_ver_from,
			     'attr_ver_to' => $a_ver_to ) );
   $form->display();
};

echo <<<END
</body>
</html>
END;

/*
 * Various functions.
 */

// Convert special characters to html, including single and double
// quotes.

function htmlify( $txt ) {
  return htmlentities( $txt, ENT_QUOTES );
}

// Display hierarchy of compound types, as an unordered list.

function display_children( $b_category, $b_parent_id ) {
  global $block_ids, $block_name, $block_category, $block_description, $block_parent_id, $block_children, $block_root, $block_ver_from, $block_ver_to;
  global $docsys_admin, $version;

  $list = array();
  if ( $b_parent_id === null ) {
    foreach ( $block_root[$b_category] as $b_id )
      if ( check_version( $version, $block_ver_from[$b_id], $block_ver_to[$b_id] ) ) $list[] = $b_id;
  } else {
    foreach ( $block_children[$b_parent_id] as $b_id )
      if ( check_version( $version, $block_ver_from[$b_id], $block_ver_to[$b_id] ) ) $list[] = $b_id;
  };

  if ( $list ) {
    echo "<ul>\n";
    foreach ( $list as $b_id ) {
      echo "<li>\n";
      if ( $b_category >= 2 )
	echo '<a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $b_id . '&amp;version=' . $version . '"><b>' . htmlify( $block_name[$b_id] ) . "</b></a>";
      else
	echo '<b>' . htmlify( $block_name[$b_id] ) . "</b>";
      if ( $docsys_admin )
	echo "\n | " . '<a href="index.php?mode=edit&amp;table=block&amp;block_id=' .$b_id . '&amp;version=' . $version . '">Edit</a>';
      echo "\n | " . nl2br( htmlify( $block_description[$b_id] ) ); 
      if ( $docsys_admin )
	echo "\n | " . '<a href="index.php?mode=action&amp;table=block&amp;action=Delete&amp;block_id=' . $b_id . '&amp;version=' . $version . '">Delete</a>';
      display_children( $b_category, $b_id );
      echo "</li>\n";
    };
    echo "</ul>\n";
  };
};

// Display parent's attributes, as part of a table.

function display_attributes( $b_id, $active, $count ) {
  global $block_attributes, $block_category, $attr_name, $attr_description, $block_parent_id, $attr_type_id, $attr_type_name, $attr_arg_id, $attr_arg_name, $attr_arr1_id, $attr_arr1_name, $attr_arr1_num, $attr_arr2_id, $attr_arr2_name, $attr_arr2_num, $attr_cond_id, $attr_cond_name, $attr_cond_val, $attr_precedence, $attr_cond_type, $attr_ver_from, $attr_ver_to, $version_description;
  global $req_block_id;
  global $docsys_admin, $version;
  
  // Show parent attributes.
  
  if ( $block_parent_id[$b_id] !== null )
    $count += display_attributes( $block_parent_id[$b_id], false, $count );
  
  // Show attributes.
  $is1st = 1;
  foreach ( $block_attributes[$b_id] as $a_id ) {
    if ( ! check_version( $version, $attr_ver_from[$a_id], $attr_ver_to[$a_id] ) ) continue;
    if ( $active ) {
      if ( ($count & 1) === 0 )
	$bgcol = 'reg0';
      else
	$bgcol = 'reg1';
    } else {
      if ( ($count & 1) === 0 )
	$bgcol = 'inact0';
      else
	$bgcol = 'inact1';
    };
    if ( $attr_precedence[$a_id] === -1 ) $bgcol = 'extrnl'; # light up the external attribute in greenish

    echo '<tr class="' . $bgcol . '">' . "\n";
    echo "<td><i>" . htmlify( $attr_name[$a_id] ) . "</i></td>\n";
    //if ( $block_category[ $attr_type_id[$a_id] ] >= 2 )
    echo '<td><a href="index.php?mode=list&amp;table=attr&amp;block_id=' . $attr_type_id[$a_id] . '&amp;version=' . $version . '"><b>' . htmlify( $attr_type_name[$a_id] ) . "</b></a></td>\n";
    //else
    //echo '<td><b>' . htmlify( $attr_type_name[$a_id] ) . "</b></td>\n";
    if ( $attr_arg_id[$a_id] !== null )
      echo "<td><i>" . htmlify( $attr_arg_name[$a_id] ) . "</i></td>\n";
    else
      echo '<td></td>' . "\n";
    if ( $attr_arr1_id[$a_id] !== null )
      echo "<td><i>" . htmlify( $attr_arr1_name[$a_id] ) . "</i></td>\n";
    else if ( $attr_arr1_num[$a_id] !== null )
      echo "<td>" . $attr_arr1_num[$a_id] . "</td>\n";
    else
      echo '<td></td>' . "\n";
    if ( $attr_arr2_id[$a_id] !== null )
      echo "<td><i>" . htmlify( $attr_arr2_name[$a_id] ) . "</i></td>\n";
    else if ( $attr_arr2_num[$a_id] !== null )
      echo "<td>" . $attr_arr2_num[$a_id] . "</td>\n";
    else
      echo '<td></td>' . "\n";
    $cond_expr = '';
    if ( $attr_cond_id[$a_id] ) {
      $cond_expr .= "<i>" . htmlify( $attr_cond_name[$a_id] ) . "</i>";
      if ( $attr_cond_val[$a_id] === null )
        $cond_expr .= " != 0";
      else {
        if ( ( $attr_cond_type[$a_id] === null ) or ( $attr_cond_type[$a_id] === 0 ) )
          $cond_expr .= "&nbsp;==&nbsp;";
        else
          $cond_expr .= "&nbsp;!=&nbsp;";
        $cond_expr .= $attr_cond_val[$a_id];
      };
    };
    echo '<td>' . $cond_expr . '</td>' . "\n";
    echo "<td>" . nl2br( htmlify( $attr_description[$a_id] ) ) . "</td>\n";

    if ( $version === null ) {
      if ( $attr_ver_from[$a_id] !== null ) echo "<td>" . $version_description[$attr_ver_from[$a_id]] . "</td>"; else echo "<td>Any</td>";
      if ( $attr_ver_to[$a_id] !== null ) echo "<td>" . $version_description[$attr_ver_to[$a_id]] . "</td>"; else echo "<td>Any</td>";
    };

    if ( $docsys_admin ) {
      if ( $active ) {
	echo '<td><a href="index.php?mode=edit&amp;table=attr&amp;block_id=' . $req_block_id . '&amp;attr_id=' . $a_id . '&amp;version=' . $version . '">Edit</a></td>' . "\n";
	if ( $is1st === 1 ) {
	  echo '<td></td>' . "\n";
	  if ( $attr_precedence[$a_id] !== -1 ) $is1st = 0;
	} else
	  echo '<td><a href="index.php?mode=action&amp;table=attr&amp;action=Up&amp;block_id=' . $req_block_id . '&amp;attr_id=' . $a_id . '&amp;attr_precedence=' . $attr_precedence[$a_id] . '&amp;version=' . $version . '">Up</a></td>' . "\n";
	echo '<td><a href="index.php?mode=action&amp;table=attr&amp;action=Delete&amp;block_id=' . $req_block_id . '&amp;attr_id=' . $a_id . '&amp;version=' . $version . '">Delete</a></td>' . "\n";
      } else {
	echo "<td></td>\n";
	echo "<td></td>\n";
	echo "<td></td>\n";
      };
    };
    echo "</tr>\n";
    $count += 1;
  };
  return $count;
};

require("../footer.tpl");

?>
