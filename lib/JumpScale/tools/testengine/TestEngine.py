import sys
from JumpScale import j
import imp
import time
import unittest
import new
from io import BytesIO

class Tee:
    def __init__(self, *fobjs):
        self.fileobjs = fobjs

    def write(self, data):
        for fileobj in self.fileobjs:
            fileobj.write(data)

    def flush(self):
        for fileobj in self.fileobjs:
            fileobj.flush()


PRINTSTR = "\r%s %s"

class TestResult(unittest.result.TestResult):
    def __init__(self, debug=False):
        super(TestResult, self).__init__()
        self.tests = dict()
        self.errors = dict()
        self.failure = dict()
        self.skipped = dict()
        self._debug = debug
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def startTest(self, test):
        buffer = BytesIO()
        self.tests[test] = buffer
        if self._debug:
            sys.stdout = Tee(self._original_stdout, buffer)
            sys.stderr = Tee(self._original_stderr, buffer)
        else:
            sys.stdout = buffer
            sys.stderr = buffer

    def printStatus(self, test, state=None):
        print(test)
        if state:
            print((PRINTSTR % (state, test._testMethodName)))
        else:
            print((PRINTSTR % (' ', test._testMethodName)))
        sys.stdout.flush()

    def addSkip(self, test, reason):
        self._restore()
        self.printStatus(test, 'S')
        self.skipped[test] = reason

    def addFailure(self, test, err):
        self._restore()
        self.printStatus(test, 'F')
        self.failure[test] = err
        self._checkDebug(test, err)

    def _checkDebug(self, test, err):
        if self._debug:
            if test in self.tests:
                print((self.tests[test].getvalue()))
                print((j.errorconditionhandler.parsePythonExceptionObject(err[1], err[2])))
            j.application.stop(1)

    def addError(self, test, err):
        self._restore()
        self.printStatus(test, 'E')
        self.errors[test] = err
        self._checkDebug(test, err)

    def addSuccess(self, test):
        self._restore()
        self.printStatus(test, "\u2713")

    def stopTest(self, test):
        self._restore()

    def _restore(self):
        sys.stderr = self._original_stdout
        sys.stdout = self._original_stdout

class Test:
    def __init__(self,db,testmodule):
        self.db=db
        self.testmodule = testmodule
        self.eco=None

    def execute(self,testrunname,debug=False):
        print(("\n##TEST:%s %s"%(self.db.organization,self.db.name)))
        res = {'total': 0, 'error': 0, 'success': 0, 'failed': 0 }
        self.db.starttime = time.time() 
        self.db.state = 'OK'
        result = TestResult(debug)
        suite = unittest.defaultTestLoader.loadTestsFromModule(self.testmodule)
        suite.run(result)
        for test, buffer in list(result.tests.items()):
            res['total'] += 1
            name = test._testMethodName[5:]
            self.db.output[name]=buffer.getvalue()
            if test in result.errors or test in result.failure:
                if test in result.errors:
                    res['error'] += 1
                    error = result.errors[test]
                    self.db.teststates[name] = 'ERROR'
                    self.db.state = 'ERROR'
                else:
                    res['failed'] += 1
                    error = result.failure[test]
                    self.db.teststates[name] = 'FAILURE'
                    if self.db.state != 'ERROR':
                        self.db.state == 'FAILURE'
                with j.logger.nostdout():
                    eco=j.errorconditionhandler.parsePythonExceptionObject(error[1], error[2])
                    eco.tags="testrunner testrun:%s org:%s testgroup:%s testname:%s testpath:%s" % (self.db.testrun,\
                        self.db.organization, self.db.name,name,self.db.path)
                    eco.process()
                    self.db.result[name] = eco.guid
                print(("Fail in test %s" % name))
                print((self.db.output[name]))
                print(eco)
            else:
                res['success'] += 1
                self.db.teststates[name] = 'OK'
            pass
        self.db.endtime = time.time()
        print('')
        return res

    def __str__(self):
        out=""
        for key,val in list(self.db.__dict__.items()):
            if key[0]!="_" and key not in ["source","output"]:
                out+="%-35s :  %s\n"%(key,val)
        items=out.split("\n")
        items.sort()
        return "\n".join(items)

    __repr__ = __str__


