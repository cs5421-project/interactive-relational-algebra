import xml.etree.ElementTree as ET

def raq_converter(XML:str):
    try:
        root = ET.fromstring(XML)
    except ET.ParseError as error:
        raise Exception(error.msg)

    return parse(root)

def parse(node):
    value = ""
        
    if len(node) == 0: 
        return node.text.strip()
    
    for c in node:
        preV =  postV = ""
        
        if c.tag == "parenthesis":
            preV, postV = "(", ")"
        
        if c.tag == "binary_operator":
            preV = postV = " "
        
        value += preV + parse(c) + postV
    
    return value