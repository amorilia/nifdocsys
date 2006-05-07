from xml.dom.minidom import *
from textwrap import wrap

#
# global data
#

native_types = {}
native_types['(TEMPLATE)'] = 'T'
basic_types = {}
compound_types = {}
block_types = {}

compound_names = []
block_names = []

ACTION_READ = 0
ACTION_WRITE = 1

#
# C++ code formatting functions
#

class CFile(file):
    def __init__(self, filename, mode):
        file.__init__(self, filename, mode)
        self.indent = 0
        self.backslash_mode = False
    
    # format C++ code; the returned result always ends with a newline
    # if txt starts with "}", indent is decreased
    # if txt ends with "{", indent is increased
    def code(self, txt = None):
        # txt None means just a line break
        # this will also break the backslash, which is kind of handy
        # call code("\n") if you want a backslashed newline in backslash mode
        if txt == None:
            self.write("\n")
            return
    
        # block end
        if txt[:1] == "}": self.indent -= 1    
        # endline string
        if self.backslash_mode:
            endl = " \\\n"
        else:
            endl = "\n"
        # indent string
        prefix = "  " * self.indent
        # strip trailing whitespace, including newlines
        txt = txt.rstrip()
        # replace tabs
        txt = txt.replace("\t", "  ");
        # indent, and add newline
        result = prefix + txt.replace("\n", endl + prefix) + endl
        # block start
        if txt[-1:] == "{": self.indent += 1
    
        self.write(result)
    
    # create C++-style comments (handle multilined comments as well)
    # result always ends with a newline
    def comment(self, txt):
        if self.backslash_mode: return # skip comments when we are in backslash mode
        self.code("// " + "\n".join(wrap(txt)).replace("\n", "\n// "))
    
    # C++ member declaration
    def declare(self, block):
        for y in block.members:
            if y.is_declared and not y.is_duplicate:
                self.comment(y.description)
                self.code(y.code_declare())

    def get_attr(self, block):
        # get the attributes whose type is implemented natively by Niflib
        if block.inherit:
            self.code("attr_ref attr = %s::GetAttr( attr_name );"%block.inherit.cname)
            self.code("if ( attr.is_null() == false ) return attr;")
        for y in block.members:
            if y.is_declared and not y.is_duplicate:
                if native_types.has_key(y.type) and (not y.arr1.lhs) and (not y.arr2.lhs) and (not y.func):
                    self.code('if ( attr_name == "%s" )'%y.name)
                    self.code("\treturn attr_ref(%s);"%y.cname)
        if not block.is_ancestor:
            self.code('throw runtime_error("The attribute you requested does not exist in this block, or cannot be accessed.");')
        self.code("return attr_ref();")

    def stream(self, block, action, localprefix = "", prefix = ""):
        lastver1 = None
        lastver2 = None
        lastcond = None
        # stream name
        if action == ACTION_READ:
            stream = "in"
        elif action == ACTION_WRITE:
            stream = "out"
        # read + write: declare local variables
        for y in block.members:
            if not y.is_declared and not y.is_duplicate:
                #self.comment(y.description)
                self.code(y.code_declare(localprefix))
        # stream the ancestor
        if isinstance(block, Block):
            if block.inherit:
                if action == ACTION_READ:
                    self.code("%s::Read( %s, version );"%(block.inherit.cname, stream))
                elif action == ACTION_WRITE:
                    self.code("%s::Write( %s, version );"%(block.inherit.cname, stream))
        # now comes the difficult part: processing all members recursively
        for y in block.members:
            # resolve array & cond references
            y_arr1_lmember = None
            y_arr2_lmember = None
            y_cond_lmember = None
            y_arr1_prefix = ""
            y_arr2_prefix = ""
            y_cond_prefix = ""
            if y.arr1.lhs or y.arr2.lhs or y.cond.lhs:
                for z in block.members:
                    if not y_arr1_lmember and y.arr1.lhs == z.name:
                        y_arr1_lmember = z
                    if not y_arr2_lmember and y.arr2.lhs == z.name:
                        y_arr2_lmember = z
                    if not y_cond_lmember and y.cond.lhs == z.name:
                        y_cond_lmember = z
                if y_arr1_lmember:
                    if y_arr1_lmember.is_declared:
                        y_arr1_prefix = prefix
                    else:
                        y_arr1_prefix = localprefix
                if y_arr2_lmember:
                    if y_arr2_lmember.is_declared:
                        y_arr2_prefix = prefix
                    else:
                        y_arr2_prefix = localprefix
                if y_cond_lmember:
                    if y_cond_lmember.is_declared:
                        y_cond_prefix = prefix
                    else:
                        y_cond_prefix = localprefix
            # resolve this prefix
            if y.is_declared:
                y_prefix = prefix
            else:
                y_prefix = localprefix
            # conditioning
            y_cond = y.cond.code(y_cond_prefix)
            if lastver1 != y.ver1 or lastver2 != y.ver2:
                # we must switch to a new version block    
                # close old version block
                if lastver1 or lastver2: self.code("};")
                # close old condition block as well    
                if lastcond:
                    self.code("};")
                    lastcond = None
                # start new version block
                if y.ver1 and not y.ver2:
                    self.code("if ( version >= 0x%08X ) {"%y.ver1)
                elif not y.ver1 and y.ver2:
                    self.code("if ( version <= 0x%08X ) {"%y.ver2)
                elif y.ver1 and y.ver2:
                    self.code("if ( ( version >= 0x%08X ) && ( version <= 0x%08X ) ) {"%(y.ver1, y.ver2))
                # start new condition block
                if lastcond != y_cond and y_cond:
                        self.code("if ( %s ) {"%y_cond)
            else:
                # we remain in the same version block    
                # check condition block
                if lastcond != y_cond:
                    if lastcond:
                        self.code("};")
                    if y_cond:
                        self.code("if ( %s ) {"%y_cond)
    
            # read: calculate array sizes
            if action == ACTION_READ:
                if y.arr1.lhs:
                    self.code("%s%s.resize(%s);"%(y_prefix, y.cname, y.arr1.code(y_arr1_prefix)))
                    if y.arr2.lhs:
                        if not y.arr2_dynamic:
                            self.code("for (uint i%i = 0; i%i < %s; i%i++)"%(self.indent, self.indent, y.arr1.code(y_arr1_prefix), self.indent))
                            self.code("\t%s%s[i%i].resize(%s);"%(y_prefix, y.cname, self.indent, y.arr2.code(y_arr2_prefix)))
                        else:
                            self.code("for (uint i%i = 0; i%i < %s; i%i++)"%(self.indent, self.indent, y.arr1.code(y_arr1_prefix), self.indent))
                            self.code("\t%s%s[i%i].resize(%s[i%i]);"%(y_prefix, y.cname, self.indent, y.arr2.code(y_arr2_prefix), self.indent))
            
            # TODO handle arguments
            # loop over arrays
            if y.arr1.lhs:                self.code(\
                    "for (uint i%i = 0; i%i < %s; i%i++) {"\
                    %(self.indent, self.indent, y.arr1.code(y_arr1_prefix), self.indent))
                if y.arr2.lhs:
                    if not y.arr2_dynamic:
                        self.code(\
                            "for (uint i%i = 0; i%i < %s; i%i++) {"\
                            %(self.indent, self.indent, y.arr2.code(y_arr2_prefix), self.indent))
                    else:
                        self.code(\
                            "for (uint i%i = 0; i%i < %s[i%i]; i%i++) {"\
                            %(self.indent, self.indent, self.indent-1, y.arr2.code(y_arr2_prefix), self.indent))
    
            if native_types.has_key(y.type):
                if action in [ACTION_READ, ACTION_WRITE]:
                    if not y.arr1.lhs:
                        self.code(\
                            "NifStream( %s%s, %s, version );"\
                            %(y_prefix, y.cname, stream))
                    elif not y.arr2.lhs:
                        self.code(\
                            "NifStream( %s%s[i%i], %s, version );"\
                            %(y_prefix, y.cname, self.indent-1, stream))
                    else:
                        self.code(\
                            "NifStream( %s%s[i%i][i%i], %s, version );"\
                            %(y_prefix, y.cname, self.indent-2, self.indent-1, stream))
            else:
                subblock = compound_types[y.type]
                if not y.arr1.lhs:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s%s."%(y_prefix, y.cname))
                elif not y.arr2.lhs:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s%s[i%i]."%(y_prefix, y.cname, self.indent-1))
                else:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s%s[i%i][i%i]."%(y_prefix, y.cname, self.indent-2, self.indent-1))

            # close array loops
            if y.arr1.lhs:
                self.code("};")
                if y.arr2.lhs:
                    self.code("};")

            lastver1 = y.ver1
            lastver2 = y.ver2
            lastcond = y_cond

        if lastver1 or lastver2:
            self.code("};")
        if lastcond:
            self.code("};")
            
            

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
            if not self.lhs: return None
            if self.lhs[0] >= '0' and self.lhs[0] <= '9':
                return self.lhs
            else:
                return prefix + self.clhs
        else:
            if self.lhs[0] >= '0' and self.lhs[0] <= '9':
                return '%s %s %s'%(self.lhs, self.op, self.rhs)
            else:
                return '%s%s %s %s'%(prefix, self.clhs, self.op, self.rhs)

