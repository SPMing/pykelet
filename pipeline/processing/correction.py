import json
import re
from os import environ, path, listdir
from bs4 import BeautifulSoup

class JsonDocument():
    """Class for manipulating JSON document."""
    def __init__(self, document, root):
        self.document = document
        self.root = root
        
    def index(self, path):
        """Return value at path, return None if not found."""
        try:
            indices = [int(x) if x.isdigit() else x for x in re.split(r'[\/\[\]]+', path[1:])]
            return reduce(lambda x, y : x[y], indices, self.document)
        except:
            return None

    def dfs(self):
        """Depth first search on JSON hierarchy."""
        return self.__dfs(self.document, self.root)

    def __dfs(self, subtree, path):
        """Depth first search on JSON hierarchy."""
        if isinstance(subtree, list):
            for node in subtree:
                for child in self.__dfs(node, path + "[" + str(subtree.index(node)) + "]"):
                    yield child
        elif isinstance(subtree, dict):
            for node in subtree:
                for child in self.__dfs(subtree[node], path + "/" + node):
                    yield child
        else: # Leaf node
            yield (subtree, path)

class Validator():
    """
    Class for validating training set produced by grobid
    """
    def __init__(self, ground_truth_directory, bs_directory, output_directory):
        self.ground_truth_directory = ground_truth_directory
        self.bs_directory = bs_directory
        self.output_directory = output_directory
    """
    Correct reference_segmenter TEI
    """
    def __reference_segmenter_correction(self, ground_truth, bs):
        gt_ref = ground_truth.back.find('ref-list').find('ref')
        bs_ref = bs.find('listBibl').find('bibl')
        while gt_ref is not None:
            if bs_ref is None:
                print bs
                bs_ref = bs_ref.find_previous('bibl')
            elif bs_ref.label is None: # merge
                bs_ref = bs_ref.find_previous('bibl')
                next_ref = bs_ref.findNext('bibl')
                bs_ref.label.next_sibling.replaceWith(
                    bs_ref.label.next_sibling + next_ref.text)
                next_ref.extract()
            else:
                if bs_ref.label.string == ('[' + gt_ref.label.string + ']'):
                    gt_ref = gt_ref.findNext('ref')
                    if bs_ref.findNext('bibl') is not None:
                        bs_ref = bs_ref.findNext('bibl')
                else:
                    find_index = bs_ref.text.find("[" + gt_ref.label.string + "]")
                    if find_index >= 0: # split
                        # Split fragment around correct delimeter
                        split = bs_ref.label.next_sibling.string. \
                                split("[" + gt_ref.label.string + "]")
                        # Construct new bibl and insert
                        bibl_tag = bs.new_tag('bibl')
                        label_tag = bs.new_tag('label')
                        label_tag.string = "[" + gt_ref.label.string + "]"
                        bibl_tag.insert(0, label_tag)
                        bibl_tag.insert(1, split[1])
                        bs_ref.insert_after(bibl_tag)
                        # Correct previous bibl
                        bs_ref.label.next_sibling.replaceWith(split[0])
                        bs_ref = bs_ref.findNext('bibl')
                    else: #label not found => merge
                        bs_ref = bs_ref.find_previous('bibl')
                        next_ref = bs_ref.findNext('bibl')
                        bs_ref.label.next_sibling.replaceWith(
                            bs_ref.label.next_sibling + next_ref.text)
                        next_ref.extract()
        return bs
    """
    Correct directory of reference_segmenter training files
    """
    def reference_segmenter_validation(self):
        for file in filter(lambda x : x.endswith('referenceSegmenter.tei.xml'), listdir(self.bs_directory)):
            bs = BeautifulSoup(open(self.bs_directory + file), 'xml')
            # find ground_truth file
            ground_truth = BeautifulSoup(open(self.ground_truth_directory + file.split(".")[0] + '.xml'), 'xml')
            correction = self.__reference_segmenter_correction(ground_truth, bs)
            file = open(output_directory + file, "wb")
            file.write(correction.prettify().encode('utf-8'))
    """
    Correct citation training TEI file
    """
    def __citation_correction(self):
        gt_ref = ground_truth.back.find('ref-list').find('ref')
        bs_ref = bs.find('listBibl').find('bibl')
        while gt_ref is not None:
            if gt_ref.title is not None:
                if gt_ref.title != bs_ref.title:
                    bs_ref.title.string = gt_ref.title.string
    """
    Correct directory of citation training files
    """
    def citation_validation(self):
        for file in filter(lambda x : x.startswith('citation'), os.listdir(bs_directory)):
            bs = BeautifulSoup(open(file), 'xml')
            # find ground_truth file
            ground_truth = BeautifulSoup(open(file), 'xml')
            correction = self.__citation_correction(ground_truth, bs)
            file = open("SOMETHING.xml", "wb")
            file.write(correction.prettify().encode('utf-8'))

if __name__ == '__main__':
    directory = path.dirname(path.realpath(__file__))

    scoap3_xmls = directory + '/../training/hindawi_scoap_xmls/'
    input_directory = directory + '/../grobid/output/'
    output_directory = directory + \
    '/../grobid/grobid-trainer/resources/dataset/reference-segmenter/corpus/'

    val = Validator(ground_truth_directory = scoap3_xmls, 
                    bs_directory = input_directory,
                    output_directory = output_directory)
    val.reference_segmenter_validation()
    # val.citation_validation()