//Maya ASCII 2012 scene
//Name: bug.ma
//Last modified: Sat, May 23, 2015 12:10:17 AM
//Codeset: 1252
requires maya "2008";
fileInfo "application" "maya";
fileInfo "product" "Maya 2012";
fileInfo "version" "2012 x64";
fileInfo "cutIdentifier" "001200000000-796618";
fileInfo "osv" "Microsoft Business Edition, 64-bit  (Build 9200)\n";
createNode transform -s -n "persp";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -2.2133764800625348 1.7525202569041991 1.4566423235316257 ;
	setAttr ".r" -type "double3" -32.138352712215955 -412.59999999967255 -2.6182755992473857e-015 ;
	setAttr ".rp" -type "double3" -5.5511151231257827e-017 1.3877787807814457e-016 2.2204460492503131e-016 ;
	setAttr ".rpt" -type "double3" -2.2647538136487094e-016 2.7990918537366783e-016 
		-3.9098619850337177e-016 ;
createNode camera -s -n "perspShape" -p "persp";
	setAttr -k off ".v" no;
	setAttr ".fl" 34.999999999999979;
	setAttr ".ncp" 0.001;
	setAttr ".coi" 3.1525939112314654;
	setAttr ".imn" -type "string" "persp";
	setAttr ".den" -type "string" "persp_depth";
	setAttr ".man" -type "string" "persp_mask";
	setAttr ".tp" -type "double3" -0.77499179545367436 0.078230398124349732 -0.017372454976422036 ;
	setAttr ".hc" -type "string" "viewSet -p %camera";
createNode transform -s -n "top";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -1.1194548646420313 100.17683089704676 -0.17687556659681997 ;
	setAttr ".r" -type "double3" -89.999999999999986 0 0 ;
	setAttr ".rp" -type "double3" 0 2.7755575615628914e-017 -1.4210854715202004e-014 ;
	setAttr ".rpt" -type "double3" 0 -1.4238610290817636e-014 1.4183099139586376e-014 ;
createNode camera -s -n "topShape" -p "top";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.19414207980256;
	setAttr ".ow" 6.5119129631403192;
	setAttr ".imn" -type "string" "top";
	setAttr ".den" -type "string" "top_depth";
	setAttr ".man" -type "string" "top_mask";
	setAttr ".tp" -type "double3" -0.28060255514502025 -0.025564368029989737 -0.15874905946117859 ;
	setAttr ".hc" -type "string" "viewSet -t %camera";
	setAttr ".o" yes;
createNode transform -s -n "front";
	setAttr ".v" no;
	setAttr ".t" -type "double3" -0.01363226297728215 0.33326010313013199 100.13943527695982 ;
createNode camera -s -n "frontShape" -p "front";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 99.523953200228391;
	setAttr ".ow" 2.8286685530195395;
	setAttr ".imn" -type "string" "front";
	setAttr ".den" -type "string" "front_depth";
	setAttr ".man" -type "string" "front_mask";
	setAttr ".tp" -type "double3" -0.61560716888130618 0.53951431896497304 0.60759009786733031 ;
	setAttr ".hc" -type "string" "viewSet -f %camera";
	setAttr ".o" yes;
createNode transform -s -n "side";
	setAttr ".v" no;
	setAttr ".t" -type "double3" 100.15995694211176 0.39634771657127266 0.53194554647488557 ;
	setAttr ".r" -type "double3" 0 89.999999999999986 0 ;
	setAttr ".rp" -type "double3" -5.5511151231257827e-017 0 -1.4210854715202004e-014 ;
	setAttr ".rpt" -type "double3" -1.4155343563970749e-014 0 1.4266365866433296e-014 ;
createNode camera -s -n "sideShape" -p "side";
	setAttr -k off ".v" no;
	setAttr ".rnd" no;
	setAttr ".coi" 100.93514006116342;
	setAttr ".ow" 2.0076160691453881;
	setAttr ".imn" -type "string" "side";
	setAttr ".den" -type "string" "side_depth";
	setAttr ".man" -type "string" "side_mask";
	setAttr ".tp" -type "double3" -0.77518311905166115 0.30817385429103433 -0.39447688238365775 ;
	setAttr ".hc" -type "string" "viewSet -s %camera";
	setAttr ".o" yes;