class Member:
    def __init__(self, element):
        assert element.tagName == 'add'
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
        if True: #parent.tagName == "compound": ### DISABLED FOR NOW... TRY TO FIND OTHER SOLUTION
            # compounds don't have inheritance
            # so don't declare variables that can be calculated
            if (self.arr1_ref or self.arr2_ref or self.func) and not self.cond_ref:
                self.is_declared = False
            else:
                self.is_declared = True
        else:
            # always declare block fields, to avoid issues with inheritance
            # a calculated field might still be used by a child
            # in case we need to keep track of it
            self.is_declared = True

        # C++ names
        self.cname     = member_name(self.name)
        self.ctype     = class_name(self.type)
        self.carg      = member_name(self.arg)
        self.ctemplate = class_name(self.template)
        self.carr1_ref = [member_name(n) for n in self.arr1_ref]
        self.carr2_ref = [member_name(n) for n in self.arr2_ref]
        self.ccond_ref = [member_name(n) for n in self.cond_ref]

    # construction
    # don't construct anything that hasn't been declared
    # don't construct if it has no default
    def code_construct(self):
        if self.is_declared and self.default and not self.is_duplicate:
            return "%s(%s)"%(self.cname, self.default)

    # declaration
    def code_declare(self, prefix = ""): # prefix is used to tag local variables only
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
    def code_calculate(self, localprefix = '', prefix = ''):
        if self.cond_ref:
            assert(self.is_declared) # bug check
            return None
        elif self.arr1_ref:
            assert(not self.is_declared) # bug check
            return '%s%s = %s(%s%s.size());'%(localprefix, self.cname, self.ctype, prefix, self.carr1_ref[0])
        elif self.arr2_ref:
            assert(not self.is_declared) # bug check
            if not self.arr1.lhs:
                return '%s%s = %s(%s%s.size());'%(localprefix, self.cname, self.ctype, prefix, self.carr2_ref[0])
            else:
                # index of dynamically sized array
                result = '%s%s.resize(%s%s.size()); '%(localprefix, self.cname, prefix, self.carr2_ref[0])
                result += 'for (uint i%i = 0; i < %s%s.size(); i++) '%(indent, prefix, self.carr2_ref[0])
                result += '%s%s[i%i] = %s(%s%s[i%i].size());'%(localprefix, self.cname, indent, self.ctype, prefix, self.carr2_ref[0], indent)
                return result
        elif self.func:
            assert(not self.is_declared) # bug check
            return '%s%s = %s%s();'%(prefix, self.cname, prefix, self.func)
        else:
            assert(self.is_declared) # bug check
            return None

    # send to "out" stream
    def code_out(self, prefix = ''):
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
        self.cname = class_name(self.name)
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

    def code_construct(self):
        # constructor
        result = ''
        first = True
        for y in self.members:
            y_code_construct = y.code_construct()
            if y_code_construct:
                if not first:
                    result += ', ' + y_code_construct
                else:
                    result += ' : ' + y_code_construct
                    first = False
        return result



