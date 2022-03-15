use glyph;
use gl;
use glu;
use gltext;
use gltexture;
use rvtypes;
use commands;
use image;
use math;

documentation: """
This is an rvio overlay script. Overlay scripts are Mu modules which
contain a function called main() with specific arguments which rvio
will supply. This script is not used by rv.

This overlay script also contains an init() function which is called
only once before the first time main() is called. In this case, this
function is used to load a texture (.tiff file) only once.

This module draws a logo/bug image in the output imagery. The options to this 
    module are as follows:

required:
none

optional:
logo_file_path - path to the square power-of-two tiff to be used as the bug/logo
    if "nil" is supplied or no args then a default animal logo from
    the asset library is used.
logo_opacity - how transparent the logo is rendered (default opacity is 0.3)
logo_height - height to render the logo at into each frame (default is the 
    height of the image NOTE: will be resized to nearest power of 2)
logo_x_location - horizontal position of the logo based on native coordinate 
    system of source media (default 10 pixels in)
logo_y_location - veritical position of the logo based on native coordinate 
    system of source media (default 10 pxels in)

----
  rvio in.#.jpg -o out.mov -overlay bug logo.tif 0.4 100 15 100
                                                 opacity height x y
----

The above example will render a 40% opaque bug image 128 pixels tall 15 pixels into the frame and 100 pixels down the frame.
""";

module: mgBug
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
    global float op;
    global int size;
    global int xloc;
    global int yloc;

    documentation: "See module documentation.";

    \: init (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {

        \: log2 (float; float x) { return log(x) / log(2); }

        //
        // Convert the argv list to an options array
        //
        //string tif;
        
        let defaultImage = "Logo_onBlack_512x512.tif",
            tif = defaultImage;
        
        string[] options = string[]();
        let _ : args = argv;
        while (args neq nil)
        {
            let input : rest = args;
            options.push_back(input);
            args = rest;
        }

        //
        // Check for the logo, opacity, size, x position, y position
        //
        print(" [mgBug]ARGUMENTS:mglBug.mu optional [ tif_file|'nil', opacity, height, x, y ]\n");
        print(" [mgBug]SUPPLIED:  %s\n"%(options));
        
        if (options.size() < 1) 
        {
            print("[mgBug]INFO: using default settings %s\n"%(tif));
        }
        else  tif = options[0];
        
        if ( tif == "nil" ) tif = defaultImage;
        {
        	print("[alBug]INFO: using default file:\n\t%s\n"%(tif));
        }
        
        let logo = image(tif);
        let filename = logo.name;

        if (options.size() > 1) op = float(options[1]);
        else                    op = 1.0;

        if (options.size() > 2) size = int(options[2]);
        else                    size = 92;
        //else                    size = logo.height;

        if (options.size() > 3) xloc = int(options[3]);
        else                    xloc = w-size;

        if (options.size() > 4) yloc = int(options[4]);
        else                    yloc = h-size;

        aspect = float(logo.width) / float(logo.height);

        let msize = max(float(size), float(size) * aspect),
            n = int(log2(msize));

        //print("%s %s"%(xloc,yloc));
        //
        //  Resize the image to a power of 2 texture
        //

        if (logo.width != logo.height || 
            pow(2, n) != logo.width || 
            aspect != 1.0)
        {
            let x = log2(float(msize)),
                d = x - n,
                p = int(if d > 0.0 then pow(2, n+1) else pow(2, n));

            print("[alBug]INFO: mgBug.mu Resizing %s to %d x %d texture\n" % (filename, p, p));
            logo = resize(logo, p, p);
        }

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

        texid = createScalable2DTexture(logo);
    }

    //
    //  main is called per-frame
    //

    documentation: "See module documentation.";

    \: main (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {
        setupProjection(w, h);

        let iw      = size,
            ih      = size,
            iy      = yloc,
            ix      = xloc;            

        //print("%s %s"%(ix,iy));
        drawTexture(texid, ix, iy, iw * aspect, ih, op, true);
        glDisable(GL_TEXTURE_2D); //important
    }
}
