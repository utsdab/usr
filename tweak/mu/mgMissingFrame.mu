use rvtypes;
use commands;
use glyph;
use extra_commands;
use gl;
require gltext;

documentation: """ 

Matt Gidney Missing Frame overlay 

""";	
	
module: mgMissingFrame 
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
			print ("DEBUG: Inside init \n");
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
	
	
//	class: MissingFrameBlingMode : MinorMode
//	{ 
//		NEPair := (string, EventFunc);
//		// alias_symbol := existing_symbol_or_expression;
//		
//		
//		bool        _dispMsg;
//		string      _type;
//		EventFunc   _render;
//		NEPair[]    _typeMap;
//		
//		//			_typeMap = NEPair[] { ("hold", renderNothing),
//		//								  ("x", renderX), 
//		//								  ("show", renderShow),
//		//								  ("black", renderBlack)  };
//	
    
    class: MissingFrame
    
    {
	
    	method: renderX (void; )
		{
//			let contents  = event.contents(),
//				parts     = contents.split(";"),
//				source    = parts[1],
//				mediaPath = sourceMedia(source)._0,
//				media     = io.path.basename(mediaPath),
//				geom      = sourceGeometry(source),
//				domain    = event.domain(),
//				w         = domain.x,
//				h         = domain.y;
	
			displayFeedback("MISSING: frame %s of %s" % (frame));
	
			setupProjection(w, h);
	
			glEnable(GL_BLEND);
			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
			glEnable(GL_LINE_SMOOTH);
			glColor(Color(1,0,0,1));
	
			glBegin(GL_LINES);
			glVertex(geom[0]);
			glVertex(geom[2]);
			glVertex(geom[1]);
			glVertex(geom[3]);
			glEnd();
	
	
			glDisable(GL_BLEND);
		}
    }
//	
//		method: renderShow (void; Event event)
//		{
//			let contents  = event.contents(),
//				parts     = contents.split(";"),
//				source    = parts[1],
//				mediaPath = sourceMedia(source)._0,
//				media     = io.path.basename(mediaPath),
//				geom      = sourceGeometry(source),
//				domain    = event.domain(),
//				w         = domain.x,
//				h         = domain.y,
//				iw        = geom[2].x - geom[0].x,
//				ih        = geom[2].y - geom[0].y,
//				ix        = geom[0].x,
//				iy        = geom[0].y;
//	
//			setupProjection(w, h);
//	
//			glPushAttrib(GL_ALL_ATTRIB_BITS);
//			glEnable(GL_BLEND);
//			glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
//			glColor(Color(.5,.5,.5,.1));
//	
//			gltext.size(25);
//	
//			let text = "Missing % 4s" % parts[0],
//				b    = gltext.bounds("Missing 0000"),
//				tw   = b[2],
//				th   = b[3],
//				x    = iw / 2 - tw / 2 + ix,
//				y    = ih / 2 - th / 2 + iy;
//	
//			gltext.color(Color(0, 0, 0, 1));
//			gltext.writeAtNL(x-1, y-1, text);
//	
//			gltext.color(Color(.8, .8, .8, 1));
//			gltext.writeAtNL(x, y, text);
//	
//			glDisable(GL_BLEND);
//			glPopAttrib();
//	    }
//	
//		method: renderBlack (void; Event event)
//		{
//			let contents  = event.contents(),
//				parts     = contents.split(";"),
//				geom      = sourceGeometry(parts[1]),
//				domain    = event.domain(),
//				w         = domain.x,
//				h         = domain.y;
//	
//			setupProjection(w, h);
//	
//			glDisable(GL_BLEND);
//			glColor(Color(0, 0, 0, 1));
//	
//			glBegin(GL_QUADS);
//			glVertex(geom[0]);
//			glVertex(geom[1]);
//			glVertex(geom[2]);
//			glVertex(geom[3]);
//			glEnd();
//		}
//	
//		method: renderNothing (void; Event event)
//		{
//			; // nothing
//		}
//	
//		method: renderMissing (void; Event event)
//		{
//			//
//			// Presently rvui uses the missing-image event to display a feedback 
//			// message about the frames that are missing. If we want to stop this
//			// behavior, then we do not reject the event for rvui to see.
//			//
//	
//			_render(event);
//			if (_dispMsg)
//			{
//				event.reject();
//			}
//		}
//	
//		method: checkFunc ((int;); string name)
//		{
//			\: (int;)
//			{
//				if this._type == name then CheckedMenuState else UncheckedMenuState;
//			};
//		}
//		
//		method: setFunc (void; string name, Event event)
//		{
//			for_each (t; _typeMap) 
//			{
//				if (t._0 == name) 
//				{
//					_render = t._1;
//					_type = name;
//					writeSetting("MissingBling", "type", SettingsValue.String(name));
//				}
//			}
//		}
//	}
	