class FakeTestObj:
    def __init__(self):
        self.source = dict()
        self.output = dict()
        self.teststates = dict()
        self.result = dict()

class TestEngine:
    def __init__(self):
        self.__jslocation__ = "j.tools.testengine"
        self.paths=[]
        self.tests=[]
        self.outputpath="%s/apps/gridportal/base/Tests/TestRuns/"%j.dirs.base

    def initTests(self,noOsis, osisip="127.0.0.1",login="",passwd=""): #@todo implement remote osis
        self.noOsis = noOsis

    def _patchTest(self, testmod):
        if hasattr(testmod, 'TEST') and not isinstance(testmod.TEST, unittest.TestCase):
            testmod.TEST = new.classobj('TEST', (testmod.TEST, unittest.TestCase), {})

    def runTests(self,testrunname=None,debug=False):

        if testrunname==None:
            testrunname=j.data.time.getLocalTimeHRForFilesystem()

        for path in self.paths:
            print(("scan dir: %s"%path))
            if j.sal.fs.isDir(path):
                for item in j.sal.fs.listFilesInDir(path,filter="*__test.py",recursive=True):
                    self.testFile(testrunname, item)
            elif j.sal.fs.isFile(path):
                self.testFile(testrunname, path)

        priority={}
        for test in self.tests:
            if test.db.priority not in priority:
                priority[test.db.priority]=[]    
            priority[test.db.priority].append(test)
        prio=list(priority.keys())
        prio.sort()
        results = list()
        for key in prio:
            for test in priority[key]:
                #now sorted
                # print test
                results.append(test.execute(testrunname=testrunname,debug=debug))
                if not self.noOsis:
                    guid, change, new = self.osis.set(test.db)
        total = sum(x['total'] for x in results)
        error = sum(x['error'] for x in results)
        failed = sum(x['failed'] for x in results)
        print(("Ran %s tests" % total))
        if error:
            print(('%s Error' % error))
        if failed:
            print(('%s Failed' % failed))
        print('')


    def testFile(self, testrunname, filepath):
        if self.noOsis:
            testdb = FakeTestObj() 
        else:
            testdb=self.osis.new()

        name=j.sal.fs.getBaseName(filepath).replace("__test.py","").lower()
        testmod = imp.load_source(name, filepath)
        self._patchTest(testmod)

        if not hasattr(testmod, 'enable') or not testmod.enable:
            return

        test=Test(testdb,testmod)

        test.db.author=testmod.author
        test.db.descr=testmod.descr.strip()
        test.db.organization=testmod.organization
        test.db.version=testmod.version
        test.db.categories=testmod.category.split(",")
        test.db.enable=testmod.enable
        test.db.license=testmod.license
        test.db.priority=testmod.priority
        test.db.gid=j.application.whoAmI.gid
        test.db.nid=j.application.whoAmI.nid
        test.db.state = 'INIT'
        test.db.teststates = dict()
        test.db.testrun=testrunname
        test.db.name=name
        test.db.path=filepath
        test.db.priority=testmod.priority
        test.db.id=0

        C=j.sal.fs.fileGetContents(filepath)
        methods=j.tools.code.regex.extractBlocks(C,["def test"])
        for method in methods:
            methodname=method.split("\n")[0][len("    def test_"):].split("(")[0]
            methodsource="\n".join([item.strip() for item in method.split("\n")[1:] if item.strip()!=""])
            test.db.source[methodname]=methodsource

        if not self.noOsis:
            guid, _, _ = self.osis.set(test.db)
            test.db = self.osis.get(guid)
        self.tests.append(test)





