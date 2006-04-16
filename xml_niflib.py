import sys
from xml.sax import *
class SAXtracer(ContentHandler):
    def __init__(self,objname):
        self.objname=objname
        self.met_name=""

    def startElement(self, name, attrs):
        if name == "niblock" or name == "compound":
            print "struct ext_%s {" % (attrs.get('name', ""))
        elif name == "add":
            member_name = attrs.get('name', "")
            member_name = member_name.lower()
            member_name = member_name.replace(' ', '_')
            member_type = attrs.get('type', "")
            member_type = member_type.replace(' ', '_')
            print "   %s %s;" % (member_type, member_name)

    def endElement(self, name):
        if name == "niblock" or name == "compound":
            print "}\n"

p = make_parser()

p.setContentHandler(SAXtracer("doc_handler"))
p.parse("nif.xml")