//		method: toggleMsg(void; Event event)
//		{
//			_dispMsg = !_dispMsg;
//			writeSetting("MissingBling", "displayMsg", SettingsValue.Bool(_dispMsg));
//		}
	
//		method: dispMsg(int;)
//		{
//			return if _dispMsg then CheckedMenuState else UncheckedMenuState;
//		}
	
//		method: MissingFrameBlingMode(MissingFrameBlingMode; string name)
//		{
//			init(name,
//				 nil,
//				 [("missing-image", renderMissing, "Render indication of missing frames")],
//				 Menu 
//				 {
//					 {"View", Menu 
//						 {
//							 {"Missing Frames", Menu 
//								 {
//									 {"Hold", setFunc("hold",), nil, checkFunc("hold")},
//									 {"Red X", setFunc("x",), nil, checkFunc("x")},
//									 {"Show Frame Number", setFunc("show",), nil, checkFunc("show")},
//									 {"Black", setFunc("black",), nil, checkFunc("black")},
//									 {"_", nil},
//									 {"Display Feedback Message", toggleMsg, nil, dispMsg}
//								 }
//							 }
//						 }
//					 }
//				 });
//			print ("\n xxx\n");
			
//			let SettingsValue.String s
//				= readSetting("MissingBling", "type", SettingsValue.String("show")),
//				SettingsValue.Bool d
//				= readSetting("MissingBling", "displayMsg", SettingsValue.Bool(true));
	
//			let s = "black",
//				d = true;
//				
//			
//			
//			_dispMsg = d;
//			_type    = s;
//			_typeMap = NEPair[] { ("hold", renderNothing),
//								  ("x", renderX), 
//								  ("show", renderShow),
//								  ("black", renderBlack)  };
//	
//			for_each (t; _typeMap) if (t._0 == s) _render = t._1;
//			if (_render eq nil) _render = renderShow;
//		}
//	}
	
//	\: createMode (Mode;)
//	{
//		return MissingFrameBlingMode("missing-frame-bling");
//	}
	
	
	
	
	
	
    //
    //  main is called per-frame
    //	
	
	documentation: "main something here.";
	
	\: main (void; int w, int h, 
			 int tx, int ty,
			 int tw, int th,
			 bool stereo,
			 bool rightEye,
			 int frame,
			 [string] argv)
	{	
		documentation: "main 2 something here.";
		let _ : type : _ = argv;
		let a = float(w) / float(h);

		let M = MissingFrame();
		

//		
//				_dispMsg = true;
		
		if ( type == "nil" )  type = "x";
		
//		let format = [info,x,y,size,color[]]
		let format = ["ddd",20,20,10.0,color[1.0,1.0,1.0,1.0]]  ;            
		writeText(format);
		M.renderX();
		
		print ("DEBUG[alMissingFrame]: _type %s\n"%(type));
//		print ("DEBUG[alMissingFrame]: _dispMsg %s\n"%(dispMsg));
		
//        _typeMap = NEPair[] { ("hold", M.renderNothing),
//							  ("x", M.renderX), 
//							  ("show", M.renderShow),
//							  ("black", M.renderBlack)  };

//		for_each (t; _typeMap) if (t._0 == s) _render = t._1;
//		if (_render eq nil) _render = M.renderShow;
//        setupProjection(w, h);
//
//        int textSize = h / 30;
//        int width = 0;
//
//        gltext.size(textSize);
//        let b = gltext.bounds(texttop);
//        width = b[0] + b[2];
//        let height = b[1] + b[3];
//
//        glEnable(GL_LINE_SMOOTH);
//        glEnable(GL_BLEND);
//        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
//        gltext.color(Color(1,1,1,float(op)));
//        
//        gltext.writeAt((10), (h - height*3), texttop);
//        gltext.writeAt((10), (height*3), textbottom);

	}

}
