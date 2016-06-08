from JumpScale import j
fs=j.sal.fs
from nose.tools import assert_equal, assert_not_equal, assert_raises, raises, assert_in, assert_not_in, assert_greater
import os
import shutil
import os.path as path
import codecs
import hashlib
import glob
from functools import partial
import tarfile
import sys


def hashfile(p):
    with open(p, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def isexec(p):
    return os.access(p, os.X_OK)
def bomify(txt):
    return codecs.BOM_UTF8+bytes(txt, encoding='utf-8')

def stripbom(b):
    return b.decode(encoding='utf_8_sig')

def readfile(f):
    with open(f) as fp:
        return fp.read()

def writetofile(f, s):
    with open(f, 'w') as fp:
        fp.write(s)

def touchone(f):
    open(f, 'w').close()

def touchmany(fs):
    list(map(touchone,fs))

def removeone(f):
    if path.exists(f):
        if os.path.islink(f):
            os.unlink(f)
        else:
            os.remove(f)

def removemany(fs):
    list(map(os.remove, fs))

def getcwdfpath(f):
    return os.getcwd()+f

def tmpify(f):
    return '/tmp/'+f


def getfilesindir(f):
    return list(filter(path.isfile, [f+os.sep+x for x in os.listdir(f)]) )


def getdirsindir(f):
    return list(filter(path.isdir, [f+os.sep+x for x in os.listdir(f)]) )

def getallindir(f):
    return list([x for x in os.listdir(f) if path.isfile(f+os.sep+x) or path.isdir(f+os.sep+x)])

def isascii(filename):
    try:
        with open(filename, encoding='ascii') as f:
            f.read()
            return True
    except UnicodeDecodeError:
            return False

def isbinary(filename):
    return not isascii(filename)

cur=os.getcwd()

class TestFS(object):
    FILES=['f1.py', 'f2.py', 'f3.py']
    FILE='/tmp/hello.py'
    #create 2 files in the start.
    def setUp(self):
        touchmany(TestFS.FILES)
        txt="""
a=1
b=2
name='someone'

def inc(x):
    return x+1

        """
        with open(TestFS.FILE, 'w') as f:
            f.write(txt)

    #delete the 2 files created.
    def tearDown(self):
        os.chdir(cur)
        removemany(TestFS.FILES)
        removeone(TestFS.FILE)


    def test_validateFilename_zerolength(self):
        assert_equal(fs.validateFilename(''), False)

    def test_validateFilename_gt255(self):
        assert_equal(fs.validateFilename('f'*256), False)

    def test_validateFilename_lt255(self):
        assert_equal(fs.validateFilename('f'*255), True)

    def test_validateFilename_null(self):
        assert_equal(fs.validateFilename('f\0'), False)

    def test_validateFilename_slash(self):
        assert_equal(fs.validateFilename('f/z'), False)

    def test_statPath_raises_typeerror_on_none(self):
        assert_raises(TypeError, fs.statPath, None)

    def test_statPath_raises_oserror_on_existent(self):
        assert_raises(OSError, fs.statPath, '000000me')

    def test_statPath_returns_stat(self):
        st = fs.statPath("/bin")
        assert_equal(isinstance(st, os.stat_result), True)

    def test_pathRemoveDirPart(self):
        p = "/home/ahmed/wspace/file1"
        assert_equal(fs.pathRemoveDirPart(p, "/home/ahmed"), "wspace/file1")

    def test_targzCompress_sourceDoesntExist(self):
        assert_raises(j.exceptions.RuntimeError, fs.targzCompress, "creepypathdoesntexists", "dest")

    def test_targzCompress(self):
        os.chdir("/tmp")
        if not os.path.exists("testcomp"):
            os.mkdir("testcomp")
        files=map(tmpify, ['testcomp/f1', 'testcomp/f2', 'testcomp/f3', 'testcomp/f4'])
        touchmany(files)
        fs.targzCompress("testcomp", "comp.tar.gz")
        assert_equal(os.path.exists("comp.tar.gz"), True)

        removeone("comp.tar.gz")
        removemany(files)
        shutil.rmtree("testcomp")


    def test_targzCompressDestInTar(self):
        os.chdir("/tmp")
        if not os.path.exists("testcomp"):
            os.mkdir("testcomp")
        files = map(tmpify, ['testcomp/f1', 'testcomp/f2', 'testcomp/f3', 'testcomp/f4'])
        touchmany(files)
        fs.targzCompress("testcomp", "comp.tar.gz", destInTar='subcomp')
        assert_equal(os.path.exists("comp.tar.gz"), True)

        tf=tarfile.open("comp.tar.gz")
        assert_equal(os.path.commonpath(tf.getnames()),  'subcomp')
        removeone("comp.tar.gz")
        removemany(files)
        shutil.rmtree("testcomp")

    def test_targzUncompress(self):
        os.chdir("/tmp")
        if not os.path.exists("testcomp"):
            os.mkdir("testcomp")
        files = map(tmpify, ['testcomp/f1', 'testcomp/f2', 'testcomp/f3', 'testcomp/f4'])
        touchmany(files)
        fs.targzCompress("testcomp", "comp.tar.gz", destInTar='subcomp')
        assert_equal(os.path.exists("comp.tar.gz"), True)

        fs.targzUncompress("comp.tar.gz", "outdir")
        assert_equal(os.path.exists("outdir"), True)
        assert_equal(os.path.isdir("outdir"), True)
        assert_equal(len(glob.glob('outdir/subcomp/*')), 4)
        removeone("comp.tar.gz")
        removemany(files)
        shutil.rmtree("testcomp")
        shutil.rmtree("outdir")

    def test_gzip(self):
        f1="fz"
        writetofile(f1, "helloaa da text")
        fs.gzip(f1, "fz.gzipped")
        assert_equal(os.path.exists("fz.gzipped"), True)
        removemany(["fz", "fz.gzipped"])

    def test_gunzip(self):
        f1="fz"
        writetofile(f1, "helloaa da text")
        fs.gzip(f1, "fz.gzipped")
        assert_equal(os.path.exists("fz.gzipped"), True)
        fs.gunzip("fz.gzipped", "fzout")
        assert_equal(os.path.exists("fzout",), True)
        assert_equal(readfile(f1), readfile("fzout"))
        removemany([f1, "fzout", "fz.gzipped"])


    def test_grep(self):
        writetofile("f1", "python 33")
        writetofile("f2", "hey 24")
        writetofile("f3", "oh 41")
        oldstdout=sys.stdout
        sys.stdout=open("/tmp/grepresult", "w")
        fs.grep("f*", "\w+ \d\d")
        sys.stdout.close()

        assert_greater(len(readfile("/tmp/grepresult")), 0)

        sys.stdout=oldstdout
        removemany(["f1", "f2", "f3", "/tmp/grepresult"])


    def test_copyFile(self):
        t1=tmpify("file1")
        t2=tmpify("file1copy")

        #write somedata to t1
        writetofile(t1, "Hello This is a TEXT")
        fs.copyFile(t1, t2)
        #assert it exists
        assert_equal(path.exists(t2), True)
        assert_equal(path.getsize(t1), path.getsize(t2))

    def test_removeIrrelevantFiles(self):
        #touch some irrelevant
        if not os.path.exists("tdir"):
            os.mkdir("tdir")
        files = ['tdir/p1.pyc', 'tdir/p2.pyc', 'tdir/p2.bak', 'tdir/p3.py', 'tdir/p3.bak']
        touchmany(files)
        fs.removeIrrelevantFiles("tdir")
        assert_equal(len(glob.glob("tdir/*.pyc")), 0)
        assert_equal(len(glob.glob("tdir/*.bak")), 0)
        shutil.rmtree("tdir")

    def test_removeLinks(self):
        #create somelinks
        links=list(map(tmpify, ['link1', 'link2','link3', 'link4']))
        list(map(partial(os.symlink, 'f1.py'), links))
        assert_equal(len(glob.glob("/tmp/link*")), 4)
        fs.removeLinks("/tmp")
        assert_equal(len(glob.glob("/tmp/link*")), 0)

    def test_renameDir(self):
        if not os.path.exists("tdir"):
            os.mkdir("tdir")

        fs.renameDir("tdir", "tdirrenamed")
        assert_equal(os.path.exists("tdir"), False)
        assert_equal(os.path.exists("tdirrenamed"), True)

        os.rmdir("tdirrenamed")

    def test_changeFileNames(self):
        #makes somefiles
        files=list(map(tmpify, ["fx1", "fx2", "fx3", "fx4"]))
        touchmany(files)
        fs.changeFileNames("fx", "goodboyfile", "/tmp")
        assert_equal(len(glob.glob("/tmp/fx*")), 0)
        globbed=glob.glob("/tmp/goodboy*")
        assert_equal(len(globbed), len(files))
        removemany(globbed)

    def test_constructFilePathFromArray(self):
        arr=["/home", "ahmed", "file.py"]
        cpath=fs.constructFilePathFromArray(arr)
        assert_equal(cpath, os.path.join(*arr))
        assert_equal(cpath.endswith("/"), False)

    def test_constructDirPathFromArray(self):
        arr=["/home", "ahmed", "wspace"]
        cpath=fs.constructDirPathFromArray(arr)
        assert_equal(cpath, os.path.join(*arr)+os.path.sep)
        assert_equal(cpath.endswith("/"), True)


    def test_getBaseName(self):
        assert_equal(path.basename(TestFS.FILE), fs.getBaseName(TestFS.FILE))

    def test_getDirName(self):
        assert_equal(path.normpath(path.dirname(TestFS.FILE)), path.normpath(fs.getDirName(TestFS.FILE)))

    def test_getFileExtension(self):
        assert_in(fs.getFileExtension(TestFS.FILE), path.splitext(TestFS.FILE)[1]) #splitext includes a dot

    def test_exists(self):
        assert_equal(fs.exists(TestFS.FILE), True)

    def test_exists_raises_typeerror(self):
        assert_raises(TypeError, fs.exists, None)

    def test_isDir(self):
        assert_equal(fs.isDir('/'), True)
        assert_equal(fs.isDir(TestFS.FILE), False)

    def test_isFile(self):
        assert_equal(fs.isFile('/'), False)
        assert_equal(fs.isFile(TestFS.FILE), True)

    def test_hardlinkFile(self):
        fs.hardlinkFile('f1.py', 'f1hard.py')
        assert_equal(os.path.exists('f1hard.py'), True)
        os.remove('f1hard.py')

    def test_hardlinkFileNoneSource(self):
        assert_raises(TypeError, fs.hardlinkFile, None, 'whatever')

    def test_symlink(self):
        fs.symlink("f1.py", "f1symlink")
        assert_equal(path.islink("f1symlink"), True)
        removeone("f1symlink")

    def test_symlink_raises_typeerror(self):
        assert_raises(TypeError, fs.symlink, None, "nonelink")

    def test_isLink(self):

        os.symlink('f1.py', 'f1linked.py')
        assert_equal(path.islink('f1linked.py'), fs.isLink('f1linked.py'))
        os.unlink('f1linked.py')

    def test_dirEqual(self):
        assert_equal(fs.dirEqual("/home/user1", "\\home\\user1"), True)
        assert_equal(fs.dirEqual("/home/user1", "\\home\\user2"), False)

    def test_checkDirOrLink(self):
        f=tmpify("f1totest")
        touchone(f)
        assert_equal(fs.checkDirOrLink(f), False)
        removeone(f)

    def test_readlink(self):
        f1=tmpify("flinktest")
        touchone(f1)
        f1link=tmpify("flinktestlink")
        os.symlink(f1, f1link)
        assert_equal(os.readlink(f1link), fs.readlink(f1link))
        removemany([f1,f1link])

    def test_checkDirOrLinkIsLinkToFile(self):
        f1=tmpify("testfile")
        if not os.path.exists(f1):
            touchone(f1)
        f1link=tmpify("testlink")
        os.symlink(f1, f1link)
        assert_equal(fs.checkDirOrLink(f1link), False)
        removemany([f1,f1link])

    def test_checkDirOrLinkIsLinkToDir(self):
        d1=tmpify("testdir")
        if not os.path.exists(d1):
            os.mkdir(d1)
        d1link=tmpify("testdirlink")
        os.symlink(d1, d1link)
        assert_equal(fs.checkDirOrLink(d1link), True)
        os.rmdir(d1)
        os.remove(d1link)

    def test_checkDirOrLinkIsDir(self):

        os.mkdir("myd")
        assert_equal(fs.checkDirOrLink("myd"), True)
        os.rmdir("myd")

    def test_getcwd(self):
        assert_equal(fs.getcwd(), os.getcwd())

    def test_touch(self):
        #Better way?
        assert_equal(path.exists('test1'), False)
        fs.touch('test1')
        assert_equal(path.exists('test1'), True)

        os.remove('test1')

    def test_getTmpFilePath(self):
        t=fs.getTmpFilePath()
        assert_in('/tmp', t)
        assert_equal(path.exists(t), True)
        assert_equal(path.isfile(t), True)

    def test_getTmpDirPath(self):
        t=fs.getTmpDirPath()
        assert_in('/tmp', t)
        assert_equal(path.exists(t), True)
        assert_equal(path.isdir(t), True)

    def test_getTempFileName(self):
        t=fs.getTempFileName()
        assert_in('/tmp', t)

    def test_fileSize(self):
        assert_equal(path.getsize(TestFS.FILE), fs.fileSize(TestFS.FILE))

    def test_isEmptyDir(self):
        d=tmpify('testdir')
        os.mkdir(d)
        assert_equal(os.listdir(d), [])
        assert_equal(fs.isEmptyDir(d), True)
        os.rmdir(d)

    def test_isAbsolute(self):
        assert_equal(path.isabs(TestFS.FILE), fs.isAbsolute(TestFS.FILE))


    def test_touch(self):
        f=tmpify('testx1')
        assert_equal(path.exists(f), False)
        fs.touch(f)
        assert_equal(path.exists(f), True)
        os.remove(f)

    def test_remove(self):
        f = tmpify("testtoremove")
        touchone(f)
        fs.remove(f)
        assert_equal(os.path.exists(f), False)

    def test_remove_raises_typeerror(self):
        assert_raises(TypeError, fs.remove, None)

    def test_remove_dir(self):
        t=tmpify("TESTDIRTOREMOVE")
        os.mkdir(t)
        fs.removeDir(t)
        assert_equal(os.path.exists(t), False)

    def test_remove_dir_raises_typeerror(self):
        assert_raises(TypeError, fs.removeDir, None)

    def test_copyDirTree(self):
        os.chdir('/tmp')
        os.mkdir('treetocopy')
        os.mkdir('treetocopy/sub1')
        os.mkdir('treetocopy/sub1/sub2')
        writetofile('treetocopy/sub1/sub2/file', "hello world")
        fs.copyDirTree("/tmp/treetocopy", "/tmp/copiedtree")

        assert_equal(os.path.exists("/tmp/copiedtree"), True)
        assert_equal(os.path.exists("/tmp/copiedtree/sub1/sub2/file"), True)


        shutil.rmtree("/tmp/treetocopy")
        shutil.rmtree("/tmp/copiedtree")


    def test_replaceWordsInFiles(self):
        os.chdir('/tmp')
        if not os.path.exists('treetosearch'):
            os.mkdir('treetosearch')
            os.mkdir('treetosearch/sub1')
        writetofile('treetosearch/sub1/file1', "{greet} world")
        os.mkdir('treetosearch/sub1/sub2')
        writetofile('treetosearch/sub1/sub2/file1', "{greet}")
        writetofile('treetosearch/sub1/sub2/file2', "{greet} world")
        te = j.tools.code.templateengine.new()
        te.add('greet', 'heyyy')
        fs.replaceWordsInFiles("/tmp/treetosearch", te)

        shutil.rmtree("/tmp/treetosearch")

    def test_removeDirTree(self):
        os.chdir("/tmp")
        os.mkdir('treetoremove')
        os.mkdir('treetoremove/sub1')
        os.mkdir('treetoremove/sub1/sub2')
        writetofile('treetoremove/sub1/sub2/file',"hello world")

        fs.removeDirTree("/tmp/treetoremove")
        assert_equal(os.path.exists("/tmp/treetoremove"), False)

    def test_removeDirTreePathIsLink(self):
        os.symlink("f1.py", "f1linked")
        fs.removeDirTree("f1linked")
        assert_equal(os.path.exists("f1linked"), False)

    def test_removeDirTreePathIsFile(self):
        shutil.copy("f1.py", "f1copy")
        fs.removeDirTree("f1copy")
        assert_equal(os.path.exists("f1copy"), False)

    def test_removeDirTree_raisesValueError(self):
        assert_raises(ValueError, fs.removeDirTree, None)

    def test_listpyscripts(self):
        #touch 3 files
        d=tmpify('pyscriptstest/')
        os.mkdir(d)
        FILES=list([d+x for x in ['f1.py', 'f2.py', 'f3.py'] ])
        touchmany(FILES)
        assert_equal(len(fs.listPyScriptsInDir(d)), 3)

        #remove the 3files
        removemany(FILES)
        os.rmdir(d)

    def test_changeDir(self):
        current=os.getcwd()
        os.chdir('/')
        fs.changeDir('/tmp')
        assert_in('/tmp', os.getcwd())
        os.chdir(current)

    def test_listFilesInDir(self):
        assert_equal(getfilesindir('.'), fs.listFilesInDir('.'))

    def test_listDirsInDir(self):
        assert_equal(getdirsindir('.'), fs.listDirsInDir('.'))

    def test_listDirsInDir(self):
        assert_equal(getdirsindir('.'), fs.listDirsInDir('.'))


    def test_listFilesAndDirsInDir(self):
        assert_equal(sorted(getallindir('.')), sorted(list(map(path.normpath,fs.listFilesAndDirsInDir('.'))))) ##FAILS ..

    def test_move(self): #moveFile & moveDir call fs.move anyways.
        touchone('testfile')
        assert_equal(path.exists('testfile'), True)
        fs.move('testfile', 'newtestfile')
        assert_equal(path.exists('newtestfile'), True)
        removeone('newtestfile')

    def test_pathShorten(self):
        f='/home/st/jumpscale/lib/main/../tests/runner.py'
        assert_equal(path.normpath(f), fs.pathShorten(f))


    def test_cleanupString(self):

        s="Hello%$$$%*&^WWW"
        cleaned=fs.cleanupString(s)
        assert_not_in("$", cleaned)
        assert_not_in("%", cleaned)
        assert_not_in("^", cleaned)


    def test_joinPaths(self):

        p1='/home'
        p2='striky/wspace'
        assert_equal(path.join(p1,p2), fs.joinPaths(p1,p2))

    def test_statePath(self):
        assert_equal(os.stat('/'), fs.statPath('/'), "failed for normal behavior`")
        assert_raises(TypeError, fs.statPath, None, msg='none is passed')
        assert_raises(OSError, fs.statPath, '/tmposcreepy')


    def test_writeFile(self):
        f='testtmp'
        txt="hello world"
        assert_equal(path.exists(f), False)
        fs.writeFile(f, txt)
        assert_equal(path.exists(f), True)
        removeone(f)

    def test_isAscii(self):
        assert_equal(isascii(TestFS.FILE), fs.isAsciiFile(TestFS.FILE))


    def test_isBinaryFile(self):
        assert_equal(isbinary('/bin/bash'), fs.isBinaryFile('/bin/bash'))

    def test_unlink(self):
        f=tmpify('hellox1')
        touchone(f)
        assert_equal(path.exists(f), True )
        fs.unlinkFile(f)
        assert_equal(path.exists(f), False )

    def test_readFile(self):
        assert_equal(readfile(TestFS.FILE), fs.readFile(TestFS.FILE))

    def test_fileGetContents(self):

        assert_equal(readfile(TestFS.FILE), fs.fileGetContents(TestFS.FILE))

    # def test_fileGetTextContents(self):
    #     txt = 'Hello, World'
    #     b=bomify(txt)
    #     f=tmpify('/testbomthingy')
    #     with open(f, 'wb') as fp:
    #         fp.write(b)
    #     assert_equal(txt, fs.fileGetTextContents(f))

    def test_isExecutable(self):

        assert_equal(os.access('/bin/bash', os.X_OK), fs.isExecutable('/bin/bash'))
        assert_equal(os.access('/tmp', os.X_OK), fs.isExecutable('/bin/bash'))

    def test_isExecutable_others(self):
        #create file rwx-rw-rw
        f=tmpify('testfilex')
        if not os.path.exists(f):
            touchone(f)
        os.chmod(f, mode=447)
        os.chown(f, 0, 0)
        #only is executable by the owner for now?
        assert_equal(fs.isExecutable(f), False)
        removeone(f)


    def test_isMount(self):
        assert_equal(fs.isMount('/'), path.ismount('/'))

    def test_fileGetUncommentedContents(self):
        content="""
#this is first comment
    #this is a second comment

x=1
y=2

        """
        f="testuncommented.py"
        with open(f, 'w') as fp:
            fp.write(content)
        txt="".join(fs.fileGetUncommentedContents(f))
        assert_not_in("#", txt)
        removeone(f)

    def test_md5sum(self):
        assert_equal(hashfile(TestFS.FILE), fs.md5sum(TestFS.FILE))

    def test_createEmptyFile(self):
        #okay touch 0 size file and check if it's created and if its size=0
        fs.createEmptyFile('testempty')
        assert_equal(path.exists('testempty'), True)
        assert_equal(path.getsize('testempty'), 0)

        removeone('testempty')

    def test_getParent(self):
        assert_equal(os.path.dirname("/tmp/dir1/name"), fs.getParent("/tmp/dir1/name"))

    def test_pathClean(self):
        p="/home/ahmed/someone/st.py"
        assert_equal(path.normpath(p), fs.pathClean(p))

    def test_createDir(self):
        D=tmpify('emptydir')
        assert_equal(path.exists(D), False)
        fs.createDir(D)
        assert_equal(path.exists(D), True)
        os.rmdir(D)

    def test_pathNormalize(self):
        cur=os.getcwd()
        os.chdir("/tmp")
        assert_equal(fs.pathNormalize("home/ahmed"), '/tmp/home/ahmed')
        assert_equal(fs.pathNormalize("home/ahmed", root='/'), '/home/ahmed' )
        os.chdir(cur)

    def test_pathDirClean(self):
        assert_equal(fs.pathDirClean("/home/ahmed/sub"), "/home/ahmed/sub/")
        assert_equal(fs.pathDirClean("/home/ahmed/sub/"), "/home/ahmed/sub/")

    def test_processPathForDoubleDots(self):
        assert_equal(fs.processPathForDoubleDots("/tmp/../dir1/name"), os.path.normpath("/tmp/../dir1/name"))


    def test_getFolderMD5sum(self):
        return True
