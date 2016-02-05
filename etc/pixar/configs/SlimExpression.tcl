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
# SlimExpression.tcl
#   public package for Slim's expression evaluation
#   subsystem. The primary purpose of this package is
#   to stub out the standard procs for error-free
#   evaluation within Slim.
#
#   we also define context-establishing procs that can be overridden
#
# $Revision: #1 $
#

#  You can use this procedure to define variables used in
#  appearance-specific expressions, such as the name of
#  the shader (or "master") that is generated. As a starting
#  point we define the PALETTENAME variable to be the label
#  of the appearance's palette.
#
#  But you can create additional variables. For example,
#  this code would create a new variable based on a
#  specific entry in the palette's user data:
#
#  set pal [$apph GetRoot]
#  RMS::Scripting::SetVar PALETTEPREFIX [$pal GetUserData palettePrefix]
#
proc ::Slim::SetInstanceExpressionContext apph {
    set pal [$apph GetRoot]
    RMS::Scripting::SetVar PALETTENAME [$pal GetLabel]
}

# want all standard scripting commands to be
# in global namespace so they're available in all namespaces.
#
# ClientAttr and ClientCmd support -------------------------------------
proc mayaattribute {ch {frame {}}} {
    clientattr $ch $frame
}

proc mattr {ch {frame {}}} {
    clientattr $ch $frame
}

proc mel str {
    clientcmd $str
}

proc clientattr {str frame} {
    # our implementation doesn't care about frame and simply returns
    # the current param value at the current chan
    set value [RMS::Scripting::GetVar VALUE]
    set chan [RMS::Scripting::GetVar CHAN]
    return [lindex $value $chan] ; # since $VALUE may be a list
}

proc clientcmd {str} {
    return {}
}

proc coordsys {nm args} {
    # during slim rendering there are no defined
    # coordinate systems.  This would result in a
    # loud rendering error.
    return {}
}

# Standard procedures -----------------------------------------------
proc stmatrix0 {nm} {
    st0 $nm
}

proc stmatrix1 nm {
    st1 $nm
}

proc st0 {nm} {
    return "1 0 0"
}

proc st1 {nm} {
    return "0 1 0"
}

# Resource Referencing procedures -----------------------------------
proc shdmap {args} {
    return {}
}

proc envmap {args} {
    return {}
}

proc refmap {args} {
    return {}
}

proc imgmap {args} {
    return {}
}

proc zmap {args} {
    return {}
}

proc dso {args} {
    return {}
}

proc photonmap {args} {
    return {}
}

proc irradiancemap {args} {
    return {}
}

proc irradiancecache {args} {
    return {}
}

proc occmap {args} {
    return {}
}
proc bakefile {args} {
    return {}
}
proc bakemap {args} {
    return {}
}

::RAT::LogMsg DEBUG "Slim Expression Subsystem Loaded"



