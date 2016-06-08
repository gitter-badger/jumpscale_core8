from JumpScale import j


class ActionsBaseMgmt:

    def change_hrd_template(self, service, originalhrd):
        for methodname, obj in service.state.methods.items():
            if methodname in ["install"]:
                service.state.set(methodname, "CHANGEDHRD")
                service.state.save()

    def change_hrd_instance(self, service, originalhrd):
        for methodname, obj in service.state.methods.items():
            if methodname in ["install"]:
                service.state.set(methodname, "CHANGEDHRD")
                service.state.save()

    def change_method(self, service, methodname):
        service.state.set(methodname, "CHANGED")
        service.state.save()

    def ask_telegram(self, username, message, keyboard=[], expect_response=True, timeout=120, redis=None):
        """
        username: str, telegram username of the person you want to send the message to
        message: str, message
        keyboard: list of str: optionnal content for telegram keyboard.
        expect_response: bool, if you want to wait for a response or not. if True, this method retuns the response
            if not it return None
        timeout: int, number of second we need to wait for a response
        redis: redis client, optionnal if you want to use a specific reids client instead of j.core.db
        """
        redis = redis or j.core.db

        key = "%s:%s" % (username, j.data.idgenerator.generateGUID())

        out_evt = j.data.models.cockpit_event.Telegram()
        out_evt.io = 'output'
        out_evt.action = 'service.communication'
        out_evt.args = {
            'key': key,
            'username': username,
            'message': message,
            'keyboard': keyboard,
            'expect_response': expect_response
        }
        redis.publish('telegram', out_evt.to_json())

        data = redis.blpop(key, timeout=timeout)
        if data is None:
            raise j.exceptions.Timeout('timeout reached')

        _, resp = data
        resp = j.data.serializer.json.loads(resp)
        if 'error' in resp:
            raise j.exceptions.RuntimeError('Unexpected error: %s' % resp['error'])

        if expect_response:
            return resp['response']
