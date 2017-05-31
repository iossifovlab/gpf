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
* SFARI#<ID> - Researcher Ids are specified as groups with the SFARI#
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

## Management command `user_group_add`

Adds the specified user to the colon-separated list of groups

Example invocations of `user_group_add` command are:
```
./manage.py user_group_add research@iossifovlab.com GROUP1:GROUP2
```

## Management command `user_group_remove`

Removes the specified user from the colon-separated list of groups

Example invocations of `user_group_remove` command are:
```
./manage.py user_group_remove research@iossifovlab.com GROUP1:GROUP2
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

## Management command `user_remove`

Deletes the specified user

Example invocations of `user_remove` command are:
```
./manage.py user_remove research@iossifovlab.com
```

## Management command `user_show`

Shows the specified user

Example invocations of `user_show` command are:
```
./manage.py user_show research@iossifovlab.com
User email: research@iossifovlab.com name: Name groups: SFID#123:SSC password: <pass_hash>
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

## Management command `devusers`

The `devusers` command creates users for usage during devlopment process.
Example invocation of the command is:
```
./manage.py devusers
```

> This command should not be used in production environments.

When run command creates following users:

```
Email,Name,Groups,Password
admin@iossifovlab.com,,superuser,pass_hash
research@iossifovlab.com,,,pass_hash
```
All development users have password `secret`.
