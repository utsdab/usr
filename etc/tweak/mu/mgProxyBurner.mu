use glyph;
use gl;
use glu;
use gltext;
use gltexture;
use rvtypes;
//use rvui;
use commands;
use image;
use math;
//use extra_commands;


documentation: """ 

Matt Gidney Proxy Info  

init() is called only once before the first call to main. 
It gets the same arguments that main does, but you can do
initialization here without worrying about when/how its called

In this case we'll load the image and make a texture
out of it so we don't have to do that every frame.

This overlay is based upon the bug and frameburn overlays supplied
The idea is that we divide the image up into zones so that we can pass
info into the zones for specific purposes.
           
	                                                               
Input is assumed to be an asset that has a .xinfo file containing.....                                                          
<xinfo>
   <checkin>
      <user>
      <timestamp>
      <comment>
	   <asset name= version= versiontype= >  
      <lpath>
	      <rpath> 
      <data name= type= >
           <src>
           <size>
   <dependencies>
       <comment> 

USAGE:  rvio input.mov -o output.mov -overlay alProxyBurn ................

""";

module: mgProxyBurner
{    

    //
    //  init() is called only once before the first call to main. 
    //  It gets the same arguments that main does, but you can do
    //  initialization here without worrying about when/how its called
    //
    //  In this case we'll load the image and make a texture
    //  out of it so we don't have to do that every frame.
    //
    
    global int texid;
    global float aspect;
	
	documentation: "See module documentation.";

    \: init (void; int w, int h, 
    		 //int W, int H,
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {

        \: log2 (float; float x) { return log(x) / log(2); }

        let op  = 1.0, 
            size 	= 128.0,
            tif 	= "Logo_onBlack_512x512.tif",
            logo  	= image(tif),
            filename 	= logo.name,
            unpremult 	= true;

        aspect 	= float(logo.width) / float(logo.height);

        let msize = max(float(size), float(size) * aspect),
            n = int(log2(msize));

        //  Some logo assets are here:
        //     /jobs/alfx/al_library/assets/still/animal/logo/small_001/still_animal_logo_small_001_v008
        //  Resize the image to a power of 2 texture
        //

        if (logo.width != logo.height || pow(2, n) != logo.width ||  aspect != 1.0)
        {
            let x = log2(float(msize)),
                d = x - n,
                p = int(if d > 0.0 then pow(2, n+1) else pow(2, n));

            print("INFO: Resizing %s to %s x %s texture\n" % (filename, p, p));
            logo = resize(logo, p, p);
        }
        
        if (unpremult)
        {
            print("INFO: Unpremultiplying %s\n" % filename);
            //
            //  Un premultiply the image data for GL
            //

            for (int y = 0; y < logo.height; y++)
            {
                for (int x = 0; x < logo.width; x++)
                {
                    int index = y * logo.height + x;
                    let p = logo.data[index];
                    logo.data[index] = Color(p.x / p.w, p.y / p.w, p.z / p.w, p.w);
                }
            }
        }

        texid = createScalable2DTexture(logo);
    }
    
    \: sourceImageStructure ((int, int, int, int, bool, int); string n, string m = nil)
    {
        //
        //  This is back-compatibility function: it now returns the uncrop
        //  w and h instead of possibly croped w, h
        //

        let info = sourceMediaInfo(n, m);

        if (info neq nil)
        {
            return (info.uncropWidth,
                    info.uncropHeight,
                    info.bitsPerChannel,
                    info.channels,
                    info.isFloat,
                    info.planes);
        }
        else
        {
            return nil;
        }
    }
    
    //
    //  main is called per-frame
    //
	
	documentation: "See module documentation.";
    
    \: main (void; int w, int h, 
             //int W, int H,
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,   
             [string] argv)
	              	     
    {
        let text   	= "%04d" % frame,
            b      	= gltext.bounds("0000"),
            b1  	= gltext.bounds("1280 x 720"),
            sh     	= b[1] + b[3],
            sw     	= b[0] + b[2],
            sw2 	= b1[0] + b1[2],
            margin 	= h/45,
            margin2 = margin/2,
	        op     	= 1.0,
	        size   	= h/10,
            x      	= (w - sw)/2,
            y      	= h - sh - margin,
            y2     	= y - margin,
            y3     	= y2 - margin,
            y4		= sh,
            g      	= 1.0,
            z1 		= margin/2,
	        z2      = margin,
	        z3      = w-sw2,
            c       = Color(g, g, g, 1.0),
            c1      = Color(g, g, g, 0.8), 
            c2      = Color(g, g, g, 0.66),
	        c3      = Color(g, g, g, 0.2),
	        iw      = int(size),
            ih      = int(size),
            iy      = h - ih  - 2,
            ix      = w - iw - 2,
            
	        asset   = getStringProperty("#RVFileSource.media.movie"),
	   		//   name/name2/root.1234.exr
	   		
	   		//width  = getIntProperty("#RVRenderedImageInfo.width"),
	   		//height = getIntProperty("#RVRenderedImageInfo.height"),
	        
	        getfilebit  = asset[0].split("/"),
	        n           = getfilebit.size(),					
	        //   name/name2/root.1234.exr
	        
	        getfilebitroot = getfilebit[n-1].split(".")   	
	        //   root.1234.exr
	        ;
	        
		setupProjection(w, h);
		

		//for_each (ri; sourceRendered())
		//{
		//    let n = sourceGeometry(ri.name),
		//        width = sourceGeometry(ri.width),
		//        height = sourceGeometry(ri.height),
		//    print("INFO: Source %s %s %s \n" % (n, width, height));
		//}

 
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        
        // set draw formatting
        gltext.size(25);
		glColor(c);
        gltext.color(c);
        
        // draw frame counter
        gltext.writeAt(x, y, text);
        
        // draw Ownership
        glColor(c1);
		gltext.writeAt(z2, y, "UTS Animation");
		
		// draw file name root
		gltext.color(c2);
		gltext.size(15);
		gltext.writeAt(z2, y3, (getfilebitroot[0]));
		
		// draw dimensions
		gltext.color(c3);
		gltext.writeAt(z1, y4, ("%s x %s " % (w,h) ) );
		//gltext.writeAt(z1, y4, ("%s + %s : %d + %d" % (w,h,width[0],height[0]) ) );
		//(w + " x "+ h + " : " + assetWidth + " x "+ assetHeight )  );		
	 
		// draw Logo
        drawTexture(texid, ix, iy, iw * aspect, ih, float(op), true);
    }
}