class Block(Compound):
    def __init__(self, element):
        Compound.__init__(self, element)
        
        self.is_ancestor = (element.tagName == "ancestor")
        
        self.inherit = None   # ancestor block
        
        for inherit in element.getElementsByTagName('inherit'):
            self.inherit = block_types[inherit.getAttribute('name')]
            break



#
# import elements into our code generating classes#

doc = parse("nif.xml")

for element in doc.getElementsByTagName('basic'):
    x = Basic(element)
    assert not basic_types.has_key(x.name)
    basic_types[x.name] = x

for element in doc.getElementsByTagName("compound"):
    x = Compound(element)
    assert not compound_types.has_key(x.name)
    compound_types[x.name] = x
    compound_names.append(x.name)

for element in doc.getElementsByTagName("ancestor"):
    x = Block(element)
    assert not block_types.has_key(x.name)
    block_types[x.name] = x
    block_names.append(x.name)

for element in doc.getElementsByTagName("niblock"):
    x = Block(element)
    assert not block_types.has_key(x.name)
    block_types[x.name] = x
    block_names.append(x.name)

#
# generate header code
#

h = CFile("xml_extract.h", "w")
c = CFile("xml_extract.cpp", "w")

# generate compound code
for n in compound_names:
    x = compound_types[n]
    
    # skip natively implemented types
    if x.niflibtype: continue
    
    # header
    h.comment("\n" + x.description + "\n")
    hdr = "struct %s"%x.cname
    if x.template: hdr = "template <class T >\n%s"%hdr
    hdr += " {"
    h.code(hdr)

    # declaration
    h.declare(x)
    
    # constructor
    x_code_construct = x.code_construct()
    if x_code_construct:
        h.code("%s()"%x.cname + x_code_construct + " {};")
    
    # done
    h.code("};")
    h.code()

# generate block code
for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
    
    # declaration
    h.backslash_mode = True
    h.code('#define %s_MEMBERS'%x_define_name)
    h.declare(x)
    h.code()
    
    # get attribute
    h.code("#define %s_GETATTR"%x_define_name)
    h.get_attr(x)
    h.code()

    # parents
    if not x.inherit:
        par = "ABlock"
    else:
        par = x.inherit.cname
    h.code('#define %s_PARENTS %s'%(x_define_name, par))
    h.code()

    # istream
    h.code("#define %s_READ"%x_define_name)
    h.stream(x, ACTION_READ)
    h.code()

    # ostream
    h.code("#define %s_WRITE"%x_define_name)
    h.stream(x, ACTION_WRITE)
    h.code()
    
