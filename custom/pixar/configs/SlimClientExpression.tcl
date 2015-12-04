##
## Copyright (c) 1999 PIXAR.  All rights reserved.  This program or
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
## 1001 West Cutting Blvd.
## Richmond, CA  94804
##
## ----------------------------------------------------------------------------
#
# SlimClientExpression.tcl
#   TCL procedures required to support parameter expressions across
#   Slim clients.  This file should be viewed as a reference implementation
#   and also captures MTOR-legacy usages. For in-slim preview rendering
#   the routines are overridden here: $RMSTREE/etc/SlimExpression.tcl.
#
#   RfM overrides this file here: $RMSTREE/lib/rfm/SlimClientExpresion.tcl
#
# $Revision: #1 $
#
#
namespace eval ::SlimClient {
    # SlimClient::Expr is used to evaluate a multi-channel expression.
    # It simply loops over each channel of the object updating the
    #	global var: CHAN.
    proc Expr {nch exp} {
	for {set i 0} {$i < $nch} {incr i} {
	    RMS::Scripting::SetVar CHAN $i
	    lappend result [RMS::Interpolate "\[[list expr $exp]\]"]
	}
	return $result
    }
    # theWorklist is used to capture the list of texture
    # conversion and map computes requested by parameters and
    # appearances.
    variable theWorklist {}
    variable theExpressionContext undefined
    variable theLightHandle 0
    variable theLightHandles; # an array indexed by appid
    variable theRegisteredLights; # an array indexed by lighthandle
    variable theTxMakeMode convert; # convert | ignore
    variable theTxMakeOutfileCache; # array maps $infile$args to outfile
    variable theTxMakeWorkCache; # array maps $infile$args to worklist
}

