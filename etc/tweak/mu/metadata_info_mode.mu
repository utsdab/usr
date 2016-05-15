
//
//  Custom Heads-Up Display Widget
//  MetadataInfo 
//

module: metadata_info_mode {
use rvtypes;
use glyph;
use app_utils;
use math;
use math_util;
use commands;
use extra_commands;
use gl;
use glu;
require io;

//----------------------------------------------------------------------
//
//  MetadataInfo 
//

\: sourceName(string; string name)
{
    let s = name.split(".");
    return s[0];
}

class: MetadataInfo : Widget
{
    method: MetadataInfo (MetadataInfo; string name)
    {
        this.init(name, 
                  [ ("pointer-1--push", storeDownPoint(this,), "Move Metadata Info"),
                    ("pointer-1--drag", drag(this,), "Move Metadata Info"),
                    ("pointer-1--release", release(this, , nil), ""),
                    ("pointer--move", move(this,), "") ],
                  false);

        _x = 40;
        _y = 60;
    }

    method: render (void; Event event)
    {
        State state = data();

        let pinfo   = state.pixelInfo,
            iname   = if (pinfo neq nil && !pinfo.empty()) 
                         then pinfo.front().name
                         else nil;

        let domain  = event.domain(),
            bg      = state.config.bg,
            fg      = state.config.fg,
            err     = isCurrentFrameError();

        string[]            metadata;
        (string,string)[]   attrs;

        try
        {
            metadata = getStringProperty("%s.site_annotation.metadata" % sourceName(iname));
        }
        catch(...)
        {
            metadata = string[] {(" =No Metadata for This Source")};
        }

        if(metadata.size() > 0)
        {
            for_index (i; metadata)
            {
                let r  = string.split(metadata[i], "=");

                if (r.size() > 1)
                {
                    attrs.push_back((r[0], string.join(r.rest(), "=")));
                }
                else if (r.size() == 1)
                {
                    attrs.push_back(("", r[0]));
                }
            }

            gltext.size(state.config.infoTextSize);
            setupProjection(domain.x, domain.y);

            let margin  = state.config.bevelMargin,
                x       = _x + margin,
                y       = _y + margin,
                tbox    = drawNameValuePairs(expandNameValuePairs(attrs),
                                             fg, bg, x, y, margin)._0,
                emin    = vec2f(_x, _y),
                emax    = emin + tbox + vec2f(margin*2.0, 0.0);

            if (_inCloseArea)
            {
                drawCloseButton(x - margin/2,
                                tbox.y + y - margin - margin/4,
                                margin/2, bg, fg);
            }

            this.updateBounds(emin, emax);
        }
    }
}

\: createMode (Mode;)
{
    return MetadataInfo("MetadataInfo");
}

}
