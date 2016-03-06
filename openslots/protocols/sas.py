"""Implement IGT's Slot Accounting System protocol"""


from collections import namedtuple, Counter


___SAS_version___ = 602     # SAS version 6.02


## Supported meters ##


# List of tuples: (id, size, name, description)
# Used to initialize SASGame instance

_602_meters = [
    (0x00, 4, 'coin_in', 'Total coin in credits'),
    (0x01, 4, 'coin_out', 'Total coin out credits'),
]


## Useful functions ##


def crc(b, seed=0):
    """Compute 16-bit CRC from bytes or sequence of ints, returns bytes"""
    for x in b:
        q = (seed ^ x) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
        q = (seed ^ (x >> 4)) & 0o17
        seed = (seed >> 4) ^ (q * 0o10201)
    return seed.to_bytes(2, byteorder='little')


def int_to_bcd(i, length=0):
    if i < 0 or not isinstance(i, int):
        raise ValueError("`i` must be a positive integer or 0")

    if length < 0 or not isinstance(length, int):
        raise ValueError("`length` must be a positive integer or 0")

    return int(str(i), 16).to_bytes(length, 'big')


def bcd_to_int(x):
    if not isinstance(x, bytes):
        raise ValueError("`x` must be bytes object")

    s = ''
    for i in x:
        s += format(i, 'x')

    return int(s, 16)


## Class definitions ##


class SASMeter(object):
    """An SASMeter stores a value and contains methods useful for SAS clients. The value can only either be incremented
    by some value or cleared (reset to zero). It also stores the digit length that will be used when converting to BCD
    in response to SAS polls. Lastly, it can easily be converted to BCD for responding to SAS polls by simply calling
    bytes() on it.
    """

    def __init__(self, i, size=4):
        self.id = int(i)
        self.__len__ = lambda: int(size)
        self._value = 0
        self._name = ''
        self.description = ''

    @property
    def name(self):
        """Short description of this meter, truncated to 50 chars"""
        return self._name

    @name.setter
    def name(self, s):
        self._name = s[:50]

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, n):
        self._value = n if n > self._value else self._value

    @value.deleter
    def value(self):
        self._value = 0

    def clear(self):
        del self.value

    def __repr__(self):
        return "<SASMeter {:#06x} {}, value {}>".format(self.id, self.name, str(self))

    def __str__(self):
        return str(self.value).rjust(self.__len__() * 2, '0')

    def __bytes__(self):
        return int_to_bcd(self.value, self.__len__())

    def __iadd__(self, n):
        self.value += n if n > 0 else 0
        return self

    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)


class SASGame(object):
    def __init__(self, meters=_602_meters):
        self._v_id = 0
        self._v_seq = 0

        self._meters = meters
        self.meters = dict()
        for m in meters:
            this_m = SASMeter(m[0], m[1])
            this_m.name = m[2].lstrip('_')
            this_m.description = m[3]

            setattr(self, this_m.name, this_m)
            self.meters[this_m.name] = this_m

    def SE_validation_number(self):
        """Generate secure-enhanced ticket validation number from seed
        values. Returns string representing the 18-digit validation
        number.
        """
        
        # TODO move to v_id and v_seq assignment from host
        # if 0 > self._v_id >= 2**24:
        #    raise ValueError("Validation ID too large, %i" % self._v_id)
        # if 0 > self._v_seq >= 2**24:
        #    raise ValueError("Validation sequence too large, %i" % self._v_seq)
        
        a = [x for x in self._v_seq.to_bytes(3, byteorder='little')]
        a += [x for x in self._v_id.to_bytes(3, byteorder='little')]
        
        b = [0] * 6
        b[5] = a[5] ^ a[1]
        b[4] = a[4] ^ a[0]
        b[3] = a[3] ^ a[1]
        b[2] = a[2] ^ a[0]
        b[1] = a[1]
        b[0] = a[0]
        
        c = crc(b[:2])
        c += crc(b[2:4])
        c += crc(b[4:])
        
        n = [0, 0]
        
        for i, v in enumerate(c[3:]):
            n[0] += v << (i * 8)
            
        for i, v in enumerate(c[:3]):
            n[1] += v << (i * 8)
            
        v = [int(x) for x in '%08i%08i' % tuple(n)]
        v.reverse()
        v[7] |= (sum(v[:8]) % 5) << 1
        v[15] |= (sum(v[8:]) % 5) << 1
        v.reverse()
        
        return '00' + ''.join([str(x) for x in v])


class SASHost(object):
    pass