#
# txmake - command to encapsulate texture conversion
# args:
#   -mode m | -smode m -tmode m
#   -filter name
#   -filterwidth xy | -sfilterwidth x -tfilterwidth y
#   -resize up | down | round | up- | down- | round- | none
#   -ch rgba
#   -pattern diagonal | single | all
#   -envlatl | -envcube | -shadow
#   -o outfile
#   -short | -type byte|short|word|float
proc txmake {infile args} {
    if {$infile == "" || $::SlimClient::theTxMakeMode == "ignore"} { return $infile }
    
    # if this same invokation of txmake has happened before 
    # use cached outfile and worklist.
    set cachekey "$infile$args$::SlimClient::theExpressionContext"
    if {[lsearch [array names ::SlimClient::theTxMakeOutfileCache] $cachekey] != -1} {
	set outfile $::SlimClient::theTxMakeOutfileCache($cachekey)
	if {$::SlimClient::theExpressionContext == "WriteSlimData"} {
	    if {[lsearch [array names ::SlimClient::theTxMakeWorkCache] $cachekey] != -1} {
		set work $::SlimClient::theTxMakeWorkCache($cachekey)
		# These control autogeneration of a node inside Maya
		# in this case it's a txmake node
		#set ::SlimClient::thePassRequest [lindex $work 0]
		#set ::SlimClient::thePassValue [lindex $work 1]
		return $outfile
	    }
	} elseif {$::SlimClient::theExpressionContext == "GenWorklist"} {
	    # check if work is in cache - work only gets cached when 
	    # txmake is called with ::SlimClient::theExpressionContext == GenWorklist
	    if {[lsearch [array names ::SlimClient::theTxMakeWorkCache] $cachekey] != -1} {
		lappend ::SlimClient::theWorklist [lindex $::SlimClient::theTxMakeWorkCache($cachekey) 0]
		return $outfile		
	    }
	} else {
	    return $outfile
	}
    }    

    ::RMS::LogMsg DEBUG "txmake not using cache"

    # make sure infile is fully qualified.
    set ff [workspace ResolvePath $infile texture]
    if {$ff == {}} {
    	set ff [workspace GlobalizePath $infile]
    }
    set infile $ff
    if {[RATC_filetype $infile] == "rtex" } { return $infile }

    set type {}
    if {-1 != [lsearch $args -short]} {
	set type short
    } elseif {-1 != [lsearch $args -float]} {
	set type float	
    }
    set smode black
    set tmode black
    set filter "catmull-rom"
    set swidth 3
    set twidth 3
    set extra {}
    set outfile {}
    set rezcode {}
    foreach {nm value} $args {
	switch -exact -- $nm {
	    "-o" {
		set outfile $value
	    }
	    "-mode" {
		set smode $value
		set tmode $value
	    }
	    "-smode" {
		set smode $value
	    }
	    "-tmode" {
		set tmode $value
	    }
	    "-filter" {
		set filter $value
	    }
	    "-filterwidth" {
		set swidth $value
		set twidth $value
	    }
	    "-sfilterwidth" {
		set swidth $value
	    }
	    "-tfilterwidth" {
		set twidth $value
	    }
	    "-type" {
		set type $value
	    }
	    "-resize" {
		append extra " \"resize\" \"$value\""
		set rezcode [string index $value 0]
		if ![string match *- $value] {
		    set rezcode [string toupper $rezcode]
		}
	    }
	    "-ch" {
		append extra " \"ch\" \"$value\""
	    }
	    "-pattern" {
		append extra " \"pattern\" \"$value\""
	    }
	}
    }
    if ![string equal {} $type] {
	append extra " \"type\" \"$type\""
    }
    if {$outfile == ""} {
	set location slimTextures
	if [ismtormode] {
	    set location torTextures
	}
	set texdir [workspace GetDir $location 1 1]
	set wrapcode "[string index $smode 0][string index $tmode 0]$rezcode"
	set tail [file rootname [file tail $infile]]
	
	set outfile [file join $texdir ${tail}_${wrapcode}.tex]
	if {![ismtormode]} {
	    set outfile [file join \$RMSPROJ $outfile]
	}
    }

    if {$::SlimClient::theExpressionContext == "WriteSlimData"} {
	set passname [file rootname [file tail $outfile]]
	set passargs "-inputfile $infile"
	if {-1 != [lsearch $args "-envlatl"]} {
	    set passtype MakeLatLongEnvironment
	    lappend passargs "-filter" $filter "-swidth" $swidth \
		"-twidth" $twidth
	} elseif {-1 != [lsearch $args "-envcube"]} {
	    set passtype MakeCubeFaceEnvironment
	} elseif {-1 != [lsearch $args "-shadow"]} {
	    set passtype MakeShadow
	} else {
	    set passtype MakeTexture
	    lappend passargs "-smode" $smode "-tmode" $tmode \
		"-filter" $filter "-swidth" $swidth "-twidth" $twidth
    	}
	eval lappend passargs $extra

	set work [list [list $passtype $passname $passargs] "$passname texture"]

	# These control autogeneration of a node inside Maya
	# in this case it's a txmake node
	#set ::SlimClient::thePassRequest [lindex $work 0]
	#set ::SlimClient::thePassValue [lindex $work 1]
	
	set ::SlimClient::theTxMakeWorkCache($cachekey) $work
    } elseif {$::SlimClient::theExpressionContext == "GenWorklist"} {
	set newwork {}

    	# when generating the worklist we require the full pathname
    	set outfile [RMS::Interpolate $outfile]
    	if [GetPref OldOutputPathLogic 0] {
	    set outfile [workspace GlobalizePath $outfile]
	} else {
	    set outfile [file join [workspace GetRootDir] $outfile]
	}
	
	# This takes the syntax of the appropriate RIB command.
	# we don't place "newer" here as it is managed elsewhere.
	if {-1 != [lsearch $args "-envlatl"]} {
  	    lappend newwork "MakeLatLongEnvironment \"$infile\" \"$outfile\" \
    		\"$filter\" $swidth $twidth \
    		$extra"
	} elseif {-1 != [lsearch $args "-envcube"]} {
	    set cmd MakeCubeFaceEnvironment
	    # unimplemented!
	} elseif {-1 != [lsearch $args "-shadow"]} {
	   lappend newwork "MakeShadow \"$infile\" \"$outfile\" \
		$extra"
	} else {
    	    lappend newwork "MakeTexture \"$infile\" \"$outfile\" \
    		\"$smode\" \"$tmode\" \"$filter\" $swidth $twidth \
    		$extra"
    	}

	lappend ::SlimClient::theWorklist [lindex $newwork 0]
	set ::SlimClient::theTxMakeWorkCache($cachekey) $newwork
    }
    set ::SlimClient::theTxMakeOutfileCache($cachekey) $outfile

    return $outfile
}

proc resettxmakecache {} {
    # clear cache arrays
    if [array exists ::SlimClient::theTxMakeOutfileCache] {
	unset ::SlimClient::theTxMakeOutfileCache
    }
    if [array exists ::SlimClient::theTxMakeWorkCache] {
	unset ::SlimClient::theTxMakeWorkCache
    }
}

#
# txmake_o: For use by glimpse2slim script to convert
# texture file parameters.  
# There are 3 major tracks this can take.
# 1) if input file exists
#   a) if texture - use it, no txmake no translation
#   b) if !texture - txmake using modes and translation
# 2) if input file ! exist
#   a) convert to output filename, no txmake
#

