//Maya ASCII 2016 scene
//Name: animation.ma
//Last modified: Sun, Aug 30, 2015 03:32:22 PM
//Codeset: 1252
requires maya "2016";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2016";
fileInfo "version" "2016";
fileInfo "cutIdentifier" "201502261600-953408";
fileInfo "osv" "Microsoft Windows 8 Business Edition, 64-bit  (Build 9200)\n";
createNode animCurveTU -n "CURVE1";
	rename -uid "7DDFBAF5-463D-2ADE-1C1F-AFA670D84DF9";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 5 10 5;
createNode animCurveTU -n "CURVE2";
	rename -uid "D07A3FD1-4A0C-2783-AEC6-239418A3F7CD";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE3";
	rename -uid "3AF34378-4733-0383-AA24-14B1D20E13E6";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.25 10 0.42958527814637792;
createNode animCurveTU -n "CURVE4";
	rename -uid "30428A38-4DCF-7407-59CF-1489BBBE7C0A";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.5 10 0.85917055629275585;
createNode animCurveTA -n "CURVE5";
	rename -uid "05B76EED-4283-6B67-6331-F2946D501359";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 45 10 30.81018202226841;
createNode animCurveTA -n "CURVE6";
	rename -uid "3C57E014-4C1C-4946-2894-E29D3AB9DA43";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 90 10 149.70880463068096;
createNode animCurveTL -n "CURVE7";
	rename -uid "DDD8DEA5-45F0-897B-2B2B-839A6E7C821D";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 0;
createNode animCurveTL -n "CURVE8";
	rename -uid "DEF6EACF-4D2F-972C-271C-11829CB508F3";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 8 10 8;
createNode animCurveTL -n "CURVE9";
	rename -uid "1B9641AF-4757-52FE-7996-E7A161FF040A";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 -12 10 11.214436147065292;
createNode animCurveTU -n "CURVE10";
	rename -uid "04C5468B-4450-4B6C-C8FA-E8838308111D";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE11";
	rename -uid "21E1020F-4358-06D3-C269-B4B9A727A1FD";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.666 10 0.666;
createNode animCurveTU -n "CURVE12";
	rename -uid "9CF53A9D-4BDA-0D2B-DB1B-369C346AF00D";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 10;
createNode animCurveTU -n "CURVE13";
	rename -uid "DAE2017B-4EFE-1912-7FD2-7E85BB67EC64";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.2 10 0.2;
createNode animCurveTU -n "CURVE14";
	rename -uid "12AF1651-41D3-068E-5326-21B372A92563";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1.4 10 1.4;
createNode animCurveTU -n "CURVE15";
	rename -uid "2973C58C-4E2F-E317-04C3-08BF27BE4E73";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 2.6 10 2.6;
createNode animCurveTU -n "CURVE16";
	rename -uid "64B1FCC6-4680-1CFD-2FAB-BBA8525D479C";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTL -n "CURVE18";
	rename -uid "C49128E2-444D-2CC1-9BF1-4A99CAB907BE";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 15;
// End