# Users management API

## Examples

### Login

```
curl -v --header "Content-Type: application/json" \
    -c ./gpf_cookie.txt \
    --request POST \
    --data '{"username": "admin@iossifovlab.com","password":"secret"}' \
    http://localhost:8000/api/v3/users/login
```

### Get users

```
curl -v --header "Content-Type: application/json" \
    -b ./gpf_cookie.txt \
    http://localhost:8000/api/v3/users
```
