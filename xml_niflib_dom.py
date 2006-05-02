from xml.dom.minidom import *

native_types = {}
native_types['(TEMPLATE)'] = 'T'
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

    def code(self, prefix):
        if not self.op:
            if not self.clhs: return None
            if self.clhs[0] >= '0' and self.clhs[0] <= '9':
                return self.clhs
            else:
                return prefix + self.clhs
        else:
            if self.clhs[0] >= '0' and self.clhs[0] <= '9':
                return '%s %s %s'%(self.clhs, self.op, self.rhs)
            else:
                return '%s%s %s %s'%(prefix, self.clhs, self.op, self.rhs)

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
        assert element.firstChild.nodeType == Node.TEXT_NODE
        self.description = element.firstChild.nodeValue.strip()
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

        # construction: should never be prefixed,
        # so we can make it a member instead of a method
        # don't construct anything that hasn't been declared
        # don't construct if it has no default
        if self.is_declared and self.default:
            self.code_construct = "%s(%s)"%(self.cname, self.default)
        else:
            self.code_construct = None

    # declaration
    def code_declare(self, prefix): # prefix is used to tag local variables only
        result = self.ctype
        if self.ctemplate:
            result += "<%s >"%self.ctemplate        
        if self.arr1.lhs:
            result = "vector<%s >"%result
            if self.arr2.lhs:
                result = "vector<%s >"%result
        result += " " + prefix + self.cname + ";"
        return result

    # handle calculated data; used when writing
    def code_calculate(self, prefix):
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

    # send to "out" stream
    def code_out(self, prefix):
        # don't print array sizes and calculated data
        if not self.is_declared:
            return "out << \"%20s:  -- calculated --\" << endl;"%self.name
        elif not self.arr1.lhs:
            return "out << \"%20s:  \" << %s%s << endl;"%(self.name, prefix, self.cname)
        else:
            return "out << \"%20s:  -- data not shown --\" << endl;"%self.name

    # read & write
    def code_nifstream(self, prefix, reading, lastver1 = None, lastver2 = None, lastcond = None, indent = 0):
        result = ''
        if self.func: return '', lastver1, lastver2, lastcond, indent # skip calculated stuff
        
        # conditioning
        if lastver1 != self.ver1 or lastver2 != self.ver2:
            # we must switch to a new version block
            # close old version block
            if lastver1 or lastver2:
                indent -= 1
                result += "\t"*indent + "};\n"
            # close old condition block as well
            if lastcond:
                indent -= 1
                result += "\t"*indent + "};\n"
                lastcond = None
            # start new version block
            if self.ver1 and not self.ver2:
                result += "\t"*indent + "if ( version >= 0x%08X ) {\n"%self.ver1
                indent += 1
            elif not self.ver1 and self.ver2:
                result += "\t"*indent + "if ( version <= 0x%08X ) {\n"%self.ver2
                indent += 1
            elif self.ver1 and self.ver2:
                result += "\t"*indent + "if ( ( version >= 0x%08X ) && ( version <= 0x%08X ) ) {\n"%(self.ver1, self.ver2)
                indent += 1
            # start new condition block
            if lastcond != self.cond.code(prefix):
                if self.cond.code(prefix):
                    result += "\t"*indent + "if ( %s ) {\n"%self.cond.code(prefix)
                    indent += 1
        else:
            # we remain in the same version block
            # check condition block
            if lastcond != self.cond.code(prefix):
                if lastcond:
                    indent -= 1
                    result += "\t"*indent + "};\n"
                if self.cond.code(prefix):
                    result += "\t"*indent + "if ( %s ) {\n"%self.cond.code(prefix)
                    indent += 1

        # calculating
        if reading:
            if self.arr1.lhs:
                result += "\t"*indent + "%s%s.resize(%s);\n"%(prefix, self.cname, self.arr1.code(prefix))
                if self.arr2.lhs:
                    if not self.arr2_dynamic:
                        result += "\t"*indent + "for (uint i = 0; i < %s; i++)\n"%self.arr1.code(prefix)
                        result += "\t"*indent + "\t%s%s[i].resize(%s);\n"%(prefix, self.cname, self.arr2.code(prefix))
                    else:
                        result += "\t"*indent + "for (uint i = 0; i < %s; i++)\n"%self.arr1.code(prefix)
                        result += "\t"*indent + "\t%s%s[i].resize(%s[i]);\n"%(prefix, self.cname, self.arr2.code(prefix))

        # nifstreaming
        # (TODO: handle arguments)
        if self.arr1.lhs:
            result += "\t"*indent + "for (uint i = 0; i < %s; i++)\n"%self.arr1.code(prefix)
            indent += 1
            if self.arr2.lhs:
                if not self.arr2_dynamic:
                    result += "\t"*indent + "for (uint j = 0; j < %s; j++) {\n"%self.arr2.code(prefix)
                else:
                    result += "\t"*indent + "for (uint j = 0; j < %s[i]; j++) {\n"%self.arr2.code(prefix)
                indent += 1

        if native_types.has_key(self.type):
            if not self.arr1.lhs:
                result += "\t"*indent + "NifStream( %s%s, in, version );\n"%(prefix, self.cname)
            elif not self.arr2.lhs:
                result += "\t"*indent + "NifStream( %s%s[i], in, version );\n"%(prefix, self.cname)
            else:
                result += "\t"*indent + "NifStream( %s%s[i][j], in, version );\n"%(prefix, self.cname)
        else:
            compound = compound_types[self.type]
            if not self.arr1.lhs:
                result2, lastver1, lastver2, lastcond, indent = compound.code_nifstream('%s%s.'%(prefix, self.cname), reading, lastver1, lastver2, lastcond, indent)
                result += result2
            elif not self.arr2.lhs:
                result2, lastver1, lastver2, lastcond, indent = compound.code_nifstream('%s%s[i].'%(prefix, self.cname), reading, lastver1, lastver2, lastcond, indent)
                result += result2
            else:
                result2, lastver1, lastver2, lastcond, indent = compound.code_nifstream('%s%s[i][j].'%(prefix, self.cname), reading, lastver1, lastver2, lastcond, indent)
                result += result2

        if self.arr1.lhs:
            indent -= 1
            result += "\t"*indent + "};\n"
            if self.arr2.lhs:
                indent -= 1
                result += "\t"*indent + "};\n"

        lastver1 = self.ver1
        lastver2 = self.ver2
        lastcond = self.cond.code(prefix)

        return result, lastver1, lastver2, lastcond, indent



