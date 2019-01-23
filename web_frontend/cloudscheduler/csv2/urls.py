from django.conf.urls import url
from django.urls import path

from . import cloud_views, group_views, job_views, server_views, settings_views, user_views, vm_views

urlpatterns = [

    path('',                                       cloud_views.status),


    path('cloud/add/',                             cloud_views.add),
    path('cloud/delete/',                          cloud_views.delete),
    path('cloud/list/',                            cloud_views.list),
    path('cloud/list/<path:selector>/',            cloud_views.list),
    path('cloud/status/',                          cloud_views.status),
    path('cloud/update/',                          cloud_views.update),
    path('cloud/metadata-add/',                    cloud_views.metadata_add),
    path('cloud/metadata-collation/',              cloud_views.metadata_collation),
    path('cloud/metadata-delete/',                 cloud_views.metadata_delete),
    path('cloud/metadata-fetch/<path:selector>/',  cloud_views.metadata_fetch),
    path('cloud/metadata-list/',                   cloud_views.metadata_list),
    path('cloud/metadata-new/<path:selector>/',    cloud_views.metadata_new),
    path('cloud/metadata-update/',                 cloud_views.metadata_update),

    path('group/add/',                             group_views.add),
    path('group/defaults/',                        group_views.defaults),
    path('group/delete/',                          group_views.delete),
    path('group/list/',                            group_views.list),
    path('group/list/<path:selector>/',            group_views.list),
    path('group/update/',                          group_views.update),
    path('group/metadata-add/',                    group_views.metadata_add),
    path('group/metadata-delete/',                 group_views.metadata_delete),
    path('group/metadata-fetch/<path:selector>/',  group_views.metadata_fetch),
    path('group/metadata-list/',                   group_views.metadata_list),
    path('group/metadata-new/',                    group_views.metadata_new),
    path('group/metadata-update/',                 group_views.metadata_update),

    path('job/list/',                              job_views.list),
##  path('job/modify/',                            job_views.modify),

    path('server/config/',                         server_views.configuration),

##  path('settings/preferences/',                  settings_views.preferences),
    path('settings/prepare/',                      settings_views.prepare),
    path('settings/log-out/',                      settings_views.log_out),

    path('user/add/',                              user_views.add),
    path('user/delete/',                           user_views.delete),
    path('user/list/',                             user_views.list),
    path('user/settings/',                         user_views.settings),
    path('user/update/',                           user_views.update),

    path('vm/list/',                               vm_views.list),
    path('vm/list/<path:selector>/',               vm_views.list),
    path('vm/update/',                             vm_views.update),
    path('vm/update/<path:selector>/',             vm_views.update),

]
