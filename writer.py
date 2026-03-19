import model
from model import OpexXmlHelper
from lxml import etree

class Writer:
    
    def __init__(self, file_path, is_dir):
        self.is_dir = is_dir
        self.file_name = file_path
        
    
    @staticmethod 
    def generate_etree(general_metadata, fs_metadata, is_dir):
        builder = OpexXmlHelper.opex_builder
        general_fragments = general_metadata.as_xml_fragments()
        fs_fragments = fs_metadata.as_xml_fragments()
    
        root = builder("OPEXMetadata")

        transfer = builder("Transfer")
        transfer.append(general_fragments.source_id)
        if is_dir:
            transfer.append(fs_fragments.manifest)
        else:
            transfer.append(fs_fragments.fixities)
        transfer.append(fs_fragments.original_filename)
        
        properties = builder("Properties")
        properties.append(general_fragments.title)
        properties.append(general_fragments.description)
        properties.append(general_fragments.identifiers)
        properties.append(general_fragments.security_descriptor)


        descriptive_metadata = general_metadata.descriptive_metadata

        root.append(transfer)
        root.append(properties)
        root.append(descriptive_metadata) 
        return root.getroottree()
    
    def write(self, general_metadata, fs_metadata):
        root = self.generate_etree(general_metadata, fs_metadata, self.is_dir)
        print(f"writing to {self.file_name}")
        root.write(self.file_name, 
            encoding = "utf-8",
            xml_declaration=True,
            pretty_print=True,
            standalone=True)
