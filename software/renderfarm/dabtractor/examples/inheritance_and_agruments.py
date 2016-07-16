'''
    This is a test bed for stupid matt to fully understanf passing agrs to objects and ingeritance

'''

class Base(object):
    '''---- Doc: Base Class '''
    def __init__(self,base=0):
        self.base=base
        print "\n",self.__doc__
        print self.__class__.__name__
        print self.__dict__
        print "Base class initialized, base=%s" % self.base


class One(Base):
    '''---- Doc: Class One '''
    def __init__(self):
        print "One class initialized"


class Two(Base):
    '''---- Doc: Class Two '''
    def __init__(self,two=2):
        super(Two, self).__init__(12)
        self.two=two
        print "Two class initialized, two=%s" % self.two


class Three(Base):
    '''---- Doc: Class Three '''
    def __init__(self,*args,**kwargs):
        try:
            super(Three, self).__init__(kwargs.get('x'))
        except:
            super(Three, self).__init__(args[0])
        print "Three class initialized"
        print args
        print kwargs


# ##############################################################################
if __name__ == "__main__":
    B = Base()
    O = One()
    T = Two()
    TH = Three()
    TH1 = Three(100)
    TH2 = Three(b=200)


