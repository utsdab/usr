use glyph;
use gl;
use glu;
use gltext;
use gltexture;
use rvtypes;
use commands;
use image;
use math;
use io;
require qt;

documentation: """ 

Matt Gidney Proxy Info  

This overlay will write text and boxes to screen
build up args like this

text:'some text',x,y,size,red,green,blue,alpha
box:x,y,w,h,red,green,blue,alpha

-overlay mgProxyBurner text:'mattg',60,60,20,0,1.0,0,1.0 text:'gidney',200,200,
40,0,1.0,1.0,1.0 box:300,300,100,100,0,0,1.0,0.5

This overlay is based upon the bug and frameburn overlays supplied
The idea is that we can pass a simple templte in to be written to screen
USAGE:  rvio input.mov -o output.mov -overlay alProxyBurn ................

""";

module: mgProxyData
{    
    //  init() is called only once before the first call to main. 
    //  It gets the same arguments that main does, but you can do
    //  initialization here without worrying about when/how its called
    //
    //  In this case we'll load the image and make a texture
    //  out of it so we don't have to do that every frame.
    
    global float aspect;
    global string[] theRest;
    global string[][] dataArray;
    global string datafile;
    global int frame;
    global bool debug = false;

    
    /*  format tolerant of spaces and tabs and comments behind a hash
    # DATA WRITTEN OUT FOR PROXY BURNIN
    #
    #
    FRAME,		S_DISP,	N_DISP,	F_DISP,	IA_DST,     Z_DST,	FSTOP,	FOCAL
    1.0,		0.5,	0.9,	1.2,	0.9,	    22.0,	22.0,	60.0
    2.0,		0.5,	0.91,	1.1,	0.9,		22.0,	22.0,	60.0
    
    */

	class: DynamicData
    {   
        method: loadFile (bool; string file)
        {

        	//print("\n[alProxyData] method\t: DynamicData.loadFile %s"%(file));
        	if (io.path.exists(file))
            {
            	print("\n[alProxyData] DataFile exists");
            	datafile = file;
            	return true;
            }
            else
            {
            	print("\n[alProxyData] Data File doesnt exist");
            	datafile = nil;
            	return false;
            }
        } 
               
        method: getFile (string;)
        {	
            return datafile;
        }
        
        method: buildStringArray (void; )            
        {
            // This is a  write to screen function
            // format = [info,x,y,size,color[]]

        	//print("\n[alProxyData] method\t: DynamicData.buildStringArray");

        	string[][] _dataArray;
            int count = 0;
            
            //let filename = datafile,
            let infile 	 = ifstream(datafile),
                cnFile 	 = qt.QFileInfo(datafile).canonicalFilePath(),
                sdir   	= path.dirname(path.dirname(cnFile)),
                lines  	= read_all(infile).split("\n\r"),
                title  	= 0;   
                    
            for_index (i; lines)
            {
                let line  = lines[i];
                // remove spaces in line
                let stuff= line.split(" ");
                string nospace;
                for_index (i;stuff) { nospace+=stuff[i]; }
                //nospace = string.join()
                // remove tabs in line
                stuff= nospace.split("\t");
                string notab;
                for_index (i;stuff) { notab+=stuff[i]; }               
                
                let parts = notab.split(",");            
                
                
                if (parts.size() >= 2 && parts[0][0] != "#") 
                {
                	// echo the data in the text file

                	//print("\n");

                	_dataArray.push_back( string[]() );
                    for_each (part;parts)
                    {
                        _dataArray[count].push_back(part);
  
						/*   _dataArray[][]   looks like this
						FRAME 	S_DISP 	N_DISP 	F_DISP 	IA_DST 	Z_DST 	FSTOP 	FOCAL 	
						1.0 	0.5 	0.9 	1.2 	0.9 	22.0 	22.0 	60.0 	
						2.0 	0.5 	0.91 	1.1 	0.9 	22.0 	22.0 	60.0 	
						3.0 	0.5 	0.92 	1.0 	0.9 	22.0 	22.0 	60.0 	
						4.0 	0.5 	0.93 	1.0 	0.9 	22.0 	22.0 	60.0 
						*/
                        
                        // echo the data in the text file
                        //print("%s \t"%( _dataArray[count].back()) );


                    }
                    count +=1;
                }
            }
            dataArray = _dataArray; 
         }        
         
        method: getStringArray (string[][]; )               
            {	
        		//print("\n[alProxyData] method: DynamicData.getStringArray %s"%(dataArray));
        		return dataArray; 
            }  
    }
        
    \: init (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {
        let _ : theRest = argv;
        string[] argArray;
        // get list into an array as the file is the last element
        for_each (arg; theRest)
        {
        	argArray.push_back(arg);
        }

        
        print("\n[alProxyData] ARGUMENTS: alProxyStaticDataDev.mu optional" );
        print("\n                         [text:'info',x,y,size,red,green,blue,alpha]");
        print("\n                         [dtext:'KEY=name',x,y,size,red,green,blue,alpha]");        
        print("\n                         [box:x,y,width,height,red,green,blue,alpha]");
        print("\n                         [dfile:'data file path']");        
        print("\n[alProxyData] SUPPLIED : %s"%( theRest ) );
        //print("\n[alProxyData] DATAFILE: %s"%argArray.back());
        let datafile = argArray.back();
        let D=DynamicData(),
        	dataOK=D.loadFile(datafile);
        
        if (dataOK)
        {
			print("\n[alProxyData] DATAFILELOADED   : %s"%( D.getFile()));
			print("\n[alProxyData] BUILDING : %s"%( "stringArray"));
			
			D.buildStringArray();
			print("\n[alProxyData] DONE \n" );
			let dataArray = D.getStringArray();  
			//print(">>>>>>>>>\n%s"%(D.getStringArray()));
        }
    }
    
    documentation: "Basically follows where, what, how";
    
    \: writeText (void;  string[] format )
                        
        {
            ///
            /// This is a  write to screen function
            /// format = [info,x,y,size,color[]]
            
            let info = format[0];
            
            if (format.size() == 8)
            {
                int x = int(format[1]);
                int y = int(format[2]);
                int size = int(format[3]);
                Color color = Color( float(format[4]),
                                     float(format[5]),
                                     float(format[6]),
                                     float(format[7]) );            

                //print("\nDEBUG[alProxyData]: writeText: %s %s %s %s %s" % (info,x,y,size,color));

                
                if (info neq nil)
                {
                    gltext.size(size);
                    gltext.color(color);
                    gltext.writeAt( x, y , info);
                }
            }
            else 
            {
            	print("\nDEBUG[alProxyData]: writeText: %s got %s" % ("Expecting 8 args",format.size()));
            }
        }


    documentation: "Writes Dynamic data from a formatted file";
          
     \: writeTextFromFile(void; string[] format, float frame)		 
    	//
    	//      dtext:	  'IA_DST=IA',650,60,	15,	0.6, 0.6, 0.6, 1.0 
    	//      IA_DST    is the key in the file and IA is the substitution  string 
    	//		format    is [ x y w h r g b a ]
		//
        {   
    	 	string[] keyNames;
            if (format.size() == 8)
            {
            	int realframe = float (format[0]);
                int x = int(format[1]);
                int y = int(format[2]);
                int size = int(format[3]);
                Color color = Color( float(format[4]),
                                     float(format[5]),
                                     float(format[6]),
                                     float(format[7]) );  
                let debug=true;
                


                //print("\nDEBUG[alProxyData]: writeTextFromFile: %s : %s %s %s %s %s %s" % (frame,realframe,x,y,size,color));


                int index = 0;                

                //print("\nDEBUG[alProxyData]: data KEYS data[0]: %s" % (dataArray[0]));
                
                int matchedKey;
                
                //
                // handle renaming of key data titles by NAME=NEWNAME
                //

                keyNames=format[0].split("=");
                if (keyNames.size() < 2)
                {
                	keyNames.push_back("");
                }
                     
                for_index (i;dataArray[0])
                {	
                	if (dataArray[0][i] == keyNames[0])
                	{
                		matchedKey = i;
                		//print("\nDEBUG: found your KEYWORD %s %s" % (dataArray[0][i], i) );
                		//print("\nDEBUG: name munging %s %s %s=>%s"% (dataArray[0][i],format[0],keyNames[0],keyNames[1]));

                	}

                }
                try
                {   
                	if ( matchedKey != "nil")
                	{
						//print("\nDEBUG: data from : %s " % (datafile) );
						//print("\nDEBUG:    format : %s " % (format) );
						//print("\nDEBUG:      data : %s " % (dataArray[frame][matchedKey]) );

						gltext.size(size);
						gltext.color(color);
						gltext.writeAt( x, y , ("%s %s"%(keyNames[1],dataArray[frame][matchedKey])));
                	}
                	else
                	{ throw ("No matching Key"); }
                }
                catch (exception exc)
                {
                    print("\n[alProxyData] exception thrown");
                }
            }
            else 
            {
                print("\nWARNING[alProxyData]: Couldnt write format wrong: %s " % ( keyNames[0] ) );
            }
        }


    \: writeBox (void;  string[] format)
    	// format is [ x y w h r g b a ]
        {  
            if (format.size() == 8)
            {
                int x = int(format[0]);
                int y = int(format[1]);
                int w = int(format[2]);
                int h = int(format[3]);
                Color color = Color( float(format[4]),
                                     float(format[5]),
                                     float(format[6]),
                                     float(format[7]) ); 

                //print("\nDEBUG[alProxyData]: writeBox: %s %s %s %s %s" % (x,y,w,h,color));

                {
                    glColor(color);
                    glBegin(GL_QUADS);
                    glVertex(x, y);
                    glVertex(x+w, y);
                    glVertex(x+w, y+h);
                    glVertex(x, y+h);         
                    glEnd();
                }
            }
            else 
            {

            	print("\nDEBUG[alProxyData]: writeBox: %s " % ("Failed"));

            }
       
        }
    
    
    documentation: "Writes a square that is scaled dynamically - like a bar graph";
    
    \: writeBarFromFile (void; string[] format, float frame)		 
		//
		//      dbox:	  'IA_DST',650,60,	15,	0.6, 0.6, 0.6, 1.0 
		//      dbox:	  key,     x,  y,  basedimension,  scale, 0.6, 0.6, 0.6, 1.0 				
		//      IA_DST    is the key in the file to read
		//		format    is [ x y w h r g b a ]
		//      THIS IS WIP!!!
		{   
			string[] keyNames;
			if (format.size() == 8)
			{
				int realframe = float (format[0]);
				int x = int(format[1]);
				int y = int(format[2]);
				int size = int(format[3]);
				Color color = Color( float(format[4]),
									 float(format[5]),
									 float(format[6]),
									 float(format[7]) );  

				//print("\nDEBUG[alProxyData]: writeText: %s : %s %s %s %s %s %s" % (frame,realframe,x,y,size,color));

				int index = 0;
				//print("\nDEBUG[alProxyData]: data KEYS data[0]: %s" % (dataArray[0]));
				int matchedKey;
				
				// handle renaming of key data titles by NAME=NEWNAME
				keyNames=format[0].split("=");
				if (keyNames.size() < 2)
				{
					keyNames.push_back("");
				}
					 
				for_index (i;dataArray[0])
				{	
					if (dataArray[0][i] == keyNames[0])
					{
						matchedKey = i;

						//print("\nDEBUG[alProxyData]: found your KEYWORD %s %s" % ( dataArray[0][i], i) );
						//print("\nDEBUG[alProxyData]: name munging %s %s %s=>%s"% ( dataArray[0][i],format[0],keyNames[0],keyNames[1]));

					}
				}
				try
				{   
					if ( matchedKey != "nil")
					{

						//print("\nDEBUG[alProxyData]: data from : %s " % (datafile) );
						//print("\nDEBUG[alProxyData]:    format : %s " % (format) );
						//print("\nDEBUG[alProxyData]:      data : %s " % (dataArray[frame][matchedKey]) );

						gltext.size(size);
						gltext.color(color);
						gltext.writeAt( x, y , ("%s %s"%(keyNames[1],dataArray[frame][matchedKey])));
					}
					else
					{ throw ("No matching Key"); }
				}
				catch (exception exc)
				{
					print("\n[alProxyData] exception thrown");
				}
			}
			else 
			{
				print("\nWARNING[alProxyData]: Couldnt write: %s " % ( keyNames[0] ) );
			}
		}

    
    
        
    \: writeSomething (void; string type, string[] format, float frame )
        {
    		if (debug)
    		{
    			print("\nDEBUG[alProxyData]: writeSomething: %s %s %s" % (type, format, frame));
    		}
        	case (type)
            {
                "text" -> {  writeText(format); }
                "box"  -> {  writeBox(format); }
                "dtext"-> {  writeTextFromFile(format,frame); }
                "dbox" -> {  writeBarFromFile(format,frame); }
            }
        }
      
    //
    //  main is called per-frame
    //  need to figure out how to call from a file per frame
    //
	
	documentation: "See module documentation";
    
    \: main (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,   
             [string] argv)
	              	     
    {
        let _ : theRest = argv;
        [string] lines = nil;
        bool noerror = true;
            
	    setupProjection(w, h);
	
        glDisable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        string[][] zo;
        int count = 0;


        for_each (arg; theRest)
        {
        	// text:'scene_060',500,60,20,1.0,1.0,1.0,1.0 \
        	// dtext:'IA_DST=IA',650,60,15,0.6,0.6,0.6,1.0 \

        	string withoutspaces;
        	let spaces = string.split(arg, " ");
            for_index (i;spaces) { withoutspaces+=spaces[i]; }               
             
        	let bits = string.split(withoutspaces, ":");
            let smallbits = string.split(bits.back(), ",");
            zo.push_back( string[]() );
            zo[count].push_back(bits.front());
            
            for_each (smallbit;smallbits)
            {
                zo[count].push_back(smallbit);
            }
            writeSomething( zo[count].front(), zo[count].rest(), frame );
            count += 1;
        }
    }
}

