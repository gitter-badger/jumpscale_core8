"""
Test module for CuisineBuilder
"""

import unittest
from unittest import mock

class TestCuisineBuilder(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_all(self):
        """
        Test all
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine.installer.jumpscale_installed.return_value = False
            cuisine.core.isDocker = False
            cuisine.core.isLxc = False
            cuisine_builder.all()
            self.assertTrue(cuisine.installerdevelop.pip.called)
            self.assertTrue(cuisine.installerdevelop.python.called)
            self.assertTrue(cuisine.installerdevelop.jumpscale8.called)
            self.assertTrue(cuisine.apps.mongodb.build.called)
            self.assertTrue(cuisine.apps.portal.install.called)
            self.assertTrue(cuisine.apps.redis.build.called)
            self.assertTrue(cuisine.apps.syncthing.build.called)
            self.assertTrue(cuisine.apps.controller.build.called)
            self.assertTrue(cuisine.apps.fs.build.called)
            self.assertTrue(cuisine.apps.stor.build.called)
            self.assertTrue(cuisine.apps.etcd.build.called)
            self.assertTrue(cuisine.apps.caddy.build.called)
            self.assertTrue(cuisine.apps.influxdb.build.called)
            self.assertTrue(cuisine.apps.weave.build.called)


    def test_all_2(self):
        """
        Test all 2
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine.installer.jumpscale_installed.return_value = False
            cuisine.core.isDocker = False
            cuisine.core.isLxc = False
            cuisine_builder.sandbox = mock.MagicMock()
            cuisine_builder.all(sandbox=True, stor_addr='fake_host')
            self.assertTrue(cuisine_builder.sandbox.called)

    def test_all_2_failure(self):
        """
        Test all 2 failure case
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine.installer.jumpscale_installed.return_value = False
            cuisine.core.isDocker = False
            cuisine.core.isLxc = False
            cuisine_builder.sandbox = mock.MagicMock()
            self.assertRaises(RuntimeError, cuisine_builder.all, sandbox=True)


    def test_sandbox(self):
        """
        Test sandbox
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine_builder.cuisine.core.run = mock.MagicMock()
            expected_output = 'fake_store/static/js8_opt.flist'
            actual_output = cuisine_builder.sandbox(stor_addr='fake_store')
            self.assertEquals(expected_output, actual_output)


    def test_dedupe(self):
        """
        Test debupe
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine.core.dir_remove = mock.MagicMock()
            cuisine_builder._sandbox_python = mock.MagicMock()
            j.data.types.list.check.return_value = True
            j.tools.sandboxer.dedupe = mock.MagicMock()
            put_file_upload_hash = 'uploadhash'
            store_mock = mock.MagicMock()
            store_mock.putFile.return_value = put_file_upload_hash
            j.clients.storx.get = mock.MagicMock(return_value = store_mock)
            j.sal.fs.joinPaths = mock.MagicMock()
            j.sal.fs.listFilesInDir = mock.MagicMock(return_value=['path_to_file'])
            j.data.hash.md5 = mock.MagicMock(return_value=put_file_upload_hash)

            # actions
            cuisine_builder.dedupe(dedupe_path=['fake_path'], namespace='fake_namespace', store_addr='fake_store')

            # asserts
            self.assertTrue(cuisine.core.dir_remove.called)
            self.assertTrue(cuisine_builder._sandbox_python.called)
            self.assertTrue(j.clients.storx.get.called)
            self.assertTrue(j.sal.fs.joinPaths.called)
            self.assertTrue(j.sal.fs.listFilesInDir.called)
            self.assertTrue(j.data.hash.md5.called)
            self.assertTrue(store_mock.putStaticFile.called)


    def test_dedupe_failure(self):
        """
        Test debupe failure case
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineBuilder
            JumpScale.tools.cuisine.CuisineBuilder.j = j
            from JumpScale.tools.cuisine.CuisineBuilder import CuisineBuilder
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            executor = j.tools.executor.getLocal()
            cuisine = j.tools.cuisine.local
            cuisine_builder = CuisineBuilder(executor, cuisine)
            cuisine.core.dir_remove = mock.MagicMock()
            cuisine_builder._sandbox_python = mock.MagicMock()
            j.data.types.list.check.return_value = True
            j.tools.sandboxer.dedupe = mock.MagicMock()
            put_file_upload_hash = 'uploadhash'
            store_mock = mock.MagicMock()
            store_mock.putFile.return_value = put_file_upload_hash
            j.clients.storx.get = mock.MagicMock(return_value = store_mock)
            j.sal.fs.joinPaths = mock.MagicMock()
            j.sal.fs.listFilesInDir = mock.MagicMock(return_value=['path_to_file'])
            j.data.hash.md5 = mock.MagicMock(return_value='differentuploadhash')

            # actions
            self.assertRaises(RuntimeError, cuisine_builder.dedupe, dedupe_path=['fake_path'], namespace='fake_namespace', store_addr='fake_store')

            # asserts
            self.assertTrue(cuisine.core.dir_remove.called)
            self.assertTrue(cuisine_builder._sandbox_python.called)
            self.assertTrue(j.clients.storx.get.called)
            self.assertTrue(j.sal.fs.joinPaths.called)
            self.assertTrue(j.sal.fs.listFilesInDir.called)
            self.assertTrue(j.data.hash.md5.called)
            self.assertFalse(store_mock.putStaticFile.called)
