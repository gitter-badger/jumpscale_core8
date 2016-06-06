"""
Test CuisineCore module
"""
import unittest
from unittest import mock

class TestCuisineCore(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_create_cuisine_core(self):
        """
        Test creating CuisineCore instance
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)


    def test_reset_actions(self):
        """
        Test reset actions
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            cuisine_core.reset_actions()
            self.assertTrue(j.actions.reset.called)

    def test_id_property(self):
        """
        Test accessing the id property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            self.assertIsNotNone(cuisine_core.id)

    def test_isJS8Sandbox_property(self):
        """
        Test accessing the isJS8Sandbox property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            self.assertIsNotNone(cuisine_core.isJS8Sandbox)

    def test_dir_paths_property(self):
        """
        Test accessing the dir_paths property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            self.assertIsNotNone(cuisine_core.dir_paths)


    def test_args_replace(self):
        """
        Test args replace
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            cuisine_core.run = mock.MagicMock()
            cuisine_core.run.return_value = 'hostname'
            input_text = "$base:$appDir:$tmplsDir:$varDir:$binDir:$codeDir:$cfgDir:$homeDir:$jsLibDir:$libDir:$logDir:$pidDir:$tmpDir:$hostname"
            expected_output = "/opt/jumpscale8:/opt/jumpscale8/apps:/opt/jumpscale8/templates:/optvar/:/opt/jumpscale8/bin:/opt/code/:/optvar//cfg:/root:/opt/jumpscale8/lib/JumpScale/:/opt/jumpscale8/lib/:/optvar//log:/optvar//pid:/optvar//tmp:hostname"
            actual_output = cuisine_core.args_replace(input_text)
            self.assertEqual(expected_output, actual_output)

    def test_file_get_tmp_path(self):
        """
        Test file get tmp path
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            cuisine_core.run = mock.MagicMock()
            cuisine_core.run.return_value = 'hostname'
            j.data.idgenerator.generateXCharID.return_value = 10*'a'
            expected_output = '/optvar//tmp/aaaaaaaaaa'
            actual_output = cuisine_core.file_get_tmp_path()
            self.assertEquals(expected_output, actual_output)
            expected_output = '/optvar//tmp/path'
            actual_output = cuisine_core.file_get_tmp_path(basepath="path")
            self.assertEquals(expected_output, actual_output)

    def test_file_download(self):
        """
        Test file download
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            url = 'http://hallo.com/downloadme.txt'
            to = '/tmp/path'
            cuisine_core.file_exists = mock.MagicMock()
            cuisine_core.file_exists.return_value = False
            cuisine_core.createDir = mock.MagicMock()
            cuisine_core.file_unlink = mock.MagicMock()
            cuisine_core.run = mock.MagicMock()
            cuisine_core.run.side_effect = [(33, 'Ok'),(0, 'Ok')]
            cuisine_core.touch = mock.MagicMock()
            cuisine_core.file_download(url, to)
            self.assertTrue(cuisine_core.touch.called)
            self.assertFalse(j.sal.fs.getBaseName.called)

    def test_file_download_fail(self):
        """
        Test file download wth failure
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            url = 'http://hallo.com/downloadme.txt'
            to = '/tmp/path'
            cuisine_core.file_exists = mock.MagicMock()
            cuisine_core.file_exists.return_value = False
            cuisine_core.createDir = mock.MagicMock()
            cuisine_core.file_unlink = mock.MagicMock()
            cuisine_core.run = mock.MagicMock()
            cuisine_core.run.side_effect = [(32, 'Ok'),(0, 'Ok')]
            cuisine_core.touch = mock.MagicMock()
            self.assertRaises(RuntimeError, cuisine_core.file_download, url, to)

    def test_file_expand(self):
        """
        Test file expand
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            path = '/tmp/file.tgz'
            to = '/tmp/dest'
            cuisine_core.run = mock.MagicMock()
            cuisine_core.args_replace = mock.MagicMock()
            cuisine_core.file_expand(path, to)

    def test_file_expand_fail(self):
        """
        Test file expand failure case
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            path = '/tmp/file.txt'
            to = '/tmp/dest'
            cuisine_core.run = mock.MagicMock()
            cuisine_core.args_replace = mock.MagicMock()
            cuisine_core.args_replace.side_effect = (path, to)
            self.assertRaises(RuntimeError, cuisine_core.file_expand, path, to)

    def test_touch(self):
        """
        Test touch
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineCore
            JumpScale.tools.cuisine.CuisineCore.j = j
            from JumpScale.tools.cuisine.CuisineCore import CuisineCore
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_core = CuisineCore(executor, cuisine)
            cuisine_core.run = mock.MagicMock()
            cuisine_core.args_replace = mock.MagicMock()
            cuisine_core.file_write = mock.MagicMock()
            self.assertIsNone(cuisine_core.touch('/tmp/hello'))
            self.assertTrue(cuisine_core.file_write.called)


    # def file_upload_binary(self, local, remote):
    # def file_upload_local(self, local, remote):
    # def file_download_binary(self, local, remote):
    # def file_download_local(self,remote, local):
    # def file_copy(self, source, dest, recursive=False, overwrite=False):
    # def file_move(self, source, dest, recursive=False):
    # def joinpaths(self, *args):
    # def fs_find(self,path,recursive=True,pattern="",findstatement="",type="",contentsearch="",extendinfo=False):
    # def sudo(self, cmd, die=True,showout=True):
    # def run(self,cmd,die=True,debug=None,checkok=False,showout=True,profile=False,replaceArgs=True,check_is_ok=False):
    # def run_script(self,content,die=True,profile=False):
    # def command_location(self,command):
    # def tmux_execute_jumpscript(self,script,sessionname="ssh", screenname="js"):
    # def execute_jumpscript(self,script):
    # def execute_jumpscript(self,script):
