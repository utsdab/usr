
//
//  Widget to display/select versions
//

module: versioning_selector
{

use rvtypes;
use commands;
use rvui;
use gl;
use glyph;
use app_utils;
use math;
use math_util;
use extra_commands;
use glu;
require python;
require glyph;
require runtime;

\: deb(void; string s)  { if (false) print("vwid: " + s + "\n"); }
\: rdeb(void; string s) { if (false) print("vwid: " + s + "\n"); }

\: sourceName(string; string name)
{
    let s = name.split(".");
    return s[0];
}

class: VersioningSelector : Widget
{

    int     _activeVersionIndex;
    int     _selectVersionIndex;
    bool    _set;
    bool    _in;
    float   _th;
    int     _nSources;
    Vec2    _tbox;
    bool    _drawInMargin;

    python.PyObject _pyGetVersionDataFromSource;
    python.PyObject _pySourceHasVersionData;
    python.PyObject _pyResetSourceFrame;
    python.PyObject _pyStaticSetVersion;

    class: IntWrapper
    {
        int _int;
        method: IntWrapper (IntWrapper; int i) { _int = i; }
    }

    class: VersionDataMu
    {
        string[] _media;
        string[] _name;
        int      _current;
        int      _last;
        string   _source;

        rvtypes.Color[]  _color;

        method: VersionDataMu (VersionDataMu;)
        {
            _media       = string[]();
            _name        = string[](); 
            _color       = rvtypes.Color[]();
            _current     = 0;
            _last        = 0;
            _source      = "";
        }

        method: size (int; )
        {
            return _media.size();
        }

        method: empty (bool; )
        {
            return (size() == 0);
        }
    }

    method: getVersionDataMuFromSource (VersionDataMu; string sourceName=nil)
    {
        //  deb ("getVersionDataMuFromSource");
        let s = sourceName,
            vd = VersionDataMu();

        if (s eq nil || s == "")
        {
            extra_commands.updatePixelInfo(nil);

            State state = data();

            let hasVD = false;

            if (state.pixelInfo neq nil && state.pixelInfo.size() > 0)
            {
                s = nodeGroup(state.pixelInfo[0].node) + "_source";
                hasVD = propertyExists (s + ".versioning.media");
            }
        }
	
        if (s eq nil || s == "") return vd;

        let propPrefix = s + ".versioning.";

        if (propertyExists(propPrefix + "media"))        vd._media       = getStringProperty (propPrefix + "media");
        if (propertyExists(propPrefix + "name"))         vd._name        = getStringProperty (propPrefix + "name");

        if (vd._name.size() != vd._media.size())
        {
            require io;

            vd._name.clear();
            for_each (m; vd._media)
            {
                vd._name.push_back (io.path.basename (m));
            }
        }

        if (propertyExists(propPrefix + "currentIndex")) vd._current     = getIntProperty    (propPrefix + "currentIndex").front();
        else  
        {
            newProperty    (propPrefix + "currentIndex", IntType, 1);
            setIntProperty (propPrefix + "currentIndex", int[] { 0 }, true);
        }

        if (propertyExists (propPrefix + "lastIndex"))   vd._last        = getIntProperty    (propPrefix + "lastIndex").front();
        else  
        {
            newProperty    (propPrefix + "lastIndex", IntType, 1);
            setIntProperty (propPrefix + "lastIndex", int[] { 0 }, true);
        }

        //  deb ("    color");
        if (propertyExists(propPrefix + "color"))
        {
            float[] p = getFloatProperty (propPrefix + "color");
            if (p.size() == 3 * vd.size()) 
            {
                vd._color.resize(vd.size());
                for_index (i; vd._media) vd._color[i] = rvtypes.Color(p[3*i], p[3*i+1], p[3*i+2], 1);
            }
        }

        vd._source = s;

        //  deb ("    vd %s" % vd);
        return vd;
    }

    class: PyVersionData
    {
        python.PyObject _pySetVersion;

        string[] _name;
        Color[]  _color;
        int      _last;
        int      _current;
        string   _source;

        method: PyVersionData (PyVersionData; python.PyObject vd)
        {
            if (python.is_nil (vd)) return nil;

            _name = string[]();
            let pyname = python.PyObject_GetAttr (vd, "_name");
            for (int i = 0; i < python.PyTuple_Size(pyname); ++i)
            {
                _name.push_back (to_string (python.PyTuple_GetItem (pyname, i)));
            }

            _color = Color[]();
            let pycolor = python.PyObject_GetAttr (vd, "_color");
            for (int i = 0; i < python.PyTuple_Size(pycolor); ++i)
            {
                let c = python.PyTuple_GetItem (pycolor, i);

                _color.push_back (Color(
                    to_float  (python.PyTuple_GetItem (c, 0)),
                    to_float  (python.PyTuple_GetItem (c, 1)),
                    to_float  (python.PyTuple_GetItem (c, 2)),
                    1.0));
            }

            _last    = to_int    (python.PyObject_GetAttr (vd, "_last"));
            _current = to_int    (python.PyObject_GetAttr (vd, "_current"));
            _source  = to_string (python.PyObject_GetAttr (vd, "_source"));

            _pySetVersion= python.PyObject_GetAttr (vd, "setVersion");
        }

        method: size (int; )
        {
            return _name.size();
        }

        method: setVersion (void; int index)
        {
            python.PyObject_CallObject (_pySetVersion, IntWrapper(index));
        }

        method: empty (bool; )
        {
            return (size() == 0);
        }

    } //  class PyVersionData

    method: sourceHasVersionData (bool; string source="")
    {
	return to_bool(python.PyObject_CallObject (_pySourceHasVersionData, source));
    }

    method: getVersionDataFromSource (PyVersionData; string source="")
    {
        let vd = python.PyObject_CallObject (_pyGetVersionDataFromSource, source);

        return PyVersionData(vd);
    }

    method: resetSourceFrame (void; string source)
    {
        python.PyObject_CallObject (_pyResetSourceFrame, source);
    }

    method: staticSetVersion (void; int version)
    {
        python.PyObject_CallObject (_pyStaticSetVersion, IntWrapper(version));
    }

    method: selectSource(void; Event event, int incr)
    {
        /*
        if (_getVersions eq nil) return;

        let domain  = event.domain(),
            (currentIndex, lastIndex, versions) = _getVersions();

        let idx = _selectVersionIndex - incr;

        if(idx >= 0 && idx < _nSources) _selectVersionIndex = idx;
        */

        redraw();

    }

    method: setSelectedSource(void; Event event)
    {
        _activeVersionIndex = _selectVersionIndex;
        /*
        State state = data();

        let pinfo   = state.pixelInfo,
            iname   = if (pinfo neq nil && !pinfo.empty()) 
                         then pinfo.front().name
                         else nil;

        let s = sources();

        _activeVersionIndex = _selectVersionIndex;
        let frames = getIntProperty("sequence.edl.frame");

        if (getSessionType() == StackSession)
        {
            setInPoint(1);
            setFrame(frames[1]);
            setOutPoint(frames[_selectVersionIndex + 1] - frames[_selectVersionIndex]);
        }
        else
        {
            setInPoint(frames[_selectVersionIndex]);
            setFrame(frames[_selectVersionIndex]);
            setOutPoint(frames[_selectVersionIndex + 1] - 1);
        }
        _set = true;

        redraw();
        */
    }

    method: eventToIndex(int; Point p)
    {
        State state = data();
        let margin  = state.config.bevelMargin;

        let vd = getVersionDataMuFromSource();

	if (vd eq nil || vd.empty()) return 0;

        return vd.size() - int(((p.y - _y + margin ) / _th )) + 1;
    }

    method: releaseSelect(void; Event event)
    {
        deb ("releaseSelect");
        State state = data();
        let margin  = state.config.bevelMargin;

        let rx = event.relativePointer().x;
        if(margin < rx && rx < _tbox.x + margin)
        {
            let di = eventToIndex(_downPoint),
                vd = getVersionDataMuFromSource();

	    if (vd eq nil || vd.empty()) return;

            if(di < vd.size() && di >= 0 && di != vd._current)
            {
                deb ("    di %s" % di);
                _selectVersionIndex = di;
                setSelectedSource(event);
                deb ("    calling setVersion");
                staticSetVersion (di);
                deb ("    done");
            }
        }

        if (!_drawInMargin) release(this, event, nil);
    }

    method: handleMotion(void; Event event)
    {
        let gp = event.pointer();
                    
        if (!this.contains (gp))
        {   
            _selectVersionIndex = _activeVersionIndex ;
            _in = false;
        }
        else
        {
            _in = true;
            let di = eventToIndex(event.pointer()),
                vd = getVersionDataMuFromSource();

	    if (vd eq nil || vd.empty()) return;

            if(di < vd.size() && di >= 0)
            {
                _selectVersionIndex = di;
            }
        }

        State state = data();

        let domain = event.subDomain(),
            p      = event.relativePointer(),
            tl     = vec2f(0, domain.y),
            pc     = p - tl,
            d      = mag(pc),
            m      = state.config.bevelMargin,
            lc     = this._inCloseArea,
            near   = d < m;

        if (near != lc) redraw();
        this._inCloseArea = near;

        redraw();
    }

    method: optFloatingVersioningSelector (void; Event event)
    {   
        _drawInMargin = !_drawInMargin;
        writeSetting ("VersioningSelector", "selectorIsDocked", SettingsValue.Bool(_drawInMargin));
        
        if (_drawInMargin) drawInMargin (1);
        else
        {   
            drawInMargin (-1);
            let m = margins();
            m[1] = 0;
            setMargins (m);
        }
        redraw();
    }
    
    method: isFloatingVersioningSelector (int;)
    {   
        if _drawInMargin then UncheckedMenuState else CheckedMenuState;
    }
    
    method: popupOpts (void; Event event)
    {   
        popupMenu (event, Menu {
            {"Versions", nil, nil, \: (int;) { DisabledMenuState; }},
            {"_", nil},
            {"Floating Versions Selector", optFloatingVersioningSelector, nil, isFloatingVersioningSelector},
        });
    }

    method: invalidateSetState(void; Event ev)
    {
        _set = false;
        ev.reject();
    }

    method: VersioningSelector (VersioningSelector; string name)
    {
        deb ("** constructor");
        init(name,
             [ ("pointer-1--push", storeDownPoint(this,), ""),
               ("pointer--move", handleMotion, ""),
               ("pointer-1--release", releaseSelect, ""),
               ("pointer-1--drag", drag(this,), "Move Selector"),
               ("pointer--wheelup", selectSource(,1), "Choose Previous Source"),
               ("pointer--wheeldown", selectSource(,-1), "Choose Next Source"),
               ("pointer-2--push", setSelectedSource, "Set Selected Source") ,
               ("pointer-3--push", popupOpts, "Popup Selector Options") ,
               ("new-in-point",  invalidateSetState, "Invalidate Set State"),
               ("new-out-point", invalidateSetState, "Invalidate Set State")
               ],
             false);

        _x = 40;
        _y = 60;
        _activeVersionIndex = _selectVersionIndex = 0;
        _in = false;

        let SettingsValue.Bool b1 = readSetting ("VersioningSelector", "selectorIsDocked", SettingsValue.Bool(false));   
        _drawInMargin = b1;

        let pymodule = python.PyImport_Import ("versioning_api_front");

        _pyGetVersionDataFromSource = python.PyObject_GetAttr (pymodule, "getVersionDataFromSource");
        _pySourceHasVersionData = python.PyObject_GetAttr (pymodule, "sourceHasVersionData");
        _pyResetSourceFrame = python.PyObject_GetAttr (pymodule, "resetSourceFrame");
        _pyStaticSetVersion = python.PyObject_GetAttr (pymodule, "staticSetVersion");

        this.toggle();
        deb ("** constructor complete");
    }

    \: drawNameValuePairsColors (NameValueBounds;
                        StringPair[] pairs,
                        Color fg, Color bg,
                        int x, int y, int margin,
                        int maxw=0, int maxh=0,
                        int minw=0, int minh=0,
                        bool nobox=false,
                        Color[] colors=nil)
    {
        m := margin;    // alias

        let (tbox, nbounds, vbounds, nw) = nameValuePairBounds(pairs, m);

        let vw      = 0,
            h       = 0,
            a       = gltext.ascenderHeight(),
            d       = gltext.descenderDepth(),
            th      = a - d;

        float
            x0      = x - d,
            y0      = y - m,
            x1      = tbox.x + x0,
            y1      = tbox.y + y0;

        let xs = x1 - x0,
            ys = y1 - y0;

        if (minw > 0 && xs < minw) x1 = x0 + minw;
        if (minh > 0 && ys < minh) y1 = y0 + minh;
        if (maxw > 0 && xs > maxw ) x1 = x0 + maxw;
        if (maxh > 0 && ys > maxh ) y1 = y0 + maxh;

        tbox.x = x1 - x0;   // adjust 
        tbox.y = y1 - y0;

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        if (!nobox) drawRoundedBox(x0, y0, x1, y1, m, bg, fg * Color(.5,.5,.5,.5));

        glColor(fg * Color(1,1,1,.25));
        glBegin(GL_LINES);
        glVertex(x + nw + m/4, y0 + m/2);
        glVertex(x + nw + m/4, y1 - m/2);
        glEnd();

        for_index (i; pairs)
        {
            let (n, v)  = pairs[i],
                bn      = nbounds[i],
                bv      = vbounds[i],
                tw      = bn[2] + bn[0];

            let c1 = (if (colors neq nil) then colors[i] else fg),
                c2 = c1 - Color(0,0,0,.25);

            gltext.color(c2);
            gltext.writeAt(x + (nw - tw), y, n);
            gltext.color(c1);
            gltext.writeAt(x + nw + m/2, y, v);
            gltext.color(fg);

            y += th;
            //if (i == s - 3) y+= m/2;
        }

        glDisable(GL_BLEND);

        (tbox, nbounds, vbounds, nw);
    }

    method: cleanup (void; )
    {
	this.updateBounds(vec2f {_x,_y}, vec2f{_x,_y});
	drawInMargin(-1);
        runtime.gc.pop_api();
    }

    method: render (void; Event event)
    {
	event.reject();

        extra_commands.updatePixelInfo(nil);

	runtime.gc.push_api(3);
        State state = data();

	let hasVD = false,
	    source = "";

	if (state.pixelInfo neq nil && state.pixelInfo.size() > 0)
	{
	    source = nodeGroup(state.pixelInfo[0].node) + "_source";
	    hasVD = propertyExists (source + ".versioning.media");
	}
        rdeb ("source %s hasVD %s" % (source, hasVD));
	
	if (! hasVD) { cleanup(); return; }

	rdeb ("render");

	let vd = getVersionDataMuFromSource(source);
	//print ("vd %s\n" % vd);

	if (vd eq nil || vd.empty()) { cleanup(); return; }

	rdeb ("selIndex %s" % _selectVersionIndex);

	let domain  = event.domain(),
	    bg      = state.config.bg,
	    fg      = state.config.fg;

	if (_drawInMargin) drawInMargin(1);

	rdeb ("    resetSourceFrame");
	rdeb ("    resetSourceFrame %s" % vd._source);
        runtime.gc.push_api(0);
	resetSourceFrame (vd._source);
        runtime.gc.pop_api();
	rdeb ("    resetSourceFrame done");

	rdeb ("    attrs, colors");
	(string,string)[] attrs;
	Color[] colors = if (vd.size() == vd._color.size()) then Color[]() else nil;

	for (int i = vd.size()-1; i >= 0; --i)
	{
	    attrs.push_back(("     ", vd._name[i]));
	    if (colors neq nil) 
	    {
		if (i == _selectVersionIndex) colors.push_back (1.2*(vd._color[i]));
		else                          colors.push_back (0.8*(vd._color[i]));
	    }
	}

	gltext.size(state.config.infoTextSize);
	setupProjection(domain.x, domain.y);

	let margin  = state.config.bevelMargin,
	    vs      = viewSize(),
	    vMargins= margins(),
	    nvb1    = nameValuePairBounds(expandNameValuePairs(attrs), margin),
	    targetW = nvb1._0[0] + 1.25*margin,
	    x       = if (_drawInMargin) then vs[0] - targetW else _x + margin,
	    yspace  = vs[1]-vMargins[3]-vMargins[2],
	    midy    = vMargins[3] + yspace/2,
	    adjy    = midy - (nvb1._0[1])/2,
	    targetY = max(vMargins[3] + margin, adjy + margin);

	if (_drawInMargin)
	{
	    _y = targetY - margin;
	    let w = max (vMargins[1], targetW);
	    glColor(Color(0,0,0,1));
	    glBegin(GL_QUADS);
	    glVertex(vs[0]-w, vs[1]-vMargins[2]);
	    glVertex(vs[0], vs[1]-vMargins[2]);
	    glVertex(vs[0], vMargins[3]);
	    glVertex(vs[0]-w, vMargins[3]);
	    glEnd();
	}

	rdeb ("    draw pairs");
	let y       = _y + margin,
	    nvb     = drawNameValuePairsColors(expandNameValuePairs(attrs), fg, bg, x, y, margin,
		    0, 0, 0, 0, _drawInMargin, colors),
	    tbox    = nvb._0,
	    emin    = vec2f(if (_drawInMargin) then vs[0] - targetW else _x, _y),
	    emax    = emin + tbox + vec2f(margin + (if (_drawInMargin) then margin/4 else margin), 0.0);

	let fa = int(gltext.ascenderHeight()),
	    fd = int(gltext.descenderDepth()),
	    th = fa - fd,
	    gx = x + margin/2;

	_th = th;
	_tbox = tbox;

	glEnable(GL_POINT_SMOOTH);
	glPointSize(6.0);
	glBegin(GL_POINTS);

	rdeb ("    draw points");
	if (vd._current != vd._last)
	{   
	    glColor(Color(.40,.40,.09,1));
	    let gy = y -3 + th * (vd.size() - vd._last -1 ) + fd + th/2 + 2.0;
	    glVertex(gx, gy);
	}

	glColor(Color(.75,.75,.15,1));
	let gy = y -3 + th * (vd.size() - vd._current - 1) + fd + th/2 + 2.0;
	glVertex(gx, gy);
	glEnd();


	/*
	glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	if (vd._current != vd._last)
	{   
	    let gy = y -3 + th * (vd.size() - vd._last -1 ) + fd + th/2 + 2.0;
	    glColor(Color(.40,.40,.09,0));
	    glyph.drawCircleFan (gx, gy, 15.0, 0.0, 1.0, 0.01);
	    glColor(Color(.40,.40,.09,1));
	    glyph.drawCircleFan (gx, gy, 13.0, 0.0, 1.0, 0.01);
	}

	let gy = y -3 + th * (vd.size() - vd._current - 1) + fd + th/2 + 2.0;
	glColor(Color(.75,.75,.15,0.5));
	glyph.drawCircleFan (gx, gy, 13.0, 0.0, 1.0, 0.01);
	glColor(Color(.75,.75,.13,1));
	//glyph.drawCircleFan (gx, gy, 13.0, 0.0, 1.0, 0.01);
	glDisable(GL_BLEND);
	*/

	if (_inCloseArea && !_drawInMargin)
	{
	    drawCloseButton(x - margin/2,
			    tbox.y + y - margin - margin/4,
			    margin/2, bg, fg);
	}
	if (!_in) _selectVersionIndex = vd._current;

	//print ("update bounds %s %s\n" % (emin, emax));
	this.updateBounds(emin, emax);
	runtime.gc.pop_api();
	rdeb ("    done");
    }

    method: layout (void; Event event)
    {
        let vd = getVersionDataFromSource();

        if (vd eq nil || vd.empty()) 
        {
            this.updateBounds(vec2f {_x,_y}, vec2f{_x,_y});
            return;
        }

        State state = data();

        let domain  = event.domain(),
            bg      = state.config.bg,
            fg      = state.config.fg;

        (string,string)[] attrs;
        for (int i = vd.size()-1; i >= 0; --i)
        {
            attrs.push_back(("        ", vd._name[i]));
        }

        gltext.size(state.config.infoTextSize);

        let margin  = state.config.bevelMargin,
            vs      = viewSize(),
            vMargins= margins(),
            nvb1    = nameValuePairBounds(expandNameValuePairs(attrs), margin),
            targetW = nvb1._0[0] + 1.25*margin,
            x       = if (_drawInMargin) then vs[0] - targetW else _x + margin,
            yspace  = vs[1]-vMargins[3]-vMargins[2],
            midy    = vMargins[3] + yspace/2,
            adjy    = midy - (nvb1._0[1])/2,
            targetY = max(vMargins[3] + margin, adjy + margin);

        if (_drawInMargin)
        {
            _y = targetY - margin;
        }

        let y       = _y + margin,
        /*
            nvb     = drawNameValuePairs(expandNameValuePairs(attrs), fg, bg, x, y, margin,
                    0, 0, 0, 0, _drawInMargin),
                    */
            tbox    = nvb1._0,
            emin    = vec2f(if (_drawInMargin) then vs[0] - targetW else _x, _y),
            emax    = emin + tbox + vec2f(margin + (if (_drawInMargin) then margin/4 else margin), 0.0);

        this.updateBounds(emin, emax);
    }
}

function: createMode (Mode;)
{
    return VersioningSelector("versioning-selector");
}

function: theMode (VersioningSelector; )
{
    VersioningSelector m = rvui.minorModeFromName("versioning-selector");

    return m;
}

function: selectorIsActive (bool; )
{
    let m = theMode();

    return (m neq nil && m._active);
}

function: toggleSelector (void; )
{
    deb ("toggleSelector");
    theMode().toggle();
    deb ("toggleSelector complete");
}

}