proc txmake_o {instring inmode args} {
    set smode black
    set tmode black
    set filter "catmull-rom"
    set swidth 3
    set twidth 3
    set resize {}
    set outfile {}
    set rezcode {}
    set txOptions(P) periodic
    set txOptions(C) clamp
    set txOptions(B) black
    set txOptions(S) up-
    set txOptions(N) {}

    set infile [lindex $instring 0]

    # protection if $inmode is not set.
        
    if { $inmode == "" } { return $instring }
    set sl [string length $inmode]
    
    set cmds { {smode} {tmode} {resize} }
    for  { set i 0 } {$i < $sl} { incr i 1 } {
      set modechar [string index $inmode $i]
      set [lindex $cmds $i] $txOptions($modechar)
    }
    # make sure infile and outfile are fully qualified
    set ff [workspace ResolvePath $infile texture]
    if {$ff == {}} {
    	set ff [workspace GlobalizePath $infile]
    }
    set infile $ff
    #
    # OK, we've got the global infile now.  Let's see if it
    # exists.
    #
    
    if [file exists $infile] {
	if {[RATC_filetype $infile] == "rtex" } {
	    set outfile $infile
	    set doTxmake 0
	} else {
	    set doTxmake 1
	}  
    } else {
    
    #
    # OK, the file doesn't exist we'll convert the name
    # but no txmake.
    
	set doTxmake 0
    }
    
    #
    # We need to handle animated textures in the old
    # Glimpse style.  For example:
    # images/test.0000 -> rmantex/test.0000.PPS.tex
    # images/test.0000.tif -> rmantex/test.0000.PPS.tex
    #
    if {$outfile == ""} {
	set location slimTextures
	if [ismtormode] {
	    set location torTextures
	}
	set texdir [workspace GetDir $location 1 1]
	set wrapcode $inmode
	set tail [file tail $infile]
	if { [regexp {\.[0-9][0-9]*$} $infile] != 1 } { set tail [file rootname $tail] }
	set outfile [file join $texdir $tail.$wrapcode.tex]
    }


    if { $doTxmake != 1 } { return $outfile }
    
#
#  We only go here if source infile exists and is !texture
#
    # when generating the worklist we require the full pathname
    if [GetPref OldOutputPathLogic 0] {
	set outfile [workspace GlobalizePath $outfile]
    } else {
	set outfile [file join [workspace GetRootDir] $outfile]
    }
    
    set args [linsert $args 0 "-o" $outfile "-smode" $smode "-tmode" $tmode ]
    if { $resize != {} } { set args [linsert $args 6 "-resize" $resize ] }
    set tm [eval txmake $infile $args ]
    return $tm
	
}

#
# genmap, autoarchive: means by which work is transmitted from slim to clients
#
# genmap args:
# -resolution 256 -locator "$OBJNAME" -laziness "off"
# -crew "" -near 0 -far 0 -type "shadow" -frequency "never" 
# -depthfilter min -context ""
proc genmap {args} {
    if {$::SlimClient::theExpressionContext == "GenWorklist"} {
    	lappend ::SlimClient::theWorklist "ComputeMap $args"
    }
}

proc autoarchive {args} {
    if {$::SlimClient::theExpressionContext == "GenWorklist"} {
    	lappend ::SlimClient::theWorklist "AutoArchive $args"
    }
}

proc constructBakePassName {atlas map} {
    return ${atlas}_${map}
}

proc ptcfile {atlas map freq {crew {}}} {
    if {$::SlimClient::theExpressionContext == "WriteSlimData"} {
	# construct pass name with map and atlas arguments
	set passname [constructBakePassName $atlas $map]
	set ::SlimClient::thePassValue "$passname ptcfile"
	set result ""
    } else {
	set location slimTextures
	if [ismtormode] {
	    set location torTextures
	}
	set texdir [workspace GetFullPathForOutput $location]
	if [string equal $freq job] {
	    set fext {}
	} else {
	    set fext .[RMS::Interpolate {$F4}]
	}
	set filename "${atlas}_$map$fext.ptc"
	set result [file join $texdir $filename]
    }
    return $result
}

proc bakepassclass args {
    return ""
}

proc bakefile {ptcfile style {crew {}}} {
    switch $style {
	ptcSStoBkm -
	ptcFilterBkm -
	ptcToBkm {
	    set ext .bkm
	}
	ptcToTex {
	    set ext .tex
	}
        impliedSS -
	ptcToPtc -
        default {
	    set ext .ptc
	}
    }
    return "[file rootname $ptcfile]$ext"
}

