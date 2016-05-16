from JumpScale import j
from Base import Base
from Base import replacelabels
import re
from github.GithubObject import NotSet

re_story_name = re.compile('.+\((.+)\)$')


class Issue(Base):

    def __init__(self, repo, ddict={}, githubObj=None):
        self.logger = j.logger.get('j.clients.github.issue')
        self.repo = repo
        self._ddict = ddict
        self._githubObj = githubObj
        if githubObj is not None:
            self.load()
        #self.todo

    @property
    def api(self):
        if self._githubObj is None:
            from IPython import embed
            print("DEBUG NOW get api")
            embed()
        return self._githubObj

    @property
    def ddict(self):
        if self._ddict == {}:
            # no dict yet, fetch from github
            self.load()
        return self._ddict

    @property
    def comments(self):
        return self.ddict["comments"]

    @property
    def guid(self):
        return self.repo.fullname + "_" + str(self.ddict["number"])

    @property
    def number(self):
        return int(self.ddict["number"])

    @property
    def title(self):
        return self.ddict["title"]

    @property
    def body(self):
        return self.ddict["body"]

    @property
    def time(self):
        return self.ddict["time"]

    @property
    def url(self):
        return self.ddict["url"]

    @property
    def assignee(self):
        return self.ddict["assignee"]

    @property
    def labels(self):
        return self.ddict["labels"]

    @property
    def id(self):
        return self.ddict["id"]

    @labels.setter
    def labels(self, val):
        # check if all are already in labels, if yes nothing to do
        if len(val) == len(self.ddict["labels"]):
            self.ddict["labels"].sort()
            val.sort()
            if val == self.ddict["labels"]:
                return
        self.ddict["labels"] = val
        toset = [self.repo.getLabel(item) for item in self.ddict["labels"]]
        self.api.set_labels(*toset)

    @property
    def milestone(self):
        return self.ddict["milestone"]

    @property
    def state(self):
        states = []
        for label in self.labels:
            if label.startswith("state"):
                states.append(label)
        if len(states) == 1:
            return states[0][len("state"):].strip("_")
        elif len(states) > 1:
            self.state = "question"
        else:
            return ""

    @state.setter
    def state(self, val):
        return self._setLabels(val, "state")

    @property
    def type(self):
        items = []
        for label in self.labels:
            if label.startswith("type"):
                items.append(label)
        if len(items) == 1:
            return items[0][len("type"):].strip("_")
        else:
            self.type = ""
            return ""

    @type.setter
    def type(self, val):
        return self._setLabels(val, "type")

    @property
    def priority(self):
        items = []
        for label in self.labels:
            if label.startswith("priority"):
                items.append(label)
        if len(items) == 1:
            return items[0][len("priority"):].strip("_")
        else:
            self.priority = "normal"
            return self.priority

    @priority.setter
    def priority(self, val):
        return self._setLabels(val, "priority")

    @property
    def process(self):
        items = []
        for label in self.labels:
            if label.startswith("process"):
                items.append(label)
        if len(items) == 1:
            return items[0][len("process"):].strip("_")
        else:
            return ""

    @process.setter
    def process(self, val):
        return self._setLabels(val, "process")

    @property
    def tasks(self):
        """
        If this issue is a story, list all tasks related to it
        """
        if not self.isStory:
            raise j.exceptions.Input("This issue is not a story")

        tasks = []
        for issue in self.repo.issues:
            if issue.title.startswith('%s:' % self.story_name):
                tasks.append(issue)
        return tasks

    def _setLabels(self, val, category):
        if val is None or val == '':
            return

        if val.startswith(category):
            val = val[len(category):]
        val = val.strip("_")
        val = val.lower()

        val = "%s_%s" % (category, val)

        if val not in self.repo.labelnames:
            self.repo.labelnames.sort()
            llist = ",".join(self.repo.labelnames)
            raise j.exceptions.Input(
                "Label needs to be in list:%s (is understood labels in this repo on github), now is: '%s'" %
                (llist, val))

        # make sure there is only 1
        labels2set = self.labels
        items = []
        for label in self.labels:
            if label.startswith(category):
                items.append(label)
        if len(items) == 1 and val in items:
            return
        for item in items:
            labels2set.pop(labels2set.index(item))
        if val is not None or val != "":
            labels2set.append(val)
        self.labels = labels2set

    def load(self):

        self._ddict = {}

        # check labels
        labels = [item.name for item in self.api.labels]  # are the names
        newlabels = []
        for label in labels:
            if label not in self.repo.labelnames:
                if label in replacelabels:
                    if replacelabels[label] not in newlabels:
                        newlabels.append(replacelabels[label])
            else:
                if label not in newlabels:
                    newlabels.append(label)

        if labels != newlabels:
            self.logger.info(
                "change label:%s for %s" %
                (labels, self.api.title))
            labels2set = [self.repo.getLabel(item) for item in newlabels]
            self.api.set_labels(*labels2set)
            labels = newlabels

        comments = [comment for comment in self.api.get_comments()]
        commentsToSet = []
        if len(comments) > 0:
            for comment in comments:
                obj = {}
                user = self.repo.client.getUserLogin(githubObj=comment.user)
                obj["user"] = user
                obj["url"] = comment.url
                obj["id"] = comment.id
                obj["body"] = comment.body
                obj["time"] = j.data.time.any2HRDateTime(
                    [comment.last_modified, comment.created_at])
                commentsToSet.append(obj)

        self._ddict["labels"] = labels
        self._ddict["id"] = self.api.id
        self._ddict["url"] = self.api.html_url
        self._ddict["number"] = self.api.number

        self._ddict["assignee"] = self.repo.client.getUserLogin(
            githubObj=self.api.assignee)
        self._ddict["state"] = self.api.state
        self._ddict["title"] = self.api.title

        self._ddict["body"] = self.api.body

        self._ddict["comments"] = commentsToSet

        self._ddict["time"] = j.data.time.any2HRDateTime(
            [self.api.last_modified, self.api.created_at])

        print("LOAD:%s %s" % (self.repo.fullname, self._ddict["title"]))

        if self.api.milestone is None:
            self._ddict["milestone"] = ""
        else:
            ms = self.repo.client.getMilestone(githubObj=self.api.milestone)
            self._ddict["milestone"] = "%s:%s" % (ms.number, ms.title)

    def getMarkdown(self, priotype=True):
        md = j.data.markdown.getDocument()
        md.addMDComment1Line("issue:%s" % self.number)
        md.addMDHeader(4, self.title)
        if self.body is not None and self.body.strip() != "":
            md.addMDBlock(self.body)
        h = [self.state, "[%s](%s)" % (self.number, self.url)]
        rows = []
        t = md.addMDTable()
        t.addHeader(h)
        t.addRow(["milestone", self.milestone])
        t.addRow([self.priority, self.type])
        t.addRow(["assignee", self.assignee])
        t.addRow(["time", self.time])

        if self.comments != []:
            for comment in self.comments:
                md.addMDHeader(5, "comment")
                md.addMDBlock(comment["body"])
                h = [
                    comment["user"], "[%s](%s)" %
                    (comment["id"], comment["url"])]
                t = md.addMDTable()
                t.addHeader(h)
                t.addRow(["time", comment["time"]])

        return md

    def _loadMD(self,content):
        md=j.data.markdown.getDocument(content)
        title=md.items[0]
        self._ddict["title"]=title.title
        body=md.items[1]
        self._ddict["body"]=body.text
        table=md.items[2]
        state,tmp=table.header
        #first label
        self._ddict["labels"]=["state_%s"%state]

        prio,ttype=table.rows[1]
        self._ddict["labels"].append("priority_%s"%prio)
        self._ddict["labels"].append("type_%s"%ttype)

        self._ddict["comments"]=[]

        for row in  table.rows:
            if row[0]=="milestone":
                ms=row[1]
                if ms!=".":
                    self._ddict["milestone"]=ms
            elif row[0]=="assignee":
                assignee=row[1]
                if assignee!=".":
                    self._ddict["assignee"]=assignee
            elif row[0]=="time":
                ttime=row[1]
                if ttime!=".":
                    self._ddict["time"]=ttime

        for i in range(3):
            md.items.pop(0)

        state="title"
        comment={}
        for item in md.items:
            if state=="title":
                comment={}
                state="body"
                continue
            if state=="body":
                comment["body"]=item.text
                state="table"
                continue
            if state=="table":
                assignee=item.header[0]
                url=item.header[1]
                ttime=item.rows[0][1]
                id=url.split("]",1)[0].strip("[")
                comment["id"]=int(id)
                url=url.split("]",1)[1].strip("()")
                comment["url"]=url
                comment["time"]=ttime
                state="title"
                #now add the comment
                self._ddict["comments"].append(comment)
                continue

    @property
    def todo(self):
        if "_todo" not in self.__dict__:
            todo = []
            if self.body!=None:                
                for line in self.body.split("\n"):
                    if line.startswith("!! "):
                        todo.append(line.strip().strip("!! "))
            for comment in self.comments:
                for line in comment['body'].split("\n"):
                    if line.startswith("!! "):
                        todo.append(line.strip().strip("!! "))
            self._todo = todo
        return self._todo

    @property
    def isStory(self):
        if self.type == 'story' or self.title.lower().endswith('story'):
            return True
        return False

    @property
    def isTask(self):
        if self.type == 'task' or self.title.lower().endswith('task'):
            return True
        return False

    @property
    def story_name(self):
        if not self.isStory:
            return ''

        for name in re_story_name.findall(self.title):
            if name != '':
                return name

        return ''

    def move_to_repo(self, repo):
        print ("%s: move to repo:%s"%(self,repo))
        body = "Issue moved from %s\n\n" % self.api.url
        for line in self.api.body.splitlines():
            if line.startswith("!!") or line.startswith(
                    '### Tasks:') or line.startswith('### Part of Story'):
                continue
            body += "%s\n" % line
        assignee = self.api.assignee if self.api.assignee else NotSet
        labels = self.api.labels if self.api.labels else NotSet
        moved_issue = repo.api.create_issue(title=self.title, body=body,
                                            assignee=assignee, labels=labels)
        moved_issue.create_comment(self._create_comments_backlog())
        self.api.create_comment("Moved to %s" % moved_issue.url)
        self.api.edit(state='close')

    def _create_comments_backlog(self):
        out = "## backlog comments of '%s' (%s)\n\n" % (self.title, self.url)
        for comment in self.api.get_comments():
            if comment.body.find("!! move") != -1:
                continue
            date = j.data.time.any2HRDateTime(
                [comment.last_modified, comment.created_at])
            out += "from @%s at %s\n" % (comment.user.login, date)
            out += comment.body + "\n\n"
            out += "---\n\n"
        return out

    def add_task(self, task):
        """
        If this issue is a story, add a link to a subtasks
        """
        print ("%s: add task:%s"%(self,task))
        if self.repo.api.id != task.repo.api.id:
            raise j.exceptions.Input(
                "The task and the story have to be in the same Repository.")

        if not self.isStory:
            raise j.exceptions.Input("This issue is not a story")

        task_line_found = False
        new_body = ''
        for line in self.api.body.splitlines():
            if line.startswith('### Tasks:'):
                task_line_found = True
                tasks = line[len('### Tasks:'):].split(',')
                tasks = [task.strip() for task in tasks]
                if "#%d" % task.api.number not in tasks:
                    line += " , #%d " % task.api.number
            new_body += line if line != '' else '\n\n'

        if not task_line_found:
            new_body = '%s\n\n### Tasks: #%d' % (
                self.api.body, task.api.number)

        #@todo (1) dirty hack why is this required
        # while "\n\n\n" in new_body:
        #     new_body=new_body.replace("\n\n","\n")

        self.api.edit(body=new_body)
            

    def link_to_story(self, story):
        """
        If this issue is a task from a story, add link in to the story in the description
        """
        print ("%s: link to story:%s"%(self,story))
        if self.repo.api.id != story.repo.api.id:
            raise j.exceptions.Input(
                "The task and the story have to be in the same Repository.")

        if not self.isTask:
            raise j.exceptions.Input("This issue is not a task")

        story_line_found = False
        new_body = ''
        for line in self.api.body.splitlines():
            if line.startswith('### Part of Story:'):
                story_line_found = True
                line = '### Part of Story: #%d' % (story.api.number)
            new_body += line if line != '' else '\n\n'

        if not story_line_found:
            new_body = '### Part of Story: #%d\n\n%s' % (
                story.api.number, self.api.body)

        self.api.edit(body=new_body)

    def __str__(self):
        return "issue:%s" % self.title

    __repr__ = __str__
