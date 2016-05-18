from JumpScale import j


class ActionsBaseMgmt:
    def __init__(self, service):
        self.service = service

    def change_hrd_template(self, originalhrd):
        for methodname,obj in self.service.state.methods.items():
            if methodname in ["install"]:
                self.service.state.set(methodname,"CHANGEDHRD")
                self.service.state.save()


    def change_hrd_instance(self, originalhrd):
        for methodname,obj in self.service.state.methods.items():
            if methodname in ["install"]:
                self.service.state.set(methodname,"CHANGEDHRD")
                self.service.state.save()

    def change_method(self, methodname):
        self.service.state.set(methodname, "CHANGED")
        self.service.state.save()

        # set consumers' consume states to changed as well
        for consumer in self.service.get_consumers():
            if 'consume' in consumer.action_methods.keys():
                consumer.actions.change_method('consume')
