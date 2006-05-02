from xml.dom.minidom import *

native_types = {}
basic_types = {}
compound_types = {}

def class_name(n):
    if n == None: return None
    try:
        return native_types[n]
    except KeyError:
        return n.replace(' ', '_')

    if n == None: return None
    try:
        return native_types[n]
    except KeyError:
        pass
    if n == '(TEMPLATE)': return 'T'
    n2 = ''
    for i, c in enumerate(n):
        if ('A' <= c) and (c <= 'Z'):
            if i > 0: n2 += '_'
            n2 += c.lower()
        elif (('a' <= c) and (c <= 'z')) or (('0' <= c) and (c <= '9')):
            n2 += c
        else:
            n2 += '_'
    return n2

def define_name(n):
    n2 = ''
    for i, c in enumerate(n):
        if ('A' <= c) and (c <= 'Z'):
            if i > 0:
                n2 += '_'
                n2 += c
            else:
                n2 += c
        elif (('a' <= c) and (c <= 'z')) or (('0' <= c) and (c <= '9')):
            n2 += c.upper()
        else:
            n2 += '_'
    return n2

def member_name(n):
    if n == None: return None
    if n == '(ARG)': return 'attr_arg'
    n2 = ''
    lower = True
    for i, c in enumerate(n):
        if c == ' ':
            lower = False
        elif (('A' <= c) and (c <= 'Z')) or (('a' <= c) and (c <= 'z')) or (('0' <= c) and (c <= '9')):
            if lower:
                n2 += c.lower()
            else:
                n2 += c.upper()
                lower = True
        else:
            n2 += '_'
            lower = True
    return n2

def version2number(s):
    if not s: return None
    l = s.split('.')
    if len(l) != 4:
        assert(False)
        return int(s)
    else:
        return (int(l[0]) << 24) + (int(l[1]) << 16) + (int(l[2]) << 8) + int(l[3])

class Expr:
    def __init__(self, n):
        if n == None:
            self.lhs = None
            self.clhs = None
            self.op = None
            self.rhs = None
            return
        
        x = None
        for op in [ '==', '!=', '&' ]:
            if n.find(op) != -1:
                x = n.split(op)
                break
        if not x:
            self.lhs = n.strip()
            self.clhs = member_name(self.lhs)
            self.op = None
            self.rhs = None
        elif len(x) == 2:
            self.lhs = x[0].strip()
            self.clhs = member_name(self.lhs)
            self.op = op
            self.rhs = x[1].strip()
        else:
            # bad syntax
            print x
            raise str('"%s" is an invalid expression'%n)

    def code(self):
        if not self.op:
            return self.clhs
        else:
            return '%s %s %s'%(self.clhs, self.op, self.rhs)

