
import copy
from dataclasses import dataclass, fields
from typing import Optional, Self, NamedTuple, NewType
import lxml.etree as etree
import os
from lxml.builder import ElementMaker
import hashlib

from enum import Enum

class OpexXMLFragments(Enum):
    """
    These classes are primarily meant for internal use.

    The writer API expect the model dataclasses
    to have an `as_xml_fragments` method which converts the
    metadata stored in dataclasses (as native python types)
    to XML fragments i.e. lxml Elements. 

    This makes the writer's job simpler by having it focus
    on mainly putting lxml elements in the correct place in 
    the correct order and not have to concern itself
    with the specifics of data layout or data serialization

    An OpexXMLFragment describes 1 of 4 named tuples, one
    for the descriptive metadata fields, and one each for 
    the administrative metadata of each type of object an
    opex file can describe (file, folder, pax).

    The elements of the named tuples themselves map onto 
    an OPEX XML tagnames.
    """
    
    @dataclass(slots=True)
    class MetadataContentOpexFragments:
        """
        OPEX tags that correspond to Descriptive Metadata 
        of an object i.e. metadata that provides facts about
        the object. Note that this is distinct from the 
        DescriptiveMetadata tag of OPEX as it includes 
        tags like title and description. 

        The DescriptiveMetadata tag can contain arbitrary XML
        that a user can add to provide additional XML metadata,
        that the user wants to be archived
        """
        title: Optional[etree._Element] = None 
        description: Optional[etree._Element] = None# <Description> ... </Description>
        source_id: Optional[etree._Element] = None
        identifiers: Optional[etree._Element] = None
        descriptive_metadata: Optional[etree._ElementTree] = None

    @dataclass(slots=True)
    class FileContentOpexFragments:
        """
        Opex tags corresponding to Administrative Metadata
        of files.

        Files are atoms and don't contain further items within
        them. Thus they do not possess a manifest tag 
        and only contain fixities.
        """
        original_filename: Optional[etree._Element]
        security_descriptor: etree._Element # <SecurityDescriptor>...</Sec...>
        fixities: Optional[etree._Element]

    class FolderContentOpexFragments(NamedTuple):
        """
        Opex tags corresponding to Administrative Metadata
        of folders.
        
        Folders can contain files and folders within them, but
        don't contain any content. Thus they have a manifest, but
        no fixities.
        """
        original_filename: Optional[etree._Element]
        security_descriptor: etree._Element # <SecurityDescriptor>...</Sec...>
        manifest: Optional[etree._Element]

    class PaxContentOpexFragments(NamedTuple):
        """
        Opex tags corresponding to Administrative Metadata
        of PAX objects.

        Pax objects can either be zipped files or folders,
        that contain one or more files corresponding to structural
        metadata of the object. They may have a manifest that 
        enumerates content files within the PAX object as 
        well as possibly fixities for the content files.

        Note that paths in the mainfest for PAX objects
        are unlike those for regular folders, as regular folders
        only allow direct children of the folder to be in the
        manifest for that folder, while PAX manifests can contain
        files that are multiple folders deep.
        """
        original_filename: Optional[etree._Element]
        security_descriptor: etree._Element # <SecurityDescriptor>...</Sec...>
        manifest: Optional[etree._Element]
        fixities: Optional[etree._Element]
    
    DescriptiveFragments = MetadataContentOpexFragments
    AdministrativeFragmentsFile = FileContentOpexFragments
    AdministrativeFragmentsFolder = FolderContentOpexFragments
    AdministrativeFragmentsPAX = PaxContentOpexFragments

    def __call__(self, *args, **kwargs):
        return self.value(*args, **kwargs)
    

class HashAlgorithm(Enum):
    md5 = 'MD5'
    sha256 = 'SHA-256'
    sha512 = 'SHA-512'
    sha1 = 'SHA-1'

    def as_hashlib(self):
        match self.value:
            case 'MD5':
                return hashlib.md5
            case 'SHA-256':
                return hashlib.sha256
            case 'SHA-512':
                return hashlib.sha512
            case 'SHA-1':
                return hashlib.sha1

    def hexdigest(self, content):
        return self.as_hashlib()(content).hexdigest

