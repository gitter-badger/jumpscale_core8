"""
Test module for cuisine ActionDecorator module
"""
import unittest
from JumpScale.tools.cuisine.ActionDecorator import ActionDecorator
from JumpScale import j

class TestActionDecorator(unittest.TestCase):
    def setUp(self):
        j.core.db.flushall()

    def tearDown(self):
        pass

    def say_hello(self, executor=None):
        return 'Hello'

    def test_create_actiondecorator(self):
        """
        Test creating an action decorator object
        """
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
        cuisine = j.tools.cuisine.local
        ad = ActionDecorator(action=True)
        ad.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj='hello'"
        action = ad(self.say_hello)
        action(*[cuisine])

    def test_call_actoindecorator_no_action(self):
        """
        Test call a decorated action when action flag is set to false
        """
        cuisine = j.tools.cuisine.local
        ad = ActionDecorator(action=False)
        ad.selfobjCode="cuisine=j.tools.cuisine.getFromId('$id');selfobj='hello'"
        action = ad(self.say_hello)
        action()




if __name__ == '__main__':
    unittest.main()
