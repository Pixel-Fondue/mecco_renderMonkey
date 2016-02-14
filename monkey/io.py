# python

import os, traceback, json, re, random
import modo
import util, yaml


def yaml_save_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting YAML file destination.
    """

    try:
        return os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileSave',
                title='Save Batch File',
                names=['yaml'],
                unames=['Batch File (YAML)'],
                patterns=['*.yaml'],
                ext=['yaml']
            )
        )
    except:
        return False


def lxo_open_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting LXO file source.
    """

    try:
        return os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileOpen',
                title='Select Scene File',
                names=('lxo',),
                unames=('MODO Scene file',),
                patterns=('*.lxo',),
                path=None
            )
        )
    except:
        return False


def yaml_open_dialog():
    """
    By Adam O'Hern for Mechanical Color

    File dialog requesting YAML file source.
    """

    try:
        return os.path.normpath(
            modo.dialogs.customFile(
                dtype='fileOpen',
                title='Select Batch File',
                names=('yaml',),
                unames=('renderMonkey Batch File',),
                patterns=('*.yaml',),
                path=None
            )
        )
    except:
        return False


def read_json(file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns a Python object (list or dict, as appropriate) from a given JSON file path.
    """

    try:
        json_file = open(file_path, 'r')
    except:
        util.debug(traceback.format_exc())
        return False

    try:
        json_object = json.loads(json_file.read())
    except:
        util.debug(traceback.format_exc())
        json_file.close()
        return False

    json_file.close()
    return json_object


def read_yaml(file_path):
    """
    By Adam O'Hern for Mechanical Color

    Returns a Python object (list or dict, as appropriate) from a given YAML file path.
    We use YAML because it's easier and more human readable than JSON. It's harder to mess up,
    easier to learn, and--imagine!--it supports commenting.

    Note: YAML does not support hard tabs (\t), so this script replaces those with four spaces ('    ').
    """

    yaml_file = open(file_path, 'r')
    yaml_object = yaml.safe_load(re.sub('\\t', '    ', yaml_file.read()))

    yaml_file.close()
    return yaml_object


def test_writeable(test_dir_path):
    """
    By Adam O'Hern for Mechanical Color

    Easier to ask forgiveness than permission.
    If the test path doesn't exist, tries to create it. If it can't, returns False.
    Then writes to a file in the target directory. If it can't, returns False.
    If all is well, returns True.
    """

    if not os.path.exists(test_dir_path):
        try:
            os.mkdir(test_dir_path)
        except OSError:
            return False

    test_path = os.path.join(test_dir_path, "tmp_%s.txt" % random.randint(100000, 999999))
    try:
        test = open(test_path, 'w')
        test.write("Testing write permissions.")
        test.close()
        os.remove(test_path)
        return True
    except:
        return False


def yamlize(data):
    return yaml.dump(data, indent=4, width=999, default_flow_style=False).replace("\n-", "\n\n-")


def write_yaml(data, output_path):
    if not test_writeable(os.path.dirname(output_path)):
        return False

    target = open(output_path, 'w')
    target.write(yamlize(data))
    target.close()