# tags with attributes are reoresented via 
# dataclasses with slots = True
class CompoundTags:
    @dataclass(slots=True)
    class Identifier:
        value: str
        type: Optional[str]
    
    
    @dataclass(slots=True)
    class FileFixity:
        alg: HashAlgorithm
        value: str
    
    @dataclass(slots = True)
    class PaxFixity:
        alg: HashAlgorithm
        value: str
        path: str
    

    class Fixity(Enum):
        pax = PaxFixity
        file = FileFixity
        pass

    
    # type alias
    class PaxPath(str):
        pass 
    
    ## maifest: list[folder] + list[file]
    @dataclass(slots= True)
    class ManifestFile:
        path: str | PaxPath
        size: int
        type: str

        def uses_pax_path(self) -> bool:
            return isinstance(self, PaxPath)
        
        pass
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("This class is a namespace "
                           "wrapper and not meant to be instantiated")


class OpexMetadata(Enum):
    """

    """

@dataclass
class OpexMetadataContent:
    # a class to represent the content within an opex file independent
    # of xml
    title: Optional[str]
    description: Optional[str]
    source_id: str
    identifiers: list[CompoundTags.Identifier]
    descriptive_metadata: etree._ElementTree = None
    

    def as_xml_fragments(self: Self
                        ) -> OpexXMLFragments.DescriptiveFragment:
        """
        Serialize fields of self into OPEX XML tags, as 
        lxml elements. 

        Input: self
        Output: Dataclass consisting of Opex Elements, populated
        by fields of self
        """
        builder = OpexXmlHelper.opex_builder
        self_fields = [field.name for field in fields(self)]
        ret = OpexXMLFragments.DescriptiveFragment()
        
        for i, field in enumerate(self_fields):
            field_val = getattr(self, field)
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
                        id_tag.text = identifer.value
                        if identifier.type is not None:
                            id_tag.set("type", identifier.type)
                        ret.identifiers.append(id_tag)
                        
                case "descriptive_metadata":
                    self.append_descriptive_metadata(field_val)
                else:
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
    def from_xml(cls, tree: lxml._ElementTree | lxml._Element):
        """
        Deserialize an OPEX XML document and extract it's 
        properties associated with descriptive metadata.
        Note that find is agnostic to element tree or element.
        """
        ret = cls()

        # getattr(x, y, z) == x.y if x.y possible else z
        # so if x is None, getattr(x, y, z) == z

        title = OpexXmlHelper.find(tree, "Properties/Title")
        ret.title = getattr(title, "text", None)

        description = OpexXmlHelper.find(tree, "Properties/Description")
        ret.description = getattr(description, "text", None)

        source_id = OpexXmlHelper.find(tree, "Transfer/SourceID")
        ret.source_id = getattr(source_id, "text", None)

        descriptive_metadata = OpexXmlHelper.find(tree, "DescriptiveMetadata")
        ret.append_descriptive_metadata(descriptive_metadata)

        identifiers = []
        identifiers_el = OpexXmlHelper.find(tree, "Properties/Identifiers")
        if identifiers_el is None:
            identifiers_el = []
            
        for identifier_el in identifiers_el:
            identifier_data = CompounTags.Identifier(
                    value = identifier_el.text,
                    type = identifier_el.get("type")
                    )
            identifiers.append(identifier_data)
        return ret       