createNode transform -n "FitSkeleton";
	addAttr -ci true -sn "visCylinders" -ln "visCylinders" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "visBoxes" -ln "visBoxes" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "visBones" -ln "visBones" -min 0 -max 1 -at "bool";
	addAttr -ci true -sn "lockCenterJoints" -ln "lockCenterJoints" -dv 1 -min 0 -max 
		1 -at "bool";
	addAttr -ci true -sn "visGap" -ln "visGap" -dv 0.75 -min 0 -max 1 -at "double";
	setAttr ".ove" yes;
	setAttr -l on -k off ".tx";
	setAttr -l on -k off ".ty";
	setAttr -l on -k off ".tz";
	setAttr -l on -k off ".rx";
	setAttr -l on -k off ".ry";
	setAttr -l on -k off ".rz";
	setAttr ".visBoxes" yes;
	setAttr ".visGap" 1;
createNode nurbsCurve -n "FitSkeletonShape" -p "FitSkeleton";
	setAttr -k off ".v";
	setAttr ".ove" yes;
	setAttr ".ovc" 29;
	setAttr ".cc" -type "nurbsCurve" 
		3 8 2 no 3
		13 -2 -1 0 1 2 3 4 5 6 7 8 9 10
		11
		0.98469668269722466 6.029528202980848e-017 -0.98469668269722144
		-1.5887574610742614e-016 8.5270405593665845e-017 -1.3925714034942092
		-0.98469668269722199 6.0295282029808492e-017 -0.98469668269722199
		-1.3925714034942092 1.0383295679287425e-032 -1.4545925907859694e-016
		-0.98469668269722221 -6.029528202980848e-017 0.98469668269722155
		-4.1960894146112109e-016 -8.5270405593665845e-017 1.3925714034942094
		0.98469668269722144 -6.0295282029808492e-017 0.98469668269722199
		1.3925714034942092 -6.0124835748922184e-032 1.0060259116220501e-015
		0.98469668269722466 6.029528202980848e-017 -0.98469668269722144
		-1.5887574610742614e-016 8.5270405593665845e-017 -1.3925714034942092
		-0.98469668269722199 6.0295282029808492e-017 -0.98469668269722199
		;
createNode joint -n "Root" -p "FitSkeleton";
	addAttr -ci true -sn "run" -ln "run" -dt "string";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.12058014269062001 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	addAttr -ci true -k true -sn "centerBtwFeet" -ln "centerBtwFeet" -min 0 -max 1 -at "bool" -dv true;
	setAttr ".t" -type "double3" 1.365977845382518e-009 0.55826854430755157 -0.29454359721885059 ;
	setAttr -l on ".tx";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 90 -84.254300032051603 90.000000000000128 ;
	setAttr ".dl" yes;
	setAttr ".typ" 1;
	setAttr ".radi" 0.5;
	setAttr -k on ".run" -type "string" "";
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 2.5;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.25;
createNode joint -n "BackLeg1" -p "Root";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.2935083498285731 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" -0.043688548240601532 0.088710231653218674 -0.19961293493071036 ;
	setAttr ".r" -type "double3" 1.2722218725854058e-014 -6.3611093629270533e-015 1.8129161684342046e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -45.367055369411226 43.064045359681465 133.26544015152356 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "LegAimBack";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.08;
	setAttr ".fatYabs" 0.079999998211860657;
	setAttr ".fatZabs" 0.079999998211860657;
createNode joint -n "BackLeg2" -p "BackLeg1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.20558358898105644 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.29350834982857321 9.9920072216264089e-016 -5.5511151231257827e-017 ;
	setAttr ".r" -type "double3" 7.7167331722885295e-014 1.082960117614064e-013 -1.5902773407317574e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".dsp" yes;
	setAttr ".jo" -type "double3" 0 0 70.944252364459061 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "HipBack";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.05000000074505806;
