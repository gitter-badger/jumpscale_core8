from JumpScale import j
from Issue import Issue
from Base import replacelabels
import copy
from Milestone import RepoMilestone
from JumpScale.core.errorhandling.OurExceptions import Input


class GithubRepo():

    def __init__(self, client, fullname):
        self.logger = j.logger.get('j.clients.github.repo')
        self.client = client
        self.fullname = fullname
        self._repoclient = None
        self._labels = None
        self.issues = []
        self.issues_loaded = False
        self._milestones = []

    @property
    def api(self):
        if self._repoclient is None:
            self._repoclient = self.client.api.get_repo(self.fullname)
        return self._repoclient

    @property
    def name(self):
        return self.fullname.split("/", 1)[-1]

    @property
    def type(self):
        if self.name in ["home"]:
            return "home"
        elif self.name.startswith("proj"):
            return "proj"
        elif self.name.startswith("org_"):
            return "org"
        elif self.name.startswith("www"):
            return "www"
        elif self.name.startswith("doc"):
            return "doc"
        elif self.name.startswith("cockpit"):
            return "cockpit"
        else:
            return "code"

    @property
    def labelnames(self):
        return [item.name for item in self.labels]

    @property
    def labels(self):
        if self._labels is None:
            self._labels = [item for item in self.api.get_labels()]
        return self._labels

    @property
    def stories(self):
        # walk overall issues find the stories (based on type)
        # only for home type repo, otherwise return []
        # if not self.fullname.lower().endswith('home'):
        #     return []

        if self.issues == []:
            self.loadIssues()

        def filter(issue):
            return issue.type == 'story'
        issues = self.issues_by_type(filter)
        return issues['story']

    @property
    def tasks(self):
        # walk overall issues find the stories (based on type)
        # only for home type repo, otherwise return []
        # if not self.fullname.lower().endswith('home'):
        #     return []

        if self.issues == []:
            self.loadIssues()

        def filter(issue):
            return issue.type == 'task'
        issues = self.issues_by_type(filter)
        return issues['task']

    def labelsSet(self, labels2set,ignoreDelete=["p_"],delete=True):
        """
        @param ignore all labels starting with ignore will not be deleted
        """

        for item in labels2set:
            if not j.data.types.string.check(item):
                raise j.exceptions.Input(
                    "Labels to set need to be in string format, found:%s" %
                    labels2set)

        # walk over github existing labels
        labelstowalk = copy.copy(self.labels)
        for item in labelstowalk:
            name = item.name.lower()
            if name not in labels2set:
                # label in repo does not correspond to label we need
                if name in replacelabels:
                    nameNew = replacelabels[item.name.lower()]
                    if nameNew not in self.labelnames:
                        color = self.getColor(name)
                        self.logger.info(
                            "change label in repo: %s oldlabel:'%s' to:'%s' color:%s" %
                            (self.fullname, item.name, nameNew, color))
                        item.edit(nameNew, color)
                        self._labels = None
                else:
                    # no replacement
                    name = 'type_unknown'
                    color = self.getColor(name)
                    try:
                        item.edit(name, color)
                    except:
                        item.delete()
                    self._labels = None

        # walk over new labels we need to set
        for name in labels2set:
            if name not in self.labelnames:
                # does not exist yet in repo
                color = self.getColor(name)
                self.logger.info(
                    "create label: %s %s %s" %
                    (self.fullname, name, color))
                self.api.create_label(name, color)
                self._labels = None

        name = ""

        if delete:
            labelstowalk = copy.copy(self.labels)
            for item in labelstowalk:
                if item.name not in labels2set:
                    self.logger.info("delete label: %s %s" % (self.fullname, item.name))
                    ignoreDeleteDo=False
                    for filteritem in ignoreDelete:
                        if item.name.startswith(filteritem):
                            ignoreDeleteDo=True
                    if ignoreDeleteDo==False:
                        from pudb import set_trace; set_trace() 
                        item.delete()
                    self._labels = None

        # check the colors
        labelstowalk = copy.copy(self.labels)
        for item in labelstowalk:
            # we recognise the label
            self.logger.info(
                "check color of repo:%s labelname:'%s'" %
                (self.fullname, item.name))
            color = self.getColor(item.name)
            if item.color != color:
                self.logger.info(
                    "change label color for repo %s %s" %
                    (item.name, color))
                item.edit(item.name, color)
                self._labels = None

    def getLabel(self, name):
        for item in self.labels:
            self.logger.info("%s:look for name:'%s'" % (item.name, name))
            if item.name == name:
                return item
        raise j.exceptions.Input("Dit not find label: '%s'" % name)

    def getIssueFromMarkdown(self, issueNumber, markdown):
        i = self.getIssue(issueNumber, False)
        i._loadMD(markdown)
        self.issues.append(i)
        return i

    def getIssue(self, issueNumber, die=True):
        for issue in self.issues:
            if issue.number == issueNumber:
                return issue
        # not found in cache, try to load from github
        github_issue = self.api.get_issue(issueNumber)

        if github_issue:
            issue = Issue(repo=self, githubObj=github_issue)
            self.issues.append(issue)
            return issue

        if die:
            raise j.exceptions.Input("cannot find issue:%s in repo:%s" % (issueNumber, self))
        else:
            i = Issue(self)
            i._ddict["number"] = issueNumber
            return i

    def issues_by_type(self, filter=None):
        """
        filter is method which takes  issue as argument and returns True or False to include
        """
        res = {}
        for item in self.types:
            res[item] = []
            for issue in self.issues:
                if issue.type == item:
                    if filter is None or filter(issue):
                        res[item].append(issue)
        return res

    def issues_by_state(self, filter=None):
        """
        filter is method which takes  issue as argument and returns True or False to include
        """
        res = {}
        for item in self.states:
            res[item] = {}
            for issue in self.issues:
                if issue.state == item:
                    if filter is None or filter(issue):
                        res[item].append(issue)
        return res

    def issues_by_priority(self, filter=None):
        """
        filter is method which takes  issue as argument and returns True or False to include
        """
        res = {}
        for item in self.priorities:
            res[item] = {}
            for issue in self.issues:
                if issue.priority == item:
                    if filter is None or filter(issue):
                        res[item].append(issue)
        return res

    def issues_by_type_state(self, filter=None, collapsepriority=True):
        """
        filter is method which takes  issue as argument and returns True or False to include
        returns dict of dict keys: type, state and then issues sorted following priority
        """
        res = {}
        for type in self.types:
            res[type] = {}
            for state in self.states:
                res[type][state] = {}
                for priority in self.priorities:
                    res[type][state][priority] = []
                    for issue in self.issues:
                        if issue.type == type and issue.state == state:
                            if filter is None or filter(issue):
                                res[type][state][priority].append(issue)
                if collapsepriority:
                    # sort the issues following priority
                    temp = res[type][state]
                    res[type][state] = []
                    for priority in self.priorities:
                        for subitem in temp[priority]:
                            res[type][state].append(subitem)
        return res

    @property
    def types(self):
        return ["story", "ticket", "task", "bug",
                "feature", "question", "monitor", "unknown"]

    @property
    def priorities(self):
        return ["critical", "urgent", "normal", "minor"]

    @property
    def states(self):
        return ["new", "accepted", "question",
                "inprogress", "verification", "closed"]

    @property
    def milestones(self):
        if self._milestones == []:
            for ms in self.api.get_milestones():
                milestoneObj = self.getMilestoneFromGithubObj(githubObj=ms)
                self._milestones.append(milestoneObj)
        return self._milestones

    @property
    def milestoneTitles(self):
        return [item.title for item in self.milestones]

    @property
    def milestoneNames(self):
        return [item.name for item in self.milestones]

    def getMilestoneFromGithubObj(self, githubObj):

        found = None
        for item in self._milestones:
            if int(githubObj.number) == int(item.number):
                found = item

        if found is None:
            obj = RepoMilestone(self, githubObj=githubObj)
            obj._ddict["number"] = githubObj.number
            self._milestones.append(obj)
            return obj
        else:
            return found

    def getMilestone(self, name, die=True):
        name = name.strip()
        if name == "":
            raise j.exceptions.Input("Name cannot be empty.")
        for item in self.milestones:
            if name == item.name.strip() or name == item.title.strip():
                return item
        if die:
            raise j.exceptions.Input("Could not find milestone with name:%s" % name)
        else:
            return None

    def createMilestone(self, name, title, description="", deadline="", owner=""):

        def getBody(descr, name, owner):
            out = "%s\n\n" % descr
            out += "## name:%s\n" % name
            out += "## owner:%s\n" % owner
            return out

        ms = None
        for s in [name, title]:
            ms = self.getMilestone(s, die=False)
            if ms is not None:
                break

        if ms is not None:
            if ms.title != title:
                ms.title = title
            # if ms.deadline != deadline:
            #     ms.deadline = deadline
            tocheck = getBody(description.strip(), name, owner)
            if ms.body.strip() != tocheck.strip():
                ms.body = tocheck
        else:
            self._milestones = []
            due = j.data.time.epoch2pythonDateTime(int(j.data.time.any2epoch(deadline)))
            self.logger.info("Create milestone on %s: %s" % (self, title))
            body = getBody(description.strip(), name, owner)
            # workaround for https://github.com/PyGithub/PyGithub/issues/396
            milestone = self.api.create_milestone(title=title, description=body)  # , due_on=due)
            milestone.edit(title=title, due_on=due)

    def deleteMilestone(self, name):
        if name.strip() == "":
            raise j.exceptions.Input("Name cannot be empty.")
        self.logger.info("Delete milestone on %s: '%s'" % (self, name))
        try:
            ms = self.getMilestone(name)
            ms.api.delete()
            self._milestones = []
        except Input:
            self.logger.info("Milestone '%s' doesn't exist. no need to delete" % name)

    def _labelSubset(self, cat):
        res = []
        for item in self.labels:
            if item.startswith(cat):
                item = item[len(cat):].strip("_")
                res.append(item)
        res.sort()
        return res

    def getColor(self, name):

        # colors={'state_question':'fbca04',
        #  'priority_urgent':'d93f0b',
        #  'state_verification':'006b75',
        #  'priority_minor':'',
        #  'type_task':'',
        #  'type_feature':'',
        #  'process_wontfix':"ffffff",
        #  'priority_critical':"b60205",
        #  'state_inprogress':"e6e6e6",
        #  'priority_normal':"e6e6e6",
        #  'type_story':"ee9a00",
        #  'process_duplicate':"",
        #  'state_closed':"5319e7",
        #  'type_bug':"fc2929",
        #  'state_accepted':"0e8a16",
        #  'type_question':"fbca04",
        #  'state_new':"1d76db"}

        if name.startswith("state"):
            return("c2e0c6")  # light green

        if name.startswith("process"):
            return("d4c5f9")  # light purple

        if name.startswith("type"):
            return("fef2c0")  # light yellow

        if name.startswith("priority_critical"):
            return("b60205")

        if name.startswith("priority_urgent"):
            return("d93f0b")

        if name.startswith("priority"):
            return("f9d0c4")  # roze

        # if name in colors:
        #     color=colors[name]
        #     if color=="":
        #         color="ffffff"
        #     return color

        return "ffffff"

    def process_issues(self, issues=[]):
        """
        find all todo's
        cmds supported

        !! prio $prio  ($prio is checked on first 4 letters, e.g. critical, or crit matches same)
        !! p $prio (alias above)

        !! move gig-projects/home (move issue to this project, try to keep milestones, labels, ...)

        """
        # close command is irrelevent, if we have time to write a comment '!!close'
        # Then we have time to click the close button the issue directly

        # def close(issue, comment=''):
        #     if comment == '':
        #         comment = 'Automatic closing'
        #     issue.api.create_comment(comment)
        #     issue.api.edit(state='close')

        priorities_map = {
            'crit': 'critical',
            'mino': 'minor',
            'norm': 'normal',
            'urge': 'urgent',
        }

        stories_name = [story.story_name for story in self.stories]

        def get_story(name):
            for story in self.stories:
                if story.story_name == name:
                    return story

        # process commands & execute
        if issues == []:
            issues = self.issues

        for issue in issues:
            for todo in issue.todo:
                try:
                    cmd, args = todo.split(' ', 1)
                except Exception as e:
                    self.logger.warning("%s, cannot process todo for %s" % (str(e), todo))
                    continue

                if cmd == 'move':
                    destination_repo = self.client.getRepo(args)
                    issue.move_to_repo(repo=destination_repo)
                    if issue.isStory:
                        for task in issue.tasks:
                            task.move_to_repo(repo=destination_repo)

                elif cmd == 'p' or cmd == 'prio':
                    if len(args) == 4:
                        prio = priorities_map[args]
                    else:
                        prio = args

                    if prio not in priorities_map.values():
                        # Try to set
                        self.logger.warning(
                            'Try to set an non supported priority : %s' % prio)
                        continue

                    prio = "priority_%s" % prio
                    if prio not in issue.labels:
                        labels = issue.labels.copy()
                        labels.append(prio)
                        issue.labels = labels
                # elif cmd == 'delete':
                #     delete(self, args)
                else:
                    self.logger.warning("command %s not supported" % cmd)

            # Logic after this point is only for home and org repo
            valid = False
            for typ in ['org_', 'proj_']:
                if not self.fullname.lower().startswith(typ):
                    valid = True
                    break
            if not valid:
                continue

            start = issue.title.split(":", 1)[0]
            if start not in stories_name:
                continue
            story = get_story(start)
            if "type_task" not in issue.labels:
                labels = issue.labels.copy()
                labels.append("type_task")
                issue.labels = labels

            if "type_story" not in story.labels:
                labels = story.labels.copy()
                labels.append("type_story")
                story.labels = labels

            # creaet link between story and tasks
            issue.link_to_story(story)
            story.add_task(issue)

    def loadIssues(self):
        for item in self.api.get_issues():
            self.issues.append(Issue(self, githubObj=item))
        self.issues_loaded=True
        return self.issues

    def serialize2Markdown(self,path):

        md=j.data.markdown.getDocument()
        md.addMDHeader(1, "Issues")

        res=self.issues_by_type_state()

        for type in self.types:
            typeheader=False
            for state in self.states:
                issues=res[type][state]
                stateheader=False
                for issue in issues:
                    if typeheader==False:
                        md.addMDHeader(2, "Type:%s"%type)
                        typeheader=True
                    if stateheader==False:
                        md.addMDHeader(3, "State:%s"%state)
                        stateheader=True
                    md.addMDBlock(str(issue.getMarkdown()))

        j.sal.fs.writeFile(path,str(md))


    def __str__(self):
        return "gitrepo:%s" % self.fullname

    __repr__ = __str__
