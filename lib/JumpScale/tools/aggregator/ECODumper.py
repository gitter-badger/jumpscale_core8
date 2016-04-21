import Dumper
from JumpScale import j


class ECODumper(Dumper.BaseDumper):
    QUEUE = 'queues:eco'

    def __init__(self, cidr='127.0.0.1', ports=[7777]):
        super(ECODumper, self).__init__(cidr, ports=ports)

    def dump(self, redis):
        """
        :param redis:
        :return:
        """
        while True:
            key = redis.lpop(self.QUEUE)
            if key is None:
                return
            key = key.decode()

            data = redis.get("eco:%s" % key)
            data = data.decode()

            obj = j.data.serializer.json.loads(data)

            eco = j.data.models.system.Errorcondition()
            eco.guid = obj["id"]
            eco.reload()
            for key, value in obj.items():
                setattr(eco, key, value)
            eco.occuranecs = getattr(eco, 'occurrences', 0) + 1

            eco.save()