proc bakepassid {atlas map bakecontext {crew {}}} {
    if {$::SlimClient::theExpressionContext == "WriteSlimData"} {
	# construct pass name with map and atlas arguments
	set passname [constructBakePassName $atlas $map]
	set ::SlimClient::thePassValue "$passname bakepassid"
    }
    return $bakecontext
}

# bakemap:
#   this proc is called to register a ptcloud conversion request.
#   either as slim data, or via a BakeMap request (used by clients).
#   such requests are assumed to be originated in cahoots with
#   a bake pass - (workgen reference pass).  
proc bakemap {args} {
    set atlas ""
    set disable 0
    set freq ""
    set map ""
    set maxsolidangle ""
    set passargs ""
    set style ""

    set result {}

    for {set i 0} {$i < [llength $args]} {incr i} {
	set arg [lindex $args $i]
	switch -glob -- $arg {
	    "-atlas" {
		set atlas [lindex $args [incr i]]
	    }
	    "-disable" {
		set disable [lindex $args [incr i]]
	    }
	    "-freq" {
		set freq [lindex $args [incr i]]
	    }
	    "-map" {
		set map [lindex $args [incr i]]
	    }
	    "-maxsolidangle" {
		set maxsolidangle [lindex $args [incr i]]
	    }
	    "-style" {
		set style [lindex $args [incr i]]
	    }
	    "-ptfilter:*" {
		lappend passargs $arg [lindex $args [incr i]]
	    }
	}
    }

    if {$::SlimClient::theExpressionContext == "WriteSlimData"} {
	# construct pass name with map and atlas arguments
	set passname [constructBakePassName $atlas $map]

	# build passargs
	if {$freq != ""} {
	    lappend passargs "-frequency" $freq
	}
	if {$maxsolidangle != ""} {
	    lappend passargs "-maxsolidangle" $maxsolidangle
	}

	# figure out type, result
	if {$style == "ptcFilterBkm"} {
	    set passtype PtcFilterBkm
	    set passresult brickmap
	} else {
	    set passtype ""
	    set passresult ""
	}

	# build pass request, value
	if {$passtype != ""} {
	    set ::SlimClient::thePassRequest [list $passtype $passname $passargs]
	}
	if {$passresult != ""} {
	    set ::SlimClient::thePassValue [list $passname $passresult]
	}
    } elseif !$disable {
	# here we do always invoke the converter.  We rely on
	# -newer to take shortcuts.  The conversion is controlled
	# by -style.  Input file is always ptcloud, output file
	# is either brickmap or texture.  When generating a texture
	# we must take a double-hop.  From ptc to tiff to tex.
	# As far as clients of bakemap are concerned only the
	# ptcloud and bkm or tex file names are important.
	set in [ptcfile $atlas $map $freq]
	set out [bakefile $in $style]
	if {![string equal $in $out] &&
	    [string equal $::SlimClient::theExpressionContext GenWorklist]} {
	    lappend ::SlimClient::theWorklist "BakeMap $args -in \"$in\" -out \"$out\""
	    
	}
	set result [workspace LocalizePath $out]
    }
    if {![ismtormode]} {
        # if $result is empty there is no point in returning anything, better
        # to return empty string so the shader can at least choose to do
        # something sensible in that case.
        if {$result == ""} {
            return ""
        } else {
            set result [file join \$RMSPROJ $result]
        }
    }
    return $result
}

# torattr - the means by which per-appearance attributes are transmitted
# from appearance server (slim) to client (mtor).
proc torattr {op args} {
    switch -exact -- $op {
	write {
	    array unset ::SlimClient::AppearanceAttributes
	    foreach {nm value} $args {
		set ::SlimClient::AppearanceAttributes($nm) $value
	    }
	}
	read {
	    if {[llength $args] != 1} {
		error "torattr - invalid arguments for read operation ($args)"
	    }
	    if ![info exists ::SlimClient::AppearanceAttributes($args)] {
		error "torattr - nonexistant attribute: $args"
	    } else {
		return $::SlimClient::AppearanceAttributes($args)
	    }
	}
	default {
	    ::RMS::LogMsg WARNING "unexpected call to torattr ($op $args)"
	}
    }
}

