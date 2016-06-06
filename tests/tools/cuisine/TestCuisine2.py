"""
Test Cuisine2  (core)
"""
import unittest
from unittest import mock

class TestCuisine2(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create_cuisine2(self):
        """
        Test creating an instance
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertEqual(cuisine.core.executor, executor_mock)
            self.assertEqual(cuisine.sshreflector.executor, executor_mock)
            self.assertEqual(cuisine.proxy.executor, executor_mock)
            self.assertEqual(cuisine.bootmediaInstaller.executor, executor_mock)
            self.assertEqual(cuisine.vrouter.executor, executor_mock)
            self.assertEqual(cuisine.tmux.executor, executor_mock)
            self.assertEqual(cuisine.pnode.executor, executor_mock)
            self.assertEqual(cuisine.stor.executor, executor_mock)
            self.assertEqual(cuisine.done, [])

    def test_create_cuisine2_btrfs(self):
        """
        Test accessing btrfs property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.btrfs)

    def test_create_cuisine2_package(self):
        """
        Test accessing package property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.package)

    def test_create_cuisine2_process(self):
        """
        Test accessing process property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.process)

    def test_create_cuisine2_pip(self):
        """
        Test accessing pip property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.pip)


    def test_create_cuisine2_fw(self):
        """
        Test accessing fw property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.fw)

    def test_create_cuisine2_golang(self):
        """
        Test accessing golang property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.golang)

    def test_create_cuisine2_geodns(self):
        """
        Test accessing geodns property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.geodns)

    def test_create_cuisine2_apps(self):
        """
        Test accessing apps property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.apps)

    def test_create_cuisine2_builder(self):
        """
        Test accessing builder property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.builder)

    def test_create_cuisine2_id(self):
        """
        Test accessing id property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.id)

    def test_create_cuisine2_platformtype(self):
        """
        Test accessing platformtype property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.platformtype)

    def test_create_cuisine2_installer(self):
        """
        Test accessing installer property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.installer)

    def test_create_cuisine2_installerdevelop(self):
        """
        Test accessing installerdevelop property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.installerdevelop)

    def test_create_cuisine2_ns(self):
        """
        Test accessing ns property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.ns)

    def test_create_cuisine2_docker(self):
        """
        Test accessing docker property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.docker)

    def test_create_cuisine2_ssh(self):
        """
        Test accessing ssh property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.ssh)

    def test_create_cuisine2_avahi(self):
        """
        Test accessing avahi property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.avahi)

    def test_create_cuisine2_dnsmasq(self):
        """
        Test accessing dnsmasq property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.dnsmasq)

    def test_create_cuisine2_bash(self):
        """
        Test accessing bash property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.bash)

    def test_create_cuisine2_net(self):
        """
        Test accessing net property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.net)

    def test_create_cuisine2_user(self):
        """
        Test accessing user property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.user)

    def test_create_cuisine2_group(self):
        """
        Test accessing group property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.group)


    def test_create_cuisine2_git(self):
        """
        Test accessing git property
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.Cuisine2
            JumpScale.tools.cuisine.Cuisine2.j = j
            from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
            executor_mock = mock.MagicMock()
            j.tools.executor.getLocal.return_value = executor_mock
            cuisine = JSCuisine(j.tools.executor.getLocal())
            self.assertIsNotNone(cuisine.git)

    def test_create_cuisine2_processmanager(self):
        """
        Test accessing processmanager property
        """
        with mock.patch("JumpScale.j") as j_mock:
            with mock.patch("JumpScale.tools.cuisine.ProcessManagerFactory.ProcessManagerFactory") as process_manager_factory_mock:
                from JumpScale.tools.cuisine.ProcessManagerFactory import ProcessManagerFactory
                from JumpScale import j
                import JumpScale.tools.cuisine.Cuisine2
                JumpScale.tools.cuisine.Cuisine2.ProcessManagerFactory = ProcessManagerFactory
                JumpScale.tools.cuisine.Cuisine2.j = j
                from JumpScale.tools.cuisine.Cuisine2 import JSCuisine
                executor_mock = mock.MagicMock()
                j.tools.executor.getLocal.return_value = executor_mock
                cuisine = JSCuisine(j.tools.executor.getLocal())
                self.assertIsNotNone(cuisine.processmanager)
