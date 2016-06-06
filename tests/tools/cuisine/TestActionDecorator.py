"""
Test module for cuisine ActionDecorator module
"""
import unittest
from unittest import mock

class TestActionDecorator(unittest.TestCase):
    def setUp(self):
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale import j
            j.core.db.flushall()

    def tearDown(self):
        pass

    def say_hello(self, executor=None):
        return 'Hello'

    def test_create_actiondecorator(self):
        """
        Test creating an action decorator object
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale.tools.cuisine.ActionDecorator import ActionDecorator
            # from JumpScale import j
            ad = ActionDecorator()
            self.assertTrue(ad.action)
            self.assertFalse(ad.force)
            self.assertTrue(ad.actionshow)

            ad = ActionDecorator(action=False)
            self.assertFalse(ad.action)
            self.assertFalse(ad.force)
            self.assertTrue(ad.actionshow)

            ad = ActionDecorator(force=True)
            self.assertTrue(ad.action)
            self.assertTrue(ad.force)
            self.assertTrue(ad.actionshow)

            ad = ActionDecorator(actionshow=False)
            self.assertTrue(ad.action)
            self.assertFalse(ad.force)
            self.assertFalse(ad.actionshow)


    def test_call_actoindecorator(self):
        """
        Test call a decorated action
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale.tools.cuisine.ActionDecorator import ActionDecorator
            from JumpScale import j
            cuisine = j.tools.cuisine.local
            cuisine.cuisine.core.id = 'fake_id'
            action_mock = mock.MagicMock()
            j.actions.add.return_value = action_mock
            action_mock.state = "OK"
            cuisine.core.id.__str__ = (lambda x : 'fake_cuisine_id')
            ad = ActionDecorator(action=True)
            ad.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj='hello'"
            action = ad(self.say_hello)
            action(*[cuisine])

    def test_call_actoindecorator_no_action(self):
        """
        Test call a decorated action when action flag is set to false
        """
        with mock.patch("JumpScale.j") as j_mock:
            from JumpScale.tools.cuisine.ActionDecorator import ActionDecorator
            from JumpScale import j
            cuisine = j.tools.cuisine.local
            cuisine.cuisine.core.id = 'fake_id'
            action_mock = mock.MagicMock()
            j.actions.add.return_value = action_mock
            action_mock.state = "OK"
            cuisine.core.id.__str__ = (lambda x : 'fake_cuisine_id')
            ad = ActionDecorator(action=False)
            ad.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj='hello'"
            action = ad(self.say_hello)
            action()



if __name__ == '__main__':
    unittest.main()
