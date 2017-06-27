import ipaddress
import json
import base58
import re

from plenum.common.constants import DOMAIN_LEDGER_ID, POOL_LEDGER_ID
from abc import ABCMeta, abstractmethod


class FieldValidator(metaclass=ABCMeta):
    """"
    Interface for field validators
    """

    @abstractmethod
    def validate(self, val):
        """
        Validates field value
        
        :param val: field value to validate 
        :return: error message or None
        """


class FieldBase(FieldValidator, metaclass=ABCMeta):
    """
    Base class for field validators
    """

    _base_types = ()

    def __init__(self, optional=False, nullable=False):
        self.optional = optional
        self.nullable = nullable

    def validate(self, val):
        """
        Performs basic validation of field value and then passes it for 
        specific validation.
        
        :param val: field value to validate 
        :return: error message or None
        """

        if self.nullable and val is None:
            return
        type_er = self.__type_check(val)
        if type_er:
            return type_er

        spec_err = self._specific_validation(val)
        if spec_err:
            return spec_err

    @abstractmethod
    def _specific_validation(self, val):
        """
        Performs specific validation of field. Should be implemented in 
        subclasses. Use it instead of overriding 'validate'.
        
        :param val: field value to validate 
        :return: error message or None 
        """

    def __type_check(self, val):
        if self._base_types is None:
            return  # type check is disabled
        for t in self._base_types:
            if isinstance(val, t):
                return
        return self._wrong_type_msg(val)

    def _wrong_type_msg(self, val):
        types_str = ', '.join(map(lambda x: x.__name__, self._base_types))
        return "expected types '{}', got '{}'" \
               "".format(types_str, type(val).__name__)


class BooleanField(FieldBase):
    _base_types = (bool,)

    def _specific_validation(self, val):
        return


class NonEmptyStringField(FieldBase):
    _base_types = (str,)

    def _specific_validation(self, val):
        if not val:
            return 'empty string'


class SignatureField(FieldBase):
    _base_types = (str, type(None))
    # TODO do nothing because EmptySignature should be raised somehow

    def _specific_validation(self, val):
        return


class RoleField(FieldBase):
    _base_types = (str, type(None))
    # TODO implement

    def _specific_validation(self, val):
        return


class NonNegativeNumberField(FieldBase):

    _base_types = (int,)

    def _specific_validation(self, val):
        if val < 0:
            return 'negative value'


class ConstantField(FieldBase):
    _base_types = None

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def _specific_validation(self, val):
        if val != self.value:
            return 'has to be equal {}'.format(self.value)


class IterableField(FieldBase):

    _base_types = (list, tuple)

    def __init__(self, inner_field_type: FieldValidator, **kwargs):
        assert inner_field_type
        assert isinstance(inner_field_type, FieldValidator)

        self.inner_field_type = inner_field_type
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        for v in val:
            check_er = self.inner_field_type.validate(v)
            if check_er:
                return check_er


class MapField(FieldBase):
    _base_types = (dict, )

    def __init__(self, key_field: FieldBase, value_field: FieldBase,
                 **kwargs):
        super().__init__(**kwargs)
        self._key_field = key_field
        self._value_field = value_field

    def _specific_validation(self, val):
        for k, v in val.items():
            key_error = self._key_field.validate(k)
            if key_error:
                return key_error
            val_error = self._value_field.validate(v)
            if val_error:
                return val_error


class NetworkPortField(FieldBase):
    _base_types = (int,)

    def _specific_validation(self, val):
        if val < 0 or val > 65535:
            return 'network port out of the range 0-65535'


class NetworkIpAddressField(FieldBase):
    _base_types = (str,)
    _non_valid_addresses = ('0.0.0.0', '0:0:0:0:0:0:0:0', '::')

    def _specific_validation(self, val):
        invalid_address = False
        try:
            ipaddress.ip_address(val)
        except ValueError:
            invalid_address = True
        if invalid_address or val in self._non_valid_addresses:
            return 'invalid network ip address ({})'.format(val)


class ChooseField(FieldBase):
    _base_types = None

    def __init__(self, values, **kwargs):
        self._possible_values = values
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        if val not in self._possible_values:
            return "expected one of '{}', unknown value '{}'" \
                   .format(', '.join(map(str, self._possible_values)), val)


class LedgerIdField(ChooseField):
    _base_types = (int,)
    ledger_ids = (POOL_LEDGER_ID, DOMAIN_LEDGER_ID)

    def __init__(self, **kwargs):
        super().__init__(self.ledger_ids, **kwargs)


