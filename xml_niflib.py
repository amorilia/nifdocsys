from xml.dom.minidom import *
from textwrap import wrap

import sys
import os

#
# global data
#

root_dir = "."
prev = ""
for i in sys.argv:
    if prev == "-p":
        root_dir = i
    prev = i

native_types = {}
native_types['TEMPLATE'] = 'T'
basic_types = {}
compound_types = {}
block_types = {}

basic_names = []
compound_names = []
block_names = []

ACTION_READ = 0
ACTION_WRITE = 1
ACTION_OUT = 2
ACTION_FIXLINKS = 3
ACTION_REMOVECROSSREF = 4
ACTION_GETLINKS = 5

#
# C++ code formatting functions
#

class CFile(file):
    def __init__(self, filename, mode):
        file.__init__(self, root_dir + os.sep + filename, mode)
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
        # special, private:, public:, and protected:
        if txt[-1:] == ":": self.indent -= 1
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
        # special, private:, public:, and protected:
        if txt[-1:] == ":": self.indent += 1
    
        self.write(result)
    
    # create C++-style comments (handle multilined comments as well)
    # result always ends with a newline
    def comment(self, txt):
        if self.backslash_mode: return # skip comments when we are in backslash mode
        self.code("/*!\n * " + "\n".join(wrap(txt)).replace("\n", "\n * ") + "\n */")
    
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

    def stream(self, block, action, localprefix = "", prefix = "", arg_prefix = "", arg_member = None):
        lastver1 = None
        lastver2 = None
        lastcond = None
        # stream name
        if action == ACTION_READ:
            stream = "in"
        elif action == ACTION_WRITE:
            stream = "out"
        elif action == ACTION_OUT:
            stream = "out" # CHEATING!!! turn this back to out when we're done debugging...

        # preperation
        if isinstance(block, Block):
            if action == ACTION_READ:
                if block.has_links or block.has_crossrefs:
                    self.code("uint block_num;")
            if action == ACTION_OUT:
                self.code("stringstream out;")
            if action == ACTION_GETLINKS:
                self.code("list<blk_ref> links;")

        # stream the ancestor
        if isinstance(block, Block):
            if block.inherit:
                if action == ACTION_READ:
                    self.code("%s::Read( %s, link_stack, version );"%(block.inherit.cname, stream))
                elif action == ACTION_WRITE:
                    self.code("%s::Write( %s, link_map, version );"%(block.inherit.cname, stream))
                elif action == ACTION_OUT:
                    self.code("%s << %s::asString();"%(stream, block.inherit.cname))
                elif action == ACTION_FIXLINKS:
                    self.code("%s::FixLinks( objects, link_stack, version );"%block.inherit.cname)
                elif action == ACTION_REMOVECROSSREF:
                    self.code("%s::RemoveCrossRef(block_to_remove);"%block.inherit.cname)
                elif action == ACTION_GETLINKS:
                    self.code("links.extend(%s::GetLinks());"%block.inherit.cname)

        # declare and calculate local variables
        if action in [ACTION_READ, ACTION_WRITE, ACTION_OUT]:
            block.members.reverse() # calculated data depends on data further down the structure
            for y in block.members:
                # read + write + out + fixlinks: declare
                if not y.is_declared and not y.is_duplicate:
                    # declare it
                    self.code(y.code_declare(localprefix))
                    # write + out: calculate
                    if action in [ACTION_WRITE, ACTION_OUT]:
                        if y.cond_ref:
                            assert(y.is_declared) # bug check
                        elif y.arr1_ref:
                            assert(not y.is_declared) # bug check
                            self.code('%s%s = %s(%s%s.size());'%(localprefix, y.cname, y.ctype, prefix, y.carr1_ref[0]))
                        elif y.arr2_ref:
                            assert(not y.is_declared) # bug check
                            if not y.arr1.lhs:
                                self.code('%s%s = %s(%s%s.size());'%(localprefix, y.cname, y.ctype, prefix, y.carr2_ref[0]))
                            else:
                                # index of dynamically sized array
                                self.code('%s%s.resize(%s%s.size());'%(localprefix, y.cname, prefix, y.carr2_ref[0]))
                                self.code('for (uint i%i = 0; i%i < %s%s.size(); i%i++)'%(self.indent, self.indent, prefix, y.carr2_ref[0], self.indent))
                                self.code('\t%s%s[i%i] = %s(%s%s[i%i].size());'%(localprefix, y.cname, self.indent, y.ctype, prefix, y.carr2_ref[0], self.indent))
                        elif y.func:
                            assert(not y.is_declared) # bug check
                            self.code('%s%s = %s%s();'%(localprefix, y.cname, prefix, y.func))
                        else:
                            assert(y.is_declared) # bug check
            block.members.reverse() # undo reverse
                            
        # now comes the difficult part: processing all members recursively
        for y in block.members:
            # get block
            try:
                subblock = basic_types[y.type]
            except KeyError:
                subblock = compound_types[y.type]
            # check for links
            if action in [ACTION_FIXLINKS, ACTION_GETLINKS]:
                if not subblock.has_links and not subblock.has_crossrefs:
                    continue # contains no links, so skip this member!
            if action == ACTION_OUT:
                if y.is_duplicate:
                    continue # don't write variables twice
            # resolve array & cond references
            y_arr1_lmember = None
            y_arr2_lmember = None
            y_cond_lmember = None
            y_arg = None
            y_arr1_prefix = ""
            y_arr2_prefix = ""
            y_cond_prefix = ""
            y_arg_prefix = ""
            if y.arr1.lhs or y.arr2.lhs or y.cond.lhs or y.arg:
                for z in block.members:
                    if not y_arr1_lmember and y.arr1.lhs == z.name:
                        y_arr1_lmember = z
                    if not y_arr2_lmember and y.arr2.lhs == z.name:
                        y_arr2_lmember = z
                    if not y_cond_lmember and y.cond.lhs == z.name:
                        y_cond_lmember = z
                    if not y_arg and y.arg == z.name:
                        y_arg = z
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
                if y_arg:
                    if y_arg.is_declared:
                        y_arg_prefix = prefix
                    else:
                        y_arg_prefix = localprefix
            # resolve this prefix
            if y.is_declared:
                y_prefix = prefix
            else:
                y_prefix = localprefix
            # resolve arguments
            if y.arr1 and y.arr1.lhs == 'ARG':
                y.arr1.lhs = arg_member.name
                y.arr1.clhs = arg_member.cname
                y_arr1_prefix = arg_prefix
            if y.arr2 and y.arr2.lhs == 'ARG':
                y.arr2.lhs = arg_member.name
                y.arr2.clhs = arg_member.cname
                y_arr2_prefix = arg_prefix
            if y.cond and y.cond.lhs == 'ARG':
                y.cond.lhs = arg_member.name
                y.cond.clhs = arg_member.cname
                y_cond_prefix = arg_prefix
            # conditioning
            y_cond = y.cond.code(y_cond_prefix)
            if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS]:
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
            elif action == ACTION_OUT:
                # check condition block
                if lastcond != y_cond:
                    if lastcond:
                        self.code("};")
                    if y_cond:
                        self.code("if ( %s ) {"%y_cond)
    
            # read: also resize arrays
            if action == ACTION_READ:
                if y.arr1.lhs:
                    if y.arr1.lhs.isdigit() == False:
                        self.code("%s%s.resize(%s);"%(y_prefix, y.cname, y.arr1.code(y_arr1_prefix)))
                    if y.arr2.lhs:
                        if y.arr2.lhs.isdigit() == False:
                            if not y.arr2_dynamic:
                                self.code("for (uint i%i = 0; i%i < %s%s.size(); i%i++)"%(self.indent, self.indent, y_prefix, y.cname, self.indent))
                                self.code("\t%s%s[i%i].resize(%s);"%(y_prefix, y.cname, self.indent, y.arr2.code(y_arr2_prefix)))
                            else:
                                self.code("for (uint i%i = 0; i%i < %s%s.size(); i%i++)"%(self.indent, self.indent, y_prefix, y.cname, self.indent))
                                self.code("\t%s%s[i%i].resize(%s[i%i]);"%(y_prefix, y.cname, self.indent, y.arr2.code(y_arr2_prefix), self.indent))
                
            # loop over arrays
            # and resolve variable name
            if not y.arr1.lhs:
                z = "%s%s"%(y_prefix, y.cname)
            else:
                if y.arr1.lhs.isdigit() == False:
                    self.code(\
                        "for (uint i%i = 0; i%i < %s%s.size(); i%i++) {"\
                        %(self.indent, self.indent, y_prefix, y.cname, self.indent))
                else:
                    self.code(\
                        "for (uint i%i = 0; i%i < %s; i%i++) {"\
                        %(self.indent, self.indent, y.arr1.code(y_arr1_prefix), self.indent))
                if not y.arr2.lhs:
                    z = "%s%s[i%i]"%(y_prefix, y.cname, self.indent-1)
                else:
                    if not y.arr2_dynamic:
                        if y.arr2.lhs.isdigit() == False:
                            self.code(\
                                "for (uint i%i = 0; i%i < %s%s[i%i].size(); i%i++) {"\
                                %(self.indent, self.indent, y_arr2_prefix, y.cname, self.indent-1, self.indent))
                        else:
                            self.code(\
                                "for (uint i%i = 0; i%i < %s; i%i++) {"\
                                %(self.indent, self.indent, y.arr2.code(y_arr2_prefix), self.indent))
                    else:
                        self.code(\
                            "for (uint i%i = 0; i%i < %s[i%i]; i%i++) {"\
                            %(self.indent, self.indent, y.arr2.code(y_arr2_prefix), self.indent-1, self.indent))
                    z = "%s%s[i%i][i%i]"%(y_prefix, y.cname, self.indent-2, self.indent-1)
    
            if native_types.has_key(y.type):
                # resolve variable name
                if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS]:
                    if (not subblock.is_link) and (not subblock.is_crossref):
                        if action in [ACTION_READ, ACTION_WRITE]:
                            if not y.arg:
                                self.code("NifStream( %s, %s, version );"%(z, stream))
                            else:
                                self.code("NifStream( %s, %s, version, %s%s );"%(z, stream, y_prefix, y.carg))
                    else:
                        if action == ACTION_READ:
                            self.code("NifStream( block_num, %s, version );"%stream)
                            if y.is_declared and not y.is_duplicate:
                                self.code("link_stack.push_back( block_num );")
                        elif action == ACTION_WRITE:
                            self.code("NifStream( link_map[StaticCast<NiObject>(%s)], %s, version );"%(z, stream))
                        elif action == ACTION_FIXLINKS:
                            if y.is_declared and not y.is_duplicate:
                                self.code("if (link_stack.empty())")
                                self.code("\tthrow runtime_error(\"Trying to pop a link from empty stack. This is probably a bug.\");")
                                self.code("if (link_stack.front() != 0xffffffff)")
                                self.code("\t%s = DynamicCast<%s>(objects[link_stack.front()]);"%(z,y.ctemplate))
                                self.code("else")
                                self.code("\t%s = NULL;"%z)
                                self.code("link_stack.pop_front();")
                elif action == ACTION_OUT:
                    if (not subblock.is_link) and (not subblock.is_crossref):
                        if not y.arr1.lhs:
                            self.code('%s << "%*s%s:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, z))
                        elif not y.arr2.lhs:
                            self.code('%s << "%*s%s[" << i%i << "]:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, self.indent-1, z))
                        else:
                            self.code('%s << "%*s%s[" << i%i << "][" << i%i << "]:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, self.indent-2, self.indent-1, z))
                    else:
                        if not y.arr1.lhs:
                            self.code('%s << "%*s%s:  " << "%s" << endl;'%(stream, 2*self.indent, "", y.name, y.ctemplate))
                        elif not y.arr2.lhs:
                            self.code('%s << "%*s%s[" << i%i << "]:  " << "%s" << endl;'%(stream, 2*self.indent, "", y.name, self.indent-1, y.ctemplate))
                        else:
                            self.code('%s << "%*s%s[" << i%i << "][" << i%i << "]:  " << "%s" << endl;'%(stream, 2*self.indent, "", y.name, self.indent-2, self.indent-1, y.ctemplate))
            else:
                subblock = compound_types[y.type]
                if not y.arr1.lhs:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s."%z, y_arg_prefix,  y_arg)
                elif not y.arr2.lhs:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s."%z, y_arg_prefix, y_arg)
                else:
                    self.stream(subblock, action, "%s%s_"%(localprefix, y.cname), "%s."%z, y_arg_prefix, y_arg)

            # close array loops
            if y.arr1.lhs:
                self.code("};")
                if y.arr2.lhs:
                    self.code("};")

            lastver1 = y.ver1
            lastver2 = y.ver2
            lastcond = y_cond

        if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS]:
            if lastver1 or lastver2:
                self.code("};")
                
        if lastcond:
            self.code("};")

        # the end
        if isinstance(block, Block):
            if action == ACTION_OUT:
                self.code("return out.str();")
            if action == ACTION_GETLINKS:
                self.code("return links;")



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
    if n == 'TEMPLATE': return 'T'
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
    if n == 'ARG': return 'ARG'
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
        
        if n.find('&&') != -1:
            self.lhs = Expr(n[n.find('(')+1:n.find(')')])
            self.clhs = None
            self.op = '&&'
            self.rhs = Expr(n[n.rfind('(')+1:n.rfind(')')])
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
            if self.op != '&&':
                if self.lhs[0] >= '0' and self.lhs[0] <= '9':
                    return '(%s %s %s)'%(self.lhs, self.op, self.rhs)
                else:
                    return '(%s%s %s %s)'%(prefix, self.clhs, self.op, self.rhs)
            else:
                return '((%s) && (%s))'%(self.lhs.code(prefix), self.rhs.code(prefix))

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
        if not self.default and (not self.arr1.lhs and not self.arr2.lhs):
            if self.type in ["uint", "ushort", "byte"]:
                self.default = "0"
            elif self.type == "bool":
                self.default = "false"
            elif self.type in ["Ref", "Ptr"]:
                self.default = "NULL"
            elif self.type in "float":
                self.default = "0.0"
            elif self.type == "HeaderString":
                pass
            elif self.type in basic_names:
                self.default = "0"
        if self.default:
            if self.type == "string":
                self.default = "\"" + self.default + "\""
            elif self.type == "float":
                self.default += "f"
            elif self.type in ["Ref", "Ptr", "bool"]:
                pass
            else:
                self.default = "(%s)%s"%(class_name(self.type), self.default)
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
        self.arr2_dynamic = False  # true if arr2 refers to an array
        sis = element.previousSibling
        while sis:
            if sis.nodeType == Node.ELEMENT_NODE:
                sis_name = sis.getAttribute('name')
                if sis_name == self.name:
                    self.is_duplicate = True
                sis_arr1 = Expr(sis.getAttribute('arr1'))
                sis_arr2 = Expr(sis.getAttribute('arr2'))
                if sis_name == self.arr2.lhs and sis_arr1.lhs:
                    self.arr2_dynamic = True
            sis = sis.previousSibling

        # calculate stuff from reference to next members
        self.arr1_ref = [] # names of the attributes it is a (unmasked) size of
        self.arr2_ref = [] # names of the attributes it is a (unmasked) size of
        self.cond_ref = [] # names of the attributes it is a condition of
        sis = element.nextSibling
        while sis != None:
            if sis.nodeType == Node.ELEMENT_NODE:
                sis_name = sis.getAttribute('name')
                sis_arr1 = Expr(sis.getAttribute('arr1'))
                sis_arr2 = Expr(sis.getAttribute('arr2'))
                sis_cond = Expr(sis.getAttribute('cond'))
                if sis_arr1.lhs == self.name and not sis_arr1.rhs:
                    self.arr1_ref.append(sis_name)
                if sis_arr2.lhs == self.name and not sis_arr2.rhs:
                    self.arr2_ref.append(sis_name)
                if sis_cond.lhs == self.name:
                    self.cond_ref.append(sis_name)
            sis = sis.nextSibling
        # true if it is declared in the class, if false, this field is calculated somehow
        # so don't declare variables that can be calculated; ("Num Vertices" is a dirty hack, it's used in derived classes as array size so we must declare it)
        #if (self.arr1_ref or self.arr2_ref or self.func) and not self.cond_ref and self.name != "Num Vertices":
        #    self.is_declared = False
        #else:
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
        suffix1 = ""
        suffix2 = ""
        if self.ctemplate:
            if result != "*":
                result += "<%s >"%self.ctemplate
            else:
                result = "%s *"%self.ctemplate
        if self.arr1.lhs:
            if self.arr1.lhs.isdigit():
                suffix1 = "[%s]"%self.arr1.lhs
            else:
                if self.arr2.lhs and self.arr2.lhs.isdigit():
                    result = "vector< array<%s,%s> >"%(result,self.arr2.lhs)
                else:
                    result = "vector<%s >"%result
            if self.arr2.lhs:
                if self.arr2.lhs.isdigit():
                    if self.arr1.lhs.isdigit():
                        suffix2 = "[%s]"%self.arr2.lhs
                else:
                    result = "vector<%s >"%result
        result += " " + prefix + self.cname + suffix1 + suffix2 + ";"
        return result



class Basic:
    def __init__(self, element):
        global native_types

        self.name = element.getAttribute('name')
        assert(self.name) # debug
        self.cname = class_name(self.name)
        self.niflibtype = element.getAttribute('niflibtype')
        assert element.firstChild.nodeType == Node.TEXT_NODE
        self.description = element.firstChild.nodeValue.strip()

        self.is_link = False
        self.is_crossref = False
        self.has_links = False
        self.has_crossrefs = False

        if self.niflibtype:
            native_types[self.name] = self.niflibtype
            if self.niflibtype == "Ref":
                self.is_link = True
                self.has_links = True
            if self.niflibtype == "*":
                self.is_crossref = True
                self.has_crossrefs = True



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
            if x.type == 'TEMPLATE':
                self.template = True
            if x.template == 'TEMPLATE':
                self.template = True

            # detect argument
            if x.uses_argument:
                self.argument = True
            else:
                self.argument = False

            # detect links & crossrefs
            y = None
            try:
                y = basic_types[x.type]
            except KeyError:
                try:
                    y = compound_types[x.type]
                except KeyError:
                    pass
            if y:
                if y.has_links:
                    self.has_links = True
                if y.has_crossrefs:
                    self.has_crossrefs = True

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
        
        self.is_ancestor = (element.getAttribute('abstract') == "1")
        inherit = element.getAttribute('inherit')
        if inherit:
            self.inherit = block_types[inherit]
        else:
            self.inherit = None
        self.has_interface = (element.getElementsByTagName('interface') != [])



#
# import elements into our code generating classes
#

doc = parse("nif.xml")

for element in doc.getElementsByTagName('basic'):
    x = Basic(element)
    assert not basic_types.has_key(x.name)
    basic_types[x.name] = x
    basic_names.append(x.name)

for element in doc.getElementsByTagName("compound"):
    x = Compound(element)
    assert not compound_types.has_key(x.name)
    compound_types[x.name] = x
    compound_names.append(x.name)

for element in doc.getElementsByTagName("niblock"):
    x = Block(element)
    assert not block_types.has_key(x.name)
    block_types[x.name] = x
    block_names.append(x.name)

# generate compound code

for n in compound_names:
    x = compound_types[n]
    
    # skip natively implemented types
    if x.niflibtype: continue
    if n[:3] == 'ns ': continue

    h = CFile('gen/' + x.cname + '.h', 'w')  
    h.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    h.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    h.code()
    h.code( '#ifndef _' + x.cname.upper() + '_H_' )
    h.code( '#define _' + x.cname.upper() + '_H_' )
    h.code()
    h.code( '#include \"NIF_IO.h\"' )

    #additional structure includes
    for y in x.members:
        if y.ctype in compound_names and compound_types[y.ctype].niflibtype == '':
            h.code( '#include \"gen/%s.h\"'%y.ctype )
    
    l = [] #new empty list
    

    #detect need for ref inclusion/forward declarations
    for y in x.members:
        if y.ctype == "Ref" or y.ctype == "*":
            l.append( 'class %s;'%y.ctemplate )

    if len(l) > 0:
        h.code( '#include \"Ref.h\"' )
        h.code()
        h.code( '//Forward Declarations' )
        for y in l:
            h.code( y )

    h.code()
    
    # header
    h.comment(x.description)
    hdr = "struct %s"%x.cname
    if x.template: hdr = "template <class T >\n%s"%hdr
    hdr += " {"
    h.code(hdr)
    
    #constructor/destructor
    if not x.template:
        h.code( '/*! Default Constructor */' )
        h.code( "%s()"%x.cname + ';' )
        h.code( '/*! Default Destructor */' )
        h.code( "~%s()"%x.cname + ';' )

    # declaration
    h.declare(x)


    # done
    h.code("};")
    h.code()
    h.code( '#endif' )

    if not x.template:
        cpp = CFile('gen/' + x.cname + '.cpp', 'w')
        cpp.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
        cpp.code( 'All rights reserved.  Please see niflib.h for licence. */' )
        cpp.code()
        cpp.code( '#include \"' + x.cname + '.h\"' )
        
        #additional includes
        for y in x.members:
            if y.ctype == "Ref" or y.ctype == "*":
                cpp.code( '#include \"obj/%s.h\"'%y.ctemplate )
            
        cpp.code()
        cpp.code( '//Constructor' )
        
        # constructor
        x_code_construct = x.code_construct()
        if x_code_construct:
            cpp.code("%s::%s()"%(x.cname,x.cname) + x_code_construct + " {};")
        cpp.code()

        cpp.code( '//Destructor' )
        
        # destructor
        cpp.code("%s::~%s()"%(x.cname,x.cname) + " {};")
    
# generate block code

h = CFile("gen/obj_defines.h", "w")

# file header

h.write("""/* Copyright (c) 2006, NIF File Format Library and Tools
All rights reserved.  Please see niflib.h for licence. */

#ifndef _OBJ_DEFINES_H_
#define _OBJ_DEFINES_H_

#include "NIF_IO.h"
#include "Ref.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

""")

# for now just include all the unimplimented structures
for y in compound_names:
    if compound_types[y].niflibtype == '' and y[:3] != 'ns ':
        h.code( '#include \"gen/%s.h\"'%y )
h.code()

# forward declaration of the block classes
for n in block_names:
    x = block_types[n]
    h.code("class %s;"%x.cname)

h.code()

h.backslash_mode = True

for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
        
    # declaration
    h.code('#define %s_MEMBERS'%x_define_name)
    h.declare(x)
    h.code()
    
    # get attribute
    #h.code("#define %s_GETATTR"%x_define_name)
    #h.get_attr(x)
    #h.code()

    # parents
    if not x.inherit:
        par = ""
    else:
        par = x.inherit.cname
    # declaration
    h.code('#define %s_INCLUDE \"%s.h\"'%(x_define_name, par))
    h.code()
    h.code('#define %s_PARENT %s'%(x_define_name, par))
    h.code()

    # constructor
    h.code("#define %s_CONSTRUCT "%x_define_name)
    x_code_construct = x.code_construct()
    if x_code_construct:
        h.code(x_code_construct)
    h.code()
    
    # istream
    h.code("#define %s_READ"%x_define_name)
    h.stream(x, ACTION_READ)
    h.code()

    # ostream
    h.code("#define %s_WRITE"%x_define_name)
    h.stream(x, ACTION_WRITE)
    h.code()
    
    # as string
    h.code("#define %s_STRING"%x_define_name)
    h.stream(x, ACTION_OUT)
    h.code()

    # fix links
    h.code("#define %s_FIXLINKS"%x_define_name)
    h.stream(x, ACTION_FIXLINKS)
    h.code()

    # remove cross reference
    #h.code("#define %s_REMOVECROSSREF"%x_define_name)
    #h.stream(x, ACTION_REMOVECROSSREF)
    #h.code()

    # get links
    #h.code("#define %s_GETLINKS"%x_define_name)
    #h.stream(x, ACTION_GETLINKS)
    #h.code()

h.backslash_mode = False
        
h.code("#endif")

h.close()

# Factories

f = CFile("gen/obj_factories.cpp", "w")
f.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
f.code( 'All rights reserved.  Please see niflib.h for licence. */' )
f.code()
f.code('#include "obj/NiObject.h"')
f.code('typedef NiObject*(*blk_factory_func)();')
f.code('extern map<string, blk_factory_func> global_block_map;')
f.code()
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('#include "obj/%s.h"'%x.cname)
        f.code('NiObject * Create%s() { return new %s; }'%(x.cname,x.cname))
f.code()
f.code('//This function registers the factory functions with global_block_map which is used by CreateBlock')
f.code('void RegisterBlockFactories() {')
for n in block_names:
    x = block_types[n]
    if not x.is_ancestor:
        f.code('global_block_map["%s"] = Create%s;'%(x.cname, x.cname))
f.code('}')

# SConstruct file names

scons = open("SConstruct", "w")

scons.write("""
import sys
import os
import time
from distutils import sysconfig

Help(\"\"\"
'scons' to build niflib library and niflib python wrapper
'scons -c' to clean
\"\"\")

# detect platform
if sys.platform == 'linux2' or sys.platform == 'linux-i386':
    python_lib = ['python%d.%d' % sys.version_info[0:2]]
    python_libpath = [sysconfig.get_python_lib (0, 1) + '/config']
    python_include = [sysconfig.get_python_inc ()]
    cppflags = '-fPIC -Wall'
elif sys.platform == 'cygwin':
    python_lib = ['python%d.%d' % sys.version_info[0:2]]
    python_libpath = [sysconfig.get_python_lib (0, 1) + '/config']
    python_include = [sysconfig.get_python_inc ()]
    cppflags = '-Wall'
elif sys.platform == 'win32':
    python_include = [sysconfig.get_python_inc()]
    python_libpath = [sysconfig.get_python_lib(1, 1) + '/../libs']
    python_lib = ['python24']
    cppflags = '/EHsc /O2 /ML /GS /Zi /TP'
else:
    print "Error: Platform %s not supported."%sys.platform
    Exit(1)

env = Environment(ENV = os.environ)

# detect SWIG
try:
    env['SWIG']
except KeyError:
    print \"\"\"
Error: SWIG not found.
Please install SWIG, it's needed to create the python wrapper.
You can get it from http://www.swig.org/\"\"\"
    if sys.platform == "win32": print "Also don't forget to add the SWIG directory to your %PATH%."
    Exit(1)

# build niflib and python wrapper

""")

scons.write("objfiles = '")
for n in block_names:
    scons.write('obj/' + n + '.cpp ')
scons.write("'\n\n")

scons.write("""niflib = env.StaticLibrary('niflib', Split('niflib.cpp nif_math.cpp NIF_IO.cpp kfm.cpp docsys_extract.cpp obj/Type.cpp ' + objfiles), CPPPATH = '.', CPPFLAGS = cppflags)
#nifshlib = env.SharedLibrary('_niflib', 'pyniflib.i', LIBS=['niflib'] + python_lib, LIBPATH=['.'] + python_libpath, SWIGFLAGS = '-c++ -python', CPPPATH = ['.'] + python_include, CPPFLAGS = cppflags, SHLIBPREFIX='')
# makes sure niflib.lib is built before trying to build _niflib.dll
#env.Depends(nifshlib, niflib)


# Here's how to compile niflyze:
#env.Program('niflyze', 'niflyze.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

# A test program:
#env.Program('test', 'test.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

""")

scons.close()

# Templates

for n in block_names:
    x = block_types[n]
    x_define_name = define_name(x.cname)
    
    out = CFile('obj/' + x.cname + '.h', 'w')
    out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    out.code()
    out.code( '#ifndef _' + x.cname.upper() + '_H_' )
    out.code( '#define _' + x.cname.upper() + '_H_' )
    out.code()
    out.code( '#include \"xml_extract.h\"' )
    out.code( '#include ' + x_define_name + '_INCLUDE')
    out.code()
    out.code( '/*' )
    out.code( ' * ' + x.cname)
    out.code( ' */' )
    out.code()
    out.code( 'class ' + x.cname + ';' )
    out.code( 'typedef Ref<' + x.cname + '> ' + x.cname + 'Ref;' )
    out.code()
    out.code( 'class ' + x.cname + ' : public ' + x_define_name + '_PARENT {' )
    out.code( 'public:' )
    out.code( x.cname + '();' )
    out.code( '~' + x.cname + '();' )
    out.code( '//Run-Time Type Information' )
    out.code( 'static const Type TYPE;' )
    out.code( 'virtual void Read( istream& in, list<uint> & link_stack, unsigned int version );' )
    out.code( 'virtual void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version ) const;' )
    out.code( 'virtual string asString( bool verbose = false ) const;\n' )
    out.code( 'virtual void FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version );' );
    out.code( 'virtual const Type & GetType() const;' )
    out.code( 'protected:' )
    for y in x.members:
        if y.func:
            if not y.template:
                out.code( '%s %s() const;'%(y.ctype, y.func) )
            else:
                if y.ctype != "*":
                    out.code( '%s<%s > %s::%s() const;'%(y.ctype, y.ctemplate, x.cname, y.func) )
                else:
                    out.code( '%s * %s::%s() const;'%(y.ctemplate, x.cname, y.func ) )
    out.code( x_define_name + '_MEMBERS' )
    out.code( '};' );
    out.code();
    out.code( '#endif' );
    out.close()

    out = CFile('obj/' + x.cname + '.cpp', 'w')
    out.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
    out.code( 'All rights reserved.  Please see niflib.h for licence. */' )
    out.code()
    out.code( '#include \"' + x.cname + '.h\"' )
    for y in x.members:
        if y.ctype == "Ref" or y.ctype == "*":
            out.code( '#include \"%s.h\"'%y.ctemplate )
        elif y.ctype == "NodeGroup":
            out.code( '#include "NiNode.h"' )
        elif y.ctype in ["SkinShape", "SkinShapeGroup"]:
            out.code( '#include "NiTriShape.h"' )
            out.code( '#include "NiSkinInstance.h"' )
        elif y.ctype == "ControllerLink":
            out.code( '#include "NiInterpolator.h"' )
            out.code( '#include "NiStringPalette.h"' )
        elif y.ctype == "AVObject":
            out.code( '#include "NiAVObject.h"' )
        elif y.ctype in ["TexDesc", "ShaderTexDesc"]:
            out.code( '#include "NiSourceTexture.h"' )
    out.code()
    out.code( '//Definition of TYPE constant' )
    out.code ( 'const Type ' + x.cname + '::TYPE(\"' + x.cname + '\", &' + x_define_name + '_PARENT::TYPE );' )
    out.code()
    out.code( x.cname + '::' + x.cname + '() ' + x_define_name + '_CONSTRUCT {}' )
    out.code()
    out.code( x.cname + '::' + '~' + x.cname + '() {}' )
    out.code()
    out.code( 'void ' + x.cname + '::Read( istream& in, list<uint> & link_stack, unsigned int version ) {' )
    out.code( x_define_name + '_READ' )
    out.code( '}' )
    out.code()
    out.code( 'void ' + x.cname + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version ) const {' )
    out.code( x_define_name + '_WRITE' )
    out.code( '}' )
    out.code()
    out.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
    out.code( x_define_name + '_STRING' )
    out.code( '}' )
    out.code()
    out.code( 'void ' + x.cname + '::FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version ) {' );
    out.code( x_define_name + '_FIXLINKS' )
    out.code( '}' )
    out.code()
    out.code( 'const Type & %s::GetType() const {'%(x.cname) )
    out.code( 'return TYPE;' )
    out.code( '};' )
    out.code()
    for y in x.members:
        if y.func:
            if not y.template:
                out.code( '%s %s::%s() const { return %s(); }'%(y.ctype, x.cname, y.func, y.ctype) )
            else:
                if y.ctype != "*":
                    out.code( '%s<%s > %s::%s() const { return %s<%s >(); }'%(y.ctype, y.ctemplate, x.cname, y.func, y.ctype, y.ctemplate) )
                else:
                    out.code( '%s * %s::%s() const { return NULL; }'%(y.ctemplate, x.cname, y.func ) )
    out.close()
    
