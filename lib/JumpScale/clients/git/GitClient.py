from JumpScale import j


class GitClient(object):

    def __init__(self, baseDir):  # NOQA

        self._repo = None
        if not j.sal.fs.exists(path=baseDir):
            raise j.exceptions.Input("git repo on %s not found." % baseDir)

        # split path to find parts
        baseDir = baseDir.replace("\\", "/")  # NOQA
        baseDir = baseDir.rstrip("/")

        while ".git" not in j.sal.fs.listDirsInDir(baseDir, recursive=False, dirNameOnly=True, findDirectorySymlinks=True):
            baseDir = j.sal.fs.getParent(baseDir)
            
            if baseDir == "/":
                break



        baseDir=baseDir.rstrip("/")

        if baseDir.strip()=="":
            raise j.exceptions.RuntimeError("could not find basepath for .git in %s"%baseDir)

        if baseDir.find("/code/") == -1:
            raise j.exceptions.Input(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")
        base = baseDir.split("/code/", 1)[1]

        if base.count("/") != 2:
            raise j.exceptions.Input(
                "jumpscale code management always requires path in form of $somewhere/code/$type/$account/$reponame")


        self.type, self.account, self.name = base.split("/",2)

        self.baseDir=baseDir

        # if len(self.repo.remotes) != 1:
        #     raise j.exceptions.Input("git repo on %s is corrupt could not find remote url" % baseDir)

    def __repr__(self):
        return str(self.__dict__)

    def __str__(self):
        return self.__repr__

    @property
    def remoteUrl(self):
        return self.repo.remotes[0].url

    @property
    def branchName(self):
        return self.repo.git.rev_parse('HEAD', abbrev_ref=True)

    @property
    def repo(self):
        # Load git when we absolutly need it cause it does not work in gevent mode
        import git
        if not self._repo:
            j.sal.process.execute("git config --global http.sslVerify false")
            if not j.sal.fs.exists(self.baseDir):
                self._clone()
            else:
                self._repo = git.Repo(self.baseDir)
        return self._repo

    def init(self):
        self.repo

    def switchBranch(self, branchName, create=True):  # NOQA
        if create:
            import git
            try:
                self.repo.git.branch(branchName)
            except git.GitCommandError:
                # probably branch exists.
                pass
        self.repo.git.checkout(branchName)

    def checkFilesWaitingForCommit(self):
        res=self.getModifiedFiles()
        if res["D"]!=[]:
            return True
        if res["M"]!=[]:
            return True
        if res["N"]!=[]:
            return True
        if res["R"]!=[]:
            return True

    def getModifiedFiles(self,collapse=False,ignore=[]):
        result = {}
        result["D"] = []
        result["N"] = []
        result["M"] = []
        result["R"] = []

        def checkignore(ignore,path):
            for item in ignore:
                if path.find(item)!=-1:
                    return True
            return False


        cmd = "cd %s;git status --porcelain" % self.baseDir
        rc, out = j.sal.process.execute(cmd)
        for item in out.split("\n"):
            item = item.strip()
            if item == '':
                continue
            state, _, _file = item.partition(" ")
            if state == '??':
                if checkignore(ignore,_file):
                    continue
                result["N"].append(_file)

        for diff in self.repo.index.diff(None):
            path = diff.a_blob.path
            if checkignore(ignore,path):
                continue
            if diff.deleted_file:
                result["D"].append(path)
            elif diff.new_file:
                result["N"].append(path)
            elif diff.renamed:
                result["R"].append(path)
            else:
                result["M"].append(path)

        if collapse:
            result=result["N"]+result["M"]+result["R"]+result["D"]
        return result

    def getUntrackedFiles(self):
        return self.repo.untracked_files

    def checkout(self,path):
        cmd = 'cd %s;git checkout %s' % (self.baseDir,path)
        j.sal.process.execute(cmd)

    def addRemoveFiles(self):
        cmd = 'cd %s;git add -A :/' % self.baseDir
        j.sal.process.execute(cmd)
        # result=self.getModifiedFiles()
        # self.removeFiles(result["D"])
        # self.addFiles(result["N"])

    def addFiles(self, files=[]):
        if files != []:
            self.repo.index.add(files)

    def removeFiles(self, files=[]):
        if files != []:
            self.repo.index.remove(files)

    def pull(self):
        self.repo.git.pull()

    def fetch(self):
        self.repo.git.fetch()

    def commit(self, message='', addremove=True):
        if addremove:
            self.addRemoveFiles()
        return self.repo.index.commit(message)

    def push(self, force=False):
        if force:
            self.repo.git.push('-f')
        else:
            self.repo.git.push('--all')

    def getChangedFiles(self, fromref='', toref='', fromepoch=None, toepoch=None, author=None, paths=[]):
        """
        list all changed files since ref & epoch (use both)
        @param fromref = commit ref to start from
        @param toref = commit ref to end at
        @param author if limited to author
        @param path if only list changed files in paths
        @param fromepoch = starting epoch
        @param toepoch = ending epoch
        @return
        """
        commits = self.getCommitRefs(fromref=fromref, toref=toref, fromepoch=fromepoch, toepoch=toepoch, author=author, paths=paths,files=True)
        files = [f for commit in commits for f in commit[3]]
        return list(set(files))

    def getCommitRefs(self, fromref='', toref='', fromepoch=None, toepoch=None, author=None, paths=None,files=False):
        """
        @return [[$epoch, $ref, $author]] if no files (default)
        @return [[$epoch, $ref, $author, $files]] if files
        @param files = True means will list the files
        """
        kwargs = {'branches': [self.branchName]}
        if fromepoch:
            kwargs["max-age"] = fromepoch
        if toepoch:
            kwargs['min-age'] = toepoch
        if fromref or toref:
            if fromref and not toref:
                kwargs['rev'] = '%s' % fromref
            elif fromref and toref:
                kwargs['rev'] = '%s..%s' % (fromref, toref)
        if author:
            kwargs['author'] = author
        commits = list()
        for commit in list(self.repo.iter_commits(paths=paths, **kwargs)):
            if files:
                commits.append((commit.authored_date, commit.hexsha, commit.author.name, list(commit.stats.files.keys())))
            else:
                commits.append((commit.authored_date, commit.hexsha, commit.author.name))
        return commits

    def getFileChanges(self, path):
        """
        @return lines which got changed
        format:
        {'line': [{'commit sha': '', 'author': 'author'}]}
        """
        # TODO (*3*) limit to max number?
        diffs = dict()
        blame = self.repo.blame(self.branchName, path)
        for commit, lines in blame:
            for line in lines:
                diffs[line] = list() if line not in diffs else diffs[line]
                diffs[line].append({'author': commit.author.name, 'commit': commit.hexsha})
                
        return diffs



    def patchGitignore(self):
        gitignore = '''# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]

# C extensions
*.so

# Distribution / packaging
.Python
develop-eggs/
eggs/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
.tox/
.coverage
.cache
nosetests.xml
coverage.xml

# Translations
*.mo

# Mr Developer
.mr.developer.cfg
.project
.pydevproject

# Rope
.ropeproject

# Django stuff:
*.log
*.pot

# Sphinx documentation
docs/_build/
'''
        ignorefilepath = j.sal.fs.joinPaths(self.baseDir, '.gitignore')
        if not j.sal.fs.exists(ignorefilepath):
            j.sal.fs.writeFile(ignorefilepath, gitignore)
        else:
            lines = gitignore.splitlines()
            inn = j.sal.fs.fileGetContents(ignorefilepath)
            lines = inn.splitlines()
            linesout = []
            for line in lines:
                if line.strip():
                    linesout.append(line)
            for line in lines:
                if line not in lines and line.strip():
                    linesout.append(line)
            out = '\n'.join(linesout)
            if out.strip() != inn.strip():
                j.sal.fs.writeFile(ignorefilepath, out)
