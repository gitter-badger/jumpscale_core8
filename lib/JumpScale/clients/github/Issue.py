from JumpScale import j
from Base import Base
from Base import replacelabels
import re
from github.GithubObject import NotSet
from Milestone import RepoMilestone

re_story_name = re.compile('.+\((.+)\)\s*$')
re_task_estimate = re.compile('.+\[([^\]]+)\]\s*$')
re_story_estimate = re.compile('^ETA:\s*(.+)\s*$', re.MULTILINE)

class Issue(Base):

    def __init__(self, repo, ddict={}, githubObj=None):
        self.logger = j.logger.get('j.clients.github.issue')
        self.repo = repo
        self._ddict = ddict
        self._githubObj = githubObj
        if githubObj is not None:
            self.load()
        # self.todo

    @staticmethod
    def get_story_name(title):
        m = re_story_name.match(title.strip())
        if m is None:
            return None

        return m.group(1)

    @property
    def api(self):
        if self._githubObj is None:
            self._githubObj = self.repo.api.get_issue(self.number)
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

    @body.setter
    def body(self, val):
        self.ddict["body"] = val
        self.api.edit(body=self.ddict['body'])

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
        #we return a copy so changing the list doesn't actually change the ddict value
        return self.ddict["labels"][:]

    @property
    def task_estimate(self):
        m = re_task_estimate.match(self.title)
        if m is not None:
            return m.group(1).strip()
        return None

    @property
    def story_estimate(self):
        if not len(self.comments):
            return None, None
        # find last comment with ETA
        for last in reversed(self.comments):
            m = re_story_estimate.search(last['body'])
            if m is not None:
                return m.group(1), last['id']
        return None, None

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
    def isOpen(self):
        return self.ddict['open'] == True

    @property
    def type(self):
        items = []
        for label in self.labels:
            if label.startswith("type"):
                items.append(label)
        if len(items) == 1:
            return items[0].partition("_")[-1]

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
            return items[0].partition("_")[-1]
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
            _, _, val = val.partition('_')

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
        self._ddict['open'] = self.api.state == 'open'

        self._ddict["assignee"] = self.repo.client.getUserLogin(
            githubObj=self.api.assignee)
        self._ddict["state"] = self.api.state
        self._ddict["title"] = self.api.title

        self._ddict["body"] = self.api.body

        self._ddict["comments"] = commentsToSet

        self._ddict["time"] = j.data.time.any2HRDateTime(
            [self.api.last_modified, self.api.created_at])

        self.logger.debug("LOAD:%s %s" % (self.repo.fullname, self._ddict["title"]))

        if self.api.milestone is None:
            self._ddict["milestone"] = ""
        else:
            ms = RepoMilestone(repo=self.repo, githubObj=self.api.milestone)
            self._ddict["milestone"] = "%s:%s" % (ms.number, ms.title)

    def getMarkdown(self, priotype=True):
        md = j.data.markdown.getDocument()
        md.addMDComment1Line("issue:%s" % self.number)
        md.addMDHeader(4, self.title)
        if self.body is not None and self.body.strip() != "":
            md.addMDBlock(self.body)

        md.addMDHeader(5, "meta")

        t = md.addMDTable()
        h = [self.state, "[%s](%s)" % (self.number, self.url)]
        rows = []
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

    def _loadMD(self, content):
        md = j.data.markdown.getDocument(content)
        title = md.items[0]
        self._ddict["title"] = title.title
        body = md.items[1]
        self._ddict["body"] = body.text
        table = md.items[2]
        state, tmp = table.header
        # first label
        self._ddict["labels"] = ["state_%s" % state]

        prio, ttype = table.rows[1]
        self._ddict["labels"].append("priority_%s" % prio)
        self._ddict["labels"].append("type_%s" % ttype)

        self._ddict["comments"] = []

        for row in table.rows:
            if row[0] == "milestone":
                ms = row[1]
                if ms != ".":
                    self._ddict["milestone"] = ms
            elif row[0] == "assignee":
                assignee = row[1]
                if assignee != ".":
                    self._ddict["assignee"] = assignee
            elif row[0] == "time":
                ttime = row[1]
                if ttime != ".":
                    self._ddict["time"] = ttime

        for i in range(3):
            md.items.pop(0)

        state = "title"
        comment = {}
        for item in md.items:
            if state == "title":
                comment = {}
                state = "body"
                continue
            if state == "body":
                comment["body"] = item.text
                state = "table"
                continue
            if state == "table":
                assignee = item.header[0]
                url = item.header[1]
                ttime = item.rows[0][1]
                id = url.split("]", 1)[0].strip("[")
                comment["id"] = int(id)
                url = url.split("]", 1)[1].strip("()")
                comment["url"] = url
                comment["time"] = ttime
                state = "title"
                # now add the comment
                self._ddict["comments"].append(comment)
                continue

    @property
    def todo(self):
        if "_todo" not in self.__dict__:
            todo = []
            if self.body is not None:
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
        if self.type == 'story' or self.story_name != '':
            return True
        return False

    @property
    def isTask(self):
        if self.type == 'task' or self.title.lower().endswith('task'):
            return True
        return False

    @property
    def story_name(self):
        name = Issue.get_story_name(self.title)
        if name is None:
            return ''
        return name

    @property
    def tasks(self):
        """
        Only works for issue that is a story.
        returns the tasks linked to this story.
        """
        tasks = []
        if self.isStory:
            for issue in self.repo.tasks:
                if issue.title.startswith(self.story_name):
                    tasks.append(issue)
        return tasks

    def move_to_repo(self, repo):
        self.logger.info("%s: move to repo:%s" % (self, repo))
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
        out = "### backlog comments of '%s' (%s)\n\n" % (self.title, self.url)
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
        if self.repo.api.id != task.repo.api.id:
            j.exceptions.Input("The task and the story have to be in the same Repository.")
            return

        if not self.isStory:
            j.exceptions.Input("This issue is not a story")
            return

        def state(s):
            s = s.lower()
            if s == 'verification':
                return ':white_circle: Verification'
            elif s == 'inprogress':
                return ':large_blue_circle: In Progress'
            elif s == 'closed':
                return ':white_check_mark: Closed'
            else:
                return ':red_circle: Open'

        task_table_found = False
        change = False
        doc = j.data.markdown.getDocument(self.body)
        i = 0

        for item in doc.items:
            if change is True:
                return
            if item.type == 'table':
                task_table_found = True
                table = item
                existing_tasks = [r[2] for r in table.rows]
                # add task is not in table yet
                if not "#%d" % task.number in existing_tasks:
                    self.logger.info("%s: add task:%s" % (self, task))
                    change = True
                    table.addRow([state(task.state), task.title, "#%s" % task.number])
                    break
                else:
                    # update task status if needed
                    for row in table.rows:
                        current_state = state('open') if task.isOpen else state('closed')
                        if row[2] == '#%s' % task.number and row[0] != current_state:
                            self.logger.info("%s: update task:%s" % (self, task))
                            change = True
                            row[0] = current_state
                            row[1] = task.title
                            break

        if not task_table_found:
            change = True
            table = doc.addMDTable()
            table.addHeader(['status', 'title', 'link'])
            table.addRow([state(task.state), task.title, "#%s" % task.number])

        if change:
            self.ddict["body"] = str(doc)
            self.api.edit(body=str(doc))

    def link_to_story(self, story):
        """
        If this issue is a task from a story, add link in to the story in the description
        """
        if self.repo.api.id != story.repo.api.id:
            raise j.exceptions.Input("The task (%s) and the story (%s) have to be in the same Repository." % (self.title, story.task))
            # return

        body = self.body
        if body is None:
            body = ''

        doc = j.data.markdown.getDocument(body)

        change = False
        story_line_found = False
        for item in doc.items:
            if item.type == 'header' and item.level == 3 and item.title.find("Part of Story") != -1:
                story_line_found = True
                story_number = item.title.lstrip('Part of Story: ')
                if story_number != '#%d' % story.number:
                    item.title = 'Part of Story: #%s' % story.number
                    change = True
                break

        if not story_line_found:
            change = True
            doc.addMDHeader(3, 'Part of Story: #%s' % story.number)
            # make sure it's on the first line of the comment
            title = doc.items.pop(-1)
            doc.items.insert(0, title)

        if change:
            self.logger.info("%s: link to story:%s" % (self, story))
            self.body = str(doc)

    def __str__(self):
        return "issue:%s" % self.title

    __repr__ = __str__
