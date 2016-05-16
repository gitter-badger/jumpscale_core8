from JumpScale import j

'''Definition of several primitive type properties (integer, string,...)'''


class String():

    '''Generic string type'''
    def __init__(self):

        self.NAME = 'string'
        self.BASETYPE = 'string'


    def fromString(self,s):
        """
        return string from a string (is basically no more than a check)
        """
        # if not isinstance(value, str):
        #     raise ValueError("Should be string:%s"%s)
        s=str(s)
        return s


    def toString(self,v):
        if self.check(v):
            return str(v)
        else:
            raise ValueError("Could not convert to string:%s"%v)

    def check(self,value):
        '''Check whether provided value is a string'''
        return isinstance(value, str)

    def get_default(self):
        return ""

    def clean(self,value):
        """
        used to change the value to a predefined standard for this type
        """
        return value

class Bytes():
    '''Generic array of bytes type'''
    def __init__(self):

        self.NAME = 'bytes'
        self.BASETYPE = 'bytes'

    def fromString(self,s):
        """
        return string from a string (is basically no more than a check)
        """
        # if not isinstance(value, str):
        #     raise ValueError("Should be string:%s"%s)
        return s.encode()

    def toString(self, v):
        if self.check(v):
            return v.decode()
        else:
            raise ValueError("Could not convert to bytes:%s" % v)

    def check(self,value):
        '''Check whether provided value is a array of bytes'''
        return isinstance(value, bytes)

    def get_default(self):
        return ""

    def clean(self,value):
        """
        used to change the value to a predefined standard for this type
        """
        return value


class Boolean():

    '''Generic boolean type'''
    def __init__(self):
        self.NAME = 'boolean'
        self.BASETYPE = 'boolean'


    def fromString(self,s):
        if isinstance(s, bool):
            return s
        s = str(s)
        if s.upper() in ('0', 'FALSE'):
            return False
        elif s.upper() in ('1', 'TRUE'):
            return True
        else:
            raise ValueError("Invalid value for boolean: '%s'" % s)


    def checkString(self,s):
        try:
            self.fromString(s)
            return True
        except ValueError:
            return False


    def toString(self,boolean):
        if self.check(s):
            return str(boolean)
        else:
            raise ValueError("Invalid value for boolean: '%s'" % boolean)


    def check(self,value):
        '''Check whether provided value is a boolean'''
        return value is True or value is False


    def get_default(self):
        return True

    def clean(self,value):
        """
        used to change the value to a predefined standard for this type
        """
        return value


class Integer():

    '''Generic integer type'''
    def __init__(self):
        self.NAME = 'integer'
        self.BASETYPE = 'integer'


    def checkString(self,s):
        return s.isdigit()


    def check(self,value):
        '''Check whether provided value is an integer'''
        return isinstance(value, int)


    def toString(self,value):
        if self.check(value):
            return str(value)
        else:
            raise ValueError("Invalid value for integer: '%s'" % value)


    def fromString(self,s):
        return j.data.text.getInt(s)


    def get_default(self):
        return 0

    def clean(self,value):
        """
        used to change the value to a predefined standard for this type
        """
        return value



class Float():

    '''Generic float type'''
    def __init__(self):
        self.NAME = 'float'
        self.BASETYPE = 'float'


    def checkString(self,value):
        try:
            float(value)
            return True
        except ValueError:
            return False


    def check(self,value):
        '''Check whether provided value is a float'''
        return isinstance(value, float)


    def toString(self,value):
        if self.check(value):
            return str(value)
        else:
            raise ValueError("Invalid value for float: '%s'" % value)


    def fromString(self,s):
        return j.data.text.getFloat(s)


    def get_default(self):
        return 0.0

    def clean(self,value):
        """
        used to change the value to a predefined standard for this type
        """
        return value
        
