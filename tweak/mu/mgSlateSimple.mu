use glyph;
use gl;
use gltext;
use rvtypes;
use commands;

documentation: """
This is an rvio leader script. A leader script has a main() function
which is called to render a complete frame for output.

The simpleslate script creates a slate. 

Most companies have some type of environment set up which describes 
the current shot, show, etc. So normally, you'd want the slate function 
to get values from there or a database somehow

In this case, we're going to pass all the information in the argv
list.  the arguments will take the form:

----
    name=value
----

So for example: "Artist=John Doe" "Show=Blockbuster" "Shot=BestShot-01"
will render each piece of data on its own line.  For multiple values
(like multiple Artists) you can add more =values:

----
    "Artists=John Doe=Jane Doe"
----

This code calls some RV ui functions to format the results like the
image info HUD widget.

Example usage:

----
rvio in.#.jpg -o out.mov -leader mgSimpleslate 
"FilmCo"  "Artist=Jane Q. Artiste" "Shot=S01" "Show=BlockBuster"  "Comments=You said it was too blue so I made it red"
----

"""

module: mgSlateSimple
{
    global byte[32,32] halftone_bitmap = {
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55, 
        0xaa, 0xaa, 0xaa, 0xaa, 0x55, 0x55, 0x55, 0x55 };

    \: main (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {
        gltext.init(); // default font
        // note: you could do gltext.init("/path/to/font.ttf") for 
        // a custom font.

	    glViewport(0, 0, w, h);

        \: reverse ((string,string)[] s)
        {
            (string,string)[] n;
            for (int i=s.size()-1; i >= 0; i--) n.push_back(s[i]);
            n;
        }

        //
        //  This uses a list pattern match to get the arguments.
        //
        //  ignore the fist list element (its always "simpleslate")
        //  this is done using the _ pattern which discards that place.
        //
        //  the second is the text to draw sideways.
        //
        //  the rest are name=val lines. 
        //
        

        
        
        string sidetext = nil;
        [string] lines  = nil;
        let _ : theRest = argv,
                m = w / 24;
        
        print(" ARGUMENTS: alSlateSimple.mu optional \"FilmCo\"  \"Artist=Jane\" \"Shot=S01\" \"Show=Job\"  \"Comments=Something\"\n");
        print(" EXAMPLE  : -leader alSlateSimple FilmCo Artist=Jane Shot=S01 Show=Job  Comments=Something\n");
        print(" SUPPLIED :  %s\n"%(theRest));
        
        if (theRest neq nil) 
        {
            let s : l = theRest;
            sidetext = s;
            lines = l;
        }

        StringPair[] pairs;

        for_each (arg; lines)
        {
            let nv = string.split(arg, "=");

            if (nv.size() > 1)
            {
                for_index (i; nv)
                {
                    if (i == 1) pairs.push_back((nv[0], nv[i]));
                    else if (i > 1) pairs.push_back(("", nv[i]));
                }
            }
            else
            {
                pairs.push_back(("", nv.front()));
            }
        }

        setupProjection(w, h);

        //
        //  If you want an image background you could do that here
        //  see the "bug" example on how to load a .tif file and use
        //  it as a texture.
        //

        glClearColor(.18, .18, .18, 1.0);
        glClear(GL_COLOR_BUFFER_BIT);

        //
        //  Draw the left side "company name"
        //

        let n = 10, sw = 50;

        \: drawClapboardStripes (int polytype)
        {
            for (int i = -1; i < n; i++)
            {
                float sc = ((i+1) % 2) * .3 + .1;
                glColor(Color(sc, sc, sc, 1));
                
                let hn = h / n,
                    h0 = hn * i,
                    h1 = hn * (i+1),
                    h2 = hn * (i+2);

                glBegin(polytype);
                glVertex(0, h0);
                glVertex(sw, h1);
                glVertex(sw, h2);
                glVertex(0, h1);
                glEnd();
            }
        }

        glEnable(GL_BLEND);
        glEnable(GL_LINE_SMOOTH);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        drawClapboardStripes(GL_POLYGON);
        drawClapboardStripes(GL_LINE_LOOP);

        //
        //  Draw some ramps and colors for gamma purposes
        //

        glColor(Color(0,0,0,1));

        glBegin(GL_POLYGON);
        glVertex(w - 20, 0);
        glVertex(w, 0);
        glColor(Color(1,1,1,1));
        glVertex(w, h);
        glVertex(w - 20, h);
        glEnd();

        glDisable(GL_BLEND);

        glColor(Color(0,0,0,1));
        glBegin(GL_POLYGON);
        glVertex(w - 30, 0); glVertex(w - 20, 0);
        glVertex(w - 20, h); glVertex(w - 30, h);
        glEnd();

        glEnable(GL_POLYGON_STIPPLE);
        glPolygonStipple(halftone_bitmap);

        glColor(Color(1,1,1,1));
        glBegin(GL_POLYGON);
        glVertex(w - 30, 0); glVertex(w - 20, 0);
        glVertex(w - 20, h); glVertex(w - 30, h);
        glEnd();

        glDisable(GL_POLYGON_STIPPLE);

        gltext.size(10);
        gltext.color(.5, .5, .5, 1);

        for_each (gamma; [2.2, 1.8, 1.0])
        {
            let gh = math.pow(.5, 1.0 / gamma);
            gltext.writeAt(w-60, h * gh - 3, "%1.1f" % gamma);

            glColor(Color(.5,.5,.5,1));
            glBegin(GL_LINES);
            glVertex(w-45, h * gh); 
            glVertex(w-30, h * gh);
            glEnd();
        }
        
        Color[] colors = 
        {
            {0, 0, 0, 1},
            {1, 1, 1, 1},
            {1, 1, 0, 1},
            {1, 0, 1, 1},
            {0, 1, 1, 1},
            {0, 0, 1, 1},
            {0, 1, 0, 1},
            {1, 0 ,0, 1},
        };

        for_index (i; colors)
        {
            glColor(colors[i]);
            glBegin(GL_POLYGON);
            glVertex(w - 40 - i * 20 - 40, h - 20);
            glVertex(w - 20 - i * 20 - 40, h - 20);
            glVertex(w - 20 - i * 20 - 40, h);
            glVertex(w - 40 - i * 20 - 40, h);
            glEnd();
        }

        //
        //  Draw the rotated text
        //

        let bh = 0;
        if (sidetext neq nil)
        {
            let sidesize = math.min(fitTextInBox(sidetext, h * .8, 80), 80);

            glMatrixMode(GL_MODELVIEW);
            glPushMatrix();
            glRotate(90, 0, 0, 1);
            gltext.size(sidesize);
            gltext.color(.5, .5, .6, 1);

            let b = gltext.bounds(sidetext),
                bw = b[0] + b[2];

            bh = b[1] + b[3];

            gltext.writeAt((h - bw) / 2,        // in rotated space
                        -(bh + 20) - sw, 
                        sidetext);
            glPopMatrix();
        }

        if (pairs.size() != 0)
        {
            let leftmargin = math.abs(-(bh + 20) - sw);

            //
            //  Text
            //

            int tsize = math.min(100, fitNameValuePairsInBox(pairs, 
                                                            m, 
                                                            w - leftmargin - 60 - m, 
                                                            h * .9));
            gltext.size(tsize);
            let drawPairs = reverse(pairs);
            let (tbox, _, _, _) = nameValuePairBounds(drawPairs, m);
            
            //
            //  Center it
            //

            let x = (w - leftmargin - tbox.x - m - 60) / 2 + leftmargin,
                y = (h - tbox.y) / 2;

            drawNameValuePairs(drawPairs, 
                            Color(.75,.75,.75,1),
                            Color(0,0,0,1),
                            x, y, m,
                            0, 0 ,0, 0, true);
        }
    }
}
