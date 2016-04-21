--message, messagepub, str(level), type, tags, code, funcname, funcfilepath, backtrace, str(time)
-- key, message, messagepub, str(level), type,
--                                 tags, code, funcname, funcfilepath, backtrace, str(timestamp)
local rediskey = KEYS[2]
redis.call("SET", "last", ARGV[1])
local eco = cjson.decode(ARGV[1])

--There is no hashing library built in lua, and redis doesn't allow importing external libraries.
--so the key=md5(message + messagepub + code + funcname + funcfilepath) is calculated by the caller.

local value = redis.call("get", rediskey)
local flushtime = 0

if value then
    local ecodb = cjson.decode(value)
    eco.occurrences = ecodb.occurrences + 1
    flushtime = ecodb.epoch
else
    eco.occurrences = 1
end

local function save(key, eco)
    -- set before we push to the queue to make sure object is already uptodate
    local value = cjson.encode(eco)
    redis.call("set", key, value)
    redis.call("expire", key, 24*60*60)
end

-- time in milliseond
if flushtime < (eco.epoch - 300000) then
    save(rediskey, eco)
    --new eco or has been more than 5 min since last orccuance
    redis.call("RPUSH", "queues:eco", eco.id)
    --only keep last 1000 ecos
    redis.call("LTRIM", "queues:eco", -1000, -1)
else
    save(rediskey, eco)
end

return cjson.encode(eco)
