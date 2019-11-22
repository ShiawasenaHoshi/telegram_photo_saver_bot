import hashlib
import os


def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return hasher.hexdigest() if ashexstr else hasher.digest()


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


def calc_hash(file_path):
    return hash_bytestr_iter(file_as_blockiter(open(file_path, 'rb')), hashlib.sha256())[:16]


def create_yd_folder_if_not_exist(folder, ya_disk):
    if not ya_disk.exists(folder):
        try:
            ya_disk.mkdir(folder)
        except BaseException as e:
            pass


def create_folder_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)
