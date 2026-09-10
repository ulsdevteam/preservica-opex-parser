

from typing import Optional
from dataclasses import dataclass
from enum import Enum
import hashlib
from lxml import etree
#from collections.abc import abc

class XMLFragmentCollection:
    pass 

# type alias
class PaxPath(str):
    pass 

@dataclass
class DescriptiveFragments(XMLFragmentCollection):
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
    title: etree._Element | None = None 
    description: etree._Element | None = None# <Description> ... </Description>
    source_id: etree._Element | None = None
    identifiers: etree._Element | None = None
    descriptive_metadata: etree._Element | None = None
    

@dataclass
class FileFragments(XMLFragmentCollection):
    """
    Opex tags corresponding to Administrative Metadata
    of files.

    Files are atoms and don't contain further items within
    them. Thus they do not possess a manifest tag 
    and only contain fixities.
    """
    original_filename: etree._Element | None
    security_descriptor: etree._Element | None
    fixities: etree._Element | None

@dataclass
class FolderFragments(XMLFragmentCollection):
    """
    Opex tags corresponding to Administrative Metadata
    of folders.
        
    Folders can contain files and folders within them, but
    don't contain any content. Thus they have a manifest, but
    no fixities.
    """
    original_filename: etree._Element | None
    security_descriptor: etree._Element # <SecurityDescriptor>...</Sec...>
    manifest: etree._Element | None

@dataclass
class PAXFragments(XMLFragmentCollection):
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
    original_filename: etree._Element | None
    security_descriptor: etree._Element # <SecurityDescriptor>...</Sec...>
    manifest: etree._Element | None
    fixities: etree._Element | None


class HashAlgorithm(Enum):
    md5 = 'MD5'
    sha256 = 'SHA-256'
    sha512 = 'SHA-512'
    sha1 = 'SHA-1'
    
    def __str__(self):
        return self.value

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
        return self.as_hashlib()(content).hexdigest()

# tags with attributes are reoresented via 
# dataclasses with slots = True
class CompoundTags:
    @dataclass(slots=True)
    class Identifier:
        value: str
        type: str | None = None
    
    
    
    
    
    class Fixity(Enum):
        @dataclass
        class FileFixity:
            alg: HashAlgorithm
            digest: str
    
        @dataclass
        class PaxFixity:
            alg: HashAlgorithm
            digest: str
            path: str
        pax = PaxFixity
        file = FileFixity
        

    

    
    ## maifest: list[folder] + list[file]
    @dataclass(slots= True)
    class ManifestFile:
        path: str | PaxPath
        size: int
        type: str

        def uses_pax_path(self) -> bool:
            return isinstance(self, PaxPath)
        
        
    def __new__(cls, *args, **kwargs):
        raise RuntimeError("This class is a namespace "
                           "wrapper and not meant to be instantiated")

# tags with attributes are reoresented via 
# dataclasses with slots = True
