use glyph;
use gl;
use gltext;
use rvtypes;
use commands;

documentation: """
This is an rvio overlay script. Overlay scripts are Mu modules which
contain a function called main() with specific arguments which rvio
will supply. This script is not used by rv.

Draws a water mark centered on the image. The script takes two
arguments: the string to render as a watermark and the opacity of the
watermark. The font size is determined by the bounding box of the
characters in the input string. So large strings are scaled down to
fit into the image.

----
  rvio in.#.jpg -o out.mov -overlay mgBottomLine "Topline" "Bottomline" .25
----

Draws small across the bottom of the frame
""";

module: mgBottomLine
{
    documentation: "See module documentation.";

    \: main (void; int w, int h, 
             int tx, int ty,
             int tw, int th,
             bool stereo,
             bool rightEye,
             int frame,
             [string] argv)
    {
        let _ : texttop : textbottom : op : _ = argv;
        let a = float(w) / float(h);


        setupProjection(w, h);

        int textSize = h / 30;
        int width = 0;

        gltext.size(textSize);
        let b = gltext.bounds(texttop);
        width = b[0] + b[2];
        let height = b[1] + b[3];

        glEnable(GL_LINE_SMOOTH);
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        gltext.color(Color(1,1,1,float(op)));
        
        gltext.writeAt((10), (h - height*3), texttop);
        gltext.writeAt((10), (height*3), textbottom);

    }
}
