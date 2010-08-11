#!/usr/bin/env python

import gordon
import gordon.web.gordonweb.model as M

M.metadata.bind = gordon.model.engine

M.groups_table.create()
M.users_table.create()
M.visits_table.create()
M.visit_identity_table.create()
M.user_group_table.create()    
M.permissions_table.create()
M.group_permission_table.create()

def create_row(obj, **kwargs):
    t = obj
    for k,v in kwargs.items():
        setattr(t, k, v)
    M.session.add(t)
    M.session.flush()
    return t
    

plisten=create_row(M.Permission(),
                   permission_name=u'listen',description=u'listen')
pdownload=create_row(M.Permission(),
                     permission_name=u'download',description=u'download')
pedit=create_row(M.Permission(),
                 permission_name=u'edit',description=u'edit')

user = gordon.config.DEF_DBUSER
password = gordon.config.DEF_DBPASS
ugordon=create_row(M.User(), user_name=user, display_name=user,
                   password=password)

glisten=create_row(M.Group(),
                   group_name=u'listen',display_name=u'listen')
gdownload=create_row(M.Group(),
                     group_name=u'download',display_name=u'download')
gedit=create_row(M.Group(),
                 group_name=u'edit',display_name=u'edit')

glisten.permissions.append(plisten)
gdownload.permissions.append(pdownload)
gedit.permissions.append(pedit)
M.session.add(glisten); M.session.flush()
M.session.add(gdownload); M.session.flush()
M.session.add(gedit); M.session.flush()

ugordon.groups.append(glisten)
ugordon.groups.append(gdownload)
ugordon.groups.append(gedit)
M.session.add(ugordon); M.session.flush()
