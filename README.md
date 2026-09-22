## Quick Start

1. Clone repo into source directory

```
git clone https://github.com/ulsdvevteam/preservica-opex-parser
```

2. 

## Introduction

Preservica is a long term storage and archival 
solution. Ingestion of content into Preservica can be done
either file by file using the WebUI or in bulk folder uploads.

Aside from content ingestion for preservation, we would also want
the uploaded content to have metadata associated with it, as 
well as ensure that the content is not corrupted or partially 
uploaded. For small upload manual checking and manual 
metadata entry is feasible, but for bulk content, a proper
manifest and metadata solution is required.

OPEX is the manifest and metadata solution provided by Preservica.
This library aims to make interaction with the 
OPEX Standard more convenient.


## What is OPEX

For any file or folder being uploaded to Preservica, one can 
put a corresponding XML file `file.opex` or `folder.opex` containing
manifest and metadata information about the file or folder.



An opex package is a folder containing files that consists
of some content meant to be archived. The contents of the
folder are optionally annotated by OPEX files. 

An OPEX file is an XML based format that contains some technical 
metadata, such as file checksums or folder contents, as 
well as descriptive metadata such as a title, description
and a security descriptors.

An OPEX file can describe either a file, folder or a 
PAX object.


## Related Projects

- opex manifest generator


