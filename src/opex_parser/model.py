
import copy
import hashlib
import os
from dataclasses import dataclass, fields, field
from enum import Enum
from typing import NamedTuple, Self
import glob
import re

import lxml
from lxml import etree
from lxml.builder import ElementMaker
from . import model_types
from .model_types import HashAlgorithm, CompoundTags


@dataclass
class OpexMetadataContent:
    # a class to represent the content within an opex file independent
    # of xml
    title: str | None
    description: str | None
    source_id: str | None
    identifiers: list[CompoundTags.Identifier]
    descriptive_metadata: etree._Element | None = None
    

    def as_xml_fragments(self: Self
                        ) -> model_types.DescriptiveFragments:
        """
        Serialize fields of self into OPEX XML tags, as 
        lxml elements. 

        Input: self
        Output: Dataclass consisting of Opex Elements, populated
        by fields of self
        """
        builder = OpexXmlHelper.opex_builder
        self_fields = [ field.name for field in fields(self)]
        ret = model_types.DescriptiveFragments()
        
        for i, field_name in enumerate(self_fields):
            field_val = getattr(self, field_name)
            #print(field, field_val)
            if field_val is None:
                continue
            match field:
                case "title":
                    ret.title = builder("Title")
                    ret.title.text = field_val
                case "description":
                    ret.description = builder("Description")
                    ret.description.text = field_val
                case "source_id":
                    ret.source_id = builder("SourceID")
                    ret.source_id.text = field_val
                case "identifiers":
                    ret.identifiers = builder("Identifiers")
                        
                    for identifier in self.identifiers:
                        id_tag = builder("Identifier")
                        id_tag.text = identifier.value
                        if identifier.type is not None:
                            id_tag.set("type", identifier.type)
                        ret.identifiers.append(id_tag)
                        
                case "descriptive_metadata":
                    self.append_descriptive_metadata(field_val)
                case _:
                    continue
        return ret
        
    def append_descriptive_metadata(self, subtree:etree._Element |
                                    etree._ElementTree):
        if isinstance(subtree, etree._ElementTree):
            subtree = subtree.getroot()
        subtree = copy.deepcopy(subtree)
        if self.descriptive_metadata is None:
            self.descriptive_metadata = (
                OpexXmlHelper.opex_builder("DescriptiveMetadata"))
        self.descriptive_metadata.append(subtree)

    @classmethod
    def from_xml(cls, tree: etree._ElementTree | etree._Element):
        """
        Deserialize an OPEX XML document and extract it's 
        properties associated with descriptive metadata.
        Note that find is agnostic to element tree or element.
        """
        #ret = cls()

        # getattr(x, y, z) == x.y if x.y possible else z
        # so if x is None, getattr(x, y, z) == z

        title_el = OpexXmlHelper.find(tree, "Properties/Title")
        title = getattr(title_el, "text", None)

        description_el = OpexXmlHelper.find(tree, "Properties/Description")
        description = getattr(description_el, "text", None)

        source_id_el = OpexXmlHelper.find(tree, "Transfer/SourceID")
        source_id = getattr(source_id_el, "text", None)

        descriptive_metadata_el = OpexXmlHelper.find(tree, "DescriptiveMetadata")
        #ret.append_descriptive_metadata(descriptive_metadata)

        identifiers = []
        identifiers_el = OpexXmlHelper.find(tree, "Properties/Identifiers")
        if identifiers_el is None:
            identifiers_el = []
            
        for identifier_el in identifiers_el:
            identifier_data = CompoundTags.Identifier(
                    value = identifier_el.text,
                    type = identifier_el.get("type")
                    )
            identifiers.append(identifier_data)
        ret = cls(title, description, source_id, identifiers)
        if descriptive_metadata_el is not None:
            ret.append_descriptive_metadata(descriptive_metadata_el)
        return ret 

