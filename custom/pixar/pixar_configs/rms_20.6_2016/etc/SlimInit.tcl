##
## Copyright (c) 2005 PIXAR.  All rights reserved.  This program or
## documentation contains proprietary confidential information and trade
## secrets of PIXAR.  Reverse engineering of object code is prohibited.
## Use of copyright notice is precautionary and does not imply
## publication.
##
##                      RESTRICTED RIGHTS NOTICE
##
## Use, duplication, or disclosure by the Government is subject to the
## following restrictions:  For civilian agencies, subparagraphs (a) through
## (d) of the Commercial Computer Software--Restricted Rights clause at
## 52.227-19 of the FAR; and, for units of the Department of Defense, DoD
## Supplement to the FAR, clause 52.227-7013 (c)(1)(ii), Rights in
## Technical Data and Computer Software.
##
## Pixar
## 1200 Park Ave
## Emeryville, CA 94608
##
## ----------------------------------------------------------------------------
#
# SlimInit.tcl
#   procedures used by slim.ini
#   to handle the registering of templates
#   and configuration of menus
#
# $Revision: #4 $
#

#  
# These procedures help establish the preferences used to
# fill in the menus for "Import Appearance"
#
# Note that the "CreateMenu" procedures are obsolete with Slim 7
#

# ::Slim::ClearImportMenuDescriptions
#
# Clear menu descriptions. Usually done at the beginning of slim.ini
#
proc ::Slim::ClearImportMenuDescriptions {} {
    set ::Slim::ImportMenuDescriptions {}
}

#
# ::Slim::AddImportMenuDescriptions
#
# Create menu descriptions for imported appearances
# This expects a list of lists containing:
#
#    { master  label  menuPosition }
#
# e.g.
#
# {
#    { Mondo.slo             Mondo        /Surface }
#    { constant.slo          Constant     /Surface/Utility }
#    { depthcue.slo          "Depth Cue"  /Volume }
#    { plugins/mtorFur.slim  Fur          /RIBGen }
# }
#
proc ::Slim::AddImportMenuDescriptions info {
    set ::Slim::ImportMenuDescriptions \
	[concat $::Slim::ImportMenuDescriptions $info]
    ::Slim::SetMenuDescPreferences $::Slim::ImportMenuDescriptions Import
}

# These are obsolete with Slim 7
# For now, quietly do nothing
proc ::Slim::ClearCreateMenuDescriptions {} {
}

proc ::Slim::AddCreateMenuDescriptions info {
}


# ::Slim::ClearLazyTemplateTable:
#   Clears the named table, presumably to wipe the slate clean
#   in preparation for alternate template subsystem.
proc ::Slim::ClearLazyTemplateTable {} {
    set ::Slim::LazyTemplateTable {}
}

# ::Slim::AddLazyTemplateFile
#   Appends the LazyTemplateTable
proc ::Slim::AddLazyTemplateFile {file contents} {
    lappend ::Slim::LazyTemplateTable $file $contents
}

#
# ::Slim::RegisterLazyTemplates
#
# Register templates using "LoadExtension slimtmplt"
#
# An example format for the table can be found in _basicTemplates.ini
#
proc ::Slim::RegisterLazyTemplates {lazyTemplateTable args} { 
    # currently we employ the policy that any template located
    # below a directory named legacy will be hidden.
    if {$lazyTemplateTable eq {}} {
        set lazyTemplateTable $::Slim::LazyTemplateTable
    }
    set legacyPattern "legacy*"
    for {set i 0} {$i < [llength $args]} {incr i} {
	switch -- [lindex $args $i] {
	    "-legacyPattern" {
		set legacyPattern [lindex $args [incr i]]
	    }
	    default {
		::RAT::LogMsg WARNING \
            "Unknown option [lindex $args $i] passed to RegisterLazyTemplates"
	    }
	}
    }

    # register templates
    foreach {fileref tmpltList} $lazyTemplateTable {
	set filter {}
	foreach pat $legacyPattern {
	    if [string match $pat $fileref] {
		set filter hidden
	    }
	}
	foreach template $tmpltList {
	    foreach {id type label tags icon} $template {}; # multi-assignment
	    array unset interface
	    array set   interface {}
	    # type can either be a single word, representing the type
	    # (or "multiple"), or it can have the interface form
	    # {?inputs {<input types>}? outputs {<output types>}}
	    # so that {outputs {float}} and float mean the same thing
	    if {[llength $type] > 1} {
		array set interface $type
		if [info exists interface(outputs)] {
		    set type $interface(outputs)
		    if {[llength $type] > 1} {
			set type "multiple"
		    }
		}
	    }
	    LoadExtension slimtmplt $fileref \
              [list $id $type $label $filter $tags $icon [array get interface]]
	}
    }
}

#
# ::Slim::RegisterImportedAppearances
#
# Register importedappearances using "LoadExtension slimmaster"
# and build up a table of menu descriptions used
# by the procedures above.
#
# An example format for the table can be found in slim.ini
#
proc ::Slim::RegisterImportedAppearances appTable {
    set menuDesc {}
    foreach entry $appTable {
	# vector assignment trick:
	foreach {master type label menu} $entry {}
	# load extension
	LoadExtension slimmaster $master [list $type $label]
	# add menu information to list
	# { ratCollector.slo RATCollector /Surface/Utility }
	lappend menuDesc [list $master $label $menu]
    }
    ::Slim::AddImportMenuDescriptions $menuDesc
}


# this proc provides the guts of Add*MenuDescriptions (above)
# it loops through the descriptions building menus and
# setting the appropriate preferences
proc ::Slim::SetMenuDescPreferences {info {prefix {}}} {

    # convert list to an array indexed by path
    array set menus {}
    foreach tmplt $info {
	foreach {id label menupath} $tmplt {
	    lappend menus($menupath) $label $id
	}
    }

    # process paths and create/update Menu preferences
    foreach menupath [lsort -decreasing [array names menus]] {

	set parent [file dirname $menupath]
	if {![string match "/*" $menupath]} {
	    # no slash means an infinite loop below. skip.
	    ::RAT::LogMsg WARNING \
"\"$menupath\" (used by $menus($menupath)) is not a valid menu path. Skipping."
	    continue
	}

	# create any intermediate cascade menus
	# that don't contain any templates
	while {![string equal $parent /]} {
	    if {![info exists menus($parent)]} {
		set mstr ""
		foreach child [lsort [array names menus $parent/*]] {
		    append mstr "{    _cascade [file tail $child] {\n"
		    append mstr "     {_menuDesc $prefix$child}\n"
		    append mstr "}}\n"
		}
		SetPref Menu($prefix$parent) $mstr
		set menus($parent) $mstr
	    }
	    set parent [file dirname $parent]
	}

	# add template descriptions
	# and any other cascades specified
	set mstr ""
	catch {unset ids}
	# build an array so we can sort on the label
	array set ids $menus($menupath)
	foreach item [lsort [array names ids]] {
	    if {$prefix == "Import"} {
		# entry contains a _master identifier
		append mstr "{_master $ids($item)}\n" ; # master
	    } else {
		# just add the entry
		append mstr "$ids($item)\n"; # simple list of ids
	    }
	}
	set clen [llength [file split $menupath]]
	incr clen
	foreach child [lsort [array names menus "$menupath/*"]] {
	    if {[llength [file split $child]] == $clen} {
		append mstr "{    _cascade [file tail $child] {\n"
		append mstr "     {_menuDesc $prefix$child}\n"
		append mstr "}}\n"
	    }
	}
	SetPref Menu($prefix$menupath) $mstr
    }
}