#
# lighthandle: simple means of generating unique light handles for RIB
#   usage:
#   	-reset  (resets the stack of lighthandle generation, called at the beginning of a subframe)
#	-pushBase h (pushes the current lighthandle, causes a new "context" for light handles)
#	-popBase (resets the current lighthandle, from the handle stack)
#   	-register handle id (registers a handle generated elsewhere, to prevent collisions)
#	-generate id (generates a new light handles)
#   	-get id  (return the lighthandle for id, error if nonexistant)
#
proc lighthandle {args} {
    #::RMS::LogMsg NOTICE "lighthandle $args"
    switch -exact -- [lindex $args 0] {
	-reset {
	    catch "unset ::SlimClient::theLightHandles"
	    catch "unset ::SlimClient::theRegisteredLights"
	    set ::SlimClient::theLightHandles(_) {}; # init as array
	    set ::SlimClient::theRegisteredLights(_) {}
	    if {![info exists ::SlimClient::theLightBaseStack] ||
		$::SlimClient::theLightBaseStack == {}} {
		set ::SlimClient::theLightBaseStack 500
	    }
	    set ::SlimClient::theLightHandle [lindex $::SlimClient::theLightBaseStack end]

	}
	-pushBase {
	    set h [lindex $args 1]
	    lappend ::SlimClient::theLightBaseStack $h
	    set ::SlimClient::theLightHandle $h
	}
	-popBase {
	    set ::SlimClient::theLightBaseStack [lreplace $::RMS::theLightBaseStack end end]
	}
	-register {
	    set handle [lindex $args 1]
	    set id [lindex $args 2]
	    set ::SlimClient::theRegisteredLights($handle) $id
	    return {}
	}
	-generate {
	    if [string equal [GetPref RIBHandleStyle] string] {
		set h [lindex $args 1]
		if [info exists ::SlimClient::theRegisteredLights($h)] {
		    # this case can occur in normal operation - due to 
		    # multipass work generation with slim appearances.
		    ::RMS::LogMsg DEBUG "SlimClient::lighthandle -generate $h conflict"
		} else {
		    set ::SlimClient::theRegisteredLights($h) $h
		    set ::SlimClient::theLightHandles($h) $h
		}
		return \"$h\"
	    } else {
		set id [lindex $args 1]
		set h $::SlimClient::theLightHandle
		while {[info exists ::SlimClient::theRegisteredLights($h)]} {
		    incr h
		}
		set ::SlimClient::theRegisteredLights($h) $id
		lappend ::SlimClient::theLightHandles($id) $h
		set ::SlimClient::theLightHandle [incr h]
		return [lindex $::SlimClient::theLightHandles($id) end]
	    }
	}
	-get {
	    set id [lindex $args 1]
	    if [info exists ::SlimClient::theLightHandles($id)] {
		return [lindex $::SlimClient::theLightHandles($id) 0]
	    } else {
		::RMS::LogMsg ERROR "can't find light handle for $id"    
	    }
	}
    }
}

#
#
# tclbox: called to arrange for the execution of the provided script
#
proc tclbox script {
    if [catch "uplevel #0 {$script}" msg] {
	set name [RMS::Interpolate {$INSTANCENAME}]
	::RAT::LogMsg ERROR "error in tclbox $name: $msg"
    }
    return {}
}

#
# adaptor: one means by which procedural selection of appearances
# is achieved.  This design is coupled with the adaptorui template.
#
# ruleset is a list of rules
#
# rule is comprised of four values:
#   1) cmethod - the method to use for pattern matching, currently
#       match: string match, regexp: regexp, lsearch
#   2) varname - the name of a GLOBAL, safe variable whose value
#       is compared against values in the rules.
#   3) condition - a pattern matched against $varname's value.
#   4) id - the id of the appearance.
#
# The rules are evaluated in the order provided. When a match is made,
#  the iteration terminates and the associated app id is returned in
#  a special format: "id:$id".
#
proc adaptor ruleset {
    foreach rule $ruleset {
        foreach {cmethod varname condition id} $rule {}; #fancy 4-way set.
        set value [set $varname]; # this evaluates the variable
        switch $cmethod {
            match {
                if [string match $condition $value] {
                    return id:$id
                }
            }
            regexp {
                if [regexp $condition $value] {
                    return id:$id
                }
            }
            lsearch {
                if {-1 != [lsearch $condition $value]} {
                    return id:$id
                }
            }
        }
    }
    return {}; # no matches
}

proc ismtormode {} {
    ::RMS::Scripting::IsRATMode
}

proc SSFindRenderPass args {
    return ""
}

proc SSFindConversionPass args {
    return ""
}

proc SSFindConversionPassClass args {
    return ""
}

proc PassFileName args {
    return ""
}

::RMS::LogMsg DEBUG "Slim Client Expression Subsystem Loaded"
