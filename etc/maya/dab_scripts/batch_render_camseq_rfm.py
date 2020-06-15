# This script if launched from a maya shelf button
# it is a wrapper for submitting RFM batch jobs to the farm.
#

def run():
    try:
        import maya_tools.uts_tools.mg_camseq_render as mgs

    except ImportError as ie:
        print("Failed to import module: {}".format(ie))

    else:
        mgs.main()


if __name__ == "__main__":
    print "RUNNING Batch Render Rfm ...."
    run()