class Member:
    def __init__(self, element):
        assert(element.tagName == 'add')
        parent = element.parentNode
        sisters = parent.getElementsByTagName('add')
        # member attributes
        self.name      = element.getAttribute('name')
        self.type      = element.getAttribute('type')
        self.arg       = element.getAttribute('arg')
        self.template  = element.getAttribute('template')
        self.arr1      = Expr(element.getAttribute('arr1'))
        self.arr2      = Expr(element.getAttribute('arr2'))
        self.cond      = Expr(element.getAttribute('cond'))
        self.func      = element.getAttribute('function')
        self.default   = element.getAttribute('default')
        self.description = '' # got to look this up: element.get????
        self.ver1      = version2number(element.getAttribute('ver1'))
        self.ver2      = version2number(element.getAttribute('ver2'))
        
        # calculate other stuff
        self.uses_argument = (self.cond.lhs == '(ARG)' or self.arr1.lhs == '(ARG)' or self.arr2.lhs == '(ARG)')
        self.type_is_native = native_types.has_key(self.name) # true if the type is implemented natively

        # calculate stuff from reference to previous members
        # true if this is a duplicate of a previously declared member
        self.is_duplicate = False
        sis = element.previousSibling
        while sis:
            if sis.nodeType == Node.ELEMENT_NODE:
                if sis.getAttribute('name') == self.name:
                    self.is_duplicate = True
                    break
            sis = sis.previousSibling

        # calculate stuff from reference to next members
        self.arr1_ref = [] # names of the attributes it is a (unmasked) size of
        self.arr2_ref = [] # names of the attributes it is a (unmasked) size of
        self.cond_ref = [] # names of the attributes it is a condition of
        self.arr2_dynamic = False  # true if arr2 refers to an array
        sis = element.nextSibling
        while sis:
            if sis.nodeType == Node.ELEMENT_NODE:
                sis_name = sis.getAttribute('name')
                sis_arr1 = Expr(sis.getAttribute('arr1'))
                sis_arr2 = Expr(sis.getAttribute('arr2'))
                sis_cond = Expr(sis.getAttribute('cond'))
                if sis_arr1.lhs == self.name and not sis_arr1.rhs:
                    self.arr1_ref.append(sis_arr1.lhs)
                if sis_arr2.lhs == self.name and not sis_arr2.rhs:
                    self.arr2_ref.append(sis_arr2.lhs)
                if sis_cond.lhs == self.name:
                    self.cond_ref.append(sis_cond.lhs)
                if sis_name == self.arr2.lhs and sis_arr1.lhs:
                    self.arr2_dynamic = True
            sis = sis.nextSibling
        # true if it is declared in the class, if false, this field is calculated somehow
        if (self.arr1_ref or self.arr2_ref or self.func) and not self.cond_ref:
            self.is_declared = False
        else:
            self.is_declared = True

        # C++ names
        self.cname     = member_name(self.name)
        self.ctype     = class_name(self.type)
        self.carg      = member_name(self.arg)
        self.ctemplate = class_name(self.template)
        self.carr1_ref = [member_name(n) for n in self.arr1_ref]
        self.carr2_ref = [member_name(n) for n in self.arr2_ref]
        self.ccond_ref = [member_name(n) for n in self.cond_ref]

        # declaration
        self.code_declare = self.ctype
        if self.ctemplate:
            self.code_declare += "<%s >"%self.ctemplate        
        if self.arr1.lhs:
            self.code_declare = "vector<%s >"%self.code_declare
            if self.arr2.lhs:
                self.code_declare = "vector<%s >"%self.code_declare
        self.code_declare += " " + self.cname + ";"

        # construction
        # don't construct anything that hasn't been declared
        # don't construct if it has no default
        if self.is_declared and self.default:
            self.code_construct = "%s(%s)"%(self.cname, self.default)
        else:
            self.code_construct = None

    def calculate(self, prefix):
        # handle calculated data; used when writing
        if self.cond_ref:
            assert(self.is_declared) # bug check
            return None
        elif self.arr1_ref:
            assert(not self.is_declared) # bug check
            return '%s%s = %s(%s%s.size());'%(prefix, self.cname, self.ctype, prefix, self.carr1_ref[0])
        elif self.arr2_ref:
            assert(not self.is_declared) # bug check
            if not self.arr1.lhs:
                return '%s%s = %s(%s%s.size());'%(prefix, self.cname, self.ctype, prefix, self.carr2_ref[0])
            else:
                # index of dynamically sized array
                result = '%s%s.resize(%s%s.size()); '%(prefix, self.cname, prefix, self.carr2_ref[0])
                result += 'for (uint i = 0; i < %s%s.size(); i++) '%(prefix, self.carr2_ref[0])
                result += '%s%s[i] = %s(%s%s[i].size());'%(prefix, self.cname, self.ctype, prefix, self.carr2_ref[0])
                return result
        elif self.func:
            assert(not self.is_declared) # bug check
            return '%s%s = %s%s();'%(prefix, self.cname, prefix, self.func)
        else:
            assert(self.is_declared) # bug check
            return None

    def read(self):
        pass

    def write(self):
        pass

    def lshift(self, prefix):
        # don't print array sizes and calculated data
        if not self.is_declared:
            return "out << \"%20s:  -- calculated --\" << endl;"%self.name
        elif not self.arr1.lhs:
            return "out << \"%20s:  \" << %s%s << endl;"%(self.name, prefix, self.cname)
        else:
            return "out << \"%20s:  -- data not shown --\" << endl;"%self.name



class Basic:
    def __init__(self, element):
        global native_types

        self.name = element.getAttribute('name')
        assert(self.name) # debug
        self.cname = cpp_type_name(self.name)
        self.niflibtype = element.getAttribute('niflibtype')

        if self.niflibtype:
            native_types[self.name] = self.niflibtype



class Compound(Basic):
    # create a compound type from the XML <compound /> attributes
    def __init__(self, element):
        Basic.__init__(self, element)
        
        self.members = []     # list of all members (list of Member)
        self.template = False # does it use templates?

        # store all attribute data
        for member in element.getElementsByTagName('add'):
            x = Member(member)
            self.members.append(x)

    def declare(self, prefix):
        pass

    def construct(self, prefix):
        pass



class Block(Compound):
    def __init__(self, attrs):
        Compound.__init__(self, attrs)
        
        self.inherit = None   # ancestor name
        self.cinherit = None  # ancestor C++ name
        self.interface = None # does it have a special interface? (not used)



doc = parse("nif.xml")

# parse elements
for element in doc.getElementsByTagName('basic'):
    x = Basic(element)
    basic_types[x.name] = x

for element in doc.getElementsByTagName("compound"):
    x = Compound(element)
    compound_types[x.name] = x

for element in doc.getElementsByTagName("ancestor"):
    x = Block(element)
    block_types[x.name] = x

for element in doc.getElementsByTagName("niblock"):
    x = Block(element)
    block_types[x.name] = x
