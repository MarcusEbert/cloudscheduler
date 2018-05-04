#from django.shortcuts import render, get_object_or_404, redirect
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied

from django.contrib.auth.models import User #to get auth_user table
from .models import user as csv2_user

from .view_utils import db_execute, db_open, getAuthUser, getcsv2User, verifyUser, getSuperUserStatus, map_parameter_to_field_values, qt, render, set_user_groups
from collections import defaultdict
import bcrypt

from sqlalchemy import exists
from sqlalchemy.sql import select
from lib.schema import *
import sqlalchemy.exc
import datetime

'''
USER RELATED WEB REQUEST VIEWS
'''

#-------------------------------------------------------------------------------


USER_KEYS = (
    # The following fields are the key fields for the table:
    (
        'username',
        ),
    # The following fields maybe in the input form but should be ignored.
    (    
        'csrfmiddlewaretoken',
        'password1',
        'password2',
        ),
    )

#-------------------------------------------------------------------------------

def list(
    request, 
    selector=None,
    user=None, 
    username=None, 
    response_code=0, 
    message=None, 
    active_user=None, 
    user_groups=None,
    attributes=None
    ):

    if not verifyUser(request):
        raise PermissionDenied

    # open the database.
    db_engine,db_session,db_connection,db_map = db_open()

    # Retrieve the active user, associated group list and optionally set the active group.
    if not active_user:
        response_code,message,active_user,user_groups = set_user_groups(request, db_session, db_map)
        if response_code != 0:
            db_connection.close()
            return render(request, 'csv2/users.html', {'response_code': 1, 'message': message})

    #get user info
    s = select([csv2_user])
    user_list = qt(db_connection.execute(s))

    s = select([csv2_groups])
    group_list = qt(db_connection.execute(s))

    #user_list = {'ResultProxy': [dict(r) for r in db_connection.execute(s)]}

    db_connection.close()

    # Position the page.
    obj_act_id = request.path.split('/')
    if user:
        if user == '-':
            current_user = ''
        else:
            current_user = user
    elif len(obj_act_id) > 2 and len(obj_act_id[3]) > 0:
        current_user = str(obj_act_id[3])
    else:
        if len(user_list) > 0:
            current_user = str(user_list[0]['username'])
        else:
            current_user = ''

    # Render the page.
    context = {
            'active_user': active_user,
            'active_group': active_user.active_group,
            'user_groups': user_groups,
            'user_list': user_list,
            'group_list': group_list,
            'current_user': current_user,
            'response_code': 0,
            'message': None
        }

    return render(request, 'csv2/users.html', context)

def manage(request, response_code=0, message=None):
    print("+++ manage +++", response_code, message)
    if not verifyUser(request):
        raise PermissionDenied

    if not getSuperUserStatus(request):
        raise PermissionDenied

    user_list = csv2_user.objects.all()
    context = {
            'user_list': user_list,
            'response_code': response_code,
            'message': message
    }

    return render(request, 'csv2/users.html', context)


