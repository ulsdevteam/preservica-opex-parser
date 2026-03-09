
from .model import OpexXmlHelper, OpexMetadataContent, OpexFileContent, OpexFolderContent
import xmltodict

class Reader:
    @staticmethod
    def read_to_dict(tree):
        return xmltodict.parse(tree)
        # iterating through tree would lead to 
        # checking many cases so just using find
        return_dict = dict()
        properties_el = OpexXmlHelper.find(tree, "Properties")
        transfer_el = OpexXmlHelper.find(tree, "Transfer")
        descriptive_metadata_el = OpexXmlHelper.find(tree, "DescriptiveMetadata")
        
        if properties_el is not None:
            properties_dict = dict()
            properties_dict['title'] = OpexXmlHelper.find(properties_el, "Title")
            properties_dict['description'] = OpexXmlHelper.find(properties_el, "Description")
            properties_dict['security_descriptor'] = OpexXmlHelper.find(
                                            properties_el, "SecurityDescriptor")
            properties_dict['identifiers'] = None
            identifiers_el = OpexXmlHelper.find(properties_el, "Identifiers")
            if identifiers_el is not None:
                properties_dict['identifiers'] = []
                for i in identifiers_el:
                    properties_dict['identifiers'].append(
                        (i.text, i.attrib)
                    )
            if filter_missing:
                for key, value in properties_dict.items():
                    if value is None:
                        properties_dict.pop(key)
                    elif isinstance(value, etree.ET):
                        properties_dict[key] = properties_dict[key].text
            return_dict['properties'] = properties_dict
        
        elif not filter_missing:
            return_dict['properties'] = None
        if transfer_el is not None:
            raise NotImplementedError
        
        if descriptive_metadata_el is not None:
            
                        
                        
            
        
                                                        
            
        
        