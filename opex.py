
import lxml
import lxml.etree as etree
import logging
from itertools import takewhile

logger = logging

def next_or_none(iterator):
    try:
        return next(iterator)
    except StopIteration:
        return None
        

def localname(element):
    return etree.QName(element).localname

class OpexReaderIter:
    def __init__(self, filename):
        self._tree = etree.parse(filename)

    def _read_properties(self, iterator):
        return_dict = dict()
        property_fields = ["Title", "Description", "Identifiers",
            "SecurityDescriptor"]
        for element, event in iterator:
            if (element.tag, event) == ("Properties", "end"):
                break
            if element.tag not in property_fields:
                logger.warn(f"Unknown tag {element.tag}, ignoring")
                continue
        
            if element.tag == "Identifiers":
                identfier_tags = takewhile(
                    lambda ev: ev != ("Identifiers", "end"),
                    iterator)
                
                identifiers = [el.text for el in identifier_tags]
                return_dict[element.tag] = identifiers
                continue
            # rest of tags are simple
            return_dict[element.tag] = element.text
            
        return return_dict

    def _read_transfer(self, iterator):
        """
        return_dict = dict()
        for element, event in iterator:
            return_dict[element.tag] = element.text
            if element.tag == "Properties" and event == "stop":
                break
        return return_dict
        """
        pass

    def read(self):
        pass
    def read_iter(self):
        tree_walker = etree.iterwalk(self._tree, events=("start", "end"))
        return_dict = dict()
        next(tree_walker) # skip root start
        for event, element in tree_walker: 
            print(event, element.tag)
            if event == "start":
                if element.tag == "Properties":
                    return_dict.add({
                        'properties': self._read_properties(tree_walker)
                    })
                if element.tag == "Transfer":
                    return_dict.add({
                        'transfer': self._read_transfer(tree_walker)
                    })
                if element.tag == "DescriptiveMetadata":
                    return_dict.add({
                        'descriptive_metadata': element
                    })
        return return_dict
                    
                                    
a = OpexReader("/home/ojm15/dev/oai_egress/oai-pmh-preservation/oaipmh-storage/oai_d-scholarship.pitt.edu_2649/files/licence.txt.opex")

print(a.read())