@dataclass
class OpexFileContent:
    # a class to represent opex content associated with 
    # file existing within filesystem
    original_filename: Optional[str] = None
    security_descriptor: str = ""
    fixities: list[CompoundTags.Fixity] = []
    #fixity_algs: list[str]
    #fixity_values: list[str]
    #fixity_paths: Optional[list[str]] = None
    
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
            fixity_list.append(CompoundTags.Fixity.File.value(alg_name, digest))
        return cls(filename, fixity_list, security_descriptor)
    
    '''
    @classmethod
    def from_fs_pax(self, pax_file, pax_file_list):
        """ Unzip pax file at `pax_file` and generate paths and
        fixities for files within zipped pax object"""
        assert pax_file.endswith(".pax.zip")
        raise NotImplementedError()
    '''

    def as_xml_fragments(self) -> FileContentOpexFragments:
        builder = OpexXmlHelper.opex_builder
        ret = OpexXMLFragments.AdministrativeFragmentsFile.value()

        if self.original_filename is not None:
            ret.original_filename = builder("OriginalFilename")
            ret.original_filename.text = self.original_filename
        
        ret.security_descriptor = builder("SecurityDescriptor")
        ret.security_descriptor.text = self.security_descriptor
        ret.fixities = builder("Fixities")
         
        for fixity in self.fixities:
            fixity_tag = builder("Fixity")
            fixity_tag.set("type", fixity.type)
            fixity_tag.set("value", fixity.value)
            ret.fixities.append(fixity)
        return ret

    @classmethod
    def from_xml(cls, tree):
        ret = cls()
        filename = OpexXmlHelper.find(tree, "Transfer/OriginalFilename")
        ret.filename = getattr(filename, "text", None)

        security_descriptor = OpexXmlHelper.find(tree, 
                                        "Transfer/SecurityDescriptor")
        
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
    
    subfiles: list[CompoundTag.ManifestFile]
    
    # todo: check if original filename is stored with folder opex
    def as_xml_fragments(self) -> FolderContentOpexFragments:
        builder = OpexXmlHelper.opex_builder
        ret_type = OpexXMLFragments.FolderContentOpexFragments
        #ret_type = namedtuple("Fragment", ["original_filename", "manifest"])
        ret = [None, None]
        if self.original_filename is not None:
            ret[0] = builder("OriginalFilename")
            ret[0].text = self.original_filename
        root = builder("Manifest")
        folder_root = builder("Folders")
        for folder_name in self.subfolder_names:
            folder_tag = builder("Folder")
            folder_tag.text = folder_name
            folder_root.append(folder_tag)

        files_root = builder("Files")
        for filename, size, ftype in zip(self.subfile_names, 
                                        self.subfile_sizes, 
                                        self.subfile_types):

            file_tag = builder("File")
            file_tag.text = filename
            file_tag.set("size", str(size))
            file_tag.set("type", ftype)
            files_root.append(file_tag)

        root.append(folder_root)
        root.append(files_root)
        ret[1] = root
        return ret_type._make(ret)
        pass

    @classmethod
    def from_fs(cls, file_path, skip_patterns=None):
        root, subdirs, subfiles = next(os.walk(file_path))
        if skip_patterns is not None:
            matches_patterns = lambda x: any(ptrn in x for ptrn in skip_patterns) 
            subdirs = list(filter(lambda x: not matches_patterns(x), subdirs))
            subfiles = list(filter(lambda x: not matches_patterns(x)), subfiles)
        
        subfile_sizes = []
        subfile_types = []
        for f in subfiles:
            size = os.stat(os.path.join(root, f)).st_size
            filetype = "metadata" if f.endswith(".opex") else "content"
            subfile_sizes.append(size)
            subfile_types.append(filetype)
            
        return cls(file_path, subdirs, subfiles, subfile_sizes, subfile_types)
    
    '''
    @classmethod
    def from_fs_pax(cls, base_path, file_paths, folder_paths):
        # let user tell me paths
        # currently only look for representation_preservation
        subfolder_names = []
        subfile_names = []
        subfile_types = []
        subfile_sizes = []
        assert os.path.isdir(base_path)
        for path in folder_paths:
            full_path = os.path.join(base_path, path)
            assert os.path.exists(full_path)
            subfolder_names.append(path)

        for path in file_paths:
            full_path = os.path.join(base_path, path)

            assert ps.path.exists(full_path)
            size = os.stat(full_path).st_size
            filetype = "metadata" if path.endswith(".opex") else "content"
            subfile_names.append(path)
            subfile_types.append(filetype)
            subfile_sizes.append(size)


        return cls(None, subfolder_names, subfile_names, 
                   subfile_sizes, subfile_types)
    '''
                
            
    @classmethod
    def from_xml(cls, tree):
        
        # look for manifest
        manifest_el = OpexXmlHelper.find(tree, "Transfer/Manifest")
        if manifest_el is None:
            return None
        
        file_path = OpexXmlHelper.find(tree, "Transfer/OriginalFilename")
        if file_path is not None:
            file_path = file_path.text
        # find all Manifest/Folders/Folder and store text of each folder
        folders_el = OpexXmlHelper.find(manifest_el, "Folders")
        folders_el = folders_el if folders_el is not None else []
        subfolder_names = []
        for folder_el in folders_el:
            subfolder_names.append(folder_el.text)
        files_el = OpexXmlHelper.find(manifest_el, "Files")
        files_el = files_el if files_el is not None else []

        # Find all Manifest/Files/File and store properties
        subfile_names = []
        subfile_sizes = []
        subfile_types = []
        for file_el in files_el:
            subfile_names.append(file_el.text)
            subfile_sizes.append(int(file_el.get("size")))
            subfile_types.append(file_el.get("type"))
        
        return cls(file_path, subfolder_names, subfile_names, subfile_sizes, subfile_types)


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
    subfolder_names: list[str]
    
    subfiles: list[CompoundTags.ManifestFile]
    subfile_names: list[str]
    subfile_sizes: list[int]
    subfile_types: list[str]

    fixities: list[CompoundTag.PaxFixity]

    @classmethod
    def from_fs(cls, pax_path, algs):
        alg_dict = {
            "SHA-1": hashlib.sha1,
            "SHA-256": hashlib.sha256,
            "SHA-512": hashlib.sha512,
            "MD5": hashlib.md5,
        }

        hash_names = []
        hash_values = []
        fixity_paths = []

        for file_path in get_subfiles(pax_path, relative=False): 
            with open(file_path, "rb") as f:
                content = f.read()
            for alg in algs:
                assert alg in alg_dict
                digest = alg_dict[alg](content).hexdigest()
                hash_names.append(alg)
                hash_values.append(digest)
                fixity_paths.append(os.path.relpath(file_path, pax_path))

            subfolder_names = []
            subfile_names = []
            subfile_types = []
            subfile_sizes = []
            assert os.path.isdir(pax_path)
            for path in folder_paths:
                full_path = os.path.join(base_path, path)
                assert os.path.exists(full_path)
                subfolder_names.append(path)

            for path in file_paths:
                full_path = os.path.join(base_path, path)

                assert ps.path.exists(full_path)
                size = os.stat(full_path).st_size
                filetype = "metadata" if path.endswith(".opex") else "content"
                subfile_names.append(path)
                subfile_types.append(filetype)
                subfile_sizes.append(size)


            filename = os.path.basename(pax_path)
            return cls(filename, subfolder_names, subfile_names, 
                   subfile_sizes, subfile_types, hash_names,
                       hash_values, fixity_paths)
        pass

    @classmethod
    def from_xml(cls, tree):
        opex_helper = OpexXmlHelper
        filename = opex_helper.find("Transfer/OriginalFilename")
        if filename is not None:
            filename = filename.text
        fixities_el = opex_helper.find("Transfer/Fixities")
        manifest_el = opex_helper.find("Transfer/Manifest")
        
        ret_val = cls()
        ret_val.original_filename = filename
        if fixities_el is not None:
            for fixity_el in fixities_el:
                ret_val.fixity_algs.append(fixity_el.get("type"))
                ret_val.fixity_values.append(fixity_el.get("value"))
                ret_val.fixity_paths.append(fixity_el.get("path"))
        
        if manifest_el is not None:
            folders_el = opex_helper.find(manifest_el, "Folders")
            if folders_el is None:
                folders_el = []
            for folder in folders_el:
                ret_val.subfolder_names.append(folder.text)
            
            files_el = opex_helper.find(mainfest_el, "Files")
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
        folder_fragments = OpexFolderContnent(self.original_filename, 
                                              self.subfolder_names, 
                                              self.subfile_names,
                                              self.subfile_sizes,
                                              self.subfile_types
                                              ).as_xml_fragments()
        # add in fixity paths
        if file_fragments.fixities is not None:
            for i, fixity_el in enumerate(file_fragments.fixities):
                fixity_el.set("path", self.fixity_paths[i])

        return PaxContentOpexFragments(self.original_filename, 
                                       folder_fragments.manifest,
                                       file_fragments.fixities
                                       )

        
        
        pass
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
    
    
    
   
    