@dataclass
class OpexFileContent:
    """
    Metadata associated with the bytestream being put in preservation,
    i.e. the file being preserved. 
    """

    # a class to represent opex content associated with 
    # file existing within filesystem
    original_filename: str | None = None
    fixities: list[CompoundTags.Fixity] = field(default_factory = list)
    security_descriptor: str = ""

    def set_security(self, level: str):

        self.security_descriptor = level

    @classmethod
    def from_fs(cls, file_path, fixity_algs, security_descriptor = ""):
        assert os.path.exists(file_path) and os.path.isfile(file_path)
        filename = os.path.basename(file_path)
        fixity_list = []
        with open(file_path, "rb") as f:
            content = f.read()
        for alg_name in fixity_algs:
            alg = HashAlgorithm(alg_name)
            digest = alg.hexdigest(content)
            fixity_list.append(CompoundTags.Fixity.file.value(alg_name, digest))
        return cls(filename, fixity_list, security_descriptor)
    
    '''
    @classmethod
    def from_fs_pax(self, pax_file, pax_file_list):
        """ Unzip pax file at `pax_file` and generate paths and
        fixities for files within zipped pax object"""
        assert pax_file.endswith(".pax.zip")
        raise NotImplementedError()
    '''

    def as_xml_fragments(self) -> model_types.FileFragments:
        builder = OpexXmlHelper.opex_builder
        ret = model_types.FileFragments(None, None, None)

        if self.original_filename is not None:
            ret.original_filename = builder("OriginalFilename")
            ret.original_filename.text = self.original_filename
        
        ret.security_descriptor = builder("SecurityDescriptor")
        print(self.security_descriptor)
        ret.security_descriptor.text = self.security_descriptor
        ret.fixities = builder("Fixities")
         
        for fixity in self.fixities:
            fixity_tag = builder("Fixity")
            fixity_tag.set("type", str(fixity.alg))
            fixity_tag.set("value", fixity.digest)
            ret.fixities.append(fixity_tag)
        return ret

    @classmethod
    def from_xml(cls, tree):
        ret = cls()
        filename = OpexXmlHelper.find(tree, "Transfer/OriginalFilename")
        ret.original_filename = getattr(filename, "text", None)

        security_descriptor = OpexXmlHelper.find(tree, 
                                        "Properties/SecurityDescriptor")
        
        ret.security_descriptor = getattr(security_descriptor, "text", "")
        fixities_element = OpexXmlHelper.find(tree, "Transfer/Fixities")
        fixities_list = []
        if fixities_element is None:
            fixities_element = []
        for fixity_el in fixities_element:
            fixities_list.append(CompoundTags.Fixity.File.value(
                type=fixity_el.get("type"),
                value=fixity_el.get("value")))
        ret.fixities = fixities_list
        return ret
            
@dataclass
class OpexFolderContent:
    original_filename: str
    security_descriptor: str
    subfolder_names: list[str]
    
    subfiles: list[CompoundTags.ManifestFile]
    
    # todo: check if original filename is stored with folder opex
    def as_xml_fragments(self) -> model_types.FolderFragments:
        builder = OpexXmlHelper.opex_builder
        #ret_type = namedtuple("Fragment", ["original_filename", "manifest"])
        #ret = [None, None]
        filename_element = None
        if self.original_filename is not None:
            filename_element = builder("OriginalFilename")
            filename_element.text = self.original_filename
        security_element = builder("SecurityDescriptor")
        security_element.text = self.security_descriptor
        manifest_root = builder("Manifest")
        folder_root = builder("Folders")
        for folder_name in self.subfolder_names:
            folder_tag = builder("Folder")
            folder_tag.text = folder_name
            folder_root.append(folder_tag)

        files_root = builder("Files")
        for filedata in self.subfiles:

            file_tag = builder("File")
            file_tag.text = filedata.path
            file_tag.set("size", str(filedata.size))
            file_tag.set("type", filedata.type)
            files_root.append(file_tag)

        manifest_root.append(folder_root)
        manifest_root.append(files_root)
        return model_types.FolderFragments(filename_element, security_element, manifest_root)
        

    @classmethod
    def from_fs(cls: Self, file_path, security_descriptor = "", skip_pattern=None):
        root, subdirs, subfiles = next(os.walk(file_path))
        if skip_pattern is not None:

            skip_regex = re.compile(glob.translate(skip_pattern)) 
            subdirs = list(filter(lambda x: not skip_regex.match(x). subdirs))
            subfiles = list(filter(lambda x: not skip_regex.match(x), subfiles))
        
        subfile_metadata = []
        for f in subfiles:
            size = os.stat(os.path.join(root, f)).st_size
            filetype = "metadata" if f.endswith(".opex") else "content"
            subfile_metadata.append(model_types.CompoundTags.ManifestFile(f, size, filetype))
            
        return cls(file_path, security_descriptor, subdirs, subfile_metadata)
                
            
    @classmethod
    def from_xml(cls, tree):
        
        # look for manifest
        manifest_el = OpexXmlHelper.find(tree, "Transfer/Manifest")

        security_descriptor = OpexXmlHelper.find(tree, "Properties/SecurityDescriptor")
        security_descriptor = getattr(security_descriptor, "text", None)
        file_path = OpexXmlHelper.find(tree, "Transfer/OriginalFilename")
        file_path = getattr(file_path, "text", None)
        if manifest_el is None:
            return cls(file_path, security_descriptor, None, None)

        # find all Manifest/Folders/Folder and store text of each folder
        folders_el = OpexXmlHelper.find(manifest_el, "Folders")
        folders_el = folders_el if folders_el is not None else []
        subfolder_names = []
        for folder_el in folders_el:
            subfolder_names.append(folder_el.text)
        files_el = OpexXmlHelper.find(manifest_el, "Files")
        files_el = files_el if files_el is not None else []

        # Find all Manifest/Files/File and store properties
        subfiles = []
        for file_el in files_el:
            file_obj = model_types.CompoundTags.ManifestFile(
                name = file_el.text,
                size = int(file_el.get("size")),
                type = file_el.get("type")
            )
            subfiles.append(file_obj)
        
        return cls(file_path, security_descriptor, subfolder_names, subfiles)
        #return cls(file_path, subfolder_names, subfile_names, subfile_sizes, subfile_types)