createNode joint -n "BackLeg3" -p "BackLeg2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.4692374153920939 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.20558358898105611 -6.6613381477509392e-016 -1.6653345369377348e-016 ;
	setAttr ".r" -type "double3" -1.8068325138953206e-013 1.5589711151344229e-013 2.2263882770244594e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -98.423440798312555 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.04;
	setAttr ".fatYabs" 0.039999999105930328;
	setAttr ".fatZabs" 0.039999999105930328;
createNode joint -n "BackLeg4" -p "BackLeg3";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.46923741539209496 2.1094237467877974e-015 -1.4155343563970746e-015 ;
	setAttr ".r" -type "double3" -7.4736379479414609e-014 1.5902773407317398e-014 -3.8166656177562214e-014 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 63.359999217430058 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "FootBack";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "BackLeg5" -p "BackLeg4";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.10000000000000087 -6.9388939039072284e-017 8.3266726846886741e-017 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "Tail1" -p "Root";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.3583554885424719 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	addAttr -ci true -k true -sn "flipOrient" -ln "flipOrient" -dv 1 -min 0 -max 1 -at "bool";
	setAttr ".t" -type "double3" -0.12031120800408235 0.0101394628513366 -2.7037973066386857e-017 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 180 5.7456999679483225 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 2.2600000000000002;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.22599999606609344;
createNode joint -n "Tail2" -p "Tail1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.3797362039513571 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.35835548854247085 -6.6613381477509392e-016 -2.2998425708918122e-016 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 7.5830332791013915e-022 8.2421297049297272e-005 5.8840000000059787 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 1.8599999999999999;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.18600000441074371;
createNode joint -n "Tail3" -p "Tail2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.33656727282739374 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.37973620395136132 -5.5511151231257827e-016 5.2939559203393771e-021 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -8.8372009801031453e-006 8.9672244096015656e-006 6.1220000000015036 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.10000000149011612;
createNode joint -n "Tail4" -p "Tail3";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.33656727282739374 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.33656727282739141 8.8817841970012523e-016 -5.7174723939665273e-021 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 1.8234786759325473e-005 0 0 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.05000000074505806;
createNode joint -n "Spine1" -p "Root";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.18824553795606544 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.20852776831318184 1.1102230246251565e-016 1.5615757912894819e-014 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 3.1542549154146032e-006 5.0162424078386318e-005 7.1961391499249077 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 1.9100000000000001;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.19099999964237213;
createNode joint -n "MiddleLeg1" -p "Spine1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.29910718046138385 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.11620926012536031 0.098575762731570316 -0.16093528479152078 ;
	setAttr ".r" -type "double3" -1.6220828875463929e-013 2.5444437451708349e-014 1.5584717939171225e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -84.082926565173281 42.416801004747398 92.589403391720637 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "LegAimMiddle";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.08;
	setAttr ".fatYabs" 0.079999998211860657;
	setAttr ".fatZabs" 0.079999998211860657;
createNode joint -n "MiddleLeg2" -p "MiddleLeg1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.30844950380849151 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.29910718046138496 7.2164496600635175e-016 -1.2490009027033011e-016 ;
	setAttr ".r" -type "double3" -1.5868348459203976e-014 -1.9333926474547748e-014 4.3255543667903831e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 78.754976019861303 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "HipMiddle";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.05000000074505806;
createNode joint -n "MiddleLeg3" -p "MiddleLeg2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.48991914618521171 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.30844950380849084 2.4980018054066022e-015 1.3183898417423734e-016 ;
	setAttr ".r" -type "double3" 1.938787681804698e-014 -1.9475997455268577e-014 1.2722218725854067e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -89.740173513695098 ;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "Hip2";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.04;
	setAttr ".fatYabs" 0.039999999105930328;
	setAttr ".fatZabs" 0.039999999105930328;