class Base58Field(FieldBase):
    _base_types = (str,)

    def __init__(self, byte_lengths=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._alphabet = set(base58.alphabet)
        self.byte_lengths = byte_lengths

    def _specific_validation(self, val):
        invalid_chars = set(val) - self._alphabet
        if invalid_chars:
            # only 10 chars to shorten the output
            to_print = sorted(invalid_chars)[:10]
            return 'should not contains the following chars {}{}' \
                .format(to_print,
                        ' (truncated)' if len(to_print) < len(invalid_chars) else '')
        if self.byte_lengths is not None:
            # TODO could impact performace, need to check 
            b58len = len(base58.b58decode(val))
            if b58len not in self.byte_lengths:
                return 'b58 decoded value length {} should be one of {}' \
                    .format(b58len, list(self.byte_lengths))


class IdentifierField(Base58Field):
    _base_types = (str, )

    def __init__(self, *args, **kwargs):
        # TODO the tests in client are failing because the field
        # can be short and long both. It is can be an error.
        # We have to double check the type of the field.
        super().__init__(byte_lengths=(16, 32), *args, **kwargs)


class DestNodeField(Base58Field):
    _base_types = (str,)

    def __init__(self, *args, **kwargs):
        # TODO the tests in client are failing because the field
        # can be short and long both. It is can be an error.
        # We have to double check the type of the field.
        super().__init__(byte_lengths=(16, 32), *args, **kwargs)


class DestNymField(Base58Field):
    _base_types = (str, )

    def __init__(self, *args, **kwargs):
        # TODO the tests in client are failing because the field
        # can be short and long both. It is can be an error.
        # We have to double check the type of the field.
        super().__init__(byte_lengths=(16, 32), *args, **kwargs)


class RequestIdentifierField(FieldBase):
    _base_types = (list, tuple)
    _length = 2

    def _specific_validation(self, val):
        if len(val) != self._length:
            return "should have length {}".format(self._length)
        idr_error = IdentifierField().validate(val[0])
        if idr_error:
            return idr_error
        ts_error = NonNegativeNumberField().validate(val[1])
        if ts_error:
            return ts_error


class TieAmongField(FieldBase):
    _base_types = (list, tuple)
    _length = 2

    def _specific_validation(self, val):
        if len(val) != self._length:
            return "should have length {}".format(self._length)
        idr_error = NonEmptyStringField().validate(val[0])
        if idr_error:
            return idr_error
        ts_error = NonNegativeNumberField().validate(val[1])
        if ts_error:
            return ts_error


class VerkeyField(FieldBase):
    _base_types = (str, )
    _b58abbreviated = Base58Field(byte_lengths=(16,))
    _b58full = Base58Field(byte_lengths=(32,) )

    def _specific_validation(self, val):
        if val.startswith('~'):
            #abbreviated base58
            return self._b58abbreviated.validate(val[1:])
        #full base58
        return self._b58full.validate(val)


class HexField(FieldBase):
    _base_types = (str, )

    def __init__(self, length=None, **kwargs):
        super().__init__(**kwargs)
        self._length = length

    def _specific_validation(self, val):
        try:
            int(val, 16)
        except ValueError:
            return "invalid hex number '{}'".format(val)
        if self._length is not None and len(val) != self._length:
            return "length should be {} length".format(self._length)


class MerkleRootField(Base58Field):
    _base_types = (str, )

    def __init__(self, *args, **kwargs):
        super().__init__(byte_lengths=(32,), *args, **kwargs)


class TimestampField(FieldBase):
    _base_types = (float, int)

    def _specific_validation(self, val):
        normal_val = val
        if isinstance(val, int):
            # This is needed because timestamp is usually multiplied
            # by 1000 to "make it compatible to JavaScript Date()"
            normal_val /= 1000
        if normal_val <= 0:
            return 'should be a positive number but was {}'.format(val)


class JsonField(FieldBase):
    _base_types = (str,)

    def _specific_validation(self, val):
        # TODO: Need a mechanism to ensure a non-empty JSON if needed
        try:
            json.loads(val)
        except json.decoder.JSONDecodeError:
            return 'should be a valid JSON string'


class SerializedValueField(FieldBase):
    _base_types = (bytes, str)

    def _specific_validation(self, val):
        if not val:
            return 'empty serialized value'


class TxnSeqNoField(FieldBase):

    _base_types = (int,)

    def _specific_validation(self, val):
        if val < 1:
            return 'cannot be smaller than 1'


class Sha256HexField(FieldBase):
    """
    Validates a sha-256 hash specified in hex
    """
    _base_types = (str,)
    regex = re.compile('^[A-Fa-f0-9]{64}$')

    def _specific_validation(self, val):
        if self.regex.match(val) is None:
            return 'not a valid hash (needs to be in hex too)'