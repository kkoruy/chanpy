// chanbot_db
db = db.getSiblingDB('chanbot_db');

db.createUser(
    {
        user: 'chanbot',
        pwd: 'poolsclosed',
        roles: [
            {
                role: 'readWrite',
                db: 'chanbot_db'
            }
        ]
    }
);

db.createCollection('threads');

db.createCollection('posts');

db.createCollection('attachments');

db.createCollection("fstats", {timeseries: {timeField: "ts", granularity: "minutes"}});


// users_db
db = db.getSiblingDB('users_db');

db.createUser(
    {
        user: 'useragent',
        pwd: 'osilayer8',
        roles: [
            {
                role: 'readWrite',
                db: 'users_db'
            }
        ]
    }
);

db.createCollection('api_tokens');

db.createCollection('users');