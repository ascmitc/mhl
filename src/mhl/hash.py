from src.util import logger
import xattr
import tempfile
import hashlib
import xxhash
import subprocess

def create_filehash(filepath, hashformat, write_xattr = False):
    """creates a hash value for a file and returns the hex string

    arguments:
    filepath -- string value, the path to the file
    hashformat -- string value, one of the supported hash formats, e.g. 'MD5', 'xxhash'
    write_xattr -- bool value, write the created hash into the xattr of the the filesystem for that file
    """
    hash_string = None
    if hashformat == 'MD5':
        hash_string = md5(filepath)
    elif hashformat == 'SHA1':
        hash_string = sha1(filepath)
    elif hashformat == 'xxhash':
        hash_string = xxhash64(filepath)
    elif hashformat == 'C4':
        hash_string = c4(filepath)
    else:
        logger.error(f'unsupported hash format {hashformat}')

    if write_xattr:
        if hash_string is not None:
            try:
                xattr.setxattr(filepath, "com.theasc.asc-mhl." + hashformat, hash_string.encode('utf8'))
            except IOError:
                logger.error(f'couldnt set xattr for {filepath}, errno {IOError}')

    return hash_string


# TODO: change this to just use the internal hashlib and avoid writing out to file entirely
#  for reference on how to do this... https://github.com/ImagineProducts/hive/blob/dev/cli/cli/src/seal.py
def create_datahash(data, hashformat):
    """creates a hash value for a data blob and returns the hex string

    arguments:
    data -- binary data
    hashformat -- string value, one of the supported hash formats, e.g. 'MD5', 'xxhash'
    """
    file = tempfile.NamedTemporaryFile(delete=False)
    file.write(data)
    file.close()

    filehash = create_filehash(file.name, hashformat, False)
    return filehash


def generate_checksum(csum_type, file_path):
    """
    generate a checksum for the hashlib checksum type.
    :param csum_type: the hashlib compliant checksum type
    :param file_path: the absolute path to the resource being hashed
    :return: hexdigest of the checksum
    """
    csum = csum_type()
    with open(file_path, 'rb') as fd:
        # process files in 1MB chunks so that large files won't cause excessive memory consumption.
        chunk = fd.read(1024 * 1024)
        while chunk:
            csum.update(chunk)
            chunk = fd.read(1024 * 1024)
    return csum.hexdigest()


def md5(file_path):
    return generate_checksum(hashlib.md5, file_path)


def sha1(file_path):
    return generate_checksum(hashlib.sha1, file_path)


def xxhash64(file_path):
    return generate_checksum(xxhash.xxh64, file_path)


def c4(file_path):
    sha512_string = generate_checksum(hashlib.sha512, file_path)

    charset = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    base58 = 58         # the encoding basis
    c4id_length = 90    # the guaranteed length
    zero = '1'          # '0' is not in the C4ID alphabet so '1' is zero

    hash_value = int(sha512_string, 16)
    c4_string = ""
    while hash_value is not 0:
        modulo = hash_value % base58
        hash_value = hash_value // base58
        c4_string = charset[modulo] + c4_string

    c4_string = "c4" + c4_string.ljust(c4id_length - 2, zero)
    return c4_string

def sign_hash(hash_string, private_key_filepath):
    """ create a base64-encoded signature for hash value

    :param hash_string:             the has to sign    # FIXME: sign the hash data or the hash string?
    :param private_key_filepath:    path to PEM file with private key
    :return:
    """

    temp_hash_file = tempfile.NamedTemporaryFile('w+', delete=False)
    temp_hash_file.write(hash_string)
    temp_hash_file.close()

    temp_sig_file = tempfile.NamedTemporaryFile(delete=False)

    # $ openssl rsautl -sign -inkey mykey.pem -keyform PEM -in self.hash_string > sig.dat
    # $ base64 -i sig.dat -o sig.base64.txt

    result_string = subprocess.check_output(['openssl',
                                             'rsautl', '-sign',
                                             '-inkey', private_key_filepath,
                                             '-keyform', 'PEM',
                                             '-in', temp_hash_file.name,
                                             '-out', temp_sig_file.name], encoding="utf-8")
    # TODO check for errors

    result_string = subprocess.check_output(['base64',
                                             '-i', temp_sig_file.name], encoding="utf-8")
    # TODO check for errors

    return result_string


def check_signature(signature_string, public_key_filepath):

    temp_sig_file = tempfile.NamedTemporaryFile('w+', delete=False)
    temp_sig_file.write(signature_string)
    temp_sig_file.close()

    temp_sig_data_file = tempfile.NamedTemporaryFile(delete=False)

    # verifying (only shows the hash that was signed)
    # $ base64 -D -i sig.base64.txt -o sig.dat
    # $ openssl rsautl -verify -inkey pubkey.pem -pubin -keyform PEM -in sig.dat

    result_string = subprocess.check_output(['base64', '-D',
                                             '-i', temp_sig_file.name,
                                             '-o', temp_sig_data_file.name], encoding="utf-8")
    # TODO check for errors

    result_string = subprocess.check_output(['openssl',
                                             'rsautl', '-verify',
                                             '-inkey', public_key_filepath,
                                             '-pubin',
                                             '-keyform', 'PEM',
                                             '-in', temp_sig_data_file.name], encoding="utf-8")
    # TODO check for errors

    return result_string

