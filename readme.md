
## Setup using [dokku](http://dokku.viewdocs.io/dokku/)

1. On server:

```sh
dokku apps:create tagger
```

2. On client:

```sh
git remote add dokku dokku@<IPADDRESS>:tagger
```

3. On server:

```sh
# use the "main" branch for deployment
dokku git:set tagger deploy-branch main

# create a persistant directory
mkdir -p /var/lib/dokku/data/storage/tagger
mkdir -p /var/lib/dokku/data/storage/tagger/data
chown -R dokku:dokku /var/lib/dokku/data/storage/tagger
chown -R 32767:32767 /var/lib/dokku/data/storage/tagger
dokku storage:mount tagger /var/lib/dokku/data/storage/tagger:/app/storage

# set up settings
dokku config:set -no-restart tagger AIRTABLE_API_KEY=keyGOESHERE
dokku config:set -no-restart tagger AIRTABLE_BASE_ID=appGOESHERE
dokku config:set -no-restart tagger DATA_DIR=/app/storage/data
```

4. On client:

Copy the `completed.pkl` file to the server

```sh
scp "/local/path/to/completed.pkl" root@<IPADDRESS>:/var/lib/dokku/data/storage/tagger/data/completed.pkl
scp "/local/path/to/charities_active.csv" root@<IPADDRESS>:/var/lib/dokku/data/storage/tagger/data/charities_active.csv
```

Push the changes to the server

```sh
git push dokku main
```