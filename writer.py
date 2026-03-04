from lxml import etree

from enum import Enum
from lxml.builder import ElementMaker
import logging
logger = logging.getLogger(__name__)

class OpexType(Enum):
    dir = "dir"
    file = "file"

class Validator:
    
    @staticmethod
    def fixities():
        pass

OPEX_NS = opex_ns = "http://www.openpreservationexchange.org/opex/v1.2"

def find_orelse_append(root, el_name, element_maker, ns=None):
    el = root.find(el_name, namespaces = ns)
    if el is None:
        el = element_maker.tag(el_name)
        root.append(el)
    return el
    

class Writer:
    
    def __init__(self, fs_path, opex_type, init_dict = None):
        if init_dict is None:
            init_dict = dict()
        
        if fs_path is None:
            logger.info("fs path not provided "
             "for Writer")
        self.fs_path = fs_path
        self.prop_dict = init_dict
        self.ns_dict = {'opex': OPEX_NS}
        self.element_maker = ElementMaker(
            namespace = OPEX_NS, 
            nsmap = {'opex':OPEX_NS}
        )
        self.root = self.element_maker.OPEXMetadata()
        for key, val in init_dict.items():
            setattr(self, key, value)
    # getters
    @property
    def source_id(self):
        return self.prop_dict.get("source_id")
    
    @property
    def description(self):
        return self.prop_dict.get("description")
    
    @property
    def title(self):
        return self.prop_dict.get("title")
    
    @property
    def original_filename(self):
        return self.prop_dict.get("original_filename")

    @property
    def indentifiers(self):
        return self.prop_dict.get("identifiers")
    
    @property
    def security_descriptor(self):
        return self.prop_dict.get("security_descriptor")
    
    @property
    def fixities(self):
        return self.prop_dict.get("fixities")

    def _put_val_in_xml_path(self, path, val, sep='/'):
        el = self.root
        for el_name in path.sep('/'):
            el = find_orelse_append(el, 
                el_name, 
                self.element_maker, 
                self.ns_dict)
        el.text = val

    def _find_or_create_xml_path(self, path, sep='/'):
        el = self.root
        for el_name in path.sep('/'):
            el = find_orelse_append(el, 
                el_name, 
                self.element_maker, 
                self.ns_dict)
        return el
        

    # setters
    @source_id.setter
    def source_id(self, val):
        if self.prop_dict.get("source_id") == val:
            return
        self._put_val_in_xml_path( 
            "opex:Transfer/opex:SourceID",
            val)

        self.prop_dict["source_id"] = val
    
    @description.setter
    def description(self, val):
        if self.prop_dict.get("description") == val:
            return
        self._put_val_in_xml_path(
            "opex:Properties/opex:Description",
            val)
        self.prop_dict["source_id"] = val
   
    @title.setter
    def title(self, val):
        if self.prop_dict.get("title") == val:
            return
        self._put_val_in_xml_path(
            "opex:Properties/opex:Title",
            val)
        self.prop_dict["title"] = val
        
    @identifiers.setter
    def identifiers(self, val_list):
        parent_el = _find_or_create_xml_path(
            "opex:Properties/opex:Identifiers")
        for val in val_list:
            el = self.element_maker.Identifier()
            
            if isinstance(val, tuple):
                el.text = val[0]
                for attr in val[1]:
                    el.set(attr, val[1][attr])
            else:
                el.text = val
            parent_el.append(el)
                    
    @security_descriptor.setter        
    def security_descriptor(self, val):
        self._put_val_in_xml_path( 
            "opex:Properties/opex:SecurityDescriptor",
            val)

        self.prop_dict["security_descriptor"] = val
    
        
if __name__ == '__main__':
    
    pass