class Basic:
    def __init__(self, element):
        global native_types

        self.name = element.getAttribute('name')
        assert(self.name) # debug
        self.cname = cpp_type_name(self.name)
        self.niflibtype = element.getAttribute('niflibtype')
        assert element.firstChild.nodeType == Node.TEXT_NODE
        self.description = element.firstChild.nodeValue.strip()

        if self.niflibtype:
            native_types[self.name] = self.niflibtype



class Compound(Basic):
    # create a compound type from the XML <compound /> attributes
    def __init__(self, element):
        Basic.__init__(self, element)

        self.members = []     # list of all members (list of Member)
        self.template = False # does it use templates?
        self.argument = False # does it use an argument?

        # store all attribute data & calculate stuff
        for member in element.getElementsByTagName('add'):
            x = Member(member)
            self.members.append(x)
            
            # detect templates
            if x.type == '(TEMPLATE)':
                self.template = True
            if x.template == '(TEMPLATE)':
                self.template = True

            # detect argument
            if x.uses_argument:
                self.argument = True
            else:
                self.argument = False

    def code_nifstream(self, prefix, reading, lastver1 = None, lastver2 = None, lastcond = None, indent = 0):
        result = ''
        for member in self.members:
            result2, lastver1, lastver2, lastcond, indent = member.code_nifstream(prefix, reading, lastver1, lastver2, lastcond, indent)
            result += result2
        if lastver1 or lastver2:
            indent -= 1
            result += "\t"*indent + "};\n"
            lastver1 = None
            lastver2 = None
        if lastcond:
            indent -= 1
            result += "\t"*indent + "};\n"
            lastcond = None
        return result, lastver1, lastver2, lastcond, indent

    def declare(self, prefix):
        pass

    def construct(self, prefix):
        pass



class Block(Compound):
    def __init__(self, attrs):
        Compound.__init__(self, attrs)
        
        self.inherit = None   # ancestor name
        self.cinherit = None  # ancestor C++ name
        
        for inherit in element.getElementsByTagName('inherit'):
            self.inherit = inherit.getAttribute('name')
            self.cinherit = class_name(self.inherit)
            break



doc = parse("nif.xml")

# import elements into our code generating classes
for element in doc.getElementsByTagName('basic'):
    x = Basic(element)
    basic_types[x.name] = x

for element in doc.getElementsByTagName("compound"):
    x = Compound(element)
    compound_types[x.name] = x

for element in doc.getElementsByTagName("ancestor"):
    x = Block(element)
    block_types[x.name] = x
    print x.name
    print x.code_nifstream('', True)[0]

for element in doc.getElementsByTagName("niblock"):
    x = Block(element)
    block_types[x.name] = x
