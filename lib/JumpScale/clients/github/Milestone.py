from JumpScale import j
from Base import Base


class RepoMilestone(Base):
    """
    milestone as defined on 1 specific repo
    """

    def __init__(self, repo, githubObj=None):
        self.logger = j.logger.get('j.clients.github.milestone')
        self._ddict = {}
        self._githubObj = githubObj
        if githubObj is not None:
            self.load()
        self.repo=repo

    @property
    def api(self):
        if self._githubObj is None:
            from IPython import embed
            print("DEBUG NOW get api for milestone")
            embed()
        return self._githubObj

    def load(self):
        self._ddict = {}
        self._ddict["deadline"] = j.data.time.any2HRDateTime(self.api.due_on)
        self._ddict["id"] = self.api.id
        self._ddict["url"] = self.api.url
        self._ddict["title"] = self.api.title
        self._ddict["body"] = self.api.description
        self._ddict["number"] = self.api.number
        self._ddict["name"] = ""
        self._ddict["owner"] = ""

        # load the props
        self.owner
        self.name

    @property
    def title(self):
        return self._ddict["title"]

    @title.setter
    def title(self, val):
        self._ddict["title"] = val
        self.api.edit(title=val)

    @property
    def name(self):
        """
        is name, corresponds to ays instance of milestone who created this
        """
        if self._ddict["name"] == "":
            self._ddict["name"] = self.tags.tagGet("name", default="")
        if self._ddict["name"] == "":
            return self.title
        return self._ddict["name"]

    @property
    def owner(self):
        """
        is name, corresponds to ays instance of milestone who created this
        """
        if self._ddict["owner"] == "":
            self._ddict["owner"] = self.tags.tagGet("owner", default="")
        return self._ddict["owner"]

    @property
    def descr(self):
        return self.bodyWithoutTags

    # synonym to let the tags of super class work
    @property
    def body(self):
        return self._ddict["body"]

    @body.setter
    def body(self, val):
        if self._ddict["body"] != val:
            self._ddict["body"] = val
            self.api.edit(self.title, description=val)

    @property
    def deadline(self):
        return self._ddict["deadline"]

    @deadline.setter
    def deadline(self, val):
        due = j.data.time.epoch2pythonDateTime(int(j.data.time.any2epoch(val)))
        self._ddict["deadline"] = val
        self.api.edit(title=self.title, due_on=due)

    @property
    def id(self):
        return self._ddict["id"]

    @property
    def url(self):
        return self._ddict["url"]

    @property
    def number(self):
        return self._ddict["number"]
