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
# SlimBuildShaderData.tcl
#   TCL procedures to support user generated annotations in Slim-generated
#   shaders
#
# $Revision: #1 $
#
#

# This file embodies the support for generating arbitrary metadata at shader
# generation time. The idea is that when the shader generation starts the
# routine GetShaderMetadata, here is called and its return value is used to
# generate the data at the head of the shader.
# To have your routine called too, you can register it with the call
# ::Slim::RegisterShaderMetadataProvider <yourfunction>
# You can remove it from the calling queue with the call
# ::Slim::DeregisterShaderMetadataProvider <yourfunction>
# Last, you can query the current queue with the call
# ::Slim::GetShaderMetadataProviders

namespace eval ::Slim {
    variable shaderMetadataProviders ""

    # Handle the Metadata Providers queue
    proc RegisterShaderMetadataProvider procname {
	variable shaderMetadataProviders
	lappend shaderMetadataProviders $procname
    }
    proc GetShaderMetadataProviders {} {
	variable shaderMetadataProviders
	return $shaderMetadataProviders
    }
    proc DeregisterShaderMetadataProvider procname {
	variable shaderMetadataProviders
	if {[set i [lsearch $shaderMetadataProviders $procname]] != -1} {
	    set shaderMetadataProviders [lreplace $shaderMetadataProviders $i $i]
	}
    }

    # Called by Slim to build the metadata for a shader, whose handle will
    # be in $func
    proc GetShaderMetadata { func } {
	set result [list]
	foreach provider [GetShaderMetadataProviders] {
	    if [catch [list $provider $func] metadata] {
		global errorInfo
		::RAT::LogMsg WARNING "Unable to evaluate [list $provider $func]: $metadata : $errorInfo"
	    } else {
		lappend result $metadata
	    }
	}
	return $result
    }

    # Little utility that finds all the nodes inside a package
    proc FindPackageNodes {startNode} {
	if [$startNode isa ::Slim::AlterEgo::pkg] {
	    set nodes [$startNode GetFunctions]
	    set output [list]
	    foreach node $nodes {
		set output [concat $output [FindPackageNodes $node]]
	    }
	    return $output
	} else {
	    return $startNode
	}
    }

    # An example Metadata Provider: create a little xml report of what
    # shaders are used by the network for $func
    # Every metadata provider is expected to return a list of three elements:
    # - the first entry can be either "embed" of "file"
    #   + If it is "embed", the second element is expected to be a valid value
    #     for an xml attribute, and the contents are expected to be valid xml
    #     too. (This is always possible by means of <![CDATA[ ... ]]> sections)
    #   + If it is "file", the second element is a filename which is file
    #     join'ed with the slimShader/torShader entry of the workspace. This
    #     file will be opened and its contents set to the contents
    # - the second entry has been just explained
    # - the third entry will be the contents of the metadata information
    proc ReportTemplateUsage { func } {
	set upNodes [$func GetUpstreamNodes -network -return app]
	set upNodes [concat $func $upNodes]
	array set templateusage {}
	foreach node $upNodes {
	    foreach subnode [FindPackageNodes $node] {
		set name [$subnode GetTemplateID]
		if {$name ne {}} {
		    if [info exists templateusage($name)] {
			incr templateusage($name)
		    } else {
			set templateusage($name) 1
		    }
		}
	    }
	}
	set metadata ""
	# Write them out
	foreach name [lsort -dictionary [array names templateusage]] {
	    set nameList [::Slim::DeconstructTemplateID $name]
	    set vendor   [lindex $nameList 0]
	    set template [lindex $nameList 1]
	    set version  [lindex $nameList 2]
	    
	    append metadata "  <template vendor=\"$vendor\" version=\"$version\">\n"
	    append metadata "    <fullname>$name</fullname>\n"
	    append metadata "    <name>$template</name>\n"
	    append metadata "    <usagecount>$templateusage($name)</usagecount>\n"
	    append metadata "  </template>\n"
	}

	return [list embed slimtemplates $metadata]
    }
}

# This is how you register a function to be called at shader generation time
::Slim::RegisterShaderMetadataProvider ::Slim::ReportTemplateUsage

::RAT::LogMsg DEBUG "Slim Shader Metadata Provider Subsystem Loaded"