createNode joint -n "MiddleLeg4" -p "MiddleLeg3";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.48991914618521243 1.2212453270876722e-015 1.457167719820518e-016 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 59.400001847784829 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "FootMiddle";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "MiddleLeg5" -p "MiddleLeg4";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.099999999999998312 6.0888794006785929e-016 1.3877787807814457e-016 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "Spine2" -p "Spine1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.15443470180730007 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.18824553795606616 7.7715611723760958e-016 3.6427555177900094e-016 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 1.1848489498583668e-023 2.0705051032666526e-006 5.5899960144407093 ;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "Chest";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 1.79;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.17900000512599945;
createNode joint -n "Chest" -p "Spine2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.16620083388051768 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.15443470180729946 -6.106226635438361e-015 2.3902210980332288e-020 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -0.0004748298337115673 -0.00011696972593459957 -4.8443921670168661 ;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "Chest";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.1;
	setAttr -k on ".fatZ" 1.7600000000000002;
	setAttr ".fatYabs" 0.10000000149011612;
	setAttr ".fatZabs" 0.17599999904632568;
createNode joint -n "FrontLeg1" -p "Chest";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.26564342282514675 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" -0.0030709238556765606 0.052892428756310395 -0.11481111862929826 ;
	setAttr ".r" -type "double3" 4.0711099922732954e-013 -2.4172215579122827e-013 2.8624992133171563e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -119.19250606079 47.550382554694991 63.188431570095247 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "LegAimFront";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.08;
	setAttr ".fatYabs" 0.079999998211860657;
	setAttr ".fatZabs" 0.079999998211860657;
createNode joint -n "FrontLeg2" -p "FrontLeg1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.15630319750021404 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.26564342282514813 1.2212453270876722e-015 1.3045120539345589e-015 ;
	setAttr ".r" -type "double3" -4.1984648742597947e-014 -7.1220176958358e-014 1.2086107789561366e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 61.039122460472036 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "HipFront";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.05000000074505806;
createNode joint -n "FrontLeg3" -p "FrontLeg2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.47635918920635034 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.15630319750021221 4.163336342344337e-016 8.3266726846886741e-017 ;
	setAttr ".r" -type "double3" 1.1608380489202876e-013 -1.3687438480746489e-013 -1.3865680435570575e-028 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 -80.602865824643587 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.04;
	setAttr ".fatYabs" 0.039999999105930328;
	setAttr ".fatZabs" 0.039999999105930328;
createNode joint -n "FrontLeg4" -p "FrontLeg3";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.096076559881614343 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.47635918920635123 -2.2204460492503131e-016 1.27675647831893e-015 ;
	setAttr ".r" -type "double3" 1.2754459783475328e-013 -1.8207407477541499e-013 -2.9261103069464373e-013 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0 0 58.564074298239774 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "FootFront";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "FrontLeg5" -p "FrontLeg4";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.096076559881614343 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.096076559881612122 -5.3082538364890297e-016 4.4408920985006262e-016 ;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.02;
	setAttr ".fatYabs" 0.019999999552965164;
	setAttr ".fatZabs" 0.019999999552965164;
createNode joint -n "Head" -p "Chest";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.2 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.18410564101412683 2.6645352591003757e-015 8.4703294725430034e-022 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -3.203884797218815e-006 0.0002483685935944601 -1.4781150686944315 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr -k on ".fatZ" 1.29;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.064499996602535248;
createNode joint -n "Antenna1" -p "Head";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.099999999999999811 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.11897449038518776 0.099953184711541077 -0.10006864604229222 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 8.3338756655074828 45.16868459935413 8.5673962612055927 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "0";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.03;
	setAttr ".fatYabs" 0.029999999329447746;
	setAttr ".fatZabs" 0.029999999329447746;
createNode joint -n "Antenna2" -p "Antenna1";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.10000000000000003 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.10000000000000087 -4.9960036108132044e-016 -8.3266726846886741e-016 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -1.1848490522504026e-023 -0.023819860345811322 -0.00028576484452583992 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "1";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.03;
	setAttr ".fatYabs" 0.029999999329447746;
	setAttr ".fatZabs" 0.029999999329447746;
createNode joint -n "Antenna3" -p "Antenna2";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.099999999999999867 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.099999999999998757 3.3306690738754696e-016 1.482147737874584e-014 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 2.9621223893252418e-024 0.0057041270073429169 0.00028576483263878397 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "2";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.03;
	setAttr ".fatYabs" 0.029999999329447746;
	setAttr ".fatZabs" 0.029999999329447746;