def add(request):
    print("+++ create +++")
    if not verifyUser(request):
        raise PermissionDenied
    if not getSuperUserStatus(request):
        raise PermissionDenied

    if request.method == 'POST':

        user = request.POST.get('username')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        cert_cn = request.POST.get('cert_cn')
        su_status = request.POST.get('is_superuser')
        if not su_status:
            su_status=False
        else:
            su_status=True

        # open the database.
        db_engine,db_session,db_connection,db_map = db_open()

        # Retrieve the active user, associated group list and optionally set the active group.
        rc, msg, active_user, user_groups = set_user_groups(request, db_session, db_map)
        
        if rc != 0:
            db_connection.close()
            return list(request, selector='-', response_code=1, message=msg, active_user=active_user, user_groups=user_groups)

        # Map the field list.
        response_code, table, values = map_parameter_to_field_values(request, db_engine, 'csv2_user', USER_KEYS,  active_user)

        if response_code != 0:        
            db_connection.close()
            return list(request, selector='-', response_code=1, message='user add %s' % values, active_user=active_user, user_groups=user_groups)



        # Need to perform several checks
        # 1. Check that the username is valid (ie no username or cert_cn by that name)
        # 2. Check that the cert_cn is not equal to any username or other cert_cn
        # 3. Check that password isn't empty or less than 4 chars
        # 4. Check that both passwords are the same

        s = select([csv2_user])
        csv2_user_list = qt(db_connection.execute(s), prune=['password'])

        #csv2_user_list = csv2_user.objects.all()
        for registered_user in csv2_user_list:
            #check #1
            if user == registered_user["username"] or user == registered_user["cert_cn"]:
                #render manage users page with error message
                return manage(request, response_code=1, message="Username unavailable")
            #check #2
            if cert_cn is not None and (cert_cn == registered_user["username"] or cert_cn == registered_user["cert_cn"]):
                return manage(request, response_code=1, message="Username unavailable or conflicts with a registered Distinguished Name")
        #check #3 part 1
        if pass1 is None or pass2 is None:
            return manage(request, response_code=1, message="Password is empty")
        if len(pass1)<4:
            return manage(request, response_code=1, message="Password must be at least 4 characters")
        #check #4
        if pass1 != pass2:
            return manage(request, response_code=1, message="Passwords do not match")

        # After checks are made use bcrypt to encrypt password.
        hashed_pw = bcrypt.hashpw(pass1.encode(), bcrypt.gensalt(prefix=b"2a"))

        #if all the checks passed and the hashed password has been generated create a new user object and save import

        del values[0]['group_name']

        values[1]['password'] = hashed_pw
        values[1]['join_date'] = datetime.datetime.today().strftime('%Y-%m-%d')
        
        # Add the user.
        success,message = db_execute(db_connection, table.insert().values({**values[0], **values[1]}))
        db_connection.close()

        if success:
            return list(request, selector=values[0]['username'], response_code=0, message='user "%s" successfully added.' % (values[0]['username']), active_user=active_user, user_groups=user_groups, attributes=values[2])
        else:
            return list(request, selector=values[0]['username'], response_code=1, message='user add "%s" failed - %s.' % (values[0]['username'], message), active_user=active_user, user_groups=user_groups, attributes=values[2])

        return manage(request, response_code=0, message="User added")
    else:
        #not a post, return to manage users page
        return manage(request)

def update(request):
    print("+++ update +++")
    if not verifyUser(request):
        raise PermissionDenied
    if not getSuperUserStatus(request):
        raise PermissionDenied


    if request.method == 'POST':
        csv2_user_list = csv2_user.objects.all()
        user_to_update = csv2_user.objects.filter(username=request.POST.get('old_usr'))[0]
        new_username = request.POST.get('username')
        cert_cn = request.POST.get('common_name')
        su_status = request.POST.get('is_superuser')
        new_pass1 = request.POST.get('password1')
        new_pass2 = request.POST.get('password2')

        if not su_status:
            su_status=False
        else:
            su_status=True

        # Need to perform three checks
        # 1. Check that the new username is valid (ie no username or cert_cn by that name)
        #   if the username hasn't changed we can skip this check since it would have been done on creation.
        # 2. Check that the cert_cn is not equal to any username or other cert_cn
        # 3. Check that the password is not empty and in that case that it is also a valid password

        for registered_user in csv2_user_list:
            #check #1
            if not new_username == user_to_update.username:
                if user == registered_user.username or user == registered_user.cert_cn:
                    #render manage users page with error message
                    return manage(request, response_code=1, message="Unable to update user: new username unavailable")
            #check #2
            if cert_cn is not None and registered_user.username != user_to_update.username and (cert_cn == registered_user.username or cert_cn == registered_user.cert_cn):
                return manage(request, response_code=1, message="Unable to update user: Username unavailable or conflicts with a registered Distinguished Name")

            #check #3 part 1
            if new_pass1 not in (None, "") and new_pass2 not in (None, ""):
                # part 2
                if len(new_pass1)>3:
                    # part 3
                    if new_pass1 == new_pass2:
                        #update pass
                        hashed_pw = bcrypt.hashpw(new_pass1.encode(), bcrypt.gensalt(prefix=b"2a"))
                        user_to_update.password = hashed_pw.decode("utf-8")
                    else:
                        # passwords don't match
                        return manage(request, response_code=1, message="Passwords don't match, please try again or leave password empty to update other fields.")
                else:
                    # passwords too short
                    return manage(request, response_code=1, message="Passwords are too short, please try again or leave password empty to update other fields.")
        user_to_update.username = new_username
        user_to_update.cert_cn = cert_cn
        user_to_update.is_superuser = su_status
        user_to_update.save()
        return manage(request, response_code=0, message="User updated")

    else:
        #not a post, return to manage users page
        return manage(request)

