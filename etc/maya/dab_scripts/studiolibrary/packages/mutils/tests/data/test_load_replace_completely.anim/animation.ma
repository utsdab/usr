//Maya ASCII 2016 scene
//Name: animation.ma
//Last modified: Tue, Aug 09, 2016 08:47:08 AM
//Codeset: 1252
requires maya "2016";
currentUnit -l centimeter -a degree -t film;
fileInfo "application" "maya";
fileInfo "product" "Maya 2016";
fileInfo "version" "2016";
fileInfo "cutIdentifier" "201502261600-953408";
fileInfo "osv" "Microsoft Windows 8 Business Edition, 64-bit  (Build 9200)\n";
createNode animCurveTU -n "CURVE1";
	rename -uid "07400D46-41EF-56B5-ABE2-FCB3FDC705F2";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 5 10 5;
createNode animCurveTU -n "CURVE2";
	rename -uid "E2B997BA-4A97-2EF7-C65E-E7BD483688D6";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE3";
	rename -uid "2AF61E8F-4817-A910-3417-6B9823CED36D";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.25 10 0.42958527814637792;
createNode animCurveTU -n "CURVE4";
	rename -uid "61ED901E-4BFA-A417-6F1A-A89854BAE1F9";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.5 10 0.85917055629275585;
createNode animCurveTA -n "CURVE5";
	rename -uid "25E543E0-4233-B654-6DC2-C980CC9ED600";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 45 10 30.81018202226841;
createNode animCurveTA -n "CURVE6";
	rename -uid "3921DD56-44E6-E6D7-DB1B-C28209F3157E";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 90 10 149.70880463068096;
createNode animCurveTL -n "CURVE7";
	rename -uid "5EE5D458-498D-AD10-196B-0F99DE4A9F97";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 0;
createNode animCurveTL -n "CURVE8";
	rename -uid "81FBC4EF-479F-58C1-D24D-859C16E01BA1";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 8 10 8;
createNode animCurveTL -n "CURVE9";
	rename -uid "898B5C26-448D-366F-0E63-5082268110FB";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 -12 10 11.214436147065292;
createNode animCurveTU -n "CURVE10";
	rename -uid "139725A4-4C9A-C99F-2E9F-AF91BC3F67E9";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTU -n "CURVE11";
	rename -uid "1A5281F1-4252-087B-1631-9998C170D33B";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.666 10 0.666;
createNode animCurveTU -n "CURVE12";
	rename -uid "3B543491-429F-763A-0075-4EB85B2E50AB";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 10;
createNode animCurveTU -n "CURVE13";
	rename -uid "8532CE01-49F8-571C-2D65-A98F3427EBF0";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0.2 10 0.2;
createNode animCurveTU -n "CURVE14";
	rename -uid "D9767D2E-4DFC-F089-183D-789D8B697CF1";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1.4 10 1.4;
createNode animCurveTU -n "CURVE15";
	rename -uid "73706920-4309-DAEE-AE70-CAAF4C1D68FB";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 2.6 10 2.6;
createNode animCurveTU -n "CURVE16";
	rename -uid "70D851D4-43F8-72F5-0327-E28AEB0F174C";
	setAttr ".tan" 9;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 1 10 1;
	setAttr -s 2 ".kot[0:1]"  5 5;
createNode animCurveTL -n "CURVE18";
	rename -uid "716232B6-4903-7906-472A-569BBA3146DA";
	setAttr ".tan" 18;
	setAttr ".wgt" no;
	setAttr -s 2 ".ktv[0:1]"  1 0 10 15;
// End