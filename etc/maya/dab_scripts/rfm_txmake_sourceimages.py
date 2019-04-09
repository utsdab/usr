#  converts all non .tex images
import maya.mel as mel
import maya.cmds as mc
import rfm2.txmanager_maya as txmgr_maya
import txmanager.core as txmgr

txmgr_maya.parse_maya_scene()
mgr = txmgr_maya.manager()
queued_txmake_list = [] # list to hold txmake tasks still in the queue

for txfile in mgr.txfile_list:
    if txfile._check_source_is_tex():
        continue
    else:
        for img, item in txfile.tex_dict.iteritems():
            print img, item
    # validate all output files
    txfile.check_dirty()
    if txfile.is_dirty():
        for img, item in txfile.tex_dict.iteritems():
            if item.outfile in queued_txmake_list:
                continue
            if item.state is txmgr.STATE_EXISTS:
                continue

            all_flags = mgr.txmakeopts.get_opts_as_list() + \
                    txfile.get_params().get_params_as_list()

            # create txmake command
            argv = all_flags
            argv.append('-newer') # add newer flag
            argv.append('%D(' + img + ')')
            argv.append('%D(' + item.outfile + ')')
            txmaketasktitle = 'TxMake: %s' % (str(img))
            print txmaketasktitle,argv
            #add_txmake_task(txmakeParentTask, txmaketasktitle, argv)
