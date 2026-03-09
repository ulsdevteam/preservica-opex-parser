
from dataclass import dataclass
from typing import Optional
from lxml.etree import etree
from lxml.builder import ElementMaker
import hashlib
@dataclass
class OpexMetadataContent:
    # a class to represent the content within an opex file independent
    # of xml
    title: Optional[str]
    description: Optional[str]
    source_id: str
    security_descriptor: str = ""
    identifiers: list[Optional[str]] = None
    identifier_types: list[Optional[str]]
    descritpive_metadata: etree.ET = None
    
    @classmethod
    def from_xml(cls, tree):
        title = OpexXmlHelper.find(tree, "Title")
        if title is not None:
            title = title.text
        description = OpexXmlHelper.find(tree, "Description")
        if description is not None:
            description = description.text
        source_id = OpexXmlHelper.find(tree, "SourceID")
        if source_id is not None:
            source_id = source_id.text
        security_descriptor = OpexXmlHelper.find(tree, "SecurityDescriptor")
        if security_descriptor is not None:
            security_descriptor = security_descriptor.text
        
        descriptive_metadata = OpexXmlHelper.find("DescriptiveMetadata")
        identifiers = []
        identifier_types = []
        identifiers_el = OpexXmlHelper.find("Identifiers")
        if identifiers_el is None:
            identifiers_el = []
            
        for identifier_el in identifiers_el:
            identifiers.append(identifier_el.text)
            identifier_types.append(identifier_el.get("type"))
        return cls(title, description, source_id, identifiers, 
                identifier_types, descriptive_metadata)
        
@dataclass
class OpexFileContent:
    # a class to represent opex content associated with 
    # file existing within filesystem
    original_filename: str
    fixity_algs: list[str]
    fixitiy_values: list[str]
    
    
    @classmethod
    def from_fs(cls, file_path, fixity_algs):
        assert os.path.exists(file_path) and os.path.isfile(file_path)
        filename = os.path.basename(file_path)
        alg_dict = {
            "SHA=1": hashlib.sha1,
            "SHA-256": hashlib.sha256,
            "SHA-512": hashlib.sha512,
            "MD5": hashlib.md5,
        }
        hash_names = []
        hash_values = []
        with open(file_path, "rb") as f:
            file_content = f.read()
        for alg in fixity_algs:
            assert alg in alg_dict
            digest = alg_dict[alg](content).digest
            hash_names.append(alg)
            hash_values.append(digest)
        return cls(filename, hash_names, hash_values)
    
    @classmethod
    def from_xml(cls, tree):
        filename = OpexXmlHelper.find(tree, "OriginalFilename")
        if filename is None:
            filename = ""
        fixities_element = OpexXmlHelper.find(tree, "Fixities")
        hash_names = []
        hash_values = []
        if fixities_element is None:
            return cls(filename, hash_names, hash_values)
        for fixitity_el in fixities_element:
            hash_names.append(fixity_el.get("type"))
            hash_values.append(fixity_el.get("value"))
        return cls(filename, hash_names, hash_values)
            
@dataclass
class OpexFolderContent:
    subfolder_names: list[str]
    
    subfile_names: list[str]
    subfile_sizes: list[int]
    subfile_types: list[str]
    
    @classmethod
    def from_fs(self, file_path, skip_patterns=None):
        root, subdirs, subfiles = next(os.walk(file_path))
        if skip_pattern is not None:
            matches_patterns = lambda x: any(ptrn in x for ptrn in skip_patterns) 
            subdirs = list(filter(lambda x: not matches_patterns(x), subdirs))
            subfiles = list(filter(lambda x: not matches_patterns(x)), subfiles)
        
        subfile_sizes = []
        subfile_types = []
        for f in subfiles:
            size = os.stat(os.path.join(root, f))
            filetype = "metadata" if f.endswith(".opex") else "content"
            subfile_sizes.append(size)
            subfile_types.append(filetype)
            
        return cls(subdirs, subfiles, subfile_sizes, subfile_types)
    
    @classmethod
    def from_xml(cls, tree):
        
        # look for manifest
        manifest_el = OpexXmlHelper.find(tree, "Manifest")
        if manifest_el is None:
            return None
        
        # find all Manifest/Folders/Folder and store text of each folder
        folders_el - OpexXmlHelper.find(manifest_el, "Folders")
        folders_el = folders_el if folders_el is not None else []
        subfolder_names = []
        for folder_el in folders_el:
            subfolder_names.append(folder_el.text)
        files_el - OpexXmlHelper.find(manifest_el, "Files")
        files_el = folders_el if files_el is not None else []

        # Find all Manifest/Files/File and store properties
        subfile_names = []
        subfile_sizes = []
        subfile_types = []
        for flie_el in files_el:
            subfile_names.append(file_el.text)
            subfile_sizes.append(int(file_el.get("size")))
            subfile_types.append(file_el.get("type"))
        
        return cls(subfolder_names, subfile_names, subfile_sizes, subfile_types)

class OpexXmlHelper:
    # utility class to generate xml fragments and 
    # query Opex xml files
    OPEX_NS  = "http://www.openpreservationexchange.org/opex/v1.2"
    ns_dict = {'opex': OPEX_NS} # convert to frozendict in 3.15
    opex_builder = ElementMaker(
        namespace=OPEX_NS,
        nsmap = opex_ns_dict
    )
    
    @staticmethod
    def find(tree, name):
        tree.find(f"opex:{name}", namespace = OpexXmlHelper.ns_dict)
    
    
    
   
    