import model
from model import OpexXmlHelper
from lxml import etree
import logging

logger = logging.getLogger(__name__)

def _append_skip_none(element, value):
    if element is not None and value is not None:
        element.append(value)

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
        _append_skip_none(transfer, general_fragments.source_id)
        transfer.append(general_fragments.source_id)
        if is_dir:
            _append_skip_none(transfer, fs_fragments.manifest)
        else:
            _append_skip_none(transfer, fs_fragments.fixities)
        _append_skip_none(transfer, fs_fragments.original_filename)
        
        properties = builder("Properties")
        _append_skip_none(properties, general_fragments.title)
        _append_skip_none(properties, general_fragments.description)
        _append_skip_none(properties, general_fragments.security_descriptor)
        _append_skip_none(properties, general_fragments.identifiers)


        descriptive_metadata = general_metadata.descriptive_metadata

        root.append(transfer)
        root.append(properties)
        root.append(descriptive_metadata) 
        return root.getroottree()
    
    def write(self, general_metadata, fs_metadata):
        root = self.generate_etree(general_metadata, fs_metadata, self.is_dir)
        logger.info(f"writing to {self.file_name}")
        root.write(self.file_name, 
            encoding = "utf-8",
            xml_declaration=True,
            pretty_print=True,
            standalone=True)
