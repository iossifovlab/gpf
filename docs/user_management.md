# User Management Tools


## Management command `reload_dataset_perm`

Loads and creates users' groups defined into `variantsDB.conf` datasets
configuration.

When you change datasets' groups you need to run
```
./manage.py reload_dataset_perm
```

## Management command `import_researchers`

Imports reasearchers from CSV file. The file sould contain following columns:
* Email - researcher email
* Id - researchers identification used in process of registration
* FirstName - first name
* LastName - last name
* Groups - list of users' groups this researcher belongs to. The goups are 
separated by `:` symbol.

Example CSV file:
```
Email,Id,FirstName,LastName,Groups
u1@example.org,ID1,User,One,SSC
u2@example.org,ID1,User,Two,VIP
u3@example.org,ID1,User,Three,SSC:VIP
```

## Management command `export_users`

Export users into CSV file. Example usage of the command is:
```
./manage.py export_users output_file.csv
```
where tha last argument of the command gives a file name, where the exported
users should be stored.

Example exported users file is:

```
Email,FirstName,LastName,Groups,Superuser,Staff,Active,Id,Password
anonymous@seqpipe.org,,,anonymous,False,False,True,,<pass>
admin@iossifovlab.com,,,,True,True,True,,<pass>
research@iossifovlab.com,,,SSC:VIP,False,False,True,,<pass>
vip@iossifovlab.com,,,VIP,False,False,True,,<pass>
ssc@iossifovlab.com,,,SSC,False,False,True,,<pass>
u1@example.org,User,One,SSC,False,False,False,ID1,
u2@example.org,ID1,User,Two,False,False,False,VIP
u3@example.org,ID1,User,Three,False,False,False,SSC:VIP
```

There are additional columns in this exported file:
* Superuser - whether the user is a system adminstrator. Users with this flag `True`
has all permissions
* Staff - whether the user is a staff member. Users with this flag `True` could
have access to administrative fuctions of the system.
* Active - whether the user is active. When importing researcher they has values
of this flag set to `False`. Researchers registration process verifies the user
and turns this flag to `True` to mark the user as active. Only active users can
login into the system.
* Passwords - contains salted hash of the users' passwords.

## Management command `import_users`

To change the users settings we can import users using `import_users` command. You
can edit users CSV file from previous invocation of `export_users` command to
edit users access rights and configuration.

Example invocations of `import_users` command are:
```
./manage.py import_users users_file.csv
```

There some options that could be specified when invoking `import_users` command.

* `-r` - replaces all groups and researcher ids for users in the file. Default 
behavior when the imported user exists in the system is to append groups and 
researcher IDs found in the users file to the existings groups and IDs. If you
want to replace gropus and IDs of the existing users you need to use `-r` option.

* `--additional-groups GROUPS`, `-g GROUPS` - for all imported users appends
groups specified with this options to groups defined into the file.


## Management command `devusers`

The `devusers` command creates users for usage during devlopment process.
Example invocation of the command is:
```
./manage.py devusers
```

> This command should not be used in production environments.

When run command creates following users:

```
Email,FirstName,LastName,Groups,Superuser,Staff,Active,Id,Password
admin@iossifovlab.com,,,,True,True,True,,<pass>
research@iossifovlab.com,,,,False,False,True,,<pass>
vip@iossifovlab.com,,,,False,False,True,,<pass>
ssc@iossifovlab.com,,,,False,False,True,,<pass>
```
All development users has password `secret`.

Using `export_users` command this users could be exported and edited to assign them
into different groups. For example, if the system datasets configuration defines
`SSC` and `VIP` groups, the users file could be changed into:

```
Email,FirstName,LastName,Groups,Superuser,Staff,Active,Id,Password
admin@iossifovlab.com,,,,True,True,True,,<pass>
research@iossifovlab.com,,,VIP:SSC,False,False,True,,<pass>
vip@iossifovlab.com,,,VIP,False,False,True,,<pass>
ssc@iossifovlab.com,,,SSC,False,False,True,,<pass>
```

When this users file is imported using `import_users` command,
the user `ssc@iossifovlab.com` will have access to datasets in the `SSC` group,
the user `vip@iossifovlab.com` will have access to datasets in the `VIP` group,
and the user `research@iossifovlab.com` will have access to both. 