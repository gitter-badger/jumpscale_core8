"""
Test module for CuisineFactory
"""

import unittest
from unittest import mock

class TestCuisineFactory(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass


    def test_create_factory(self):
        """
        Test creating a factory instance
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineFactory
            JumpScale.tools.cuisine.CuisineFactory.j = j
            from JumpScale.tools.cuisine.CuisineFactory import JSCuisineFactory
            factory = JSCuisineFactory()


    def test_get_local(self):
        """
        Test getting a local cuisine instance
        """
        with mock.patch("JumpScale.j") as j_mock:
            with mock.patch("Cuisine2.JSCuisine") as jscuisine_mock:
                from JumpScale import j
                import JumpScale.tools.cuisine.CuisineFactory
                JumpScale.tools.cuisine.CuisineFactory.j = j
                from JumpScale.tools.cuisine.CuisineFactory import JSCuisineFactory
                factory = JSCuisineFactory()
                old_local = factory.local
                new_local = factory.local
                self.assertEqual(old_local, new_local)
                old_local = factory.local
                factory._local = None
                new_local = factory.local
                self.assertNotEqual(old_local, new_local)

    def test_get_push_key(self):
        """
        Test getting ssh executor
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            import JumpScale.tools.cuisine.CuisineFactory
            JumpScale.tools.cuisine.CuisineFactory.j = j
            from JumpScale.tools.cuisine.CuisineFactory import JSCuisineFactory
            factory = JSCuisineFactory()
            # check the path where the password is not set
            j.clients.ssh.get.return_value = True
            factory.getPushKey()
            self.assertTrue(j.tools.executor.getSSHBased.called)
            self.assertFalse(j.tools.console.askPassword.called)

            j.clients.ssh.get.return_value = False
            ssh_add_l_output = (0, '2048 SHA256:C7QPiMG99B+2XP/WV6Uwqdi/VIGf7Mglq74FPVHlvw0 abdelrahman@abdelrahman-work (RSA)')
            j.sal.process.execute.return_value = ssh_add_l_output
            factory.getPushKey()
            self.assertTrue(j.tools.console.askPassword.called)
            self.assertTrue(j.tools.console.askChoice.called)
