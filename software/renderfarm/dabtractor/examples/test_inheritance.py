
# class Pet(object):
#
#     def __init__(self, a="aa", b="bb"):
#         self.a = a
#         self.b = b
#
#
#
# class Dog(Pet):
#
#     def __init__(self, c="cc"):
#         super(Pet).__init__(self)
#         self.c = "cc"
#
#
#
# polly = Pet()
# fido = Dog()
# print dir(polly)
# print dir(fido)



class Foo(object):
     def __init__(self, a="aa", b="bb"):
          self.a = a
          self.b = b

class Bar(Foo):
     def __init__(self, b="bbb", c="cc"):
          super(Bar, self).__init__(b, c)
          self.b = b
          self.c = c


bar = Bar(b=1,c=2)
print "a:", bar.a
print "b:", bar.b
print "c:", bar.c