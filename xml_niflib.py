from xml.dom.minidom import *
from textwrap import wrap

import sys
import os

#
# global data
#

root_dir = "."
BOOTSTRAP = False

prev = ""
for i in sys.argv:
    if prev == "-p":
        root_dir = i
    elif i == "-b":
        BOOTSTRAP = True
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
ACTION_GETREFS = 5

#
# C++ code formatting functions
#

class CFile(file):
    """
    This class represents a C++ source file.  It is used to open the file for output
    and automatically handles indentation by detecting brackets and colons.
    It also handles writing the generated Niflib C++ code.
    """
    def __init__(self, filename, mode):
        """
        This constructor requires the name of the file to open and the IO mode to open it in.
        @param filename: The name of the ouput file to open
        @type filename: string
        @param mode: The IO Mode.  Same as fopen?  Usually should be 'r', 'w', or 'a'
        @type mode: char
        """
        file.__init__(self, root_dir + os.sep + filename, mode)
        self.indent = 0
        self.backslash_mode = False
    

    def code(self, txt = None):
        r"""
        Formats a line of C++ code; the returned result always ends with a newline.
        If txt starts with "E{rb}", indent is decreased, if it ends with "E{lb}", indent is increased.
        Text ending in "E{:}" de-indents itself.  For example "publicE{:}"
        Result always ends with a newline
        @param txt: None means just a line break.  This will also break the backslash, which is kind of handy.
            "\n" will create a backslashed newline in backslash mode.
        @type txt: string, None
         """
        # txt 
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
        prefix = "\t" * self.indent
        # strip trailing whitespace, including newlines
        txt = txt.rstrip()
        # indent, and add newline
        result = prefix + txt.replace("\n", endl + prefix) + endl
        # block start
        if txt[-1:] == "{": self.indent += 1
        # special, private:, public:, and protected:
        if txt[-1:] == ":": self.indent += 1
    
        self.write(result)
    
    
    # 
    def comment(self, txt):
        """
        Wraps text in Doxygen-style C++ comments and outputs it to the file.  Handles multilined comments as well.
        Result always ends with a newline
        @param txt: The text to enclose in a Doxygen comment
        @type txt: string
         """
        if self.backslash_mode: return # skip comments when we are in backslash mode
        self.code("/*!\n * " + "\n".join(wrap(txt)).replace("\n", "\n * ") + "\n */")
    
    def declare(self, block):
        """
        Formats the member variables for a specific class as described by the XML and outputs the result to the file.
        @param block: The class or struct to generate member functions for.
        @type block: Block, Compound
         """
        if isinstance(block, Block):
            #self.code('protected:')
            prot_mode = True
        for y in block.members:
            if y.is_declared and not y.is_duplicate:
                if isinstance(block, Block):
                    if y.is_public and prot_mode:
                        self.code('public:')
                        prot_mode = False
                    elif not y.is_public and not prot_mode:
                        self.code('protected:')
                        prot_mode = True
                self.comment(y.description)
                self.code(y.code_declare())

    def get_attr(self, block):
        """
        Get the attributes whose type is implemented natively by Niflib.  Appears to be an attempt to generate a GetAttr function and so is obsolete.
        @param block: The class or struct to generate the GetAttr function for.
        @type block: Block, Compound
         """
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
        """
        Generates the function code for various functions in Niflib and outputs it to the file.
        @param block: The class or struct to generate the function for.
        @type block: Block, Compound
        @param action: The type of function to generate, valid values are::
            ACTION_READ - Read function.
            ACTION_WRITE - Write function
            ACTION_OUT - asString function
            ACTION_FIXLINKS - FixLinks function
            ACTION_REMOVECROSSREF - RemoveCrossRef function, not used
            ACTION_GETREFS - GetRefs function
        @type action: ACTION_X constant
        @param localprefix: ?
        @type localprefix: string
        @param prefix: ?
        @type prefix: string
        @param arg_prefix: ?
        @type arg_prefix: string
        @param arg_member: ?
        @type arg_member: None, ?
         """
        lastver1 = None
        lastver2 = None
        lastuserver = None
        lastcond = None
        # stream name
        if action == ACTION_READ:
            stream = "in"
        elif action == ACTION_WRITE:
            stream = "out"
        elif action == ACTION_OUT:
            stream = "out"

        # preperation
        if isinstance(block, Block) or block.name in ["Footer", "Header"]:
            if action == ACTION_READ:
                if block.has_links or block.has_crossrefs:
                    self.code("uint block_num;")
            if action == ACTION_OUT:
                self.code("stringstream out;")
            if action == ACTION_GETREFS:
                self.code("list<Ref<NiObject> > refs;")

        # stream the ancestor
        if isinstance(block, Block):
            if block.inherit:
                if action == ACTION_READ:
                    self.code("%s::Read( %s, link_stack, version, user_version );"%(block.inherit.cname, stream))
                elif action == ACTION_WRITE:
                    self.code("%s::Write( %s, link_map, version, user_version );"%(block.inherit.cname, stream))
                elif action == ACTION_OUT:
                    self.code("%s << %s::asString();"%(stream, block.inherit.cname))
                elif action == ACTION_FIXLINKS:
                    self.code("%s::FixLinks( objects, link_stack, version, user_version );"%block.inherit.cname)
                elif action == ACTION_REMOVECROSSREF:
                    self.code("%s::RemoveCrossRef(block_to_remove);"%block.inherit.cname)
                elif action == ACTION_GETREFS:
                    self.code("refs = %s::GetRefs();"%block.inherit.cname)

        # declare and calculate local variables (TODO: GET RID OF THIS; PREFERABLY NO LOCAL VARIABLES AT ALL)
        if action in [ACTION_READ, ACTION_WRITE, ACTION_OUT]:
            block.members.reverse() # calculated data depends on data further down the structure
            for y in block.members:
                # read + write + out: declare
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
            if action in [ACTION_FIXLINKS, ACTION_GETREFS]:
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
                if lastver1 != y.ver1 or lastver2 != y.ver2 or lastuserver != y.userver:
                    # we must switch to a new version block    
                    # close old version block
                    if lastver1 or lastver2 or lastuserver: self.code("};")
                    # close old condition block as well    
                    if lastcond:
                        self.code("};")
                        lastcond = None
                    # start new version block
                    if not y.userver:
                        if y.ver1 and not y.ver2:
                            self.code("if ( version >= 0x%08X ) {"%y.ver1)
                        elif not y.ver1 and y.ver2:
                            self.code("if ( version <= 0x%08X ) {"%y.ver2)
                        elif y.ver1 and y.ver2:
                            self.code("if ( ( version >= 0x%08X ) && ( version <= 0x%08X ) ) {"%(y.ver1, y.ver2))
                    else:
                        if y.ver1 and not y.ver2:
                            self.code("if ( ( version >= 0x%08X ) && ( user_version == %s ) ) {"%(y.ver1, y.userver))
                        elif not y.ver1 and y.ver2:
                            self.code("if ( ( version <= 0x%08X ) && ( user_version == %s ) ) {"%(y.ver2, userver))
                        elif y.ver1 and y.ver2:
                            self.code("if ( ( version >= 0x%08X ) && ( version <= 0x%08X ) && ( user_version == %s ) ) {"%(y.ver1, y.ver2, y.userver))
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
    
            # loop over arrays
            # and resolve variable name
            if not y.arr1.lhs:
                z = "%s%s"%(y_prefix, y.cname)
            else:
                if y.arr1.lhs.isdigit() == False:
                    if action == ACTION_READ:
                        self.code("%s%s.resize(%s);"%(y_prefix, y.cname, y.arr1.code(y_arr1_prefix)))
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
                            if action == ACTION_READ:
                                self.code("%s%s[i%i].resize(%s);"%(y_prefix, y.cname, self.indent-1, y.arr2.code(y_arr2_prefix)))
                            self.code(\
                                "for (uint i%i = 0; i%i < %s%s[i%i].size(); i%i++) {"\
                                %(self.indent, self.indent, y_arr2_prefix, y.cname, self.indent-1, self.indent))
                        else:
                            self.code(\
                                "for (uint i%i = 0; i%i < %s; i%i++) {"\
                                %(self.indent, self.indent, y.arr2.code(y_arr2_prefix), self.indent))
                    else:
                        if action == ACTION_READ:
                            self.code("%s%s[i%i].resize(%s[i%i]);"%(y_prefix, y.cname, self.indent-1, y.arr2.code(y_arr2_prefix), self.indent-1))
                        self.code(\
                            "for (uint i%i = 0; i%i < %s[i%i]; i%i++) {"\
                            %(self.indent, self.indent, y.arr2.code(y_arr2_prefix), self.indent-1, self.indent))
                    z = "%s%s[i%i][i%i]"%(y_prefix, y.cname, self.indent-2, self.indent-1)
    
            if native_types.has_key(y.type):
                # these actions distinguish between refs and non-refs
                if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS, ACTION_GETREFS]:
                    if (not subblock.is_link) and (not subblock.is_crossref):
                        # not a ref
                        if action in [ACTION_READ, ACTION_WRITE]:
                            if not y.arg:
                                self.code("NifStream( %s, %s, version );"%(z, stream))
                            else:
                                self.code("NifStream( %s, %s, version, %s%s );"%(z, stream, y_prefix, y.carg))
                    else:
                        # a ref
                        if action == ACTION_READ:
                            self.code("NifStream( block_num, %s, version );"%stream)
                            if y.is_declared and not y.is_duplicate:
                                self.code("link_stack.push_back( block_num );")
                        elif action == ACTION_WRITE:
                            self.code("if ( %s != NULL )"%z)
                            self.code("\tNifStream( link_map[StaticCast<NiObject>(%s)], %s, version );"%(z, stream))
                            self.code("else")
                            self.code("\tNifStream( 0xffffffff, %s, version );"%stream)
                        elif action == ACTION_FIXLINKS:
                            if y.is_declared and not y.is_duplicate:
                                self.code("if (link_stack.empty())")
                                self.code("\tthrow runtime_error(\"Trying to pop a link from empty stack. This is probably a bug.\");")
                                self.code("if (link_stack.front() != 0xffffffff) {")
                                self.code("%s = DynamicCast<%s>(objects[link_stack.front()]);"%(z,y.ctemplate))
                                self.code('if ( %s == NULL )\n\tthrow runtime_error("Link could not be cast to required type during file read. This NIF file may be invalid or improperly understood.");'%z)
                                self.code("} else")
                                self.code("\t%s = NULL;"%z)
                                self.code("link_stack.pop_front();")
                        elif action == ACTION_GETREFS and subblock.is_link:
                            if y.is_declared and not y.is_duplicate:
                                self.code('if ( %s != NULL )\n\trefs.push_back(StaticCast<NiObject>(%s));'%(z,z))
                # the following actions don't distinguish between refs and non-refs
                elif action == ACTION_OUT:
                    if not y.arr1.lhs:
                        self.code('%s << "%*s%s:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, z))
                    elif not y.arr2.lhs:
                        self.code('if ( !verbose && ( i%i > MAXARRAYDUMP ) ) {'%(self.indent-1))
                        self.code('%s << "<Data Truncated. Use verbose mode to see complete listing.>" << endl;'%stream)
                        self.code('break;')
                        self.code('};')
                        self.code('%s << "%*s%s[" << i%i << "]:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, self.indent-1, z))
                    else:
                        self.code('if ( !verbose && ( i%i > MAXARRAYDUMP ) ) {'%(self.indent-1))
                        self.code('%s << "<Data Truncated. Use verbose mode to see complete listing.>" << endl;'%stream)
                        self.code('break;')
                        self.code('};')
                        self.code('%s << "%*s%s[" << i%i << "][" << i%i << "]:  " << %s << endl;'%(stream, 2*self.indent, "", y.name, self.indent-2, self.indent-1, z))
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
            lastuserver = y.userver
            lastcond = y_cond

        if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS]:
            if lastver1 or lastver2 or lastuserver:
                self.code("};")
        if action in [ACTION_READ, ACTION_WRITE, ACTION_FIXLINKS, ACTION_OUT]:
            if lastcond:
                self.code("};")

        # the end
        if isinstance(block, Block) or block.name in ["Header", "Footer"]:
            if action == ACTION_OUT:
                self.code("return out.str();")
            if action == ACTION_GETREFS:
                self.code("return refs;")



def class_name(n):
    """
    Formats a valid C++ class name from the name format used in the XML.
    @param b: The class name to format in C++ style.
    @type b: string
    @return The resulting valid C++ class name
    @rtype: string
    """
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
    """
    Formats an all-uppercase version of the name for use in C++ defines.
    @param b: The class name to format in define style.
    @type b: string
    @return The resulting valid C++ define name
    @rtype: string
    """
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
    """
    Formats a version of the name for use as a C++ member variable.
    @param b: The attribute name to format in variable style.
    @type b: string
    @return The resulting valid C++ variable name
    @rtype: string
    """
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
    """
    Translates a legibal NIF version number to the packed-byte numeric representation. For example, "10.0.1.0" is translated to 0x0A000100.
    @param s: The version string to translate into numeric form.
    @type s: string
    @return The resulting numeric version of the given version string.
    @rtype: int
    """
    if not s: return None
    l = s.split('.')
    if len(l) != 4:
        assert(False)
        return int(s)
    else:
        return (int(l[0]) << 24) + (int(l[1]) << 16) + (int(l[2]) << 8) + int(l[3])

def userversion2number(s):
    """
    Translates a legibal NIF user version number to the packed-byte numeric representation.
    Currently just converts the string to an int as this may be a raw number.
    Probably to be used just in case this understanding changes.
    @param s: The version string to translate into numeric form.
    @type s: string
    @return The resulting numeric version of the given version string.
    @rtype: int
    """
    if not s: return None
    return int(s)

class Expr:
    """
    Represents a mathmatical expression?
    """
    def __init__(self, n):
        """
        This constructor takes the expression in the form of a string and tokenizes it into left-hand side, operator, right hand side, and something called clhs.
        @param n: The expression to tokenize.
        @type n: string
        """
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
        """
        This function formats the expression as a string?  
        right hand side, and something called clhs.
        @param prefix: An optional prefix used in some situations?
        @type prefix: string
        @return The expression formatted into a string?
        @rtype: string
        """
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
    """
    This class represents a member variable?
    @ivar name:  The name of this member variable.  Comes from the "name" attribute of the <add> tag.
    @type name: string
    @ivar type: The type of this member variable.  Comes from the "type" attribute of the <add> tag.
    @type type: string
    @ivar arg: The argument of this member variable.  Comes from the "arg" attribute of the <add> tag.
    @type arg: string
    @ivar template: The template type of this member variable.  Comes from the "template" attribute of the <add> tag.
    @type template: string
    @ivar arr1: The first array size of this member variable.  Comes from the "arr1" attribute of the <add> tag.
    @type arr1: string
    @ivar arr12: The first array size of this member variable.  Comes from the "arr2" attribute of the <add> tag.
    @type arr2: string
    @ivar cond: The condition of this member variable.  Comes from the "cond" attribute of the <add> tag.
    @type cond: string
    @ivar func: The function of this member variable.  Comes from the "func" attribute of the <add> tag.
    @type func: string
    @ivar default: The default value of this member variable.  Comes from the "default" attribute of the <add> tag.
        Formatted to be ready to use in a C++ constructor initializer list.
    @type default: string
    @ivar ver1: The first version this member exists.  Comes from the "ver1" attribute of the <add> tag.
    @type ver1: string
    @ivar ver2: The last version this member exists.  Comes from the "ver2" attribute of the <add> tag.
    @type ver2: string
    @ivar userver: The user version where this member exists.  Comes from the "userver" attribute of the <add> tag.
    @type userver: string
    @ivar is_public: Whether this member will be declared public.  Comes from the "public" attribute of the <add> tag.
    @type is_public: string
    @ivar description: The description of this member variable.  Comes from the text between <add> and </add>.
    @type description: string
    @ivar uses_agrument: Specifies whether this attribute uses an argument.
    @type uses_argument: bool
    @ivar type_is_native = Specifies whether the type is implemented natively
    @type type_is_native: bool
    @ivar is_duplicate: Specifies whether this is a duplicate of a previously declared member
    @type is_duplicate: bool
    @ivar arr2_dynamic: Specifies whether arr2 refers to an array (?)
    @type arr2_dynamic: bool
    @ivar arr1_ref: Names of the attributes it is a (unmasked) size of (?)
    @type arr1_ref: string array?
    @ivar arr2_ref: Names of the attributes it is a (unmasked) size of (?)
    @type arr2_ref: string array?
    @ivar cond_ref: Names of the attributes it is a condition of (?)
    @type cond_ref: string array?
    @ivar is_declared: True if it is declared in the class, if false, then field is calculated somehow
    @type is_declared: bool
    @ivar cname: Unlike default, name isn't formatted for C++ so use this instead?
    @type cname: string
    @ivar ctype: Unlike default, type isn't formatted for C++ so use this instead?
    @type ctype: string
    @ivar carg: Unlike default, arg isn't formatted for C++ so use this instead?
    @type carg: string
    @ivar ctemplate: Unlike default, template isn't formatted for C++ so use this instead?
    @type ctemplate: string
    @ivar carr1_ref: Unlike default, arr1_ref isn't formatted for C++ so use this instead?
    @type carr1_ref: string
    @ivar carr2_ref: Unlike default, arr2_ref isn't formatted for C++ so use this instead?
    @type carr2_ref: string
    @ivar ccond_ref: Unlike default, cond_ref isn't formatted for C++ so use this instead?
    @type ccond_ref: string
    """
    def __init__(self, element):
        """
        This constructor converts an XML <add> element into a Member object.
        Some sort of processing is applied to the various variables that are copied from the XML tag...
        Seems to be trying to set reasonable defaults for certain types, and put things into C++ format generally. 
        @param prefix: An optional prefix used in some situations?
        @type prefix: string
        @return The expression formatted into a string?
        @rtype: string?
        """
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
        self.ver1      = version2number(element.getAttribute('ver1'))
        self.ver2      = version2number(element.getAttribute('ver2'))
        self.userver   = userversion2number(element.getAttribute('userver'))
        self.is_public = (element.getAttribute('public') == "1")  

        #Get description from text between start and end tags
        if element.firstChild:
            assert element.firstChild.nodeType == Node.TEXT_NODE
            self.description = element.firstChild.nodeValue.strip()
        else:
            self.description = "Unknown."
        
        # Format default value so that it can be used in a C++ initializer list
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

    def code_include_h(self):
        if self.niflibtype: return ""

        result = ""

        # include all required structures
        used_structs = []
        for y in self.members:
            if y.type in compound_names and y.type != self.name and not compound_types[y.type].niflibtype:
                file_name = "gen/%s.h"%y.ctype
                if file_name not in used_structs:
                    used_structs.append( file_name )
        if used_structs:
            result += "// Include structures\n"
        for file_name in used_structs:
            result += '#include "%s"\n'%file_name
    
        # forward declaration of blocks
        used_blocks = []
        for y in self.members:
            if y.template in block_names and y.template != self.name:
                if not y.ctemplate in used_blocks:
                    used_blocks.append( y.ctemplate )
        if used_blocks:
            result += '\n// Forward define of referenced blocks\n#include "Ref.h"\n'
        for fwd_class in used_blocks:
            result += 'class %s;\n'%fwd_class

        return result

    def code_include_cpp(self):
        if self.niflibtype: return ""

        result = ""

        if self.name in compound_names:
            result += '#include "gen/%s.h"\n'%self.cname
        elif self.name in block_names:
            result += '#include "obj/%s.h"\n'%self.cname
        else: assert(False) # bug

        # include referenced blocks
        used_blocks = []
        for y in self.members:
            if y.template in block_names and y.template != self.name:
                file_name = "obj/%s.h"%y.ctemplate
                if file_name not in used_blocks:
                    used_blocks.append( file_name )
            if y.type in compound_names:
                subblock = compound_types[y.type]
                result += subblock.code_include_cpp()
        for file_name in used_blocks:
            result += '#include "%s"\n'%file_name

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

    def code_include_h(self):
        result = ""
        if self.inherit:
            result += '#include "%s.h"\n'%self.inherit.cname
        result += Compound.code_include_h(self)
        return result



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
    h.code( '#include "NIF_IO.h"' )
    h.code( x.code_include_h() )
    if n in ["Header", "Footer"]:
        h.code( '#include "obj/NiObject.h"' )
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

    # header and footer functions
    if n in ["Header", "Footer"]:
        h.code( 'void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
        h.code( 'void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
        h.code( 'string asString( bool verbose = false ) const;' )

    # done
    h.code("};")
    h.code()
    h.code( '#endif' )

    if not x.template:
        cpp = CFile('gen/' + x.cname + '.cpp', 'w')
        cpp.code( '/* Copyright (c) 2006, NIF File Format Library and Tools' )
        cpp.code( 'All rights reserved.  Please see niflib.h for licence. */' )
        cpp.code()
        cpp.code( x.code_include_cpp() )
        
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

        # header and footer functions
        if n in ["Header", "Footer"]:
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' )
            cpp.stream(x, ACTION_READ)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'void ' + x.cname + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const {' )
            cpp.stream(x, ACTION_WRITE)
            cpp.code( '}' )
            cpp.code()
            cpp.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
            cpp.stream(x, ACTION_OUT)
            cpp.code( '}' )


# generate block code

h = CFile("gen/obj_defines.h", "w")

# file header

h.write("""/* Copyright (c) 2006, NIF File Format Library and Tools
All rights reserved.  Please see niflib.h for licence. */

#ifndef _OBJ_DEFINES_H_
#define _OBJ_DEFINES_H_

#define MAXARRAYDUMP 20

#include "NIF_IO.h"
#include "Ref.h"
#include <iostream>
#include <fstream>
#include <vector>
#include <string>

using namespace std;

""")

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

    # get references
    h.code("#define %s_GETREFS"%x_define_name)
    h.stream(x, ACTION_GETREFS)
    h.code()



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

scons = open(root_dir + os.sep + "SConstruct", "w")

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
for n in compound_names:
    x = compound_types[n]
    if n[:3] != 'ns ' and not x.niflibtype and not x.template:
        scons.write('gen/' + n + '.cpp ')
for n in block_names:
    scons.write('obj/' + n + '.cpp ')
scons.write("'\n\n")

scons.write("""niflib = env.StaticLibrary('niflib', Split('niflib.cpp nif_math.cpp NIF_IO.cpp kfm.cpp Type.cpp gen/obj_factories.cpp ' + objfiles), CPPPATH = '.', CPPFLAGS = cppflags)
#nifshlib = env.SharedLibrary('_niflib', 'pyniflib.i', LIBS=['niflib'] + python_lib, LIBPATH=['.'] + python_libpath, SWIGFLAGS = '-c++ -python', CPPPATH = ['.'] + python_include, CPPFLAGS = cppflags, SHLIBPREFIX='')
# makes sure niflib.lib is built before trying to build _niflib.dll
#env.Depends(nifshlib, niflib)


# Here's how to compile niflyze:
#env.Program('niflyze', 'niflyze.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

# A test program:
#env.Program('test', 'test.cpp', LIBS=['niflib'], LIBPATH=['.'], CPPFLAGS = cppflags)

""")

scons.close()

# all non-generated bootstrap code
if BOOTSTRAP:
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
	out.code( x.code_include_h() )
	out.code()
	out.code( '#include "gen/obj_defines.h"' )
	out.code()
	out.code( 'class ' + x.cname + ';' )
	out.code( 'typedef Ref<' + x.cname + '> ' + x.cname + 'Ref;' )
	out.code()
	out.comment( x.cname + " - " + x.description )
	out.code()
	out.code( 'class ' + x.cname + ' : public ' + x_define_name + '_PARENT {' )
	out.code( 'public:' )
	out.code( x.cname + '();' )
	out.code( '~' + x.cname + '();' )
	out.code( '//Run-Time Type Information' )
	out.code( 'static const Type TYPE;' )
	out.code( 'virtual void Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
	out.code( 'virtual void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const;' )
	out.code( 'virtual string asString( bool verbose = false ) const;\n' )
	out.code( 'virtual void FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version );' )
	out.code( 'virtual list<NiObjectRef> GetRefs() const;' )
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
	out.code( x.code_include_cpp() )
	out.code()
	out.code( '//Definition of TYPE constant' )
	out.code ( 'const Type ' + x.cname + '::TYPE(\"' + x.cname + '\", &' + x_define_name + '_PARENT::TYPE );' )
	out.code()
	out.code( x.cname + '::' + x.cname + '() ' + x_define_name + '_CONSTRUCT {}' )
	out.code()
	out.code( x.cname + '::' + '~' + x.cname + '() {}' )
	out.code()
	out.code( 'void ' + x.cname + '::Read( istream& in, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' )
	out.code( x_define_name + '_READ' )
	out.code( '}' )
	out.code()
	out.code( 'void ' + x.cname + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version, unsigned int user_version ) const {' )
	out.code( x_define_name + '_WRITE' )
	out.code( '}' )
	out.code()
	out.code( 'string ' + x.cname + '::asString( bool verbose ) const {' )
	out.code( x_define_name + '_STRING' )
	out.code( '}' )
	out.code()
	out.code( 'void ' + x.cname + '::FixLinks( const vector<NiObjectRef> & objects, list<uint> & link_stack, unsigned int version, unsigned int user_version ) {' );
	out.code( x_define_name + '_FIXLINKS' )
	out.code( '}' )
	out.code()
	out.code( 'list<NiObjectRef> %s::GetRefs() const {'%x.cname )
	out.code( x_define_name + '_GETREFS' )
	out.code( '}' )
	out.code()
	out.code( 'const Type & %s::GetType() const {'%x.cname )
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
	
