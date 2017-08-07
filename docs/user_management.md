# User Management Tools


## Management command `users_add`

Imports new users from CSV file. The file sould contain following columns:
* Email - Email address of the user

The following optional columns are also supported:
* Name - Name of the user
* Groups - List of users' groups this researcher belongs to. The groups are
separated by `:` symbol.
* Password - Hashed password.
If the password is empty, the user will be inactive


The following special groups are supported:
* SFID#<ID> - Researcher Ids are specified as groups with the SFARI#
prefix.
* superuser - Gives the user superuser permissions
* any_dataset - Gives the user access to all datasets

Example CSV file:
```
Email,Name,Groups,Password
u1@example.org,User One,superuser:SFARI#123,password_hash
u2@example.org,User Two,SSC,password_hash
u3@example.org,User Three,,
```

## Management command `users_restore`

Same as `users_add`, but will remove all existing users before importing new ones

## Management command `users_export`

Export users into CSV file. Example usage of the command is:
```
./manage.py users_export output_file.csv
```
where the last argument of the command gives a file name, where the exported
users should be stored.

Example exported users file is:

```
Email,Name,Groups,Password
anonymous@seqpipe.org,,,pass_hash
admin@iossifovlab.com,,superuser,pass_hash
research@iossifovlab.com,,,pass_hash
vip@iossifovlab.com,,,pass_hash
ssc@iossifovlab.com,,,pass_hash
```

## Management command `users_group_add`

Adds the users from the specified group to the colon-separated list of groups

Example invocations of `users_group_add` command are:
```
./manage.py users_group_add any_user GROUP1:GROUP2
```
By using the default group for each user, the command can be executed for only one user:
```
./manage.py users_group_add vip@iossifovlab.com GROUP1:GROUP2
```

## Management command `users_group_remove`

Removes the users from the specified group from the colon-separated list of groups

Example invocations of `users_group_remove` command are:
```
./manage.py users_group_remove any_user GROUP1:GROUP2
```
By using the default group for each user, the command can be executed for only one user:
```
./manage.py users_group_remove vip@iossifovlab.com GROUP1:GROUP2
```

## Management command `user_set_name`

Changes the name of the specified user

Example invocations of `user_set_name` command are:
```
./manage.py user_set_name research@iossifovlab.com "New Name"
```

## Management command `user_create`

Creates a new user. Requires one argument - email.

Additional parameters are supported:
* `-g` - Adds the user to the colon-separated list of groups
* `-n` - Sets the name of the user

Example invocations of `user_create` command are:
```
./manage.py user_create r123@iossifovlab.com -n "Name LastName" -g SSC:SFARI#123
Password:
Password (again):
Password changed successfully for user 'r123@iossifovlab.com'
```

## Management command `users_remove`

Deletes all users from the specified group

Example invocations of `users_remove` command are:
```
./manage.py users_remove any_user
```
By using the default group for each user, the command can be executed for only one user:
```
./manage.py users_remove vip@iossifovlab.com
```

## Management command `users_show`

Shows all users from the specified group

Example invocations of `users_show` command are:
```
./manage.py users_show any_user
User email: admin@iossifovlab.com
name:
groups: admin@iossifovlab.com,superuser,any_user
password: <pass_hash>
User email: vip@iossifovlab.com
name:
groups: vip@iossifovlab.com,any_user
password: <pass_hash>
```
By using the default group for each user, the command can be executed for only one user:
```
./manage.py users_show admin@iossifovlab.com
User email: admin@iossifovlab.com
name:
groups: admin@iossifovlab.com,superuser,any_user
password: <pass_hash>
```

## Management command `user_setpasswd`

Changes the password of the specified user

Example invocations of `user_setpasswd` command are:
```
./manage.py user_setpasswd research@iossifovlab.com
Changing password for user 'research@iossifovlab.com'
Password:
Password (again):
Password changed successfully for user 'research@iossifovlab.com'
```

## Management command `datasets_show`

Shows the configured datasets and the authorized groups

Example invocations of `datasets_show` command are:
```
./manage.py datasets_show
SD Authorized groups: any_user,SD,any_dataset
SSC Authorized groups: any_user,any_dataset,SSC
VIP Authorized groups: any_dataset,VIP
```
