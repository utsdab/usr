# This script if launched from a maya shelf button
# it is a wrapper for submitting RFM batch jobs to the farm.
#


def run():
    try:
        import maya_tools.uts_tools.rfm_tractor2 as rfmt2
    except ImportError as ie:
        print("Failed to import module: {}".format(ie))
    else:
        rfmt2.batch_render_spool(do_bake=False,force_tractor=True,force_local=False,force_rib=True)


if __name__ == "__main__":
    print "RUNNING Batch Render Rfm ...."
    run()