def get_subfiles(folder, as_relative=True):
    basepath = folder

    paths = []
    for root, _, files in os.walk(folder):
        for file in files:
            fullpath = os.path.join(root, file)
            if as_relative:
                relpath = os.path.relpath(fullpath, basepath)
                paths.append(relpath)
                continue
            paths.append(fullpath)


@dataclass
class OpexPaxContent:
    # pax can have both fixities and manifest so a special case
    # makes sense
    original_filename: str
    security_descriptor: str
    subfolder_names: list[str]
    
    subfiles: list[CompoundTags.ManifestFile]
    
    fixities: list[CompoundTags.PaxFixity]

    @classmethod
    def from_fs(cls, pax_path, algs: list[HashAlgorithm], security_descriptor = ""):
        subfolder_names = []
        subfiles = []
        fixities = []

        _, folder_paths, _ = next(os.walk(pax_path))
            
        assert os.path.isdir(pax_path)
        for path in folder_paths:
            full_path = os.path.join(pax_path, path)
            assert os.path.exists(full_path)
            subfolder_names.append(path)

        for file_path in get_subfiles(pax_path, relative=False): 
            with open(file_path, "rb") as f:
                content = f.read()
            for alg in algs:
                digest = alg.hexdigest(content)
                fixities.append(model_types.CompoundTags.Fixity.PaxFixity(
                    alg, 
                    digest, 
                    os.path.relpath(file_path, pax_path)
                ))
            # add in manifest

            full_path = os.path.join(pax_path, file_path)

            assert os.path.exists(full_path)
            size = os.stat(full_path).st_size
            filetype = "metadata" if path.endswith(".opex") else "content"
            subfiles.append(
                model_types.CompoundTags.ManifestFile(
                        path,
                        size,
                        filetype
                    )
                )
                

            filename = os.path.basename(pax_path)
            return cls(filename, security_descriptor, subfolder_names, subfiles, fixities)
        

    @classmethod
    def from_xml(cls, tree):
        opex_helper = OpexXmlHelper
        filename = opex_helper.find("Transfer/OriginalFilename")
        if filename is not None:
            filename = filename.text
        fixities_el = opex_helper.find("Transfer/Fixities")
        manifest_el = opex_helper.find("Transfer/Manifest")
        fixities = []
        #ret_val = cls()
        if fixities_el is not None:
            for fixity_el in fixities_el:
                fixities.append(
                    model_types.CompoundTags.Fixity.PaxFixity(
                        alg = HashAlgorithm(fixity_el.get("type")),
                        digest = fixity_el.get("value"),
                        path = fixity_el.get("path")
                        )
                    )
                
        
        if manifest_el is not None:
            folders_el = opex_helper.find(manifest_el, "Folders")
            if folders_el is None:
                folders_el = []
            for folder in folders_el:
                ret_val.subfolder_names.append(folder.text)
            
            files_el = opex_helper.find(manifest_el, "Files")
            if files_el is None:
                files_el = []

            for file_el in files_el:
                ret_val.subfile_names.append(file_el.text)
                ret_val.subfile_sizes.append(int(file_el.get("size")))
                ret_val.subfile_types.append(file_el.get("type"))

        return ret_val

    def as_xml_fragments(self):
        file_fragments = OpexFileContent(self.original_filename, 
                                         self.fixity_algs, 
                                         self.fixity_values
                                         ).as_xml_fragments()
        folder_fragments = OpexFolderContent(self.original_filename, 
                                              self.subfolder_names, 
                                              self.subfile_names,
                                              self.subfile_sizes,
                                              self.subfile_types
                                              ).as_xml_fragments()
        # add in fixity paths
        if file_fragments.fixities is not None:
            for i, fixity_el in enumerate(file_fragments.fixities):
                fixity_el.set("path", self.fixity_paths[i])

        return model_types.PAXFragments(self.original_filename, 
                                       folder_fragments.manifest,
                                       file_fragments.fixities
                                       )

        
        
        
class OpexXmlHelper:
    # utility class to generate xml fragments and 
    # query Opex xml files
    OPEX_NS  = "http://www.openpreservationexchange.org/opex/v1.2"
    ns_dict = {'opex': OPEX_NS} # convert to frozendict in 3.15
    opex_builder = ElementMaker(
        namespace=OPEX_NS,
        nsmap = ns_dict
    )
    
    @staticmethod
    def find(tree: etree._Element | etree._ElementTree, name: str):
        # prepend_ns
        name = '/'.join('opex:' + x for x in name.split('/'))
        tag = tree.find(name, namespaces = OpexXmlHelper.ns_dict)
        return tag
    
    
    
   
    
