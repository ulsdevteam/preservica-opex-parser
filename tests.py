
import shutil
import hashlib
from . import model, reader, writer
import os.path
import os
import lxml.etree as etree
import rich
import time
import random
import csv

def get_random_str(n):
    chars = (chr(random.randint(ord('a'), ord('z'))) for _ in range(n))
    return ''.join(chars)


def test_perf():
    basepath = os.path.dirname(__file__)
    test_folder_path = os.path.join(basepath, "test_folder")
    file_num = 100
    file_size = 500
    
    if os.path.exists(test_folder_path):
        shutil.rmtree(test_folder_path)
    os.makedirs(test_folder_path)
    with open(os.path.join(test_folder_path, "metadata.csv"), 'w', newline='') as f:
        csv_writer = csv.DictWriter(f, fieldnames=['filename', 'title', 'description',
                                               'identifier'])
        csv_writer.writeheader()
        for _ in range(file_num):
            filename = get_random_str(10)
            metadata = {
                'filename': filename,
                'title':get_random_str(5),
                'description': get_random_str(20),
                'identifier': get_random_str(10),
            }
            with open(os.path.join(test_folder_path, filename), 'w') as f2:
                f2.write(get_random_str(file_size))
    
            csv_writer.writerow(metadata)
    
    t1 = time.time()
    # generate opex files
    with open(os.path.join(test_folder_path, "metadata.csv"), newline='') as f:
        csv_reader = csv.DictReader(f)
        for i, row in enumerate(csv_reader):
            general_metadata = model.OpexMetadataContent(
                    title = row['title'], 
                    description = row['description'], 
                    identifiers = [row['identifier']], 
                    identifier_types = None, 
                    source_id = "test_folder_"+str(i))

            fs_metadata =\
                model.OpexFileContent.from_fs(os.path.join(test_folder_path, row['filename']), 
                                                        ['MD5', 'SHA-256'])
            opex_writer = writer.Writer(os.path.join(test_folder_path,
                                                     f"{row['filename']}.opex"),
                                        is_dir = False, is_pax=False)
            opex_writer.write(general_metadata, fs_metadata)
    fs_metadata = model.OpexFolderContent.from_fs(test_folder_path)
    writer.Writer(os.path.join(test_folder_path, "test_folder.opex"), is_dir=True, is_pax=False).write(None, fs_metadata)
    t2 = time.time()
    print(f"# of files: {file_num}\nfile size: {file_size}\ntime taken:" 
          f" {t2 -t1}\nfiles/sec: {file_num/(t2-t1)}\nbytes/sec:"
          f" {(file_num*file_size)/(t2 - t1)}")
    

def test_print_all_titles():
    test_dir = os.path.join(os.path.dirname(__file__),
                            "testfiles/oaipmh-storage")
    
    for root, _, fnames in os.walk(test_dir):
        for fname in fnames:
            fname = os.path.join(root, fname)
            if fname.endswith(".opex"):
                read_obj = reader.Reader(fname)
                metadata, fixity = read_obj.get_contents()
                with open(fname) as f:
                    s = f.read()
                tree = etree.parse(fname)
                #print(tree.find(".//opex:Title", 
                #    namespaces={'opex':"http://www.openpreservationexchange.org/opex/v1.2"}))
                #start_idx, end_idx = (
                #            s.find("<opex:Title>"),
                #            s.find("</opex:Title>"))
                print(metadata, fixity)

def test_reader_writer_roundtrip():
    file_path = os.path.join(os.path.dirname(__file__), "example.opex")
    out_path = os.path.join(os.path.dirname(__file__), "out_example.opex")
    read_obj = reader.Reader(file_path)
    metadata, file_content = read_obj.get_contents()
    print(metadata, file_content, out_path)
    writer_obj = writer.Writer(out_path, is_dir = False)
    writer_obj.write(metadata, file_content)
    
    # compare contents
    tree1 = etree.parse(file_path)
    tree2 = etree.parse(out_path)
    for node1, node2 in zip(tree1.iter(), tree2.iter()):
        if node1.text is not None and node1.text.strip() != node2.text.strip():
            print(node1.tag, node2.tag)
            print(f"text different:\n{node1.text}\n\n{node2.text}")
        if node1.tag != node2.tag:
            print(node1.tag, node2.tag)
        assert node1.tag == node2.tag
        assert node1.text == node2.text or node1.text.strip() == node2.text.strip()
        assert node1.attrib == node2.attrib
        



def test_print_checksum():
    filename = os.path.join(os.path.dirname(__file__), ("testfiles/oaipmh-storage/"
        "oai_d-scholarship.pitt.edu_13560/"
        "files/GOLDBERG_-_SOUL_SEARCHER.pdf"))
    opex_filename = filename + ".opex"
    read_obj = reader.Reader(opex_filename)
    _, file_metadata = read_obj.get_contents()
    if "SHA-256" not in file_metadata.fixity_algs:
        print("sha 256 not found")
        return

    fixity_idx = file_metadata.fixity_algs.index("SHA-256")
    checksum = file_metadata.fixity_values[fixity_idx]
    print(file_metadata.fixity_values)
    print(f"sha 256 checksum is {checksum}")

def test():
    names = globals().keys()
    names = filter(lambda x: x.startswith('test') and x != 'test', names)
    names = filter(lambda x: callable, names)
    for _test in names:
        print(f"Test {_test}")
        print("="*100)
        globals()[_test]()
if __name__ == '__main__':
    test_perf()