def delete(request):


    print("+++ delete +++")
    if not verifyUser(request):
        raise PermissionDenied
    print(">>>>>>>>>>>>>>>>>>>>>>>> 0")
    if not getSuperUserStatus(request):
        raise PermissionDenied

    print(">>>>>>>>>>>>>>>>>>>>>>>> 1")
    if request.method == 'POST':
        user = request.POST.get('username')
        user_obj = csv2_user.objects.filter(username=user)
        user_obj.delete()
        print(">>>>>>>>>>>>>>>>>>>>>>>> 2")
        return manage(request, response_code=0, message="User deleted")

    return manage(request, response_code=1, message="User NOT deleted")

def settings(request):
    print("+++ settings +++")
    if not verifyUser(request):
        raise PermissionDenied

    if request.method == 'POST':
        # proccess update

        csv2_user_list = csv2_user.objects.all()
        user_to_update = getcsv2User(request)
        new_username = request.POST.get('username')
        cert_cn = request.POST.get('common_name')
        new_pass1 = request.POST.get('password1')
        new_pass2 = request.POST.get('password2')
        
        # Need to perform three checks
        # 1. Check that the new username is valid (ie no username or cert_cn by that name)
        #   if the username hasn't changed we can skip this check since it would have been done on creation.
        # 2. Check that the cert_cn is not equal to any username or other cert_cn
        # 3. If the passwords aren't 0-3 chars and check if they are the same.
        for registered_user in csv2_user_list:
            #check #1
            if not new_username == user_to_update.username:
                if new_username == registered_user.username or new_username == registered_user.cert_cn:
                    context = {
                        'user_obj':user_to_update,
                        'response_code': 1,
                        'message': "Unable to update user: new username unavailable"
                    }
                    return render(request, 'csv2/user_settings.html', context)
            #check #2
            if cert_cn is not None and registered_user.username != user_to_update.username and (cert_cn == registered_user.username or cert_cn == registered_user.cert_cn):
                context = {
                    'user_obj':user_to_update,
                    'response_code': 1,
                    'message': "Unable to update user: Username or DN unavailable or conflicts with a registered Distinguished Name"
                }
                return render(request, 'csv2/user_settings.html', context)

        #check #3 part 1
        if new_pass1 is None or new_pass2 is None:
            context = {
                'user_obj':user_to_update,
                'response_code': 1,
                'message': "Password is empty"
            }
            return render(request, 'csv2/user_settings.html', context)
        #check #3 part 2
        if len(new_pass1)<4:
            context = {
                'user_obj':user_to_update,
                'response_code': 1,
                'message': "Password must be at least 4 characters"
            }
            return render(request, 'csv2/user_settings.html', context)
        #check #3 part 3
        if new_pass1 != new_pass2:
            context = {
                'user_obj':user_to_update,
                'response_code': 1,
                'message': "Passwords do not match"
            }
            return render(request, 'csv2/user_settings.html', context)

        #if we get here all the checks have passed and we can safely update the user data
        user_to_update.username=new_username
        if new_pass1:
            user_to_update.password = bcrypt.hashpw(new_pass1.encode(), bcrypt.gensalt(prefix=b"2a"))
        user_to_update.cert_cn=cert_cn
        user_to_update.save()
        context = {
                'user_obj':user_to_update,
                'response_code': 0,
                'message': "Update Successful"
            }
        return render(request, 'csv2/user_settings.html', context)

    else:
        #render user_settings template
        user_obj=getcsv2User(request)

        context = {
            'user_obj': user_obj,
            'response_code': 0,
            'message': None
        }
        return render(request, 'csv2/user_settings.html', context)