createNode joint -n "Antenna4" -p "Antenna3";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.099999999999999978 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.10000000000000042 -1.3322676295501878e-015 2.503552920529728e-014 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" -2.3696980933090391e-023 0.02315981950013608 0.00062844323651205767 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.03;
	setAttr ".fatYabs" 0.029999999329447746;
	setAttr ".fatZabs" 0.029999999329447746;
createNode joint -n "Antenna5" -p "Antenna4";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.099999999999999978 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.1000000000000002 4.9960036108132044e-016 -2.7922109069322687e-014 ;
	setAttr ".ro" 3;
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".dl" yes;
	setAttr ".typ" 18;
	setAttr ".otp" -type "string" "3";
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.03;
	setAttr ".fatYabs" 0.029999999329447746;
	setAttr ".fatZabs" 0.029999999329447746;
createNode joint -n "HeadEnd" -p "Head";
	addAttr -ci true -k true -sn "fat" -ln "fat" -dv 0.2 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatY" -ln "fatY" -dv 1 -min 0 -at "double";
	addAttr -ci true -k true -sn "fatZ" -ln "fatZ" -dv 1 -min 0 -at "double";
	addAttr -ci true -sn "fatYabs" -ln "fatYabs" -at "double";
	addAttr -ci true -sn "fatZabs" -ln "fatZabs" -at "double";
	setAttr ".t" -type "double3" 0.38389792835307796 -5.5511151231257827e-016 -4.6586812098986519e-021 ;
	setAttr -l on ".tz";
	setAttr -l on ".rx";
	setAttr -l on ".ry";
	setAttr ".mnrl" -type "double3" -360 -360 -360 ;
	setAttr ".mxrl" -type "double3" 360 360 360 ;
	setAttr ".jo" -type "double3" 0.00048647687496583889 -0.00017075823488923029 6.3225072365311874 ;
	setAttr ".radi" 0.5;
	setAttr -k on ".fat" 0.05;
	setAttr ".fatYabs" 0.05000000074505806;
	setAttr ".fatZabs" 0.05000000074505806;
createNode lightLinker -s -n "lightLinker1";
	setAttr -s 2 ".lnk";
	setAttr -s 2 ".slnk";
createNode displayLayerManager -n "layerManager";
	setAttr ".cdl" 1;
	setAttr -s 2 ".dli[1]"  1;

connectAttr "Root.s" "BackLeg1.is";
connectAttr "BackLeg1.s" "BackLeg2.is";
connectAttr "BackLeg2.s" "BackLeg3.is";
connectAttr "BackLeg3.s" "BackLeg4.is";
connectAttr "BackLeg4.s" "BackLeg5.is";
connectAttr "Root.s" "Tail1.is";
connectAttr "Tail1.s" "Tail2.is";
connectAttr "Tail2.s" "Tail3.is";
connectAttr "Tail3.s" "Tail4.is";
connectAttr "Root.s" "Spine1.is";
connectAttr "Spine1.s" "MiddleLeg1.is";
connectAttr "MiddleLeg1.s" "MiddleLeg2.is";
connectAttr "MiddleLeg2.s" "MiddleLeg3.is";
connectAttr "MiddleLeg3.s" "MiddleLeg4.is";
connectAttr "MiddleLeg4.s" "MiddleLeg5.is";
connectAttr "Spine1.s" "Spine2.is";
connectAttr "Spine2.s" "Chest.is";
connectAttr "Chest.s" "FrontLeg1.is";
connectAttr "FrontLeg1.s" "FrontLeg2.is";
connectAttr "FrontLeg2.s" "FrontLeg3.is";
connectAttr "FrontLeg3.s" "FrontLeg4.is";
connectAttr "FrontLeg4.s" "FrontLeg5.is";
connectAttr "Chest.s" "Head.is";
connectAttr "Head.s" "Antenna1.is";
connectAttr "Antenna1.s" "Antenna2.is";
connectAttr "Antenna2.s" "Antenna3.is";
connectAttr "Antenna3.s" "Antenna4.is";
connectAttr "Antenna4.s" "Antenna5.is";
connectAttr "Head.s" "HeadEnd.is";

// End of bug.ma