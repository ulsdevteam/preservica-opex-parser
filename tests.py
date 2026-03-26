
import hashlib
import model
import writer
import reader
import os.path
import os
import lxml.etree as etree
def test_print_all_titles():
    test_dir = "testfiles/oaipmh-storage"
    
    for root, _, fnames in os.walk(test_dir):
        for fname in fnames:
            fname = os.path.join(root, fname)
            if fname.endswith(".opex"):
                read_obj = reader.Reader(fname)
                metadata, _ = read_obj.get_contents()
                with open(fname) as f:
                    s = f.read()
                tree = etree.parse(fname)
                #print(tree.find(".//opex:Title", 
                #    namespaces={'opex':"http://www.openpreservationexchange.org/opex/v1.2"}))
                start_idx, end_idx = (
                            s.find("<opex:Title>"),
                            s.find("</opex:Title>"))
                print(metadata.title)

def reader_writer_roundtrip():
    file_path = "example.opex"
    out_path = "out_" + file_path
    read_obj = reader.Reader(file_path)
    metadata, file_content = read_obj.get_contents()
    print(metadata, file_content, out_path)
    writer_obj = writer.Writer(out_path, is_dir = False)
    writer_obj.write(metadata, file_content)
    
    # compare contents
    tree1 = etree.parse(file_path)
    tree2 = etree.parse(out_path)
    for node1, node2 in zip(tree1.iter(), tree2.iter()):
        if node1.text != node2.text:
            print(node1.tag, node2.tag)
            print(f"text different:\n{node1.text}\n\n{node2.text}")
        if node1.tag != node2.tag:
            print(node1.tag, node2.tag)
        assert node1.tag == node2.tag
        #assert node1.text == node2.text
        assert node1.attrib == node2.attrib
        



def test_print_checksum():
    filename = ("testfiles/oaipmh-storage/"
        "oai_d-scholarship.pitt.edu_13560/"
        "files/GOLDBERG_-_SOUL_SEARCHER.pdf")
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
    reader_writer_roundtrip()
if __name__ == '__main__':
    test()
