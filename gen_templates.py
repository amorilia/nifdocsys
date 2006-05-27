import sys
from xml.sax import *

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

class SAXtracer(ContentHandler):

    def __init__(self,objname):
        self.objname=objname
        self.met_name=""

    def startElement(self, name, attrs):
        if name == "niblock":
            class_name = attrs.get('name', "")
            define = define_name(class_name);
            
            out = open('obj/' + class_name + '.h', 'w')
            out.write( '/* Copyright (c) 2006, NIF File Format Library and Tools\n' )
            out.write( 'All rights reserved.  Please see niflib.h for licence. */\n' )
            out.write( '\n' )
            out.write( '#ifndef _' + class_name.upper() + '_H_\n' )
            out.write( '#define _' + class_name.upper() + '_H_\n' )
            out.write( '\n' )
            out.write( define + '_INCLUDE\n')
            out.write( '\n' )
            out.write( '/*\n' )
            out.write( ' * ' + class_name + '\n' )
            out.write( ' */\n' )
            out.write( '\n' )
            out.write( 'class ' + class_name + ';\n' )
            out.write( 'typedef Ref<' + class_name + '> ' + class_name + 'Ref;\n' )
            out.write( '\n' )
            out.write( 'class ' + class_name + ' : public ' + define + '_PARENT {\n' )
            out.write( 'public:\n' )
            out.write( '\t' + class_name + '();\n' )
            out.write( '\t' + '~' + class_name + '();\n' )
            out.write( '\t' + '//Run-Time Type Information\n' )
            out.write( '\t' + 'static const Type TYPE;\n' )
            out.write( '\t' + 'virtual void Read( istream& in, list<uint> link_stack, unsigned int version );\n' )
            out.write( '\t' + 'virtual void Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version ) const;\n' )
            out.write( '\t' + 'virtual string asString( bool verbose = false ) const;\n' )
            out.write( '\t' + 'virtual void FixLinks( const vector<NiObjectRef> & objects, list<uint> link_stack, unsigned int version );\n' );
            out.write( 'private:\n' )
            out.write( '\t' + define + '_MEMBERS\n' )
            out.write( '};' );
            out.write( '\n' );
            out.write( '#endif\n' );
            out.close()

            out = open('obj/' + class_name + '.cpp', 'w')
            out.write( '/* Copyright (c) 2006, NIF File Format Library and Tools\n' )
            out.write( 'All rights reserved.  Please see niflib.h for licence. */\n' )
            out.write( '\n' )
            out.write( '#include \"' + class_name + '.h\"\n' )
            out.write( '\n' )
            out.write( '//Definition of TYPE constant\n' )
            out.write ( 'const Type ' + class_name + '::TYPE(\"' + class_name + '\", &' + define + '_PARENT::TYPE );\n' )
            out.write( '\n' )
            out.write( class_name + '::' + class_name + '() ' + define + '_CONSTRUCT {}\n' )
            out.write( '\n' )
            out.write( class_name + '::' + '~' + class_name + '() {}\n' )
            out.write( '\n' )
            out.write( 'void ' + class_name + '::Read( istream& in, list<uint> link_stack, unsigned int version ) {\n' )
            out.write( '\t' + define + '_READ\n' )
            out.write( '}\n' )
            out.write( '\n' )
            out.write( 'void ' + class_name + '::Write( ostream& out, map<NiObjectRef,uint> link_map, unsigned int version ) const {\n' )
            out.write( '\t' + define + '_WRITE\n' )
            out.write( '}\n' )
            out.write( '\n' )
            out.write( 'string ' + class_name + '::asString( bool verbose ) const {\n' )
            out.write( '\t' + define + '_STRING\n' )
            out.write( '}\n' )
            out.write( '\n' )
            out.write( 'void ' + class_name + '::FixLinks( const vector<NiObjectRef> & objects, list<uint> link_stack, unsigned int version ) {\n' );
            out.write( '\t' + define + '_FIXLINKS\n' )
            out.write( '}\n' )
            out.write( '\n' )
            

            
            
        

p=make_parser()

p.setContentHandler(SAXtracer("doc_handler"))
p.parse("nif.xml")
