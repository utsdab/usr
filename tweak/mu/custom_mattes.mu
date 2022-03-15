module: custom_mattes {
use gl;
use glu;
use rvtypes;
use io;
use commands;
use extra_commands;
use glyph;
use system;

class: CustomMatteMinorMode : MinorMode
{
    class: MatteDescription
    {
        string name;
        float left;
        float right;
        float bottom;
        float top;
        string text;
    }

    MatteDescription    _currentMatte;
    MatteDescription[]  _mattes;

    method: parseMatteFile (MatteDescription[]; string filename)
    {
        if (!path.exists(filename)) return nil;

        let file       = ifstream(filename),
            everything = read_all(file),
            lines      = everything.split("\n\r");
        
        file.close();

        MatteDescription[] mattes;

        for_each (line; lines)
        {
            let tokens = line.split(",");
            
            if (!tokens.empty())
            {
                //
                //  This will throw if we don't have enough tokens.  So the
                //  called of the parseMatteFile() function should make sure
                //  to catch.
                //

                mattes.push_back( MatteDescription(tokens[0],
                                                   float(tokens[1]),
                                                   float(tokens[2]),
                                                   float(tokens[3]),
                                                   float(tokens[4]),
                                                   tokens[5]) );
            }
        }
        
        return mattes;
    }

    method: findAndParseMatteFile (MatteDescription[];)
    {
        return parseMatteFile( getenv("RV_CUSTOM_MATTE_DEFINITIONS") );
    }

    method: selectMatte (void; Event event, MatteDescription m)
    {
        _currentMatte = m;
        redraw();
    }

    method: currentMatteState ((int;); MatteDescription m)
    {
        \: (int;)
        {
            return if this._currentMatte eq m 
                       then CheckedMenuState
                       else UncheckedMenuState;
        };
    }

    method: CustomMatteMinorMode (CustomMatteMinorMode;)
    {
        MenuItem matteMenu = nil;
            
        try
        {
            _mattes = findAndParseMatteFile();

            let matteItems = Menu();

            matteItems.push_back( MenuItem("No Matte",
                                           selectMatte(,nil),
                                           nil,
                                           currentMatteState(nil)) );

            for_each (m; _mattes)
            {
                matteItems.push_back( MenuItem( m.name, 
                                                selectMatte(,m),
                                                nil,
                                                currentMatteState(m)) );
            }

            if (!matteItems.empty())
            {
                matteMenu = MenuItem("View", 
                                     Menu(MenuItem("_", nil), 
                                          MenuItem("Custom Mattes", 
                                                   matteItems) ) );
            }

        }
        catch (...)
        {
            _mattes = nil;
        }

        init("Custom Matte",
             nil,
             nil,
             Menu(matteMenu));
    }

    method: render (void; Event event)
    {
        if (_currentMatte eq nil) return;

        \: sort (Vec2[]; Vec2[] array)
        {
            // only handles flipping not flopping right now
            if array[0].y < array[2].y
                then Vec2[] { array[3], array[2], array[1], array[0] }
                else array;
        }


        State state = data();
        setupProjection(event.domain().x, event.domain().y);

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        gltext.size(20.0);
        gltext.color(Color(1,1,1,1) * .5);
    
        let {_, l, r, b, t, text} = _currentMatte;

        let bounds = gltext.bounds(text),
            th     = bounds[1] + bounds[3];

        Color c = state.config.matteColor;
        c.w = state.matteOpacity;

        glColor(c);
        
        for_each (ri; sourcesRendered())
        {
            let g = sort(sourceGeometry(ri.name)),
                w = g[2].x - g[0].x,
                h = g[2].y - g[0].y,
                a = w / h,
                x0 = g[0].x + l * w,
                x1 = g[2].x - r * w,
                y0 = g[0].y + t * h,
                y1 = g[2].y - b * h;

            glBegin(GL_QUADS);

            //  Top 
            glVertex(g[0]);
            glVertex(g[1]);
            glVertex(g[1].x, y0);
            glVertex(g[0].x, y0);

            //  Bottom
            glVertex(g[3].x, y1);
            glVertex(g[2].x, y1);
            glVertex(g[2]);
            glVertex(g[3]);

            //  Left
            glVertex(g[0].x, y0);
            glVertex(x0, y0);
            glVertex(x0, y1);
            glVertex(g[0].x, y1);

            //  Right
            glVertex(g[1].x, y0);
            glVertex(x1, y0);
            glVertex(x1, y1);
            glVertex(g[1].x, y1);

            glEnd();

            gltext.writeAt(x0, y1 - th - 5, text);
        }

        glDisable(GL_BLEND);
    }
}

\: createMode (Mode;)
{
    return CustomMatteMinorMode();
}

}
