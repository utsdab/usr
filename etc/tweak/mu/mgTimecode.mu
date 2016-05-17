use glyph;
use gl;
use glu;
use gltext;
use rvtypes;
use commands;


documentation: """
		This is an rvio overlay script. Overlay scripts are Mu modules which
		contain a function called main() with specific arguments which rvio
		will supply. This script is not used by rv.
		
      Attempts to produce timecode and burn it into every single frame
      input is opacity,grey,size,offset,rate,x,y
      
      ----
        rvio in.#.jpg -o out.mov -overlay mgTimecode .4 1.0 30.0
      ----
      
      The above example will render a timecode TC 00:00:00:00 in the bottom centre
      corner of the image with an opacity of 0.6 a greyscale value of 1
      (white) and point size 30.0.
      
      To change the font you must hack the frameburn.mu file to call
      gltext.init() prior to setting the font size. The argument to
      gltext.init() should be a path to a .ttf file. On the mac you need to
      make sure this file is not "old" style -- 
      it needs to have all of the font data in the data fork of the file.
      
      """;
    		  


module: mgTimecode
{
	documentation: "See module documentation.";
	global int counter = -1;
	
	
    \: main (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv,
             [(string,string)] keyvals)
    {
        	
		setupProjection(w, h);
		glEnable(GL_BLEND);
		glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
		
		
		//print(" ARGUMENTS: alTimecode.mu  [opacity,grey,size,offset,rate,xloc,yloc ]\n");
		//print(" EXAMPLE  : -leader -mgTimecode 1.0 1.0 20 1000 24.0 0.5 0.5\n");
		//print(" SUPPLIED :  %s\n"%(argv));
		
		let _ : offset :  _  = argv;
		let op = 0.6, grey = 1.0, size =  h / 30; 
		
		gltext.size(int(size));
        
		let g      = float(grey);
        let c      = Color(g, g, g, float(op));
        
        glColor(c);
        gltext.color(c);		
        
        
        
        
        let rate = fps(),
			newframe = frame + int(offset);
		
		int dispframe = newframe % int(rate);
		int seconds   = (newframe/rate) % 60;
		int minutes   = ((newframe/rate)/60) % 60;
		int hours     = (((newframe/rate)/60)/60) % 24;

		//let timecodeformat = "TC 00:00:00:00";
		let text = "TC %0.2d:%0.2d:%0.2d:%0.2d" % (hours, minutes, seconds, dispframe);
		
		
		let b = gltext.bounds("TC 00:00:00:00"),
			height = b[1] + b[3],
			width  = b[0] + b[2],
			x      = int(  (w/2.0)  - (width/2.0) ) ,
			y	   = int(   height * 2.0   );
		
		
		
		
		if (counter != -1)
		{
			let counter = newframe;
		}
		else
		{
			let counter = counter;
		}
        
		for_each (keyval; keyvals)
        {
            let (key, value) = keyval;

            if (key == "missing-image")
            {
                //
                //  Draw text red if a frame was missing
                //

                gltext.color(Color(1,0,0,float(op)));
            };
        }		

        gltext.writeAt(x, y, text);
    }
}