__author__ = '120988'

### decorators

# class gatekeeper(object):
#     def __init__(self, function):
#         self.function = function
#     def __call__(self,*args):
#         print "Entering", self.function.__name__
#         self.function(*args)
#         print "Exited", self.function.__name__
#
# @gatekeeper
# def aFunction():
#     print "aFunction running"
#
# aFunction()


class catchAll(object):
    def __init__(self, function):
        self.function = function

    def __call__(self, *args):
        print "\n    Entering", self.function.__name__
        try:
            # print "   ",self.function.__name__
            return self.function(*args)
        except Exception, e:
            print "    Error: %s" % (e)
        finally:
            print "    Exited", self.function.__name__


# @gatekeeper
@catchAll
def invert(x):
    return float(1/x*2)

print "invert(1): %s"% invert(15.0)
print "invert(0): %s"% invert(0)


